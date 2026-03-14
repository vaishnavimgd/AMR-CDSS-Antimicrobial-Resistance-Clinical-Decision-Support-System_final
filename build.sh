#!/usr/bin/env bash

# Exit on error
set -o errexit

echo "Starting build process for AMR Project..."

# 1. Install Python Dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt
pip install -r backend/requirements.txt

# 2. Compile C++ Gene Scanner for Linux
echo "Compiling C++ Gene Scanner..."
cd backend
g++ -O2 -std=c++17 gene_scanner.cpp -o gene_scanner

if [ -f "gene_scanner" ]; then
    echo "Successfully compiled gene scanner!"
    chmod +x gene_scanner
else
    echo "Error: Failed to compile gene scanner."
    exit 1
fi

cd ..
echo "Build complete."
