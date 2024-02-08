import sys
import platform

import numpy as np
import torch
from PIL import Image
from tqdm import tqdm

from upscalers import modelloader
from swinir_model_arch import SwinIR
from swinir_model_arch_v2 import Swin2SR
from upscaler import Upscaler, UpscalerData

SWINIR_MODEL_URL = "https://github.com/JingyunLiang/SwinIR/releases/download/v0.0/003_realSR_BSRGAN_DFOWMFC_s64w8_SwinIR-L_x4_GAN.pth"

device_swinir = torch.device('cpu')


class UpscalerSwinIR(Upscaler):
    def __init__(self, dirname):
        self._cached_model = None           # keep the model when SWIN_torch_compile is on to prevent re-compile every runs
        self._cached_model_config = None    # to clear '_cached_model' when changing model (v1/v2) or settings
        self.name = "SwinIR"
        self.model_url = SWINIR_MODEL_URL
        self.model_name = "SwinIR 4x"
        self.user_path = dirname
        super().__init__()
        scalers = []
        model_files = self.find_swinir_models(self.name, ext_filter=[".pt", ".pth"])
        for model in model_files:
            if model.startswith("http"):
                name = self.model_name
            else:
                name = modelloader.friendly_name(model)
            model_data = UpscalerData(name, model, self)
            scalers.append(model_data)
        self.scalers = scalers

    def do_upscale(self, img, model_file):
        current_config = (model_file, 192)


        self._cached_model = None
        try:
            model = self.load_model(model_file)
        except Exception as e:
            print(f"Failed loading SwinIR model {model_file}: {e}", file=sys.stderr)
            return img
        model = model.to(device_swinir, dtype=torch.float16)
        img = upscale(img, model)
        devices.torch_gc()
        return img

    def load_model(self, path, scale=4):
        if path.startswith("http"):
            filename = modelloader.load_file_from_url(
                url=path,
                model_dir=self.model_download_path,
                file_name=f"{self.model_name.replace(' ', '_')}.pth",
            )
        else:
            filename = path
        if filename.endswith(".v2.pth"):
            model = Swin2SR(
                upscale=scale,
                in_chans=3,
                img_size=64,
                window_size=8,
                img_range=1.0,
                depths=[6, 6, 6, 6, 6, 6],
                embed_dim=180,
                num_heads=[6, 6, 6, 6, 6, 6],
                mlp_ratio=2,
                upsampler="nearest+conv",
                resi_connection="1conv",
            )
            params = None
        else:
            model = SwinIR(
                upscale=scale,
                in_chans=3,
                img_size=64,
                window_size=8,
                img_range=1.0,
                depths=[6, 6, 6, 6, 6, 6, 6, 6, 6],
                embed_dim=240,
                num_heads=[8, 8, 8, 8, 8, 8, 8, 8, 8],
                mlp_ratio=2,
                upsampler="nearest+conv",
                resi_connection="3conv",
            )
            params = "params_ema"

        pretrained_model = torch.load(filename)
        if params is not None:
            model.load_state_dict(pretrained_model[params], strict=True)
        else:
            model.load_state_dict(pretrained_model, strict=True)
        return model


def upscale(
        img,
        model,
        tile=None,
        tile_overlap=None,
        window_size=8,
        scale=4,
):
    tile = tile or opts.SWIN_tile
    tile_overlap = tile_overlap or opts.SWIN_tile_overlap


    img = np.array(img)
    img = img[:, :, ::-1]
    img = np.moveaxis(img, 2, 0) / 255
    img = torch.from_numpy(img).float()
    img = img.unsqueeze(0).to(device_swinir, dtype=devices.dtype)
    with torch.no_grad(), devices.autocast():
        _, _, h_old, w_old = img.size()
        h_pad = (h_old // window_size + 1) * window_size - h_old
        w_pad = (w_old // window_size + 1) * window_size - w_old
        img = torch.cat([img, torch.flip(img, [2])], 2)[:, :, : h_old + h_pad, :]
        img = torch.cat([img, torch.flip(img, [3])], 3)[:, :, :, : w_old + w_pad]
        output = inference(img, model, tile, tile_overlap, window_size, scale)
        output = output[..., : h_old * scale, : w_old * scale]
        output = output.data.squeeze().float().cpu().clamp_(0, 1).numpy()
        if output.ndim == 3:
            output = np.transpose(
                output[[2, 1, 0], :, :], (1, 2, 0)
            )  # CHW-RGB to HCW-BGR
        output = (output * 255.0).round().astype(np.uint8)  # float32 to uint8
        return Image.fromarray(output, "RGB")


def inference(img, model, tile, tile_overlap, window_size, scale):
    # test the image tile by tile
    b, c, h, w = img.size()
    tile = min(tile, h, w)
    assert tile % window_size == 0, "tile size should be a multiple of window_size"
    sf = scale

    stride = tile - tile_overlap
    h_idx_list = list(range(0, h - tile, stride)) + [h - tile]
    w_idx_list = list(range(0, w - tile, stride)) + [w - tile]
    E = torch.zeros(b, c, h * sf, w * sf, dtype=devices.dtype, device=device_swinir).type_as(img)
    W = torch.zeros_like(E, dtype=devices.dtype, device=device_swinir)
    output = E.div_(W)

    return output

