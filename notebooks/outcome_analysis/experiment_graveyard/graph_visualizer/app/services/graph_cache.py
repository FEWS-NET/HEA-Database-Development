from __future__ import annotations
from typing import Any, Dict, Tuple, Optional
from collections import OrderedDict
import threading
import time
import os

class _LRUCache:
    def __init__(self, max_items: int = 32, ttl_sec: int = 0):
        self.max_items = max_items
        self.ttl = ttl_sec
        self.lock = threading.Lock()
        self.store: "OrderedDict[Tuple[Any, ...], Tuple[float, Any]]" = OrderedDict()

    def get(self, key: Tuple[Any, ...]) -> Optional[Any]:
        with self.lock:
            if key not in self.store:
                return None
            ts, value = self.store[key]
            if self.ttl and (time.time() - ts > self.ttl):
                # expired
                del self.store[key]
                return None
            # bump LRU
            self.store.move_to_end(key, last=True)
            return value

    def set(self, key: Tuple[Any, ...], value: Any) -> None:
        with self.lock:
            self.store[key] = (time.time(), value)
            self.store.move_to_end(key, last=True)
            while len(self.store) > self.max_items:
                self.store.popitem(last=False)

    def clear(self) -> None:
        with self.lock:
            self.store.clear()

    def stats(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "items": len(self.store),
                "max_items": self.max_items,
                "ttl_sec": self.ttl,
                "keys_preview": list(self.store.keys())[-5:],
            }

class GraphCache:
    """
    Caches built graphs (NetworkX DiGraph + start_node + positions + motif meta)
    per (workbook identity, sheet, cell, options...).
    """
    def __init__(self, max_items: int = 32, ttl_sec: int = 0):
        self.lru = _LRUCache(max_items=max_items, ttl_sec=ttl_sec)

    @staticmethod
    def _workbook_identity(path: str) -> Tuple[str, float, int]:
        """Return a tuple that changes when the file changes."""
        try:
            st = os.stat(path)
            return (os.path.abspath(path), st.st_mtime, st.st_size)
        except FileNotFoundError:
            # identity still includes path so cache won't collide
            return (os.path.abspath(path), 0.0, -1)

    def make_key(
        self,
        path: str,
        sheet: str,
        cell: str,
        *,
        collapse_motifs: bool,
        motif_scope: str,
        motif_min: int,
    ) -> Tuple:
        wid = self._workbook_identity(path)
        return (
            wid, sheet, cell.upper(),
            ("motifs", collapse_motifs, motif_scope, int(motif_min)),
        )

    def get(self, key: Tuple) -> Optional[dict]:
        return self.lru.get(key)

    def set(self, key: Tuple, bundle: dict) -> None:
        self.lru.set(key, bundle)

    def clear(self) -> None:
        self.lru.clear()

    def stats(self) -> Dict[str, any]:
        return self.lru.stats()
