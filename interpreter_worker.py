from hypercorn.asyncio.run import asyncio_worker
from hypercorn.config import Config, Sockets
import asyncio
import threading
import _interpchannels as channels
from socket import socket
from rich.logging import RichHandler
import interpreter_cache
import time
import logging
from typing import Any

# Variables from host interpreter
log_level: int
worker_number: int
channel_id: int
cache_channel_id: int
insecure_sockets: tuple[tuple[int, int, Any, int], ...]
application_path: str
workers: int
reload: bool

logging.basicConfig(level=log_level, format=f"[{worker_number}] %(message)s", handlers=[RichHandler()])
logger = logging.getLogger(__name__)
shutdown_event = asyncio.Event()
shutdown_event.clear()

interpreter_cache.cache = interpreter_cache.InterpreterCache(cache_channel_id)

def wait_for_signal():
    while True:
        msg = channels.recv(channel_id, default=None)
        if msg == "stop":
            logging.info("Received stop signal, shutting down")
            shutdown_event.set()
        else:
            time.sleep(0.1)

logging.info("Starting hypercorn worker")
try:
    _insecure_sockets = []
    # Rehydrate the sockets list from the tuple
    for s in insecure_sockets:
        _insecure_sockets.append(socket(*s))
    hypercorn_sockets = Sockets([], _insecure_sockets, [])

    config = Config()
    config.application_path = application_path
    config.workers = workers
    config.use_reloader = reload  # Doesn't really do anything here
    config.debug = log_level == logging.DEBUG
    config.accesslog = logger
    thread = threading.Thread(target=wait_for_signal)
    thread.start()
except Exception as e:
    logging.exception(e)

logging.debug("Starting asyncio worker")
try:
    asyncio_worker(config, hypercorn_sockets, shutdown_event=shutdown_event)
except Exception as e:
    logging.exception(e)
logging.debug("asyncio worker finished")