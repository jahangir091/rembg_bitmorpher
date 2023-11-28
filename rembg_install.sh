#!/usr/bin/env bash
#################################################
# Please do not make any changes to this file,  #
# change the variables in webui-user.sh instead #
#################################################


add-apt-repository ppa:deadsnakes/ppa
apt update
apt upgrade
apt install python3.10-venv
apt install htop
apt install git
git clone https://github.com/jahangir091/rembgtest.git
cd rembgtest
python3.10 -m venv env_rembg
source env_rembg/bin/activate
pip install rembg
pip install piexif
pip install opencv-python
pip install fastapi
pip install "uvicorn[standard]"
uvicorn main:app --host 0.0.0.0 --port 80
