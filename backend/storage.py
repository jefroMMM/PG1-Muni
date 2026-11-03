"""Thread-safe JSON persistence with atomic replacement and isolated snapshots."""
import copy
import json
import os
import shutil
import tempfile
from threading import RLock


class ConfigStore:
    def __init__(self, get_path, get_default_path):
        self.get_path = get_path
        self.get_default_path = get_default_path
        self.lock = RLock()
        self._stamp = None
        self._cached = None

    def ensure_file(self):
        with self.lock:
            path = self.get_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                shutil.copyfile(self.get_default_path(), path)

    def _signature(self):
        path = self.get_path()
        info = path.stat()
        return (str(path.resolve()), info.st_mtime_ns, info.st_size, info.st_ino)

    def load(self):
        with self.lock:
            self.ensure_file()
            stamp = self._signature()
            if stamp != self._stamp:
                with self.get_path().open("r", encoding="utf-8") as source:
                    self._cached = json.load(source)
                self._stamp = stamp
            return copy.deepcopy(self._cached)

    def save(self, config):
        with self.lock:
            self.ensure_file()
            temporary_name = None
            try:
                with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=self.get_path().parent, delete=False) as target:
                    temporary_name = target.name
                    json.dump(config, target, ensure_ascii=False, indent=2, allow_nan=False)
                    target.write("\n")
                os.replace(temporary_name, self.get_path())
                self._cached = copy.deepcopy(config)
                self._stamp = self._signature()
            finally:
                if temporary_name and os.path.exists(temporary_name):
                    os.unlink(temporary_name)
