import os
import re
import threading

# OCR configuré pour Render (Linux) ET Windows
OCR_AVAILABLE = False

try:
    from PIL import Image, ImageEnhance
    import pytesseract
    
    # Sur Windows, configurer le chemin
    if os.name == 'nt':
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    # Sur Linux (Render), Tesseract est installé via apt-get, pas besoin de chemin
    
    OCR_AVAILABLE = True
    print("✅ OCR disponible")
except Exception as e:
    print(f"⚠️ OCR non disponible: {e}")

def process_excel_file(file_path):
    """Traite un fichier Excel"""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file_path)
        ws = wb.active
        
        headers = []
        for cell in ws[1]:
            headers.append(str(cell.value).lower() if cell.value else "")
        
        name_col = None
        firstname_col = None
        table_col = None
        
        for i, header in enumerate(headers):
            if 'nom' in header or 'name' in header:
                name_col = i
            if 'prénom' in header or 'prenom' in header or 'first' in header:
                firstname_col = i
            if 'table' in header:
                table_col = i
        
        guests = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            if name_col is not None and row[name_col]:
                full_name = str(row[name_col])
                parts = full_name.split()
                
                if firstname_col is not None and row[firstname_col]:
                    first_name = str(row[firstname_col]).upper()
                    last_name = full_name.upper()
                else:
                    first_name = parts[0].upper() if parts else ""
                    last_name = " ".join(parts[1:]).upper() if len(parts) > 1 else ""
                
                if table_col is not None and row[table_col]:
                    table = str(row[table_col])
                else:
                    table = "À assigner"
                
                if first_name and last_name:
                    guests.append({
                        'first_name': first_name.strip(),
                        'last_name': last_name.strip(),
                        'table_number': table
                    })
        
        return guests
    
    except Exception as e:
        raise Exception(f"Erreur fichier: {str(e)}")

def process_image_file(file_path):
    """Analyse intelligente d'une photo de liste"""
    if not OCR_AVAILABLE:
        raise Exception("L'OCR n'est pas disponible sur ce serveur")
    
    try:
        image = Image.open(file_path)
        image = image.convert('L')  # Niveaux de gris
        
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # OCR en français
        text = pytesseract.image_to_string(image, lang='fra')
        
        guests = smart_parse_text(text)
        return guests
    
    except Exception as e:
        raise Exception(f"Erreur analyse photo: {str(e)}")

def smart_parse_text(text):
    """Parse intelligent du texte OCR - Détecte les noms et tables"""
    guests = []
    seen_names = set()
    
    text = text.replace('|', ' ').replace('\t', ' ').replace('  ', ' ')
    text = text.replace('→', ' ').replace('->', ' ')
    
    lines = text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 4:
            continue
        
        # Ignorer les en-têtes
        if any(word in line.lower() for word in ['nom', 'prénom', 'prenom', 'table', 'liste', 'invité', 'invite', 'page', 'total', 'nombre']):
            if len(line.split()) <= 4:
                continue
        
        words = line.split()
        uppercase_words = [w for w in words if w.isupper() and len(w) > 1]
        capitalized_words = [w for w in words if w[0].isupper() and not w.isupper() and len(w) > 1]
        numbers = [w for w in words if w.isdigit()]
        
        # Chercher les mots-clés de table
        table_name = None
        table_keywords = ['table', 'tbl', 'tab', 't.']
        
        for i, word in enumerate(words):
            if word.lower() in table_keywords:
                if i + 1 < len(words):
                    table_name = words[i + 1].strip(':,;-()[]{}')
                break
        
        # Détecter les noms de tables thématiques
        if not table_name:
            table_names_list = [
                'rose', 'tulipe', 'orchidée', 'orchidee', 'jasmin', 'lavande', 'pivoine',
                'france', 'italie', 'espagne', 'maroc', 'tunisie', 'senegal', 'congo',
                'paris', 'rome', 'londres', 'dubai', 'tokyo', 'barcelone', 'venise',
                'rouge', 'bleu', 'vert', 'jaune', 'violet', 'orange', 'doré', 'dore',
                'amour', 'passion', 'éternité', 'eternite', 'bonheur', 'joie', 'reve',
                'diamant', 'saphir', 'émeraude', 'emeraude', 'rubis', 'perle', 'opale',
                'etoile', 'étoile', 'lune', 'soleil', 'ciel', 'mer', 'ocean', 'océan',
            ]
            
            line_lower = line.lower()
            for table_name_candidate in table_names_list:
                if table_name_candidate in line_lower:
                    table_name = table_name_candidate
                    break
        
        # Déterminer les noms et prénoms
        if len(uppercase_words) >= 1 and len(capitalized_words) >= 1:
            last_name = uppercase_words[0]
            first_name = capitalized_words[0]
            
            if table_name:
                table = table_name
            elif numbers:
                table = numbers[0]
            else:
                table = "À assigner"
            
            key = f"{last_name}_{first_name}"
            if key not in seen_names:
                seen_names.add(key)
                guests.append({
                    'first_name': first_name.upper(),
                    'last_name': last_name.upper(),
                    'table_number': table.upper()
                })
        
        elif len(uppercase_words) >= 1 and len(words) >= 2:
            last_name = uppercase_words[0]
            first_name = None
            
            for word in words:
                if word != last_name and not word.isdigit():
                    if word.lower() not in table_keywords:
                        if word.lower() not in ['nom', 'prénom', 'prenom', 'liste']:
                            first_name = word
                            break
            
            if first_name:
                if table_name:
                    table = table_name
                elif numbers:
                    table = numbers[0]
                else:
                    table = "À assigner"
                
                key = f"{last_name}_{first_name}"
                if key not in seen_names:
                    seen_names.add(key)
                    guests.append({
                        'first_name': first_name.upper(),
                        'last_name': last_name.upper(),
                        'table_number': table.upper()
                    })
    
    return guests

def announce_table(table_number):
    """Annonce vocale"""
    print(f"Annonce vocale: Table {table_number}")

def allowed_file(filename):
    """Vérifie si le fichier est autorisé"""
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_image_file(filename):
    """Vérifie si c'est une image"""
    IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in IMAGE_EXTENSIONS