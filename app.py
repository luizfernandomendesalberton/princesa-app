import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from functools import wraps

# Função helper para converter resultados do cursor em dicionários
def cursor_to_dict(cursor, row):
    """Converte uma linha do cursor PostgreSQL em dicionário"""
    if row is None:
        return None
    return dict(zip([desc[0] for desc in cursor.description], row))

def cursor_to_dict_list(cursor, rows):
    """Converte múltiplas linhas do cursor PostgreSQL em lista de dicionários"""
    if not rows:
        return []
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]

app = Flask(__name__, template_folder='templates', static_folder='static')

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

def get_db_connection():
    """Cria conexão com o banco de dados"""
    try:
        if os.environ.get('DATABASE_URL'):
            # Produção (PostgreSQL no Render)
            database_url = os.environ['DATABASE_URL']
            # Fix para URLs do Render que podem usar postgres:// ao invés de postgresql://
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            
            connection = psycopg2.connect(
                database_url,
                sslmode='require'  # Render requer SSL
            )
        else:
            # Desenvolvimento local (PostgreSQL local)
            connection = psycopg2.connect(
                host='localhost',
                database='princesa_db',
                user='postgres', 
                password='sua_senha_local'
            )
        
        return connection
    except psycopg2.Error as err:
        print(f"Erro ao conectar com o banco: {err}")
        return None
    except Exception as e:
        print(f"Erro geral na conexão: {e}")
        return None

def init_db():
    """Inicializa o banco de dados com as tabelas necessárias"""
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        
        # Tabela de usuários (PostgreSQL syntax)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                name VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de tarefas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                completed BOOLEAN DEFAULT FALSE,
                priority VARCHAR(10) DEFAULT 'media' CHECK (priority IN ('baixa', 'media', 'alta')),
                due_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de rotinas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS routines (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                time_schedule TIME,
                days_of_week TEXT,
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de execução de rotinas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS routine_executions (
                id SERIAL PRIMARY KEY,
                routine_id INTEGER REFERENCES routines(id) ON DELETE CASCADE,
                executed_date DATE,
                executed_time TIME,
                notes TEXT
            )
        """)
        
        # Criar trigger para updated_at (PostgreSQL)
        cursor.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """)
        
        cursor.execute("""
            DROP TRIGGER IF EXISTS update_tasks_updated_at ON tasks;
            CREATE TRIGGER update_tasks_updated_at 
                BEFORE UPDATE ON tasks 
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """)
        
        # Criar usuário admin se não existir
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        admin_exists = cursor.fetchone()[0] > 0
        
        if not admin_exists:
            admin_password = generate_password_hash('admin123')
            cursor.execute("""
                INSERT INTO users (username, password_hash, name) 
                VALUES ('admin', %s, 'Administrador')
            """, (admin_password,))
        
        # Criar usuário padrão apenas se não existir
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'ana_paula'")
        user_exists = cursor.fetchone()[0] > 0
        
        if not user_exists:
            hashed_password = generate_password_hash('princesa123')
            cursor.execute("""
                INSERT INTO users (username, password_hash, name) 
                VALUES ('ana_paula', %s, 'Ana Paula Schlickmann Michels')
                RETURNING id
            """, (hashed_password,))
            
            # Inserir dados de exemplo apenas para usuário novo
            user_id = cursor.fetchone()[0]
            
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
@app.route('/health')
def health_check():
    """Rota para verificar saúde da aplicação"""
    try:
        # Testar conexão com banco
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            connection.close()
            return "OK - Banco conectado", 200
        else:
            return "ERRO - Falha na conexão com banco", 500
    except Exception as e:
        return f"ERRO - {str(e)}", 500

