import threading
import _interpchannels as channels
from typing import Any

type SetEntryMsg = tuple[str, bytes]
type RecvMsg = tuple[str, int, Any]


class InterpreterCache:
    cache: dict[str, memoryview]

    def __init__(self, cache_channel_id: int):
        self.cache = {}
        self.cache_channel_id = cache_channel_id

    def set(self, key: str, value: str):
        self.cache[key] = memoryview(value)
    
    def get(self, key: str) -> str | None:
        if key in self.cache:
            return self.cache[key].tobytes().decode("utf-8")
        else:
            # Try fetch cache record
            channels.send(self.cache_channel_id, ("get_entry", self.cache_channel_id, key))
            v = channels.recv(self.cache_channel_id, default=None)
            if v:
                self.cache[key] = v
                return v.tobytes().decode("utf-8")
            else:
                return None

    def reset(self):
        self.cache = {}


class MainInterpreterCachePoller(threading.Thread):
    cache: dict[str, memoryview]

    def __init__(self):
        self.cache = {}
        self.cache_channel_id = channels.create()
        super().__init__(target=self.run, daemon=True)
    
    def run(self):
        self.running = True
        while self.running:
            v = channels.recv(self.cache_channel_id, default=None)
            if v:
                msg: RecvMsg = v
                if msg[0] == "get_entry":
                    if msg[2] in self.cache:
                        channels.send(msg[1], self.cache[msg[2]])
                    else:
                        channels.send(msg[1], None)
                elif msg[0] == "set_entry":
                    key, value = msg[2]
                    self.cache[key] = memoryview(value)
                elif msg[0] == "reset":
                    self.cache = {}
                else:
                    raise ValueError("Unknown message type")

cache: InterpreterCache = None