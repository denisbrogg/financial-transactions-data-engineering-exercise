"""
storage_pkg/base.py
-------------------
Abstract storage interface.

The unit of exchange is `bytes`.  Callers are responsible for serialisation
(e.g. wrapping with io.BytesIO before handing to pandas / DuckDB).

    buf = storage.open_read("bronze/raw.csv")
    df  = pd.read_csv(buf)

    with storage.open_write("silver/clean.parquet") as f:
        df.to_parquet(f)
"""

from __future__ import annotations

import io
from abc import ABC, abstractmethod


class Storage(ABC):
    """Read/write bytes to an addressable location (path, key, URI …)."""

    # ------------------------------------------------------------------
    # Source API
    # ------------------------------------------------------------------

    @abstractmethod
    def read(self, path: str) -> bytes:
        """Return the raw bytes stored at *path*."""

    def open_read(self, path: str) -> io.BytesIO:
        """Wrap :meth:`read` in a seekable, file-like :class:`io.BytesIO`."""
        return io.BytesIO(self.read(path))

    # ------------------------------------------------------------------
    # Sink API
    # ------------------------------------------------------------------

    @abstractmethod
    def write(self, path: str, data: bytes) -> None:
        """Persist *data* at *path*, creating parent directories as needed."""

    def open_write(self, path: str) -> _WritableBuffer:
        """
        Return a writable file-like object whose bytes are flushed to
        storage on ``.close()`` / context-manager exit.
        """
        return _WritableBuffer(self, path)

    # ------------------------------------------------------------------
    # Introspection API
    # ------------------------------------------------------------------

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Return ``True`` if *path* holds data."""

    @abstractmethod
    def delete(self, path: str) -> None:
        """Remove *path*.  No-op if it does not exist."""

    @abstractmethod
    def list(self, prefix: str = "") -> list[str]:
        """Return all paths that start with *prefix*, relative to the root."""


class _WritableBuffer(io.BytesIO):
    """
    A :class:`io.BytesIO` that flushes its contents back to *storage* when
    closed.  Obtained via :meth:`Storage.open_write`.
    """

    def __init__(self, storage: Storage, path: str) -> None:
        super().__init__()
        self._storage = storage
        self._path = path
        self._flushed = False

    # Override close so the flush happens exactly once (guards against the
    # BytesIO superclass calling close internally on __exit__).
    def close(self) -> None:
        if not self._flushed:
            self._storage.write(self._path, self.getvalue())
            self._flushed = True
        super().close()

    def __exit__(self, *args) -> None:
        self.close()
