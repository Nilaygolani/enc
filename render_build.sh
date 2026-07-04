#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Chrome aur ChromeDriver install karne ke liye commands
STORAGE_DIR=/opt/render/project/.render

if [ ! -d "$STORAGE_DIR/chrome" ]; then
  echo "...Downloading Chrome..."
  mkdir -p $STORAGE_DIR/chrome
  cd $STORAGE_DIR/chrome
  wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
  dpkg -x google-chrome-stable_current_amd64.deb .
fi

# Link binary to standard paths so python script can find it
ln -sf $STORAGE_DIR/chrome/opt/google/chrome/google-chrome /usr/bin/google-chrome

# Render standard chromedriver setup
# Render ke native packages se chrome setup automation simple ho jata hai.
