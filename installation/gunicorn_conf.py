import os
from multiprocessing import cpu_count

# current directory path
dir_path = os.path.dirname(os.path.realpath(__name__))

# Socket path
bind = 'unix:{0}/gunicorn.sock'.format(dir_path)

# Worker Options
# workers = cpu_count() + 1
workers = 2
worker_class = 'uvicorn.workers.UvicornWorker'

# Logging Options
loglevel = 'debug'
accesslog = '/var/log/rembg/access.log'
errorlog = '/var/log/rembg/error.log'
