#!/usr/bin/with-contenv sh
# shellcheck shell=sh
set -eu

config=/config/sabnzbd.ini
whitelist=${SABNZBD_HOST_WHITELIST:?SABNZBD_HOST_WHITELIST must be set}
expected="host_whitelist = $whitelist"

# Seed the smallest valid config on first boot; SABnzbd fills in its defaults.
if [ ! -f "$config" ]; then
    umask 077
    {
        printf '[misc]\n'
        printf 'host_whitelist = %s\n' "$whitelist"
    } >"$config"
elif grep -Fqx "$expected" "$config"; then
    exit 0
elif grep -q '^[[:space:]]*host_whitelist[[:space:]]*=' "$config"; then
    sed -i \
        "s|^[[:space:]]*host_whitelist[[:space:]]*=.*|$expected|" \
        "$config"
elif grep -q '^[[:space:]]*\[misc\][[:space:]]*$' "$config"; then
    sed -i \
        "/^[[:space:]]*\[misc\][[:space:]]*$/a\\
$expected" \
        "$config"
else
    {
        printf '\n[misc]\n'
        printf 'host_whitelist = %s\n' "$whitelist"
    } >>"$config"
fi

chown abc:abc "$config"
chmod 600 "$config"
echo "configured SABnzbd host whitelist"
