#!/bin/bash
# Accept Xcode license on macOS

echo "accepting xcode license..."

# Check if Xcode command line tools are installed
if ! xcode-select -p &> /dev/null; then
    echo "installing xcode..."
    xcode-select --install
    echo "complete the installation and re-run the script"
    exit 1
fi

# Accept the Xcode license
if sudo xcodebuild -license accept; then
    echo "xcode license accepted successfully"
else
    echo "failed to accept xcode license"
    echo "run 'sudo xcodebuild -license accept' manually"
    exit 1
fi
