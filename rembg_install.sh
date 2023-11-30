#!/usr/bin/env bash
#################################################
# Please do not make any changes to this file,  #
# change the variables in webui-user.sh instead #
#################################################


prepare_installation(){
  add-apt-repository ppa:deadsnakes/ppa
  apt update -y
  apt upgrade -y
  apt install python3.10-venv -y
  apt install htop -y
  apt install git -y
  apt install nginx -y
  apt install python3-venv libgl1 libglib2.0-0 -y
  git clone https://github.com/jahangir091/rembgtest.git
  cd rembgtest
  python3.10 -m venv env_rembg
  source env_rembg/bin/activate
  pip install -r requirements.txt

  cp rembg.service /etc/systemd/system/
  service rembg start

  cp rembg.cong /etc/nginx/sites-available/
  ln -s /etc/nginx/sites-available/rembg.conf /etc/nginx/sites-enabled/
  service nginx start
}

start_rembg(){
  cd rembgtest
  git fetch
  git reset --hard origin/main
  service rembg restart
}


install="install"
start="start"

if [ "$1" == "$start" ]
then
  start_rembg
elif [ "$1" == "$install" ]
then
  prepare_installation
  start_rembg
else
  printf "\n\n expected flags 'install' or 'start' \n\n"
fi
#uvicorn main:app --host 0.0.0.0 --port 8001 --reload
#gunicorn main:app --workers "$1" --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:"$2"
