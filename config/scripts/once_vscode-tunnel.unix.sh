#!/usr/bin/env bash

tunnel=$MACHINE_ID

echo "setting up vscode tunnel: $tunnel"
code tunnel service install --name "$tunnel" --accept-server-license-terms
echo "vscode tunnel setup completed"
