#!/bin/bash
# Installer Tesseract OCR
apt-get update
apt-get install -y tesseract-ocr tesseract-ocr-fra

# Installer les dépendances Python
pip install -r requirements.txt