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


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.post("/ai/rembg")
async def rembg_remove(
    input_image: str = Body("", title='rembg input image'),
    model: str = Body("u2net", title='rembg model'),
    return_mask: bool = Body(False, title='return mask'),
    # alpha_matting: bool = Body(False, title='alpha matting'),
    # alpha_matting_foreground_threshold: int = Body(240, title='alpha matting foreground threshold'),
    # alpha_matting_background_threshold: int = Body(10, title='alpha matting background threshold'),
    # alpha_matting_erode_size: int = Body(10, title='alpha matting erode size')
):
    utc_time = datetime.now(timezone.utc)
    start_time = time.time()
    input_image = decode_base64_to_image(input_image)

    image = rembg.remove(
        input_image,
        session=rembg.new_session(model),
        only_mask=return_mask,
        # alpha_matting=alpha_matting,
        # alpha_matting_foreground_threshold=alpha_matting_foreground_threshold,
        # alpha_matting_background_threshold=alpha_matting_background_threshold,
        # alpha_matting_erode_size=alpha_matting_erode_size,
    )

    output_image = encode_pil_to_base64(image).decode("utf-8")

    print("time taken: {0}".format(time.time()-start_time))

    return {
        "server_hit_time": str(utc_time),
        "server_time": time.time()-start_time,
        "image": output_image
    }
