import lib.core.normals as normals
import os
import json
import time
import threading

def _caching():
    # Load Cache
    if os.path.exists(os.path.expanduser("~/.aspm_cache.json")):
        with open(os.path.expanduser("~/.aspm_cache.json"), "r") as f:
            try:
                normals._cache = json.load(f)
            except Exception as e:
                print(f"Fehler beim Laden des Caches: {e}")
                normals._cache = {}
    while True:
        if not hasattr(normals, "_cache"):
            normals._cache = {}
        time.sleep(10)
        # Write Cache to file:
        with open(os.path.expanduser("~/.aspm_cache.json"), "w") as f:
            json.dump(normals._cache, f)

def main():
    # Starte Caching-Thread
    cache_thread = threading.Thread(target=_caching, daemon=True)
    cache_thread.start()

