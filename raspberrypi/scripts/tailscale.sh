#!/usr/bin/env bash
# Install Tailscale and configure DNS and environment

# install tailscale if it doesn't exist
if ! command -v tailscale &>/dev/null; then
	echo "Installing Tailscale..."
	curl -fsSL https://tailscale.com/install.sh | sh
fi

echo "Updating Tailscale..."
tailscale update --yes
echo "Setting up Tailscale..."
sudo tailscale up --accept-dns=false
ip=$(tailscale ip -1)

# setup tailscale DNS
source $HOME/.zshenv
conf_file="$MACHINE/pihole/dns/00-tailscale.conf"
sudo mkdir -p "$(dirname "$conf_file")"
echo address=/pi/$ip | sudo tee $conf_file

# setup funnels
sudo tailscale serve https /chatgpt http://localhost:80/chatgpt
sudo tailscale funnel 443 on

# update machine ip and device id
if [[ -z $TAILSCALE_DEVICEID || -z $TAILSCALE_IP ]]; then
	echo "Enter the Tailscale device ID:" && read device_id
	update_env TAILSCALE_DEVICEID $device_id
	update_env TAILSCALE_IP $ip
fi
