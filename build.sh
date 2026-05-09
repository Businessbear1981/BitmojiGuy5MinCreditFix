#!/usr/bin/env bash
set -e

# Install and build the Next.js frontend
cd frontend
npm install
npm run build
cd ..

# Install Python backend dependencies
pip install -r backend/requirements.txt
