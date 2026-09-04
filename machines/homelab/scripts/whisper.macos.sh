#!/usr/bin/env bash
set -Eeuo pipefail

: "${MC_HOMELAB_DIR:?MC_HOMELAB_DIR must be set}"
: "${MC_HOME:?MC_HOME must be set}"
: "${MC_ID:?MC_ID must be set}"

# constants
# REVIEW: Pick transcription model
model_name="ggml-large-v3-turbo-q5_0.bin"
model_url="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/$model_name"
model_sha1="e050f7970618a659205450ad97eb95a18d69c9ee"

# ~/.homelab/whisper/models/model.bin
model_dir="$MC_HOMELAB_DIR/whisper/models"
model_path="$model_dir/$model_name"
mkdir -p "$model_dir"

# download the model if it doesn't exist
if [[ ! -f "$model_path" ]]; then
    partial_path="$model_path.partial"
    echo "downloading Whisper model $model_name..."
    curl --fail --location --retry 3 --continue-at - \
        --output "$partial_path" "$model_url"

    # verify the model checksum
    actual_sha1=$(shasum -a 1 "$partial_path" | awk '{print $1}')
    if [[ "$actual_sha1" != "$model_sha1" ]]; then
        rm -f "$partial_path"
        echo "Whisper model checksum verification failed" >&2
        exit 1
    fi

    mv "$partial_path" "$model_path"
fi

label="com.mc.whisper"
domain="gui/$(id -u)"
plist_source="$MC_HOME/machines/$MC_ID/$label.plist"
plist="$HOME/Library/LaunchAgents/$label.plist"

# launchd requires a regular, user-owned plist rather than mc's usual symlink.
mkdir -p "$HOME/Library/LaunchAgents"
rm -f "$plist"
install -m 600 "$plist_source" "$plist"

if launchctl print "$domain/$label" &>/dev/null; then
    launchctl bootout "$domain/$label"
fi

for _ in {1..10}; do
    if launchctl bootstrap "$domain" "$plist" 2>/dev/null; then
        exit 0
    fi
    sleep 0.5
done
