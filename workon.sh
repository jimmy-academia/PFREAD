#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Exit if WorkFolder already exists
if [ -d "WorkFolder" ]; then
  echo "Error: 'WorkFolder' already exists. Exiting."
  exit 1
fi

# Check if URL is passed
if [ -z "$1" ]; then
  echo "Usage: $0 <github_url>"
  exit 1
fi

git clone "$1"
repo_name=$(basename -s .git "$1")
mv "$repo_name" WorkFolder/

echo "Repository '$repo_name' moved to 'WorkFolder/'"
