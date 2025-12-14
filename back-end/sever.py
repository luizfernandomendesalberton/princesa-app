from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from datetime import datetime, timedelta
import os
from functools import wraps

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = 'princesa_ana_paula_2025_secret_key_muito_segura'

# Filtro customizado para formatar timedelta
@app.template_filter('format_time')
def format_time(time_value):
    """Formata timedelta ou time para HH:MM"""
    if time_value is None:
        return '---'
    
    if hasattr(time_value, 'seconds'):  # timedelta
        hours, remainder = divmod(time_value.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}"
    elif hasattr(time_value, 'strftime'):  # datetime/time
        return time_value.strftime('%H:%M')
    else:
        return str(time_value)

# Configuração do banco de dados
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # Altere conforme sua configuração
    'password': 'ecalfma',  # Adicione sua senha do MySQL
    'database': 'princesa_db'
}

def get_db_connection():
    """Cria conexão com o banco de dados"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except mysql.connector.Error as err:
        print(f"Erro ao conectar com o banco: {err}")
        return None

def init_db():
    """Inicializa o banco de dados com as tabelas necessárias"""
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        
        # Criar database se não existir
        cursor.execute("CREATE DATABASE IF NOT EXISTS princesa_db")
        cursor.execute("USE princesa_db")
        
        # Tabela de usuários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                name VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de tarefas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                completed BOOLEAN DEFAULT FALSE,
                priority ENUM('baixa', 'media', 'alta') DEFAULT 'media',
                due_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Tabela de rotinas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS routines (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                time_schedule TIME,
                days_of_week SET('segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo'),
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Tabela de execução de rotinas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS routine_executions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                routine_id INT,
                executed_date DATE,
                executed_time TIME,
                notes TEXT,
                FOREIGN KEY (routine_id) REFERENCES routines(id) ON DELETE CASCADE
            )
        """)
        
        # Criar usuário padrão para Ana Paula (senha: princesa123)
        hashed_password = generate_password_hash('princesa123')
        cursor.execute("""
            INSERT IGNORE INTO users (username, password_hash, name) 
            VALUES ('ana_paula', %s, 'Ana Paula Schlickmann Michels')
        """, (hashed_password,))
        
        connection.commit()
        cursor.close()
        connection.close()
        print("Banco de dados inicializado com sucesso!")

def login_required(f):
    """Decorator para rotas que requerem login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['name'] = user['name']
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Usuário ou senha incorretos!', 'error')
            
            cursor.close()
            connection.close()
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    connection = get_db_connection()
    tasks_pending = []
    routines_today = []
    
    if connection:
        cursor = connection.cursor(dictionary=True)
        
        # Buscar tarefas pendentes
        cursor.execute("""
            SELECT * FROM tasks 
            WHERE user_id = %s AND completed = FALSE 
            ORDER BY due_date ASC, priority DESC
            LIMIT 5
        """, (session['user_id'],))
        tasks_pending = cursor.fetchall()
        
        # Buscar rotinas do dia
        today_name = datetime.now().strftime('%A').lower()
        day_mapping = {
            'monday': 'segunda',
            'tuesday': 'terca', 
            'wednesday': 'quarta',
            'thursday': 'quinta',
            'friday': 'sexta',
            'saturday': 'sabado',
            'sunday': 'domingo'
        }
        today_pt = day_mapping.get(today_name, 'segunda')
        
        cursor.execute("""
            SELECT * FROM routines 
            WHERE user_id = %s AND active = TRUE 
            AND FIND_IN_SET(%s, days_of_week) > 0
            ORDER BY time_schedule ASC
        """, (session['user_id'], today_pt))
        routines_today = cursor.fetchall()
        
        cursor.close()
        connection.close()
    
    return render_template('dashboard.html', 
                         tasks=tasks_pending, 
                         routines=routines_today,
                         user_name=session.get('name', ''))

@app.route('/tasks')
@login_required
def tasks():
    connection = get_db_connection()
    all_tasks = []
    
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM tasks 
            WHERE user_id = %s 
            ORDER BY completed ASC, due_date ASC, priority DESC
        """, (session['user_id'],))
        all_tasks = cursor.fetchall()
        cursor.close()
        connection.close()
    
    return render_template('tasks.html', tasks=all_tasks)

