import os
import multiprocessing

# Configuration Gunicorn pour la production
bind = "0.0.0.0:8050"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "immoaanalytics"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL (à configurer pour la production)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Preload app for performance
preload_app = True

# Environment variables
raw_env = [
    "FLASK_ENV=production",
    "PYTHONPATH=/app"
]

# Server hooks
def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

# Application
def app():
    from app.main import server
    return server