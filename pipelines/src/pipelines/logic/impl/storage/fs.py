"""
storage_pkg/fs.py
-----------------
Filesystem-backed storage via ``fsspec``.

``fsspec`` provides a uniform API over dozens of backends:

    Protocol    Backend              Extra install
    --------    -------------------  -----------------------
    (none)      local filesystem     (built-in)
    file://     local filesystem     (built-in)
    memory://   fsspec MemoryFS      (built-in)
    s3://       AWS S3               pip install s3fs
    gs://       Google Cloud Storage pip install gcsfs
    az://       Azure Blob Storage   pip install adlfs
    abfs://     Azure Data Lake      pip install adlfs
    ftp://      FTP                  (built-in)
    ssh://      SFTP                 pip install paramiko

Usage::

    # Local — root-relative paths
    store = FSStorage("/data/etops")
    store.write("bronze/raw.csv", csv_bytes)

    # S3 — bucket is the root, paths are object keys
    store = FSStorage("s3://my-bucket/etops", storage_options={"key": ..., "secret": ...})
    store.write("bronze/raw.csv", csv_bytes)

    # GCS
    store = FSStorage("gs://my-bucket/etops")

All *path* arguments passed to :class:`Storage` methods are joined onto the
root URI, so callers never need to know which backend is in use.
"""

from __future__ import annotations

from pathlib import PurePosixPath

import fsspec

from pipelines.logic.abstractions.storage import Storage


class FSStorage(Storage):
    """
    :class:`Storage` implementation backed by any ``fsspec``-compatible
    filesystem.

    Parameters
    ----------
    root:
        A local path (``/data/etops``) or a URI (``s3://bucket/prefix``).
        All relative *path* arguments are joined onto this root.
    storage_options:
        Keyword arguments forwarded to :func:`fsspec.url_to_fs` / the
        underlying filesystem constructor (credentials, region, etc.).
    """

    def __init__(
        self,
        root: str,
        storage_options: dict | None = None,
    ) -> None:
        opts = storage_options or {}
        self._fs, self._root = fsspec.url_to_fs(root, **opts)
        # Normalise: strip trailing slash so joins are consistent
        self._root = self._root.rstrip("/")

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _full(self, path: str) -> str:
        """Return the absolute filesystem path for a storage-relative *path*."""
        # PurePosixPath handles forward-slash joining on all platforms
        return str(PurePosixPath(self._root) / path)

    # ------------------------------------------------------------------
    # Storage interface
    # ------------------------------------------------------------------

    def read(self, path: str) -> bytes:
        with self._fs.open(self._full(path), "rb") as f:
            return f.read()

    def write(self, path: str, data: bytes) -> str:
        full = self._full(path)
        # Create parent directories (local fs needs this; cloud fs ignores it)
        parent = str(PurePosixPath(full).parent)
        self._fs.makedirs(parent, exist_ok=True)
        with self._fs.open(full, "wb") as f:
            f.write(data)
        return full

    def exists(self, path: str) -> bool:
        return self._fs.exists(self._full(path))

    def delete(self, path: str) -> None:
        full = self._full(path)
        if self._fs.exists(full):
            self._fs.rm(full)

    def list(self, prefix: str = "") -> list[str]:
        search = self._full(prefix) if prefix else self._root
        if not self._fs.exists(search):
            return []
        # fsspec glob returns absolute paths; make them root-relative
        all_paths = self._fs.find(search)
        root_prefix = self._root.rstrip("/") + "/"
        return sorted(p.removeprefix(root_prefix) for p in all_paths)

    # ------------------------------------------------------------------
    # Extras
    # ------------------------------------------------------------------

    @property
    def protocol(self) -> str:
        """The fsspec protocol name (``'file'``, ``'s3'``, ``'gcs'`` …)."""
        proto = self._fs.protocol
        return proto[0] if isinstance(proto, tuple) else proto

    def __repr__(self) -> str:
        return f"FSStorage(root={self._root!r}, protocol={self.protocol!r})"
