#!/bin/bash

# Create necessary directories
mkdir -p temp
mkdir -p logs

# Install dependencies
pip install -r requirements.txt

# Run bot
python bot.py
