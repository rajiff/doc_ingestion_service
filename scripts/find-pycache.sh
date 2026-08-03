#!/usr/bin/env sh
echo "Running script to find __pycache__ folders"

find . -type d -name "__pycache__" -not -path "*/.venv/*"

echo "Done"
