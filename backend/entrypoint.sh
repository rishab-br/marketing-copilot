#!/bin/sh
set -e

# A mounted volume (e.g. a Fly.io volume) starts empty and root-owned. If we are
# running as root, make the data dir writable then drop to the unprivileged user.
# On Docker Compose the named volume is already appuser-owned, so this is a no-op.
if [ "$(id -u)" = "0" ]; then
  mkdir -p /app/data
  chown -R appuser /app/data
  exec gosu appuser "$@"
fi

exec "$@"
