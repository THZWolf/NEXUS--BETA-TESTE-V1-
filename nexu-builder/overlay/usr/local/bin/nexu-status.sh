#!/bin/sh
set -eu

echo "NEXU_STATUS: boot"
printf 'Host: %s\n' "$(hostname)"
printf 'Kernel: %s\n' "$(uname -r)"

for service in docker postgresql nexus-server nexus-avatar open-jarvis open-eye; do
    if systemctl is-active --quiet "$service.service"; then
        printf 'SERVICE %s: active\n' "$service"
    else
        printf 'SERVICE %s: inactive\n' "$service"
    fi
done

if docker info >/dev/null 2>&1; then
    printf 'DOCKER: ready\n'
else
    printf 'DOCKER: unavailable\n'
fi
printf 'CGROUPS: '
if grep -Eq ' - cgroup2? ' /proc/self/mountinfo; then
    echo mounted
else
    echo unavailable
fi
