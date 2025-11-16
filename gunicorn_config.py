"""
Gunicorn configuration file for production deployment
"""
import multiprocessing
import os

# Server socket
bind = f"127.0.0.1:{os.getenv('GUNICORN_PORT', '8000')}"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = os.getenv('GUNICORN_ACCESS_LOG', '-')  # '-' means stdout
errorlog = os.getenv('GUNICORN_ERROR_LOG', '-')  # '-' means stderr
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'the_project'

# Server mechanics
daemon = False
pidfile = os.getenv('GUNICORN_PIDFILE', None)
umask = 0
user = os.getenv('GUNICORN_USER', None)
group = os.getenv('GUNICORN_GROUP', None)
tmp_upload_dir = None

# SSL (if needed)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'

