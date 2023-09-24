#!/bin/bash

# Global variables
VENV="venv"
HEADLESS_VERSION="117.0.5938.88"
DRIVER_URL_LINUX="https://chromedriver.storage.googleapis.com/$HEADLESS_VERSION/chromedriver_linux64.zip"
DRIVER_NAME="chromedriver.zip"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv ${VENV}
echo "Virtual environment created."

# Upgrade pip and install requirements
pip install -U pip
pip install -r requirements.txt

# Download chromedriver
echo "Downloading chromedriver..."
curl -o ${DRIVER_NAME} ${DRIVER_URL_LINUX}
echo "Chromedriver downloaded."
echo "Unzipping chromedriver..."
unzip ${DRIVER_NAME}
echo "Chromedriver unzipped."
echo "Installing chromedriver..."
mv ./chromedriver-linux64/chromedriver ${VENV}/bin/
echo "Chromedriver installed."
