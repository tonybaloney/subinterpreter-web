"""
Testing on CPython3.13b1+

Requires some recent patches from main.
pip install hypercorn

Have successfully run the following apps:
- fastapi==0.99.0
- Flask
"""

from time import sleep, time
import _interpreters as interpreters
import _interpchannels as channels
import threading
from hypercorn.config import Config, Sockets
from hypercorn.utils import check_for_updates, files_to_watch, load_application
from socket import dup
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


WORKERS = os.cpu_count() or 2

"""
    This function is started inside the subinterpreter.

    Shared globals:
    - worker_number: int
    - workers: int
    - channel_id: int
    - insecure_sockets: tuple of tuples
    - application_path: str
    - reload: bool
    - log_level: int
"""

worker_init = open('interpreter_worker.py', 'r').read()

worker_run = """
logging.debug("Starting asyncio worker in worker {}".format({worker_number}))
try:
    asyncio_worker(config, hypercorn_sockets, shutdown_event=shutdown_event)
except Exception as e:
    logging.exception(e)
logging.debug("asyncio worker finished in worker {}".format({worker_number}))
"""


class SubinterpreterWorker(threading.Thread):

    def __init__(
        self,
        number: int,
        config: Config,
        sockets: Sockets,
        reload: bool = False,
        log_level: int = logging.INFO,
    ):
        self.worker_number = number
        self.interp = interpreters.create()
        self.channel = channels.create()
        self.config = config  # TODO copy other parameters from config
        self.sockets = sockets
        self.use_reloader = reload
        self.log_level = log_level
        super().__init__(target=self.run, daemon=True)

    def run(self):
        # Convert insecure sockets to a tuple of tuples because the Sockets type cannot be shared
        insecure_sockets = [(int(s.family), int(s.type), s.proto, dup(s.fileno())) for s in self.sockets.insecure_sockets]
        logger.debug("Starting worker {}, interpreter {}".format(self.worker_number, self.interp))
        interpreters.run_string(
            self.interp,
            worker_init,
            shared={
                "worker_number": self.worker_number,
                "insecure_sockets": tuple(insecure_sockets),
                "application_path": self.config.application_path,
                "workers": self.config.workers,
                "channel_id": self.channel,
                "reload": self.use_reloader,
                "log_level": self.log_level,
            },
        )
        logger.debug("Initialized worker {}, interpreter {}. Launching asyncio_worker".format(self.worker_number, self.interp))
        interpreters.run_string(self.interp, worker_run)
        logger.debug("Worker {}, interpreter {} finished".format(self.worker_number, self.interp))

    def is_alive(self) -> bool:
        return interpreters.is_running(self.interp) and super().is_alive()

    def request_stop(self):
        logger.info("Sending stop signal to worker {}, interpreter {}".format(self.worker_number, self.interp))
        channels.send(self.channel, "stop", blocking=False)

    def stop(self, timeout: float = 5.0):
        if self.is_alive():
            # wait to stop
            start = time()
            while self.is_alive():
                if time() - start > timeout:
                    logger.warning("Worker {}, interpreter {} did not stop in time".format(self.worker_number, self.interp))
                    break
                sleep(0.1)
        else:
            logger.debug("Worker {}, interpreter {} already stopped".format(self.worker_number, self.interp))

    def destroy(self):
        if interpreters.is_running(self.interp):
            raise ValueError("Cannot destroy a running interpreter")
        interpreters.destroy(self.interp)

def fill_pool(threads, config, min_workers, sockets):
    for i in range(min_workers - len(threads)):
        t = SubinterpreterWorker(
            i, config, sockets, reload=args.reload, log_level=logger.level
        )
        t.start()
        threads.append(t)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "application",
        help="The application to dispatch to as path.to.module:instance.path",
    )
    parser.add_argument(
        "-w",
        "--workers",
        dest="workers",
        help="The number of workers to spawn and use, defaults to the number of CPUs",
        default=WORKERS,
        type=int,
    )
    parser.add_argument(
        "--reload",
        help="Reload the server on file changes",
        action="store_true",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Increase logging verbosity",
        action="store_true",
    )
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    config = Config()
    config.application_path = args.application
    config.workers = args.workers
    sockets = config.create_sockets()
    logger.debug("Starting %s workers", args.workers)
    threads: list[SubinterpreterWorker] = []
    fill_pool(threads, config, args.workers, sockets)

    try:
        if args.reload:
            # Load the application so that the correct paths are checked for
            # changes, but only when the reloader is being used.
            load_application(config.application_path, config.wsgi_max_body_size)
            active = True

            while active:
                files = files_to_watch()
                logger.debug(f"Watching files for changes")

                # Fill thread pool to correct size of the number of interpreters
                fill_pool(threads, config, args.workers, sockets)

                while True:
                    updated = check_for_updates(files)
                    if updated:
                        logger.debug("Detected changes, reloading workers")

                        for t in threads:
                            t.request_stop()

                        for t in threads:
                            t.stop(timeout=3.0)
                            t.join()
                            # t.destroy() # see below
                        threads = []

                        sockets = config.create_sockets()
                        logger.debug("Finished reload cycle")
                        break
        else:
            for t in threads:
                t.join()
    except KeyboardInterrupt:
        logger.debug("Received keyboard interrupt, shutting down workers")
        for t in threads:
            t.request_stop()
        for t in threads:
            t.stop()
            # t.destroy()

    # Todo: destroy interpreters on recycle/reload
    # Bug: raises error about remaining sub interpreters after shutdown.