@app.route('/tasks/add', methods=['POST'])
@login_required
def add_task():
    title = request.form['title']
    description = request.form.get('description', '')
    priority = request.form.get('priority', 'media')
    due_date = request.form.get('due_date')
    
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO tasks (user_id, title, description, priority, due_date)
            VALUES (%s, %s, %s, %s, %s)
        """, (session['user_id'], title, description, priority, due_date if due_date else None))
        connection.commit()
        cursor.close()
        connection.close()
        flash('Tarefa adicionada com sucesso!', 'success')
    
    return redirect(url_for('tasks'))

@app.route('/tasks/toggle/<int:task_id>', methods=['POST'])
@login_required
def toggle_task(task_id):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE tasks SET completed = NOT completed 
            WHERE id = %s AND user_id = %s
        """, (task_id, session['user_id']))
        connection.commit()
        cursor.close()
        connection.close()
    
    return jsonify({'success': True})

@app.route('/tasks/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
            DELETE FROM tasks WHERE id = %s AND user_id = %s
        """, (task_id, session['user_id']))
        connection.commit()
        cursor.close()
        connection.close()
        flash('Tarefa removida!', 'info')
    
    return redirect(url_for('tasks'))

@app.route('/routines')
@login_required
def routines():
    connection = get_db_connection()
    all_routines = []
    
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM routines 
            WHERE user_id = %s 
            ORDER BY active DESC, time_schedule ASC
        """, (session['user_id'],))
        all_routines = cursor.fetchall()
        cursor.close()
        connection.close()
    
    return render_template('routines.html', routines=all_routines)

@app.route('/routines/add', methods=['POST'])
@login_required
def add_routine():
    title = request.form['title']
    description = request.form.get('description', '')
    time_schedule = request.form.get('time_schedule')
    days = request.form.getlist('days_of_week')
    days_str = ','.join(days) if days else ''
    
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO routines (user_id, title, description, time_schedule, days_of_week)
            VALUES (%s, %s, %s, %s, %s)
        """, (session['user_id'], title, description, time_schedule, days_str))
        connection.commit()
        cursor.close()
        connection.close()
        flash('Rotina adicionada com sucesso!', 'success')
    
    return redirect(url_for('routines'))

@app.route('/routines/toggle/<int:routine_id>', methods=['POST'])
@login_required
def toggle_routine(routine_id):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE routines SET active = NOT active 
            WHERE id = %s AND user_id = %s
        """, (routine_id, session['user_id']))
        connection.commit()
        cursor.close()
        connection.close()
    
    return jsonify({'success': True})

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin_password = request.form['admin_password']
        
        # Senha fixa do administrador (pode ser alterada depois)
        if admin_password == 'admin2025':
            session['is_admin'] = True
            flash('Login de administrador realizado com sucesso!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Senha de administrador incorreta!', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'is_admin' not in session:
        flash('Acesso negado! Faça login como administrador.', 'error')
        return redirect(url_for('admin_login'))
    
    connection = get_db_connection()
    users = []
    
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, username, name, created_at FROM users ORDER BY created_at DESC")
        users = cursor.fetchall()
        cursor.close()
        connection.close()
    
    return render_template('admin_dashboard.html', users=users)

@app.route('/admin/change_password', methods=['POST'])
def admin_change_password():
    if 'is_admin' not in session:
        return redirect(url_for('admin_login'))
    
    user_id = request.form['user_id']
    new_password = request.form['new_password']
    
    if not new_password or len(new_password) < 6:
        flash('A senha deve ter pelo menos 6 caracteres!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        hashed_password = generate_password_hash(new_password)
        cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (hashed_password, user_id))
        connection.commit()
        cursor.close()
        connection.close()
        flash('Senha alterada com sucesso!', 'success')
    else:
        flash('Erro ao conectar com o banco de dados!', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    flash('Logout de administrador realizado!', 'info')
    return redirect(url_for('login'))

# Rotas PWA
@app.route('/manifest.json')
def manifest():
    return app.send_static_file('manifest.json')

@app.route('/sw.js')
def service_worker():
    response = app.send_static_file('sw.js')
    response.headers['Cache-Control'] = 'no-cache'
    return response

@app.route('/offline')
def offline():
    return render_template('offline.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)