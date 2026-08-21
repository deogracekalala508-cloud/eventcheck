FROM python:3.11-slim

# Installer Tesseract OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-fra \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Vérifier Tesseract
RUN tesseract --version

WORKDIR /app

# Copier les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY . .

# Lancer l'application
CMD gunicorn app:app --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT