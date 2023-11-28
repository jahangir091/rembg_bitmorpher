#!/usr/bin/env bash
#################################################
# Please do not make any changes to this file,  #
# change the variables in webui-user.sh instead #
#################################################


add-apt-repository ppa:deadsnakes/ppa
apt update -y
apt upgrade -y
apt install python3.10-venv -y
apt install htop -y
apt install git -y
apt install python3-venv libgl1 libglib2.0-0 -y
git clone https://github.com/jahangir091/rembgtest.git
cd rembgtest
python3.10 -m venv env_rembg
source env_rembg/bin/activate
pip install rembg
pip install piexif
pip install opencv-python
pip install fastapi
pip install "uvicorn[standard]" gunicorn



#uvicorn main:app --host 0.0.0.0 --port 8001 --reload
gunicorn main:app --workers "$1" --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:"$2"
