# MuluOS registry

A Windows-registry-shaped key/value store backed by SQLite, mediated by a
daemon. Bundles cannot read or write each other's data — every read or
write is scoped to the bundle identity that the launcher established at
process start.

## Pieces

| Piece | Path | What it does |
|---|---|---|
| Daemon | `/usr/libexec/muluos/registryd` | Listens on a Unix socket, owns the SQLite database |
| Database | `/var/lib/muluos/registry.sqlite` | WAL-mode SQLite, mode 0600 (root only) |
| Socket | `/run/muluos/registry.sock` | World-connectable; authorization is per-op |
| OpenRC service | `/etc/init.d/muluos-registryd` | Starts the daemon at boot |
| Client lib | `/usr/lib/muluos/muluos_registry.py` | `import muluos_registry` in any bundle |
| Low-level CLI | `/usr/bin/muluos-reg` | Machine-scope reads/writes, bundle (un)registration |
| Install CLI | `/usr/bin/muluos-bundle` | High-level install — registers a bundle and creates its app-menu entry |

## Identity model

Every session has at most one bound bundle identity. The bind happens
exactly once, at the moment the launcher hands the socket to the bundle
binary. After that, the daemon refuses re-binding.

**Identity is derived from the bundle's filesystem path, not from
`Info.json`'s `id` field.** A bundle's id is whatever the `bundles` table
maps its `install_path` to. Only root can write that table, so a malicious
user who crafts a bundle with `Info.json: {"id": "com.firefox.real"}` and
plants it somewhere they control will not get firefox's identity — they
get an anonymous `local:<sha256-of-path>` identity instead.

The trusted launcher is the only process the daemon will accept a `bind`
op from. The daemon checks the peer's `/proc/<pid>/exe` is a python
interpreter and `argv[1]` is exactly `/usr/libexec/muluos/launch-bundle`.

> **Known limitation.** This check is bypassable by anything that can
> exec `python3 /usr/libexec/muluos/launch-bundle` (i.e., the legitimate
> launch path) — but doing so just launches a bundle normally; it does
> not yield an escalation because identity comes from the filesystem
> path. A future hardening step is to compile the launcher to a small C
> binary so `/proc/<pid>/exe` alone is authoritative.

## Scopes

| Scope | Read | Write |
|---|---|---|
| `user` | the bound bundle, for the caller's uid | the bound bundle, for the caller's uid |
| `machine` | anyone (bundle-scoped) | root only (installer) |

User-scope ops require an inherited fd (no fd → `not bound` error). The
fd is opened by the launcher and dup'd to fd 3 (CLOEXEC cleared) before
exec; the env var `MULUOS_REGISTRY_FD` advertises this to the client lib.

Machine-scope reads are gated by bundle id, so a bundle can still read
its own machine-scope keys without having root. Machine-scope writes
need root because the only legitimate writer is the installer.

## Wire protocol

Length-prefixed JSON over a `SOCK_STREAM` Unix socket. Each frame:

```
[4-byte big-endian length][N bytes UTF-8 JSON]
```

Requests:

| op | params | who |
|---|---|---|
| `bind` | `{path}` | launcher only |
| `get` | `{scope, key, [bundle]}` | any (after bind for user-scope) |
| `set` | `{scope, key, value, type, [bundle]}` | bound for user, root for machine |
| `delete` | `{scope, key, [bundle]}` | same as set |
| `list` | `{scope, prefix, [bundle]}` | same as get |
| `register_bundle` | `{id, path}` | root |
| `unregister_bundle` | `{id, purge}` | root |
| `list_bundles` | — | any |
| `ping` | — | any |

Responses:

- Success: `{"ok": true, ...}` with op-specific extras
- Failure: `{"ok": false, "error": "<message>"}`

Value types: `string`, `int`, `bool`, `json`, `blob` (base64 over the wire).

## Client library

In-bundle code:

```python
import muluos_registry as reg

reg.set("theme.dark", True, type="bool")
reg.set("recent.files", ["a.txt", "b.txt"], type="json")
print(reg.get("theme.dark"))           # True
for row in reg.list("recent."):
    print(row["key"], row["type"])
```

If the process wasn't launched as a bundle, the first call raises
`muluos_registry.NotBoundError`.

For installers and admin tools (machine scope, bundle registration):

```python
from muluos_registry import Client

with Client.connect_direct() as c:
    c.register_bundle("com.example.foo", "/opt/bundles/Foo.exe")
    c.machine_set("com.example.foo", "version", "1.0.0")
    print(c.machine_get("com.example.foo", "version"))
```

## CLI

Low-level access, mainly for the package installer and debugging:

```sh
muluos-reg register-bundle com.example.foo /opt/bundles/Foo.exe
muluos-reg set --bundle com.example.foo version 1.0.0
muluos-reg get --bundle com.example.foo version
muluos-reg list --bundle com.example.foo
muluos-reg list-bundles
muluos-reg unregister-bundle com.example.foo --purge
```

High-level install/uninstall (what a package manager calls):

```sh
muluos-bundle install /opt/bundles/Foo.exe              # registers + makes app-menu entry
muluos-bundle install /opt/bundles/Foo.exe --prewarm    # also warms thumbnail cache
muluos-bundle uninstall com.example.foo --purge         # remove everything
muluos-bundle prewarm-thumbnails /opt/bundles/Foo.exe   # just thumbnails, no install
```

## Well-known keys

Some keys have system-wide meaning and are read by core components at
fixed points. Admins set these via `muluos-reg set --bundle system ...`
(machine-scope writes require root).

| Bundle id | Key | Type | Read by | Purpose |
|---|---|---|---|---|
| `system` | `library_paths` | string | bundle launcher | Colon-separated extra `LD_LIBRARY_PATH` entries spliced in between bundle libs and the system loader cache. See [bundles.md](bundles.md#library-search-order). |

Add new well-known keys here when they're introduced, so app authors
know which names are reserved.

## Threat model summary

- **Bundle A reads Bundle B's user-scope data**: blocked. A's session is
  pinned to A's bundle id at bind; the daemon never lets A name B as a
  target.
- **User process forges a bundle identity**: blocked by root-only writes
  to the `bundles` table. Unregistered paths get an anonymous `local:*`
  id that cannot collide with a registered one.
- **Non-launcher process tries to bind**: refused via the `/proc` check.
- **Malicious app exfiltrates its own data**: not in scope. The user can
  always see their own data; the daemon enforces app↔app isolation, not
  user↔app.
- **Local root attacker**: not in scope. Root can rewrite the DB, the
  launcher, and the daemon binary.
