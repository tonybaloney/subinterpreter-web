import threading
import test.support.interpreters.channels as channels
from typing import Any
import logging

type SetEntryMsg = tuple[str, bytes]
type RecvMsg = tuple[str, int, Any]


class InterpreterCache:
    cache: dict[str, memoryview]

    def __init__(self, cache_channel_id: int, logger: logging.Logger):
        self.cache = {}
        self.cache_channel_id = cache_channel_id
        logger.debug("Creating cache with channel id %s", cache_channel_id)
        self.send_channel = channels.SendChannel(cache_channel_id)
        self.recv_channel = channels.RecvChannel(cache_channel_id)
        self.logger = logger

    def set(self, key: str, value: str):
        self.logger.debug("Setting cache entry %s", key)
        self.send_channel.send(("set_entry", self.cache_channel_id, (key, value.encode("utf-8"))))
        # TODO : RECV new memory view?

    def get(self, key: str) -> str | None:
        if key in self.cache:
            return self.cache[key].tobytes().decode("utf-8")
        else:
            # Try fetch cache record
            self.send_channel.send(("get_entry", self.cache_channel_id, key), timeout=1.0)
            v = self.recv_channel.recv()
            if v:
                self.cache[key] = v
                return v.tobytes().decode("utf-8")
            else:
                return None

    def reset(self):
        self.cache = {}


class MainInterpreterCachePoller(threading.Thread):
    cache: dict[str, memoryview]

    def __init__(self, logger: logging.Logger):
        self.cache = {}
        self.recv_channel, _ = channels.create()
        self.cache_channel_id = self.recv_channel.id
        logger.debug("Creating cache poller with channel id %s", self.cache_channel_id)
        self.logger = logger
        super().__init__(target=self.run, daemon=True)
    
    def run(self):
        self.logger.debug("Starting cache poller on channel %s", self.cache_channel_id)
        self.running = True
        while self.running:
            v = self.recv_channel.recv_nowait(default=None)
            if v:
                msg: RecvMsg = v
                if msg[0] == "get_entry":
                    send_channel = channels.SendChannel(msg[1])
                    if msg[2] in self.cache:
                        send_channel.send(self.cache[msg[2]], timeout=5.0)
                    else:
                        send_channel.send(None, timeout=5.0)
                elif msg[0] == "set_entry":
                    key, value = msg[2]
                    self.cache[key] = memoryview(value)
                elif msg[0] == "reset":
                    self.cache = {}
                else:
                    raise ValueError("Unknown message type")

cache: InterpreterCache = None