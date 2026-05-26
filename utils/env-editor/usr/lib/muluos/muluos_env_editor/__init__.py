"""MuluOS Environment editor.

Edits PATH additions and environment variables stored in the SQLite-backed
registry (env.* on bundle muluos.system), then regenerates
/etc/profile.d/muluos-env.sh via /usr/libexec/muluos/env-generate.
"""
