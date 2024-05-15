from hypercorn.asyncio.run import asyncio_worker
from hypercorn.config import Config, Sockets
import asyncio
import threading
import _interpchannels as channels
import logging

logging.basicConfig(level=logging.INFO)
from socket import socket
import time
shutdown_event = asyncio.Event()

def wait_for_signal():
    while True:
        msg = channels.recv(channel_id, default=None)
        if msg == "stop":
            print("Received stop signal, shutting down {} ".format(worker_number))
            shutdown_event.set()
        else:
            time.sleep(1)

print("Starting hypercorn worker in subinterpreter {} ".format({worker_number}))
_insecure_sockets = []
# Rehydrate the sockets list from the tuple
for s in insecure_sockets:
    _insecure_sockets.append(socket(*s))
hypercorn_sockets = Sockets([], _insecure_sockets, [])

config = Config()
config.application_path = application_path
config.workers = workers
thread = threading.Thread(target=wait_for_signal)
thread.start()
asyncio_worker(config, hypercorn_sockets, shutdown_event=shutdown_event)