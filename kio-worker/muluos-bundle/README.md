# muluos-bundle KIO worker (scaffold)

This is a starting point for a KIO 6 worker that makes `.exe` bundle
directories appear as a single opaque item in Dolphin — like macOS `.app`
bundles. It does **not** yet do that; the class skeleton and build system
are wired up, but the bodies of `stat()` / `listDir()` / `mimetype()`
are placeholders that return `ERR_UNSUPPORTED_ACTION`.

## Why this is needed

The shared MIME database lets us label a directory as
`application/x-muluos-bundle`, and the freedesktop thumbnailer gives each
bundle its own icon. But Dolphin's directory navigation is driven by the
`S_IFDIR` mode bit, not by MIME — so double-clicking a `.exe` directory
still descends into it. To make the bundle look like an opaque file we
need to intercept KIO's listing/stat calls and report the bundle as a
regular file with the bundle MIME type.

## What this scaffold gives you

- A KIO 6 worker target (`muluosbundle`) built against `KF6::KIOCore`.
- The `.protocol` file that registers the worker (currently as a custom
  protocol; you may want to change `protClass` and how it binds to MIME).
- A class derived from `KIO::WorkerBase` with the right entry points
  stubbed out and the `kdemain` factory in place.
- Inline `TODO` notes in [src/muluosbundleworker.cpp](src/muluosbundleworker.cpp)
  explaining what each method should do.

## Two implementation strategies

There are two ways to go from here, and the choice changes how the rest
of the worker is written:

**(A) Custom URL scheme** — register `bundle://`, list installed bundles
under that scheme by querying the registry daemon. Pro: clean, no
interference with `file://`. Con: doesn't change how a `.exe` directory
behaves when browsed via `file://`.

**(B) Replace file:// behavior for `application/x-muluos-bundle`** — set
the worker as the handler for that MIME via `.protocol`'s `defaultMimetype`,
and report `.exe` entries from `stat()` / `listDir()` with `S_IFREG` so
Dolphin treats them as opaque files. The "Show Bundle Contents" action
(already in the existing servicemenu) bypasses this worker by calling
`dolphin <path>` directly, so users can still descend on demand.

The scaffold leans toward (B); see the long comment at the top of the
`.cpp` for the decision matrix.

## Build

You need a Plasma 6 development environment:

```sh
sudo apk add extra-cmake-modules kf6-kio-dev qt6-qtbase-dev cmake make g++
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
sudo make install
```

After install, restart the user session (or run `kbuildsycoca6 --noincremental`)
so KIO discovers the new worker.

## Testing

```sh
kioclient6 ls bundle:/                    # strategy A
kioclient6 stat file:///opt/bundles/Foo.exe  # strategy B (once stat is implemented)
```

## Status

| Method      | Status |
|-------------|--------|
| `stat`      | stub — needs UDSEntry construction |
| `listDir`   | stub — needs directory enumeration |
| `get`       | unsupported (intentional) |
| `mimetype`  | stub |

A merge-able implementation will probably take a few hundred lines of
C++ and a session on a running Plasma 6 desktop to iterate against
Dolphin's actual behaviour.
