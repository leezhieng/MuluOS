"""MuluOS registry client library.

In-bundle code typically uses the module-level helpers, which talk to the
daemon over the inherited socket fd set up by the launcher:

    import muluos_registry as reg
    reg.set("theme.dark", True, type="bool")
    if reg.get("theme.dark"):
        ...

For machine-scope access or administrative use (installer, CLI), construct
a Client directly:

    client = muluos_registry.Client.connect_direct()
    client.register_bundle("com.example.foo", "/opt/bundles/Foo.exe")
    client.machine_set("com.example.foo", "version", "1.0.0")
"""
from __future__ import annotations
import json
import os
import socket
import struct
from typing import Any

SOCKET_PATH = "/run/muluos/registry.sock"
ENV_FD = "MULUOS_REGISTRY_FD"


class RegistryError(Exception):
    """Daemon returned an error response."""


class NotBoundError(RegistryError):
    """No inherited fd; this process wasn't launched as a bundle."""


class Client:
    def __init__(self, sock: socket.socket):
        self._sock = sock
        self._lock_recv = b""

    @classmethod
    def from_fd(cls, fd: int | None = None) -> "Client":
        if fd is None:
            raw = os.environ.get(ENV_FD)
            if raw is None:
                raise NotBoundError(
                    f"{ENV_FD} not set; this process was not launched as a bundle"
                )
            fd = int(raw)
        sock = socket.socket(fileno=os.dup(fd))
        return cls(sock)

    @classmethod
    def connect_direct(cls, path: str = SOCKET_PATH) -> "Client":
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(path)
        return cls(sock)

    def close(self) -> None:
        try:
            self._sock.close()
        except OSError:
            pass

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *a) -> None:
        self.close()

    def _call(self, **req: Any) -> dict:
        body = json.dumps(req, separators=(",", ":")).encode("utf-8")
        self._sock.sendall(struct.pack(">I", len(body)) + body)
        hdr = self._recv_n(4)
        (n,) = struct.unpack(">I", hdr)
        resp = json.loads(self._recv_n(n))
        if not resp.get("ok"):
            raise RegistryError(resp.get("error", "unknown error"))
        return resp

    def _recv_n(self, n: int) -> bytes:
        buf = bytearray()
        while len(buf) < n:
            chunk = self._sock.recv(n - len(buf))
            if not chunk:
                raise RegistryError("connection closed by daemon")
            buf.extend(chunk)
        return bytes(buf)

    # ---- User scope (needs inherited fd) ----
    def get(self, key: str, default: Any = None) -> Any:
        r = self._call(op="get", scope="user", key=key)
        return r["value"] if r.get("found") else default

    def set(self, key: str, value: Any, type: str = "string") -> None:
        self._call(op="set", scope="user", key=key, value=value, type=type)

    def delete(self, key: str) -> bool:
        return self._call(op="delete", scope="user", key=key)["deleted"] > 0

    def list(self, prefix: str = "") -> list[dict]:
        return self._call(op="list", scope="user", prefix=prefix)["keys"]

    # ---- Machine scope ----
    def machine_get(self, bundle: str, key: str, default: Any = None) -> Any:
        r = self._call(op="get", scope="machine", bundle=bundle, key=key)
        return r["value"] if r.get("found") else default

    def machine_set(self, bundle: str, key: str, value: Any, type: str = "string") -> None:
        self._call(op="set", scope="machine", bundle=bundle, key=key, value=value, type=type)

    def machine_delete(self, bundle: str, key: str) -> bool:
        return self._call(op="delete", scope="machine", bundle=bundle, key=key)["deleted"] > 0

    def machine_list(self, bundle: str, prefix: str = "") -> list[dict]:
        return self._call(op="list", scope="machine", bundle=bundle, prefix=prefix)["keys"]

    # ---- Bundle registry (root only) ----
    def register_bundle(self, id: str, path: str) -> str:
        return self._call(op="register_bundle", id=id, path=path)["path"]

    def unregister_bundle(self, id: str, purge: bool = False) -> None:
        self._call(op="unregister_bundle", id=id, purge=purge)

    def list_bundles(self) -> list[dict]:
        return self._call(op="list_bundles")["bundles"]

    def ping(self) -> dict:
        return self._call(op="ping")


# Module-level convenience: lazy client built from the inherited fd.
_default: Client | None = None


def _c() -> Client:
    global _default
    if _default is None:
        _default = Client.from_fd()
    return _default


def get(key: str, default: Any = None) -> Any:
    return _c().get(key, default)


def set(key: str, value: Any, type: str = "string") -> None:  # noqa: A001 (intentional shadow)
    _c().set(key, value, type)


def delete(key: str) -> bool:
    return _c().delete(key)


def list(prefix: str = "") -> "list[dict]":  # noqa: A001
    return _c().list(prefix)
