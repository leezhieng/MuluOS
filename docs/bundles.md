# MuluOS `.exe` application bundles

MuluOS applications are distributed as **bundles**: directories with a
`.exe` suffix that the desktop treats as a single, opaque, launchable
object — similar to macOS `.app` bundles. Despite the extension, these
are *not* Windows PE executables. The name was picked to feel familiar
to end users who think of `.exe` as "the app".

## Layout

```
HelloWorld.exe/
├── Info.json              # required: bundle manifest
├── Contents/
│   ├── bin/
│   │   └── helloworld     # the executable referenced by Info.json:exec
│   └── lib/               # optional: bundled .so files, auto-added to LD_LIBRARY_PATH
└── Resources/
    ├── icons/
    │   ├── 16.png
    │   ├── 32.png
    │   ├── 64.png
    │   ├── 128.png
    │   ├── 256.png
    │   └── 512.png
    └── ...                # arbitrary assets the app can read via $MULUOS_BUNDLE_RESOURCES
```

The `Resources/icons/<N>.png` naming convention is what the thumbnailer
looks for. Provide several sizes so Dolphin and Plasma can pick the
closest one without ugly upscaling.

## `Info.json`

```json
{
  "id": "com.example.helloworld",
  "name": "Hello World",
  "version": "1.0.0",
  "exec": "Contents/bin/helloworld",
  "icon": "Resources/icons/512.png",
  "env": {
    "QT_QPA_PLATFORM": "wayland"
  }
}
```

| Field     | Required | Meaning |
|-----------|----------|---------|
| `id`      | no       | Reverse-DNS identifier. Exposed as `$MULUOS_BUNDLE_ID`. |
| `name`    | no       | Human-readable name (currently unused by the launcher). |
| `version` | no       | Exposed as `$MULUOS_BUNDLE_VERSION`. |
| `exec`    | **yes**  | Path to the entry-point binary, relative to the bundle root. Must resolve inside the bundle. |
| `icon`    | no       | Fallback icon path. The thumbnailer prefers `Resources/icons/<N>.png` matches first. |
| `env`     | no       | Extra environment variables to set before exec. |

## Runtime environment

Before exec, the launcher sets:

