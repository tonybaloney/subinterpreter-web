"""
Testing on CPython3.13b1+

Requires some recent patches from main.
pip install hypercorn

Have successfully run the following apps:
- fastapi==0.99.0
- Flask
"""
import _interpreters as interpreters
import _interpchannels as channels
import threading
from hypercorn.config import Config, Sockets

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


WORKERS = 2

"""
    This function is started inside the subinterpreter.

    Shared globals:
    - worker_number: int
    - workers: int
    - channel_id: int
    - insecure_sockets: tuple of tuples
    - application_path: str
"""

# Sub interpreters don't support cell vars yet, just convert this module
# into a string.
interpreter_worker = open('interpreter_worker.py', 'r').read()


class SubinterpreterWorker(threading.Thread):

    def __init__(self, number: int, config: Config, sockets: Sockets):
        self.worker_number = number
        self.interp = interpreters.create()
        self.channel = channels.create()
        self.config = config # TODO copy other parameters from config
        self.sockets = sockets
        super().__init__(target=self.run, daemon=True)

    def run(self):
        # Convert insecure sockets to a tuple of tuples because the Sockets type cannot be shared
        insecure_sockets = []
        for s in self.sockets.insecure_sockets:
            insecure_sockets.append((int(s.family), int(s.type), s.proto, s.fileno()))

        interpreters.run_string(
            self.interp,
            interpreter_worker,
            shared={
                'worker_number': self.worker_number,
                'insecure_sockets': tuple(insecure_sockets),
                'application_path': self.config.application_path,
                'workers': self.config.workers,
                'channel_id': self.channel,
            }
        )        

    def stop(self):
        logger.info("Sending stop signal to worker {}".format(self.worker_number))
        channels.send(self.channel, "stop")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "application", help="The application to dispatch to as path.to.module:instance.path"
    )
    parser.add_argument(
        "-w",
        "--workers",
        dest="workers",
        help="The number of workers to spawn and use",
        default=WORKERS,
        type=int,
    )
    args = parser.parse_args()

    config = Config()
    config.application_path = args.application
    config.workers = args.workers
    sockets = config.create_sockets()
    logger.info("Starting %s workers", args.workers)
    threads = []
    for i in range(args.workers):
        t = SubinterpreterWorker(i, config, sockets)
        t.start()
        threads.append(t)

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        for t in threads:
            t.stop()

    # Bug: raises error about remaining sub interpreters after shutdown.
