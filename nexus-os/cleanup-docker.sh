#!/bin/sh
set -eu

PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PATH

if [ "$(id -u)" -ne 0 ]; then
    echo "Run this maintenance task as root." >&2
    exit 1
fi
if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
    echo "Docker daemon is unavailable; no cleanup was performed." >&2
    exit 1
fi

exec 9>/run/lock/nexus-docker-cleanup.lock
if ! flock -n 9; then
    echo "Another Docker cleanup is already running." >&2
    exit 0
fi

echo "Removing stopped containers older than 7 days..."
docker container prune --force --filter "until=168h"
echo "Removing only unused volumes explicitly tagged nexus.cleanup=eligible..."
docker volume prune --force --filter "label=nexus.cleanup=eligible"