- `LD_LIBRARY_PATH` — composed in the order described in
  *[Library search order](#library-search-order)* below
- `MULUOS_BUNDLE` — absolute path of the bundle
- `MULUOS_BUNDLE_RESOURCES` — `<bundle>/Resources`
- `MULUOS_BUNDLE_ID`, `MULUOS_BUNDLE_VERSION`
- `MULUOS_REGISTRY_FD=3` — an open, pre-authenticated socket to the
  [registry daemon](registry.md). Use `import muluos_registry` and call
  `reg.get()` / `reg.set()`; access is automatically scoped to this
  bundle's identity.
- Working directory — the bundle root

Apps that need to find their own assets at runtime should read
`$MULUOS_BUNDLE_RESOURCES`, not assume any system path.

## Library search order

The dynamic linker (`ld.so`) resolves a `.so` against
`LD_LIBRARY_PATH` first (after legacy `DT_RPATH`), then
`DT_RUNPATH`, then `/etc/ld.so.cache`, then `/lib` and `/usr/lib`. The
launcher uses `LD_LIBRARY_PATH` to put four bundle/admin-controlled
search tiers ahead of the system defaults:

1. `<bundle>/Contents/lib` — the bundle's own bundled libraries
2. `<dir of the bundle's executable>` — siblings of the binary (e.g.
   `Contents/bin/`), so libs can sit next to their consumer
3. **Registry-provided system paths** — admin-managed; see below
4. Caller's inherited `LD_LIBRARY_PATH` (if any)
5. `/etc/ld.so.cache` + system defaults (`/lib`, `/usr/lib`)

The launcher reads tier 3 from machine-scope registry key
`system.library_paths` (bundle id `system`). This is the MuluOS analog
of Windows' `PATH` for libraries: any admin-installed shared library
collection (`/opt/sharedlibs/...`, `/opt/myapp/lib`, etc.) can be made
visible to every bundle by adding its directory to that key. The value
is a colon-separated string just like `LD_LIBRARY_PATH` itself:

```sh
sudo muluos-reg set --bundle system library_paths "/opt/sharedlibs:/opt/myapp/lib"
muluos-reg get --bundle system library_paths
```

Only root can write the key (machine-scope write requires uid 0); any
bundle can read it. The key is read on every launch, so changes take
effect for the next bundle that starts — no daemon restart needed.

### Build-time alternative

Apps that want to keep working even when run *outside* the launcher
(e.g. directly from a shell during development) should also bake the
search path into the binary at link time using `$ORIGIN`:

```sh
gcc -o myapp myapp.c -Wl,-rpath,'$ORIGIN/../lib:$ORIGIN'
```

This stamps `DT_RUNPATH` into the ELF, so even without
`LD_LIBRARY_PATH` set the binary still finds its sibling libs. Note
the single quotes — `$ORIGIN` must reach the linker literally.
`DT_RUNPATH` is searched *after* `LD_LIBRARY_PATH`, so it doesn't
conflict with the launcher's ordering.

## How the OS treats a `.exe` directory

1. **MIME detection** — `shared-mime-info` matches the directory against
   the rule in `/usr/share/mime/packages/muluos-bundle.xml`. The
   `<treemagic>` requires an `Info.json` file inside; the `<glob>`
   hints at the `.exe` extension. Directories without `Info.json` stay
   classified as `inode/directory`.
2. **Double-click** — the desktop resolves the MIME type to
   `/usr/share/applications/muluos-bundle.desktop`, which exec's
   `/usr/libexec/muluos/launch-bundle`.
3. **Icon** — the freedesktop thumbnailer at
   `/usr/share/thumbnailers/muluos-bundle.thumbnailer` runs
   `/usr/libexec/muluos/bundle-thumbnailer`, which copies/scales the
   bundle's own icon. Each bundle therefore shows its own icon in
   Dolphin, not a generic folder.
4. **Right-click** — the KIO service menu at
   `/usr/share/kio/servicemenus/muluos-bundle-actions.desktop` offers
   *Show Bundle Contents* (open as a regular folder in Dolphin),
   *Show Bundle Info*, and *Run Bundle*.

## Building a bundle

There's nothing magic about bundle creation — it's just a directory
tree. A minimal build script could:

```sh
mkdir -p HelloWorld.exe/Contents/bin HelloWorld.exe/Resources/icons
cp helloworld    HelloWorld.exe/Contents/bin/
cp icon-512.png  HelloWorld.exe/Resources/icons/512.png
cat > HelloWorld.exe/Info.json <<'EOF'
{ "id": "com.example.helloworld", "exec": "Contents/bin/helloworld" }
EOF
```

That's enough for Dolphin to recognize it as a MuluOS bundle once the
MIME database has been refreshed.

## Installing a bundle

A bare bundle in a user directory will display correctly (its own icon
via the thumbnailer, double-click runs it via the launcher) but will
not get an app-menu entry or have access to the registry's machine
scope until it is registered. The high-level installer is:

```sh
muluos-bundle install /opt/bundles/HelloWorld.exe
```

This does three things:

1. Calls the registry daemon's `register_bundle` (root only): binds the
   bundle's id to its filesystem path. After this, double-clicking the
   bundle gives the running process the registered id; without this,
   it gets an anonymous `local:<sha>` id.
2. Writes `/usr/share/applications/muluos-bundles/<id>.desktop` so the
   bundle appears in KRunner and the application menu, with its own
   icon (the largest `Resources/icons/<N>.png` available).
3. Refreshes the desktop database.

Pass `--prewarm` to also pre-populate the freedesktop thumbnail cache
for the current user, so file managers display the bundle icon
immediately on first view rather than computing it on demand. (The
on-demand thumbnailer always works regardless — this just removes the
brief flash of the generic folder icon.)

To remove a bundle:

```sh
muluos-bundle uninstall com.example.helloworld --purge
```

`--purge` also deletes all the bundle's stored registry data.

## Auto-thumbnailing on extraction

For bundles extracted from a `.zip` or copied into the user's home
manually, no install step is needed: the freedesktop thumbnailer
mechanism runs the [bundle-thumbnailer](../assets/bundle/usr/libexec/muluos/bundle-thumbnailer)
on demand the first time a file manager scans the directory, and the
result is cached at `~/.cache/thumbnails/{normal,large,...}/`. Every
later view (Dolphin, file pickers, the desktop) reuses the cache.

If you want eager generation (e.g., before showing the user a "your
download finished" notification), call:

```sh
muluos-bundle prewarm-thumbnails /path/to/Foo.exe
```

## Making bundles truly opaque (KIO worker)

The MIME type + thumbnailer makes bundles *look* like single items, but
Dolphin still descends into a `.exe` on double-click because its
directory navigation is driven by the `S_IFDIR` mode bit. A C++/Qt
KIO worker scaffold for closing this gap lives at
[`kio-worker/muluos-bundle/`](../kio-worker/muluos-bundle/) — it is a
starting point, not a working plugin yet. Until that's filled in, the
right-click "Show Bundle Contents" → opens-in-Dolphin action is the
intended escape hatch for descending into bundles.

## Package Creator utility

[`utils/package-creator/`](../utils/package-creator/) (`muluos-package-creator`)
is the GUI for producing bundles without hand-writing `Info.json`. The
build/icon/template logic lives in
[`builder.py`](../utils/package-creator/usr/lib/muluos/muluos_package_creator/builder.py);
the PyQt6 UI in
[`widget.py`](../utils/package-creator/usr/lib/muluos/muluos_package_creator/widget.py).

It collects:

- **Executable** — a *pre-compiled* binary you select (MuluOS does not build
  from source). Copied to `Contents/bin/`.
- **Dependencies** — shared libraries copied to `Contents/lib/`. The
  **Auto-detect (ldd)** button runs `ldd` on the executable and adds the
  resolved `.so` paths, excluding the loader and core libc family
  (`ld-*`, `libc`, `libm`, `libdl`, `libpthread`, `librt`, `libresolv`) so the
  bundle never ships a libc that fights the host loader.
- **Icon** — one source image, resized to every size in the sizes field
  (default `16,32,48,64,128,256,512`) → `Resources/icons/<n>.png` (uses Pillow).
- **Metadata** — id, name, version, comment, categories.
- **Environment variables** — written to `Info.json` `env`.

Outputs: **Build Bundle** writes `<Name>.exe/`; **Build Bundle + Installer**
also wraps it (see below). **Save/Load Template** persists the whole form as
JSON for repeatable builds.

### Auto-detect caveats

- `ldd` executes the binary's loader — only auto-detect on executables you
  trust. It is Linux-only, so the button is a no-op on a non-Linux dev host.
- Auto-detect is a starting point, not a full closure: review the list and
  remove anything you'd rather inherit from the system. It does not yet
  recurse transitive deps beyond what `ldd` reports.

## Installer bundles

The creator can wrap an app bundle into an **installer bundle** — itself a
`.exe` that, when launched, runs a Windows-style step wizard:

```
MyApp Installer.exe/
  Info.json                  exec = Contents/bin/install
  Contents/bin/install       PyQt6 QWizard: Welcome -> Location -> Installing -> Done
  payload/MyApp.exe/         the app bundle being installed
  Resources/icons/<n>.png    reused from the app
```

The **Installing** step runs, under `pkexec`:

```sh
cp -r payload/MyApp.exe <install-root>/ && muluos-bundle install <install-root>/MyApp.exe
```

`pkexec` is required because `register_bundle` is root-only; it needs a polkit
agent for the password prompt (present on the KDE profile, absent in a bare
console). The default install root is `/opt/muluos/apps`.

## Uninstalling

[utils/app-manager/](../utils/app-manager/) (`muluos-app-manager`,
"Add or Remove Programs") lists installed bundles from the registry and
uninstalls the selected one via the privileged helper
[app-uninstall](../utils/app-manager/usr/libexec/muluos/app-uninstall)
(run under `pkexec`).

A custom uninstall config is **optional**. With none, the default uninstall is:
run nothing custom → `muluos-bundle uninstall <id> --purge` (unregister + remove
the app-menu entry + drop the bundle's registry data) → delete the bundle
directory.

To add custom steps, declare an `uninstall` block in `Info.json`:

```json
{
  "uninstall": {
    "exec": "Contents/bin/uninstall",
    "remove_paths": ["/opt/myapp-data", "/etc/myapp"]
  }
}
```

| Field | Meaning |
|---|---|
| `exec` | A hook script inside the bundle, run **before** removal as root with `MULUOS_BUNDLE` and `MULUOS_UNINSTALL=1` set. Use it to stop services, remove symlinks, or clean per-user data (find the invoking user via `PKEXEC_UID`). Must resolve inside the bundle. |
| `remove_paths` | Absolute paths deleted after the hook. A protected-path denylist (`/`, `/usr`, `/etc`, `/home`, …) is enforced so a bundle can't wipe the system. |

The package creator authors this block: its **Uninstall (optional)** section
takes a hook script (copied to `Contents/bin/uninstall`) and a list of paths,
and the choices are saved in the JSON template like everything else.
