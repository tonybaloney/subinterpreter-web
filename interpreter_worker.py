from hypercorn.asyncio.run import asyncio_worker  # type: ignore
from hypercorn.config import Config, Sockets
import asyncio
import threading
import _interpchannels as channels
from socket import socket
import time
import logging

logging.basicConfig(level=log_level)

shutdown_event = asyncio.Event()
shutdown_event.clear()

def wait_for_signal():
    while True:
        msg = channels.recv(channel_id, default=None)
        if msg == "stop":
            logging.info("Received stop signal, shutting down worker {} ".format(worker_number))
            shutdown_event.set()
        else:
            time.sleep(0.1)

logging.info("Starting hypercorn worker {}".format({worker_number}))
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
    thread = threading.Thread(target=wait_for_signal)
    thread.start()
except Exception as e:
    logging.exception(e)
