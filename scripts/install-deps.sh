#!/usr/bin/env bash
SUDO=""
if command -v sudo &> /dev/null; then
    SUDO="sudo"
fi

if command -v apt &> /dev/null; then
    if ! (command -v clang &> /dev/null || command -v gcc &> /dev/null); then
        echo "Neither clang nor gcc found. Installing gcc..."
        $SUDO apt update && $SUDO apt install -y gcc build-essential python3-dev
    fi

    $SUDO apt update && $SUDO apt install -y jq \
        build-essential \
        python3-dev \
        libpixman-1-dev \
        libcairo2-dev \
        libpango1.0-dev \
        libjpeg-dev \
        libgif-dev \
        librsvg2-dev
elif command -v brew &> /dev/null; then
    brew install jq
elif command -v dnf &> /dev/null; then
    $SUDO dnf install -y jq
else
    echo "Error: Could not find package manager to install jq"
    exit 1
fi
