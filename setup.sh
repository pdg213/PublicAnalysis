#!/bin/bash
# ============================================
# BAMSec Transcript Downloader - Setup Script
# ============================================
# Run this ONCE to install everything needed.
# After this, you only need to use run.sh
# ============================================

echo "Setting up BAMSec Transcript Downloader..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed."
    echo "Please install Python 3 from https://www.python.org/downloads/"
    exit 1
fi

echo "1/3  Installing Python packages..."
pip3 install -r requirements.txt

echo ""
echo "2/3  Installing browser for automation..."
python3 -m playwright install chromium

echo ""
echo "3/3  Checking for .env file..."
if [ ! -f .env ]; then
    echo ""
    echo "IMPORTANT: You need to create a .env file with your BAMSec login."
    echo ""
    echo "Create a file called '.env' (no other name) in this folder with:"
    echo ""
    echo "  BAMSEC_EMAIL=your_email@example.com"
    echo "  BAMSEC_PASSWORD=your_password"
    echo ""
    echo "(Replace with your actual BAMSec email and password)"
else
    echo ".env file found!"
fi

echo ""
echo "Setup complete! You can now use run.sh to download transcripts."
echo ""
echo "Example:  ./run.sh RH"
