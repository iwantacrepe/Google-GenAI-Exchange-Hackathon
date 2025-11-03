# gunicorn.conf.py
timeout = 800 
workers = 1
threads = 2
bind = "0.0.0.0:80"