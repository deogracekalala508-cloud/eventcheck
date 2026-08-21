#!/bin/bash

echo "=== Début de l'installation ==="

# Mettre à jour apt-get
apt-get update -y

# Installer Tesseract OCR
apt-get install -y tesseract-ocr

# Installer le français
apt-get install -y tesseract-ocr-fra

# Vérifier l'installation
echo "=== Vérification Tesseract ==="
which tesseract
tesseract --version

# Installer les dépendances Python
echo "=== Installation Python ==="
pip install -r requirements.txt

echo "=== Installation terminée ==="