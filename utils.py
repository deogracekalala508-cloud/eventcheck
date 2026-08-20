import pandas as pd
import os
import re
from werkzeug.utils import secure_filename
import pyttsx3
import threading

try:
    from PIL import Image, ImageEnhance, ImageFilter
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    OCR_AVAILABLE = True
except:
    OCR_AVAILABLE = False
    print("⚠️ OCR non disponible. Installez pytesseract et Tesseract OCR")

def process_excel_file(file_path):
    """Traite un fichier Excel/CSV"""
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        return extract_guests_from_dataframe(df)
    except Exception as e:
        raise Exception(f"Erreur fichier: {str(e)}")

def preprocess_image(image_path):
    """Améliore l'image pour meilleure reconnaissance OCR"""
    image = Image.open(image_path)
    image = image.convert('L')
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(2.0)
    width, height = image.size
    if width < 1000 or height < 1000:
        scale = max(1000/width, 1000/height)
        new_size = (int(width * scale), int(height * scale))
        image = image.resize(new_size, Image.LANCZOS)
    return image

def process_image_file(file_path):
    """Analyse intelligente d'une photo de liste d'invités"""
    if not OCR_AVAILABLE:
        raise Exception("L'OCR n'est pas installé. Impossible de traiter les photos.")
    
    try:
        image = preprocess_image(file_path)
        
        configs = [
            '--psm 6 -l fra',
            '--psm 4 -l fra',
            '--psm 3 -l fra',
        ]
        
        all_text = ""
        for config in configs:
            try:
                text = pytesseract.image_to_string(image, config=config)
                all_text += text + "\n"
            except:
                continue
        
        guests = smart_parse_text(all_text)
        return guests
    
    except Exception as e:
        raise Exception(f"Erreur analyse photo: {str(e)}")

def smart_parse_text(text):
    """Parse intelligent du texte OCR - Reconnaît tous les formats de listes"""
    guests = []
    seen_names = set()
    
    text = text.replace('|', ' ').replace('\t', ' ').replace('  ', ' ')
    
    patterns = [
        r'([A-ZÉÈÊËÀÂÄÔÖÛÜÇ]{2,})\s+([A-ZÉÈÊËÀÂÄÔÖÛÜÇa-zéèêëàâäôöûüç]+)\s+[Tt]able\s*(\d+)',
        r'[Tt]able\s*(\d+)\s*[-:]\s*([A-ZÉÈÊËÀÂÄÔÖÛÜÇ]{2,})\s+([A-ZÉÈÊËÀÂÄÔÖÛÜÇa-zéèêëàâäôöûüç]+)',
        r'(\d+)[.)]\s*([A-ZÉÈÊËÀÂÄÔÖÛÜÇ]{2,})\s+([A-ZÉÈÊËÀÂÄÔÖÛÜÇa-zéèêëàâäôöûüç]+)',
        r'([A-ZÉÈÊËÀÂÄÔÖÛÜÇ][a-zéèêëàâäôöûüç]+)\s+([A-ZÉÈÊËÀÂÄÔÖÛÜÇ]{2,})\s*[-:]\s*(\d+)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if len(match) == 3:
                if match[0].isupper() and len(match[0]) > 1:
                    last_name = match[0]
                    first_name = match[1]
                    table = match[2]
                elif match[2].isdigit():
                    if match[0].isdigit():
                        table = match[0]
                        last_name = match[1]
                        first_name = match[2]
                    else:
                        first_name = match[0]
                        last_name = match[1]
                        table = match[2]
                else:
                    continue
                
                key = f"{last_name}_{first_name}"
                if key not in seen_names:
                    seen_names.add(key)
                    guests.append({
                        'first_name': first_name.upper(),
                        'last_name': last_name.upper(),
                        'table_number': table
                    })
    
    if not guests:
        lines = text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or len(line) < 5:
                continue
            
            if any(word in line.lower() for word in ['nom', 'prénom', 'table', 'liste', 'invité', 'page', 'total']):
                continue
            
            words = line.split()
            uppercase_words = [w for w in words if w.isupper() and len(w) > 1]
            numbers = [w for w in words if w.isdigit()]
            
            if len(uppercase_words) >= 1 and len(words) >= 2:
                last_name = uppercase_words[-1]
                last_name_idx = words.index(last_name)
                
                if last_name_idx > 0:
                    first_name = words[last_name_idx - 1]
                elif last_name_idx < len(words) - 1:
                    first_name = words[last_name_idx + 1]
                else:
                    first_name = words[0]
                
                table = numbers[0] if numbers else "À assigner"
                
                if not first_name.isdigit() and len(first_name) > 1:
                    key = f"{last_name}_{first_name}"
                    if key not in seen_names:
                        seen_names.add(key)
                        guests.append({
                            'first_name': first_name.upper(),
                            'last_name': last_name.upper(),
                            'table_number': table
                        })
    
    return guests

def extract_guests_from_dataframe(df):
    """Extrait les invités d'un DataFrame pandas"""
    guests = []
    
    name_cols = [col for col in df.columns if 'nom' in col.lower() or 'name' in col.lower()]
    firstname_cols = [col for col in df.columns if 'prénom' in col.lower() or 'prenom' in col.lower() or 'first' in col.lower()]
    table_cols = [col for col in df.columns if 'table' in col.lower()]
    
    for _, row in df.iterrows():
        if firstname_cols and name_cols:
            first_name = str(row[firstname_cols[0]]) if pd.notna(row[firstname_cols[0]]) else ""
            last_name = str(row[name_cols[0]]) if pd.notna(row[name_cols[0]]) else ""
        elif name_cols:
            full_name = str(row[name_cols[0]])
            parts = full_name.split()
            first_name = parts[0] if len(parts) > 0 else ""
            last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        else:
            text_cols = df.select_dtypes(include=['object']).columns
            if len(text_cols) > 0:
                full_name = str(row[text_cols[0]])
                parts = full_name.split()
                first_name = parts[0] if len(parts) > 0 else ""
                last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
            else:
                continue
        
        if table_cols:
            table = str(int(row[table_cols[0]])) if pd.notna(row[table_cols[0]]) else "À assigner"
        else:
            num_cols = df.select_dtypes(include=['number']).columns
            table = str(int(row[num_cols[0]])) if len(num_cols) > 0 else "À assigner"
        
        if first_name and last_name:
            guests.append({
                'first_name': first_name.strip().upper(),
                'last_name': last_name.strip().upper(),
                'table_number': table
            })
    
    return guests

def announce_table(table_number):
    """Annonce vocale du numéro de table"""
    def speak():
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            for voice in voices:
                if 'french' in voice.name.lower() or 'français' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
            engine.setProperty('rate', 150)
            engine.say(f"Table {table_number}, s'il vous plaît")
            engine.runAndWait()
        except Exception as e:
            print(f"Erreur annonce vocale: {e}")
    
    thread = threading.Thread(target=speak)
    thread.daemon = True
    thread.start()

def allowed_file(filename):
    """Vérifie si le fichier est autorisé"""
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_image_file(filename):
    """Vérifie si c'est une image"""
    IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in IMAGE_EXTENSIONS