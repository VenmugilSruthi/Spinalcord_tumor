# gunicorn_config.py
import multiprocessing

# Server socket
bind = "0.0.0.0:10000"  # Render provides the port via the PORT env var, but this is a good default

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gthread"
threads = 2
timeout = 120
