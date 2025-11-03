# gunicorn.conf.py
timeout = 180  # 3 minutes to allow Gemini uploads
workers = 1
threads = 2
bind = "0.0.0.0:80"