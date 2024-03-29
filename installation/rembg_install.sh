#!/usr/bin/env bash
#################################################
# Please do not make any changes to this file,  #
# change the variables in webui-user.sh instead #
#################################################


prepare_installation(){
  add-apt-repository ppa:deadsnakes/ppa -y
  apt update -y
  apt upgrade -y
  apt install python3.10-venv -y
  apt install htop vim -y
  apt install git -y
  apt purge nginx nginx-common
  apt autoremove -y
  apt install nginx -y
  apt install python3-venv libgl1 libglib2.0-0 -y
  cd /home/
  git clone https://github.com/jahangir091/rembg_bitmorpher.git
  cd
  cd /home/rembg_bitmorpher
  python3.10 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt

  rm -rf /var/log/rembg
  mkdir /var/log/rembg
  mkdir /run/rembg
  touch /var/log/rembg/access.log
  touch /var/log/rembg/error.log
  chmod 777 -R /var/log/rembg

  cd
  cd /home/rembg_bitmorpher/installation
  rm -rf /etc/systemd/system/rembg.service
  cp rembg.service /etc/systemd/system/
  systemctl daemon-reload
  systemctl start rembg
  systemctl enable rembg
  systemctl restart rembg

  rm -rf /etc/nginx/sites-available/rembg.conf
  rm -rf /etc/nginx/sites-enabled/rembg.conf
  cp rembg_ngix.conf /etc/nginx/sites-available/
  ln -s /etc/nginx/sites-available/rembg_ngix.conf /etc/nginx/sites-enabled/
  service nginx start
  service rembg restart
  service nginx restart
}

start_rembg(){
  cd
  cd /home/rembg_bitmorpher
  service rembg restart
  service nginx restart
}

update_rembg(){
  cd
  cd /home/
  git clone https://github.com/jahangir091/rembg_bitmorpher.git
  cd rembg_bitmorpher
  git fetch
  git reset --hard origin/main
}


install="install"
start="start"
update="update"


if [ "$1" == "$start" ]
then
  start_rembg
elif [ "$1" == "$install" ]
then
  prepare_installation
  start_rembg
elif [ "$1" == "$update" ]
then
  update_rembg
else
  printf "\n\n expected flags 'install' or 'start' or 'update'\n\n"
fi
#uvicorn main:app --host 0.0.0.0 --port 8001 --reload
#gunicorn main:app --workers "$1" --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:"$2"
