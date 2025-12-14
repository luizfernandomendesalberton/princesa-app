import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__, template_folder='../templates', static_folder='../static')

# Configuração para produção
app.secret_key = os.environ.get('SECRET_KEY', 'princesa_ana_paula_2025_secret_key_muito_segura')

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

# Configuração do banco de dados para produção
def get_db_config():
    if os.environ.get('DATABASE_URL'):
        # Produção (Render/Railway com MySQL)
        return {
            'host': os.environ.get('DB_HOST', 'localhost'),
            'user': os.environ.get('DB_USER', 'root'),
            'password': os.environ.get('DB_PASSWORD', ''),
            'database': os.environ.get('DB_NAME', 'princesa_db'),
            'port': int(os.environ.get('DB_PORT', 3306))
        }
    else:
        # Desenvolvimento local
        return {
            'host': 'localhost',
            'user': 'root',
            'password': 'ecalfma',
            'database': 'princesa_db'
        }

def get_db_connection():
    """Cria conexão com o banco de dados"""
    try:
        db_config = get_db_config()
        connection = mysql.connector.connect(**db_config)
        return connection
    except mysql.connector.Error as err:
        print(f"Erro ao conectar com o banco: {err}")
        return None

def init_db():
    """Inicializa o banco de dados com as tabelas necessárias"""
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        
        # Criar database se não existir (apenas em desenvolvimento)
        if not os.environ.get('DATABASE_URL'):
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
        
        # Criar usuário padrão apenas se não existir
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'ana_paula'")
        user_exists = cursor.fetchone()[0] > 0
        
        if not user_exists:
            hashed_password = generate_password_hash('princesa123')
            cursor.execute("""
                INSERT INTO users (username, password_hash, name) 
                VALUES ('ana_paula', %s, 'Ana Paula Schlickmann Michels')
            """, (hashed_password,))
            
            # Inserir dados de exemplo apenas para usuário novo
            user_id = cursor.lastrowid
            
            # Tarefas de exemplo
            tasks_example = [
                ('💄 Rotina de skincare matinal', 'Limpeza, hidratante e protetor solar', 'alta', datetime.now().date()),
                ('👗 Escolher look do dia', 'Combinar roupas e acessórios lindos', 'media', datetime.now().date()),
                ('📚 Estudar 30 minutos', 'Focar nos estudos importantes', 'alta', datetime.now().date()),
                ('🥗 Preparar almoço saudável', 'Cozinhar algo nutritivo e gostoso', 'media', datetime.now().date()),
                ('🧘‍♀️ Momento de relaxamento', '15 minutos de meditação ou respiração', 'baixa', datetime.now().date())
            ]
            
            for task in tasks_example:
                cursor.execute("""
                    INSERT INTO tasks (user_id, title, description, priority, due_date)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, task[0], task[1], task[2], task[3]))
            
            # Rotinas de exemplo
            routines_example = [
                ('☀️ Acordar como uma princesa', 'Levantar cedo e começar o dia com energia', '07:00:00', 'segunda,terca,quarta,quinta,sexta,sabado,domingo'),
                ('💄 Skincare matinal', 'Rotina de cuidados com a pele pela manhã', '07:30:00', 'segunda,terca,quarta,quinta,sexta,sabado,domingo'),
                ('🍎 Café da manhã nutritivo', 'Tomar um café da manhã saudável e saboroso', '08:00:00', 'segunda,terca,quarta,quinta,sexta,sabado,domingo'),
                ('💪 Exercícios ou alongamento', '20 minutos de atividade física', '18:00:00', 'segunda,quarta,sexta'),
                ('🌙 Skincare noturno', 'Rotina de cuidados noturnos', '21:30:00', 'segunda,terca,quarta,quinta,sexta,sabado,domingo')
            ]
            
            for routine in routines_example:
                cursor.execute("""
                    INSERT INTO routines (user_id, title, description, time_schedule, days_of_week)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, routine[0], routine[1], routine[2], routine[3]))
        
        connection.commit()
        cursor.close()
        connection.close()
        print("Banco de dados inicializado com sucesso!")
        return True
    else:
        print("Erro: Não foi possível conectar com o banco de dados!")
        return False

# Decorator para rotas que precisam de login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Rotas da aplicação
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
                flash('Login realizado com sucesso! Bem-vinda, Princesa! 👑', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Usuário ou senha incorretos! 😔', 'error')
            
            cursor.close()
            connection.close()
        else:
            flash('Erro de conexão com o banco de dados!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso! Até logo, Princesa! 👋', 'info')
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

# [Resto das rotas permanece igual - apenas mudando get_db_connection()]

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

# Health check para monitoramento
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'app': 'Princesa Ana Paula'}, 200

if __name__ == '__main__':
    # Inicializar DB apenas em desenvolvimento
    if not os.environ.get('DATABASE_URL'):
        init_db()
    
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    app.run(debug=debug, host='0.0.0.0', port=port)