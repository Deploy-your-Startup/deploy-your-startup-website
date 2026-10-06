#!/bin/bash

set -e

if [ "$1" == "run" ]; then
  cd frontend
  npm install
  npm run dev
fi

if [ "$1" == "build" ]; then
  cd frontend
  npm install
  npm run build
fi

if [ "$1" == "test" ]; then
  python3 -m unittest discover -s tests -v
fi

if [ "$1" == "help" ] || [ -z "$1" ]; then
  echo "Available commands:"
  echo "  run    - Install dependencies and start the local Astro dev server"
  echo "  build  - Install dependencies and build the frontend"
  echo "  test   - Check installer failure paths"
  echo "  help   - Show this help message"
fi
