import boto3
from io import BytesIO

endpoint_url = "https://c052bacce8a2467f144adbeae654edc3.r2.cloudflarestorage.com"
access_key_id = "135a6fbad3ef9199cc017607e770baa1"
secret_key_id = "e8d21a533dbe410b7a8000060413dd8a7bd5e7dddd849b5a00254e04ddf6b01e"
token = "hUvJSevL5UBj5r8dFdtnj_4W-YZ0WSMnXaqFyMk2"
bucket_name = "ai-project-media-files"
public_url = "https://pub-288c4f7ae2ab4568ae80826ea3575a6b.r2.dev"

s3_client = boto3.client('s3',
  endpoint_url = endpoint_url,
  aws_access_key_id = access_key_id,
  aws_secret_access_key = secret_key_id
)

import io
import piexif
import piexif.helper

def r2_file_upload(file_path):
  with open(file_path, 'rb') as f:
    buf = BytesIO(f.read())
    file_name = file_path.split('/')[-1]
    s3_client.upload_fileobj(
      buf, bucket_name, file_name, ExtraArgs={"ACL": "public-read"}
    )


if __name__ == '__main__':
  object_information = s3_client.head_object(Bucket=bucket_name, Key ="test.jpg")
  print(object_information)

  file_name = "image.png"
  with open(file_name, 'rb') as f:
    buf = BytesIO(f.read())
    url = r2_file_upload(file_name)
    print(url)