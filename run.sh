#!/bin/bash
set -e

if [ ! -f "venv/bin/activate" ]; then
    echo "Error: virtual environment not found in ./venv"
    echo "Create it first with: python3 -m venv venv && source venv/bin/activate && pip install -r DarkGod14Bot/requirements.txt"
    exit 1
fi

source venv/bin/activate
python3 -m DarkGod14Bot
