#!/bin/bash
# Build script for Railway - installs Chrome and dependencies

set -e

echo "Installing Chrome..."
# Download and install Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
apt-get update
apt-get install -y google-chrome-stable

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Build complete!"
