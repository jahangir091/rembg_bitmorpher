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
import logging.config

from fastapi import FastAPI, Body
import rembg
from fastapi.middleware.cors import CORSMiddleware
from time import gmtime, strftime


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
    model: int = Body(6, title='rembg model'),
    return_mask: bool = Body(True, title='return mask'),
    # alpha_mat: bool = Body(False, title='alpha matting'),
    # alpha_mat_foreground_threshold: int = Body(240, title='alpha matting foreground threshold'),
    # alpha_mat_background_threshold: int = Body(10, title='alpha matting background threshold'),
    # alpha_mat_erode_size: int = Body(10, title='alpha matting erode size')
):
    utc_time = datetime.now(timezone.utc)
    start_time = time.time()
    print("time now: {0} ".format(strftime("%Y-%m-%d %H:%M:%S", gmtime())))
    input_image = decode_base64_to_image(input_image)
    model = model if model else 6
    image = rembg.remove(
        input_image,
        session=rembg.new_session(models[model]),
        only_mask=return_mask if return_mask else True,
        # alpha_matting=alpha_mat if alpha_mat else False,
        # alpha_matting_foreground_threshold=alpha_mat_foreground_threshold if alpha_mat_foreground_threshold else 240,
        # alpha_matting_background_threshold=alpha_mat_background_threshold if alpha_mat_background_threshold else 10,
        # alpha_matting_erode_size=alpha_mat_erode_size if alpha_mat_erode_size else 10,
    )

    output_image = encode_pil_to_base64(image).decode("utf-8")

    print("time taken: {0}".format(time.time()-start_time))

    return {
        "server_hit_time": str(utc_time),
        "server_process_time": time.time()-start_time,
        "output_image": output_image
    }
