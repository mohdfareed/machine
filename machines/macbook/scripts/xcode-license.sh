#!/bin/bash
# Accept Xcode license on macOS

echo "Accepting Xcode license..."

# Check if Xcode command line tools are installed
if ! xcode-select -p &> /dev/null; then
    echo "Xcode command line tools not found. Installing..."
    xcode-select --install
    echo "Please complete the Xcode command line tools installation and re-run this script"
    exit 1
fi

# Accept the Xcode license
if sudo xcodebuild -license accept; then
    echo "✓ Xcode license accepted successfully"
else
    echo "❌ Failed to accept Xcode license"
    echo "You may need to run 'sudo xcodebuild -license' manually"
    exit 1
fi