@app.route('/')
def index():
    try:
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))
    except Exception as e:
        print(f"Erro na rota index: {e}")
        return f"Erro interno: {str(e)}", 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT id, username, name, password_hash FROM users WHERE username = %s", (username,))
            user_row = cursor.fetchone()
            
            if user_row and check_password_hash(user_row[3], password):
                user = {
                    'id': user_row[0],
                    'username': user_row[1], 
                    'name': user_row[2],
                    'password_hash': user_row[3]
                }
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
        cursor = connection.cursor()
        
        # Buscar tarefas pendentes
        cursor.execute("""
            SELECT * FROM tasks 
            WHERE user_id = %s AND completed = FALSE 
            ORDER BY due_date ASC, priority DESC
            LIMIT 5
        """, (session['user_id'],))
        tasks_pending = cursor_to_dict_list(cursor, cursor.fetchall())
        
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
            AND days_of_week LIKE %s
            ORDER BY time_schedule ASC
        """, (session['user_id'], f'%{today_pt}%'))
        today_routines = cursor_to_dict_list(cursor, cursor.fetchall())
        
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
    tasks = []
    
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT * FROM tasks 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """, (session['user_id'],))
        tasks = cursor_to_dict_list(cursor, cursor.fetchall())
        cursor.close()
        connection.close()
    
    return render_template('tasks.html', tasks=tasks)

@app.route('/add_task', methods=['POST'])
@login_required
def add_task():
    title = request.form.get('title')
    description = request.form.get('description', '')
    priority = request.form.get('priority', 'media')
    due_date = request.form.get('due_date')
    
    if not title:
        flash('Título da tarefa é obrigatório!', 'error')
        return redirect(url_for('tasks'))
    
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO tasks (user_id, title, description, priority, due_date)
            VALUES (%s, %s, %s, %s, %s)
        """, (session['user_id'], title, description, priority, due_date or None))
        connection.commit()
        cursor.close()
        connection.close()
        flash('Tarefa adicionada com sucesso! ✨', 'success')
    
    return redirect(url_for('tasks'))

@app.route('/toggle_task/<int:task_id>')
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
        flash('Status da tarefa atualizado! 👑', 'success')
    
    return redirect(url_for('tasks'))

@app.route('/delete_task/<int:task_id>')
@login_required
def delete_task(task_id):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = %s AND user_id = %s", (task_id, session['user_id']))
        connection.commit()
        cursor.close()
        connection.close()
        flash('Tarefa removida! 🗑️', 'success')
    
    return redirect(url_for('tasks'))

@app.route('/routines')
@login_required
def routines():
    connection = get_db_connection()
    routines = []
    
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT * FROM routines 
            WHERE user_id = %s 
            ORDER BY time_schedule ASC
        """, (session['user_id'],))
        routines = cursor_to_dict_list(cursor, cursor.fetchall())
        cursor.close()
        connection.close()
    
    return render_template('routines.html', routines=routines)

@app.route('/add_routine', methods=['POST'])
@login_required
def add_routine():
    title = request.form.get('title')
    description = request.form.get('description', '')
    time_schedule = request.form.get('time_schedule')
    days_of_week = ','.join(request.form.getlist('days_of_week'))
    
    if not title:
        flash('Título da rotina é obrigatório!', 'error')
        return redirect(url_for('routines'))
    
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO routines (user_id, title, description, time_schedule, days_of_week)
            VALUES (%s, %s, %s, %s, %s)
        """, (session['user_id'], title, description, time_schedule or None, days_of_week))
        connection.commit()
        cursor.close()
        connection.close()
        flash('Rotina adicionada com sucesso! 📅', 'success')
    
    return redirect(url_for('routines'))

@app.route('/toggle_routine/<int:routine_id>')
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
        flash('Status da rotina atualizado! ⚡', 'success')
    
    return redirect(url_for('routines'))

@app.route('/delete_routine/<int:routine_id>')
@login_required
def delete_routine(routine_id):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM routines WHERE id = %s AND user_id = %s", (routine_id, session['user_id']))
        connection.commit()
        cursor.close()
        connection.close()
        flash('Rotina removida! 🗑️', 'success')
    
    return redirect(url_for('routines'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin_password = request.form['admin_password']
        
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
        cursor = connection.cursor()
        cursor.execute("SELECT id, username, name, created_at FROM users ORDER BY created_at DESC")
        users = cursor_to_dict_list(cursor, cursor.fetchall())
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
    print("Iniciando aplicação Princesa...")
    # Inicializar DB em desenvolvimento
    if not os.environ.get('DATABASE_URL'):
        print("Modo desenvolvimento - inicializando DB local")
        init_db()
    
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    app.run(debug=debug, host='0.0.0.0', port=port)
else:
    # Em produção, inicializar DB na primeira carga
    print("Modo produção - inicializando DB")
    try:
        init_db()
        print("✅ Banco inicializado com sucesso em produção!")
    except Exception as e:
        print(f"❌ Erro ao inicializar banco: {e}")