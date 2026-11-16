#!/bin/sh
set -u

PATH=/usr/sbin:/usr/bin:/sbin:/bin
export PATH

failures=0

check() {
    name=$1
    shift
    if "$@"; then
        printf 'PASS: %s\n' "$name"
    else
        printf 'FAIL: %s\n' "$name"
        failures=$((failures + 1))
    fi
}

check_systemd() {
    command -v systemctl >/dev/null 2>&1 && systemctl is-system-running >/dev/null 2>&1
}

check_docker() {
    command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1
}

check_cgroups() {
    [ -r /proc/self/mountinfo ] && grep -Eq ' - cgroup2? ' /proc/self/mountinfo
}

check_rootfs() {
    [ -r /etc/os-release ] && [ -x /opt/nexus-os/nexus_launch.py ] &&
        [ -f /etc/systemd/journald.conf ] &&
        python3 -m json.tool /etc/docker/daemon.json >/dev/null 2>&1
}

check "systemd init" check_systemd
check "Docker daemon" check_docker
check "cgroups mounted" check_cgroups
check "root filesystem and Nexus configuration" check_rootfs

if [ "$failures" -gt 0 ]; then
    printf 'NEXU_STATUS: critical failures=%s\n' "$failures"
    if [ -r /etc/nexus-os/nexu-alert.env ]; then
        # shellcheck disable=SC1091
        . /etc/nexus-os/nexu-alert.env
        if [ -n "${NEXU_TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${NEXU_TELEGRAM_CHAT_ID:-}" ]; then
            message="NEXU-OS sanity check failed: ${failures} checks. Inspect local journal."
            curl --fail --silent --show-error --max-time 10 \
                --data-urlencode "chat_id=${NEXU_TELEGRAM_CHAT_ID}" \
                --data-urlencode "text=${message}" \
                "https://api.telegram.org/bot${NEXU_TELEGRAM_BOT_TOKEN}/sendMessage" \
                >/dev/null || echo "Telegram alert delivery failed." >&2
        fi
    fi
    exit 1
fi

echo "NEXU_STATUS: healthy"
