FROM python:3.11-slim

# Installer Tesseract OCR (sans libgl1-mesa-glx)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-fra \
    && rm -rf /var/lib/apt/lists/*

# Vérifier que Tesseract est installé
RUN which tesseract && tesseract --version

WORKDIR /app

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le code
COPY . .

# Lancer l'application
CMD gunicorn app:app --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT