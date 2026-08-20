from flask import Flask, session, redirect, url_for, request, render_template
from flask_socketio import SocketIO
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'eventcheck2024')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('main.index'))
        return render_template('login.html', error='Mot de passe incorrect')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('login'))

@app.before_request
def require_login():
    if not request.path.startswith('/api/') and not request.path.startswith('/static/'):
        allowed_routes = ['login', 'static']
        if request.endpoint not in allowed_routes and 'admin' not in session:
            if request.endpoint != 'login':
                return redirect(url_for('login'))

from routes import main
app.register_blueprint(main)

@socketio.on('connect')
def handle_connect():
    print('Client connecté')

@socketio.on('join_event')
def handle_join_event(data):
    event_id = data.get('event_id')
    if event_id:
        from flask_socketio import join_room
        join_room(f'event_{event_id}')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client déconnecté')

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)