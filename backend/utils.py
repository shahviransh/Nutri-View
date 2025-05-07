import os
import signal

def shutdown_server():
    os.kill(os.getpid(), signal.SIGINT)

def clear_cache(cache):
    cache.clear()