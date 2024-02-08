from typing import Union
import time
from PIL import Image
from io import BytesIO
import base64
import io
import piexif
import piexif.helper
from datetime import datetime, timezone
import logging
import uvicorn
import logging.config

from fastapi import FastAPI, Body
import rembg
from fastapi.middleware.cors import CORSMiddleware
from time import gmtime, strftime
from api_analytics.fastapi import Analytics


logger = logging.getLogger(__name__)

app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(Analytics, api_key="00e0893b-82af-440c-af58-5de94649a57c")
# Check the link below for the fast api analytics
# https://pypi.org/project/fastapi-analytics/


def decode_base64_to_image(img_string):
    img = Image.open(BytesIO(base64.b64decode(img_string)))
    return img


def encode_pil_to_base64(image):
    with io.BytesIO() as output_bytes:
        if image.mode == "RGBA":
            image = image.convert("RGB")
        parameters = image.info.get('parameters', None)
        exif_bytes = piexif.dump({
            "Exif": {piexif.ExifIFD.UserComment: piexif.helper.UserComment.dump(parameters or "",
                                                                                encoding="unicode")}
        })
        image.save(output_bytes, format="JPEG", exif=exif_bytes)
        bytes_data = output_bytes.getvalue()
    return base64.b64encode(bytes_data)


models = [
    "None",
    "u2net",
    "u2netp",
    "u2net_human_seg",
    "u2net_cloth_seg",
    "silueta",
    "isnet-general-use",
    "isnet-anime",
]

@app.post("/sdapi/ai/rembg")
async def rembg_remove(
    input_image: str = Body("", title='rembg input image'),
    model: int = Body(6, title='rembg model, not required, default to 6'),
    return_mask: bool = Body(True, title='return mask, not required, default True'),
    post_process_mask: bool = Body(False, title='post process mask for a smooth boundary '
                                                'by applying Morphological Operations, not required, default False')
):
    if not input_image:
        return{
            "success": False,
            "message": "Input image not found",
            "server_hit_time": '',
            "server_process_time": '',
            "output_image": ''
        }
    utc_time = datetime.now(timezone.utc)
    start_time = time.time()
    print("time now: {0} ".format(strftime("%Y-%m-%d %H:%M:%S", gmtime())))
    input_image = decode_base64_to_image(input_image)
    model = model if model else 6
    image = rembg.remove(
        input_image,
        session=rembg.new_session(models[model]),
        only_mask=return_mask if return_mask else True,
        post_process_mask=post_process_mask if post_process_mask else False
        # alpha_matting=alpha_mat if alpha_mat else False,
        # alpha_matting_foreground_threshold=alpha_mat_foreground_threshold if alpha_mat_foreground_threshold else 240,
        # alpha_matting_background_threshold=alpha_mat_background_threshold if alpha_mat_background_threshold else 10,
        # alpha_matting_erode_size=alpha_mat_erode_size if alpha_mat_erode_size else 10,
    )

    output_image = encode_pil_to_base64(image).decode("utf-8")

    print("time taken: {0}".format(time.time()-start_time))

    return {
        "success": True,
        "message": "Returned output successfully",
        "server_hit_time": str(utc_time),
        "server_process_time": time.time()-start_time,
        "output_image": output_image
    }


from upscalers.swinir_model import UpscalerSwinIR
LANCZOS = (Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)
import numpy as np
from upscalers import gfpgan_model, codeformer_model


def resize_upscaled_image(original_img, upscaled_img, scale):
    dest_w = int((original_img.width * scale) // 8 * 8)
    dest_h = int((original_img.height * scale) // 8 * 8)
    img = upscaled_img.resize((int(dest_w), int(dest_h)), resample=LANCZOS)
    return img


def apply_gfpgan(image, gfpgan_visibility):
    if gfpgan_visibility == 0:
        return image

    restored_img = gfpgan_model.gfpgan_fix_faces(np.array(image, dtype=np.uint8))
    res = Image.fromarray(restored_img)
    if gfpgan_visibility < 1.0:
        res = Image.blend(image, res, gfpgan_visibility)
    return res


def apply_codeformer(image, codeformer_visibility, codeformer_weight):
    if codeformer_visibility == 0:
        return image

    restored_img = codeformer_model.codeformer.restore(np.array(image, dtype=np.uint8), w=codeformer_weight)
    res = Image.fromarray(restored_img)

    if codeformer_visibility < 1.0:
        res = Image.blend(image, res, codeformer_visibility)
    return res


@app.post("/sdapi/ai/v1/upscale-custom")
def upscale_single_image_api(
    input_image: str = Body("", title='rembg input image')
):
    start_time = time.time()
    utc_time = datetime.now(timezone.utc)
    input_img = decode_base64_to_image(input_image)
    upscaler = UpscalerSwinIR('')
    upscaled_img = upscaler.do_upscale(input_img.convert("RGB"), '/home/sduser/stable-diffusion-webui/models/SwinIR/SwinIR')
    resized_image = resize_upscaled_image(input_img, upscaled_img, 2)
    gfpganed_image = apply_gfpgan(resized_image, 0.95)
    final_image = apply_codeformer(gfpganed_image, 0.75, 0.0)
    output_image = encode_pil_to_base64(final_image).decode("utf-8")
    end_time = time.time()
    server_process_time = end_time - start_time
    print('server process time: {0}'.format(server_process_time))
    return {
        "server_hit_time": str(utc_time),
        "server_time": str(server_process_time),
        "image": output_image
    }


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
