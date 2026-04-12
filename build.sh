#!/usr/bin/env bash
set -e

# Install and build the React frontend
npm install
npm run build

# Install Python backend dependencies
pip install -r backend/requirements.txt
