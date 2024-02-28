import time
from PIL import Image
from io import BytesIO
import base64
import io
import piexif
import piexif.helper
from datetime import datetime, timezone
import uvicorn
import logging.config
import os, uuid

from fastapi import FastAPI, Body
import rembg
from fastapi.middleware.cors import CORSMiddleware
from time import gmtime, strftime
# from api_analytics.fastapi import Analytics


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
# app.add_middleware(Analytics, api_key="00e0893b-82af-440c-af58-5de94649a57c")
# Check the link below for the fast api analytics
# https://pypi.org/project/fastapi-analytics/


def get_img_path(directory_name):
    current_dir = '/tmp'
    img_directory = current_dir + '/.temp' + directory_name
    os.makedirs(img_directory, exist_ok=True)
    img_file_name = uuid.uuid4().hex[:20] + '.jpg'
    return img_directory + img_file_name


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

@app.post("/ai/api/v1/remove_bg")
async def remove_image_background(
    image: str = Body("", title='rembg input image'),
    model: int = Body(6, title='rembg model, not required, default to 6'),
    return_mask: bool = Body(True, title='return mask, not required, default True'),
    post_process_mask: bool = Body(False, title='post process mask for a smooth boundary '
                                                'by applying Morphological Operations, not required, default False')
):
    if not image:
        return{
            "success": False,
            "message": "Input image not found",
            "server_process_time": '',
            "output_image_url": ''
        }
    utc_time = datetime.now(timezone.utc)
    start_time = time.time()
    print("time now: {0} ".format(strftime("%Y-%m-%d %H:%M:%S", gmtime())))
    input_image = decode_base64_to_image(image)
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

    # output_image = encode_pil_to_base64(image).decode("utf-8")
    out_images_directory_name = '/rembg_images/'
    out_image_path = get_img_path(out_images_directory_name)
    image.save(out_image_path)

    print("time taken: {0}".format(time.time()-start_time))

    return {
        "success": True,
        "message": "Returned output successfully",
        "server_process_time": time.time()-start_time,
        "output_image": 'media' + out_images_directory_name + out_image_path.split('/')[-1]
    }


@app.get("/ai/api/v1/rembg-server-test")
async def rembg_server_test():

    return {
        "success": True,
        "message": "Server is OK."
    }


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
