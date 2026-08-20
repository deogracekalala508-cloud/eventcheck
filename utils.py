import pandas as pd
import os
import re
import threading
from werkzeug.utils import secure_filename

# OCR désactivé sur le serveur
OCR_AVAILABLE = False

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

def process_image_file(file_path):
    """Non disponible sur le serveur"""
    raise Exception("L'OCR n'est pas disponible sur le serveur. Utilisez un fichier Excel/CSV.")

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
    """Annonce vocale (désactivée sur le serveur)"""
    print(f"Annonce vocale: Table {table_number}")

def allowed_file(filename):
    """Vérifie si le fichier est autorisé"""
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_image_file(filename):
    """Vérifie si c'est une image (désactivé sur serveur)"""
    return False