#!/bin/bash
# ============================================
# BAMSec Transcript Downloader - Run Script
# ============================================
# Usage:
#   ./run.sh RH        (downloads 8 transcripts for RH)
#   ./run.sh AAPL      (downloads 8 transcripts for Apple)
#   ./run.sh MSFT 4    (downloads 4 transcripts for Microsoft)
# ============================================

if [ -z "$1" ]; then
    echo "BAMSec Transcript Downloader"
    echo ""
    echo "Usage:  ./run.sh TICKER [count]"
    echo ""
    echo "Examples:"
    echo "  ./run.sh RH         Download 8 most recent transcripts for RH"
    echo "  ./run.sh AAPL       Download 8 most recent transcripts for Apple"
    echo "  ./run.sh MSFT 4     Download only 4 transcripts for Microsoft"
    echo ""
    exit 0
fi

TICKER=$1
COUNT=${2:-8}

python3 main.py "$TICKER" --count "$COUNT"
