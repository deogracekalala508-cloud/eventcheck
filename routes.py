from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app
import os
from database import Database
from models import EventCreate, GuestAdd
from utils import process_excel_file, process_image_file, allowed_file, is_image_file, announce_table
from werkzeug.utils import secure_filename
from datetime import datetime

main = Blueprint('main', __name__)
db = Database()

@main.route('/')
def index():
    """Page d'accueil avec tous les événements"""
    events = db.get_all_events()
    return render_template('index.html', events=events)

@main.route('/create', methods=['GET', 'POST'])
def create_event():
    """Création d'événement avec import fichier ou photo"""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            event_date = request.form.get('event_date')
            
            event_data = EventCreate(name=name, event_date=event_date)
            event_id = db.create_event(event_data.name, event_data.event_date)
            
            if 'guest_list' in request.files:
                file = request.files['guest_list']
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    
                    try:
                        guests = None
                        
                        if is_image_file(filename):
                            guests = process_image_file(filepath)
                        else:
                            guests = process_excel_file(filepath)
                        
                        if guests:
                            db.add_guests_batch(event_id, guests)
                            
                    except Exception as e:
                        print(f"Erreur import: {e}")
                        return render_template('create_event.html', 
                                             error=f"Erreur lors de l'import: {str(e)}")
                    finally:
                        if os.path.exists(filepath):
                            os.remove(filepath)
            
            return redirect(url_for('main.event_detail', event_id=event_id))
        
        except Exception as e:
            return render_template('create_event.html', error=str(e))
    
    return render_template('create_event.html')

@main.route('/event/<int:event_id>')
def event_detail(event_id):
    """Page détail d'un événement avec tous les liens"""
    event = db.get_event(event_id)
    if not event:
        return redirect(url_for('main.index'))
    
    stats = db.get_stats(event_id)
    return render_template('event_detail.html', event=event, stats=stats)

@main.route('/event/<int:event_id>/checkin')
def checkin(event_id):
    """Interface check-in pour le personnel à la porte"""
    event = db.get_event(event_id)
    if not event:
        return redirect(url_for('main.index'))
    
    guests = db.get_guests(event_id)
    stats = db.get_stats(event_id)
    
    return render_template('checkin.html', event=event, guests=guests, stats=stats)

@main.route('/event/<int:event_id>/dashboard')
def dashboard(event_id):
    """Dashboard de contrôle pour les organisateurs"""
    event = db.get_event(event_id)
    if not event:
        return redirect(url_for('main.index'))
    
    stats = db.get_stats(event_id)
    last_checkins = db.get_last_checkins(event_id, limit=10)
    guests = db.get_guests(event_id)
    
    return render_template('dashboard.html', 
                         event=event, 
                         stats=stats, 
                         last_checkins=last_checkins,
                         guests=guests)

@main.route('/event/<int:event_id>/delete', methods=['POST'])
def delete_event(event_id):
    """Supprime un événement"""
    event = db.get_event(event_id)
    if not event:
        return redirect(url_for('main.index'))
    
    db.delete_event(event_id)
    return redirect(url_for('main.index'))

@main.route('/api/event/<int:event_id>/checkin', methods=['POST'])
def api_checkin(event_id):
    """API pour le check-in"""
    data = request.json
    guest_id = data.get('guest_id')
    
    if db.checkin_guest(guest_id):
        guests = db.get_guests(event_id)
        guest = None
        for g in guests:
            if g['id'] == guest_id:
                guest = g
                break
        
        if guest:
            announce_table(guest['table_number'])
            
            from app import socketio
            stats = db.get_stats(event_id)
            socketio.emit('guest_checked_in', {
                'guest': dict(guest),
                'stats': stats
            }, room=f'event_{event_id}')
            
            return jsonify({
                'success': True,
                'guest': dict(guest),
                'message': f"Table {guest['table_number']}"
            })
    
    return jsonify({'success': False, 'message': 'Invité non trouvé'})

@main.route('/api/event/<int:event_id>/search')
def api_search(event_id):
    """API recherche rapide"""
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    results = db.search_guests(event_id, query)
    return jsonify([dict(r) for r in results])

@main.route('/api/event/<int:event_id>/stats')
def api_stats(event_id):
    """API statistiques"""
    stats = db.get_stats(event_id)
    last_checkins = db.get_last_checkins(event_id)
    return jsonify({
        'stats': stats,
        'last_checkins': [dict(g) for g in last_checkins]
    })

@main.route('/api/event/<int:event_id>/add-guest', methods=['POST'])
def api_add_guest(event_id):
    """API pour ajouter un invité"""
    try:
        data = request.json
        guest_data = GuestAdd(**data)
        
        guest_id = db.add_guest(
            event_id,
            guest_data.first_name,
            guest_data.last_name,
            guest_data.table_number,
            guest_data.notes
        )
        
        from app import socketio
        stats = db.get_stats(event_id)
        socketio.emit('guest_added', {
            'guest_id': guest_id,
            'stats': stats
        }, room=f'event_{event_id}')
        
        return jsonify({
            'success': True,
            'guest_id': guest_id,
            'message': 'Invité ajouté avec succès'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})