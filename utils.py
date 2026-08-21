import os
import re
import threading

# ============ CONFIGURATION OCR ============
OCR_AVAILABLE = False

try:
    from PIL import Image, ImageEnhance
    import pytesseract
    
    # Détection automatique du chemin de Tesseract
    if os.path.exists('/usr/bin/tesseract'):
        # Sur Render (Linux)
        pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
    elif os.path.exists('/usr/local/bin/tesseract'):
        # Autre emplacement Linux
        pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'
    elif os.name == 'nt':
        # Sur Windows
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'C:\Users\deogr\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
        ]
        for path in possible_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                break
    
    # Tester si Tesseract fonctionne
    test_image = Image.new('RGB', (100, 50), color='white')
    pytesseract.image_to_string(test_image)
    
    OCR_AVAILABLE = True
    print("✅ OCR disponible et fonctionnel")
except Exception as e:
    print(f"⚠️ OCR non disponible: {e}")
    OCR_AVAILABLE = False

# ============ FONCTIONS ============

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
        raise Exception("L'OCR n'est pas disponible. Utilisez un fichier Excel.")
    
    try:
        # Ouvrir l'image
        image = Image.open(file_path)
        
        # Convertir en niveaux de gris
        image = image.convert('L')
        
        # Augmenter le contraste
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Augmenter la netteté
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)
        
        # Agrandir si trop petite
        width, height = image.size
        if width < 1000 or height < 1000:
            scale = max(1000/width, 1000/height)
            new_size = (int(width * scale), int(height * scale))
            image = image.resize(new_size, Image.LANCZOS)
        
        # OCR en français
        text = pytesseract.image_to_string(image, lang='fra')
        
        # Si le français ne donne rien, essayer en anglais
        if not text.strip():
            text = pytesseract.image_to_string(image, lang='eng')
        
        # Parser le texte
        guests = smart_parse_text(text)
        return guests
    
    except Exception as e:
        raise Exception(f"Erreur analyse photo: {str(e)}")

def smart_parse_text(text):
    """Parse intelligent du texte OCR - Détecte les noms et tables"""
    guests = []
    seen_names = set()
    
    # Nettoyer le texte
    text = text.replace('|', ' ').replace('\t', ' ').replace('  ', ' ')
    text = text.replace('→', ' ').replace('->', ' ').replace('➔', ' ')
    
    lines = text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 4:
            continue
        
        # Ignorer les en-têtes
        lower_line = line.lower()
        if any(word in lower_line for word in ['nom', 'prénom', 'prenom', 'table', 'liste', 'invité', 'invite', 'page', 'total', 'nombre']):
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
                'marguerite', 'tournesol', 'lys', 'iris', 'violette',
                'france', 'italie', 'espagne', 'portugal', 'maroc', 'tunisie', 'senegal',
                'congo', 'bresil', 'japon', 'chine', 'inde', 'mexique', 'grece',
                'paris', 'rome', 'londres', 'dubai', 'tokyo', 'barcelone', 'venise',
                'florence', 'nice', 'marseille', 'lyon',
                'rouge', 'bleu', 'vert', 'jaune', 'violet', 'orange', 'doré', 'dore',
                'argent', 'blanc', 'noir', 'turquoise', 'corail',
                'amour', 'passion', 'éternité', 'eternite', 'bonheur', 'joie', 'reve',
                'destin', 'harmonie', 'felicite', 'félicité', 'tendresse',
                'diamant', 'saphir', 'émeraude', 'emeraude', 'rubis', 'perle', 'opale',
                'etoile', 'étoile', 'lune', 'soleil', 'ciel', 'mer', 'ocean', 'océan',
                'montagne', 'foret', 'forêt', 'jardin', 'paradis',
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
                        if word.lower() not in ['nom', 'prénom', 'prenom', 'liste', 'monsieur', 'madame']:
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