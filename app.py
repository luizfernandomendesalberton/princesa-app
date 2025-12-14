import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from functools import wraps

# Variável global para tipo de banco
USING_SQLITE = False

def get_param_placeholder():
    """Retorna o placeholder correto para parâmetros SQL"""
    # Detectar tipo de conexão via DATABASE_URL ou variáveis de ambiente
    db_url = os.environ.get('DATABASE_URL', '')
    is_sqlite = ('External Database URL' in db_url or 
                 len(db_url) < 20 or 
                 not os.environ.get('PGHOST'))
    return "?" if is_sqlite else "%s"

# Função helper para converter resultados do cursor em dicionários
def cursor_to_dict(cursor, row):
    """Converte uma linha do cursor em dicionário (PostgreSQL ou SQLite)"""
    if row is None:
        return None
    
    # SQLite com row_factory já retorna dict-like
    if hasattr(row, 'keys'):
        return dict(row)
    
    # PostgreSQL - converter manualmente
    return dict(zip([desc[0] for desc in cursor.description], row))

def cursor_to_dict_list(cursor, rows):
    """Converte múltiplas linhas do cursor em lista de dicionários"""
    if not rows:
        return []
    
    # Se já é SQLite Row objects
    if rows and hasattr(rows[0], 'keys'):
        return [dict(row) for row in rows]
    
    # PostgreSQL - converter manualmente
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]

app = Flask(__name__, template_folder='templates', static_folder='static')

# Configuração para produção
app.secret_key = os.environ.get('SECRET_KEY', 'princesa_ana_paula_2025_secret_key_muito_segura')

# Middleware simplificado para garantir que o banco esteja sempre inicializado
@app.before_request
def ensure_database():
    """Garante que o banco esteja inicializado - executa apenas uma vez por instância"""
    if not hasattr(app, 'db_initialized'):
        try:
            print("🔄 Verificando inicialização do banco (primeira vez)...")
            # Detectar tipo de banco
            global USING_SQLITE
            db_url = os.environ.get('DATABASE_URL', '')
            USING_SQLITE = ('External Database URL' in db_url or len(db_url) < 20)
            
            if USING_SQLITE:
                # Para SQLite, sempre reinicializar no Render para garantir dados
                init_db()
                print("✅ SQLite reinicializado!")
            else:
                # PostgreSQL - verificar se precisa inicializar
                connection = get_db_connection()
                if connection:
                    cursor = connection.cursor()
                    cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'users'")
                    if cursor.fetchone()[0] == 0:
                        init_db()
                        print("✅ PostgreSQL inicializado!")
                    cursor.close()
                    connection.close()
            
            app.db_initialized = True
            print("✅ Banco verificado e pronto!")
        except Exception as e:
            print(f"❌ Erro na inicialização do banco: {e}")
            app.db_initialized = True  # Evitar loop infinito

# Filtros customizados para templates
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

@app.template_filter('format_date')
def format_date(date_value):
    """Formata data compatível com SQLite (string) e PostgreSQL (datetime)"""
    if not date_value:
        return 'Sem data'
    
    # Se já é string (SQLite), tentar converter para datetime
    if isinstance(date_value, str):
        try:
            from datetime import datetime
            # Tentar diferentes formatos de data
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']:
                try:
                    date_obj = datetime.strptime(date_value, fmt)
                    return date_obj.strftime('%d/%m/%Y')
                except ValueError:
                    continue
            # Se não conseguiu converter, retorna a string original
            return date_value
        except:
            return date_value
    
    # Se é datetime (PostgreSQL)
    if hasattr(date_value, 'strftime'):
        return date_value.strftime('%d/%m/%Y')
    
    return str(date_value)

def get_db_connection():
    """Cria conexão com o banco de dados com múltiplas estratégias incluindo SQLite fallback"""
    
    # Debug completo da DATABASE_URL
    if os.environ.get('DATABASE_URL'):
        db_url = os.environ['DATABASE_URL']
        print(f"🔍 DATABASE_URL completa: {db_url}")
        print(f"🔍 Tipo: {type(db_url)}, Tamanho: {len(db_url)}")
        
        # Verificar se é uma URL válida ou placeholder
        if 'External Database URL' in db_url or len(db_url) < 20:
            print("🚨 DATABASE_URL é um placeholder - usando SQLite")
        else:
            # Tentar conexão PostgreSQL
            return try_postgresql_connection(db_url)
    
    # Estratégia 1: Variáveis PG individuais
    if all(os.environ.get(var) for var in ['PGHOST', 'PGDATABASE', 'PGUSER', 'PGPASSWORD']):
        try:
            connection = psycopg2.connect(
                host=os.environ['PGHOST'],
                port=os.environ.get('PGPORT', 5432),
                database=os.environ['PGDATABASE'], 
                user=os.environ['PGUSER'],
                password=os.environ['PGPASSWORD'],
                sslmode='require'
            )
            print("✅ Conectado via variáveis PG individuais")
            return connection
        except Exception as e:
            print(f"❌ Falha nas variáveis PG: {e}")
    
    # Fallback para SQLite (funciona sempre)
    print("🖾 Usando SQLite como fallback")
    return get_sqlite_connection()

def try_postgresql_connection(database_url):
    """Tenta conexão PostgreSQL com diferentes métodos"""
    try:
        # Fix postgres:// → postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        # Tentar diferentes métodos de conexão
        connection_methods = [
            lambda: psycopg2.connect(database_url),
            lambda: psycopg2.connect(**parse_database_url(database_url)),
            lambda: psycopg2.connect(database_url.replace('?sslmode=require', '')),
        ]
        
        for i, method in enumerate(connection_methods, 1):
            try:
                connection = method()
                print(f"✅ PostgreSQL conectado via método {i}")
                return connection
            except Exception as e:
                print(f"❌ Método PostgreSQL {i} falhou: {e}")
                
    except Exception as e:
        print(f"❌ Erro geral PostgreSQL: {e}")
    
    # Se PostgreSQL falhou, usar SQLite
    print("🖾 PostgreSQL falhou - usando SQLite")
    return get_sqlite_connection()

def get_sqlite_connection():
    """Cria conexão SQLite como fallback"""
    try:
        # Usar caminho absoluto para persistência melhor
        import tempfile
        db_dir = os.environ.get('DATABASE_DIR', tempfile.gettempdir())
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, 'princesa.db')
        
        connection = sqlite3.connect(db_path, timeout=20.0)
        connection.row_factory = sqlite3.Row  # Para acessar colunas por nome
        connection.execute('PRAGMA journal_mode=WAL')  # Melhor para concorrência
        connection.execute('PRAGMA synchronous=NORMAL')  # Melhor performance
        print(f"✅ SQLite conectado: {db_path}")
        return connection
    except Exception as e:
        print(f"❌ Erro no SQLite: {e}")
        return None

def parse_database_url(url):
    """Parse manual da DATABASE_URL"""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    
    return {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'database': parsed.path[1:] if parsed.path.startswith('/') else parsed.path,
        'user': parsed.username,
        'password': parsed.password,
        'sslmode': 'require'
    }

def init_sqlite_db(connection):
    """Inicializa banco SQLite com tabelas adaptadas"""
    try:
        cursor = connection.cursor()
        print(f"🛠️ Inicializando tabelas SQLite...")
        
        # Tabelas SQLite
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT NOT NULL,
                description TEXT,
                completed BOOLEAN DEFAULT 0,
                priority TEXT DEFAULT 'media',
                due_date DATE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS routines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT NOT NULL,
                description TEXT,
                time_schedule TEXT,
                days_of_week TEXT,
                active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS routine_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                routine_id INTEGER,
                executed_date DATE,
                executed_time TEXT,
                notes TEXT,
                FOREIGN KEY (routine_id) REFERENCES routines(id) ON DELETE CASCADE
            )
        """)
        
        # Criar usuários padrão (sempre recria para garantir persistência no Render)
        # Limpar e recriar usuários padrão para evitar problemas de persistência
        cursor.execute("DELETE FROM users WHERE username IN ('admin', 'ana_paula')")
        
        # Admin
        admin_password = generate_password_hash('admin2025')
        cursor.execute("INSERT INTO users (username, password_hash, name) VALUES (?, ?, ?)",
                     ('admin', admin_password, 'Administrador'))
        print("👑 Admin SQLite criado")
        
        # Ana Paula
        user_password = generate_password_hash('princesa123')
        cursor.execute("INSERT INTO users (username, password_hash, name) VALUES (?, ?, ?)",
                     ('ana_paula', user_password, 'Ana Paula Schlickmann Michels'))
        print("✅ Ana Paula SQLite criada")
        
        connection.commit()
        cursor.close()
        connection.close()
        print("✅ SQLite inicializado com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro SQLite: {e}")
        return False

def init_db():
    """Inicializa o banco de dados com as tabelas necessárias"""
    connection = get_db_connection()
    if connection:
        # Detectar se é SQLite
        global USING_SQLITE
        USING_SQLITE = hasattr(connection, 'row_factory')
        
        if USING_SQLITE:
            print("🗄️ Inicializando SQLite")
            return init_sqlite_db(connection)
        else:
            print("🗄️ Inicializando PostgreSQL")
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
            admin_password = generate_password_hash('admin2025')
            cursor.execute("""
                INSERT INTO users (username, password_hash, name) 
                VALUES ('admin', %s, 'Administrador')
            """, (admin_password,))
        
        # Verificar e recriar usuário ana_paula se necessário
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'ana_paula'")
        user_exists = cursor.fetchone()[0] > 0
        
        if user_exists:
            # Deletar usuário existente para recriar com senha correta
            cursor.execute("DELETE FROM users WHERE username = 'ana_paula'")
            print("🔄 Usuário ana_paula removido para recriação")
        
        # Criar usuário ana_paula
        hashed_password = generate_password_hash('princesa123')
        cursor.execute("""
            INSERT INTO users (username, password_hash, name) 
            VALUES ('ana_paula', %s, 'Ana Paula Schlickmann Michels')
            RETURNING id
        """, (hashed_password,))
        
        # Inserir dados de exemplo apenas para usuário novo
        user_id = cursor.fetchone()[0]
        print(f"✅ Usuário ana_paula criado com ID: {user_id}")
        
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
    """Rota para verificar saúde da aplicação com diagnóstico completo"""
    try:
        # Informações detalhadas do ambiente
        env_info = {
            'DATABASE_URL': bool(os.environ.get('DATABASE_URL')),
            'DATABASE_URL_sample': os.environ.get('DATABASE_URL', '')[:30] + "..." if os.environ.get('DATABASE_URL') else 'N/A',
            'PGHOST': os.environ.get('PGHOST', 'N/A'),
            'PGDATABASE': os.environ.get('PGDATABASE', 'N/A'), 
            'PGUSER': os.environ.get('PGUSER', 'N/A'),
            'PGPASSWORD': bool(os.environ.get('PGPASSWORD')),
            'PGPORT': os.environ.get('PGPORT', 'N/A'),
            'all_pg_vars': all(os.environ.get(var) for var in ['PGHOST', 'PGDATABASE', 'PGUSER', 'PGPASSWORD'])
        }
        
        # Testar conexão com banco
        print("🔍 Testando conexão via health check...")
        connection = get_db_connection()
        
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT version()")
            db_version = cursor.fetchone()[0]
            
            # Testar se tabelas existem
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = [row[0] for row in cursor.fetchall()]
            
            cursor.close()
            connection.close()
            
            return {
                "status": "✅ OK", 
                "database": "CONECTADO",
                "db_version": db_version[:50] + "..." if len(db_version) > 50 else db_version,
                "tables_found": tables,
                "env_info": env_info
            }, 200
        else:
            return {
                "status": "❌ ERRO", 
                "database": "DESCONECTADO",
                "env_info": env_info,
                "message": "Todas as estratégias de conexão falharam",
                "suggestion": "Verifique se o banco PostgreSQL está configurado no Render"
            }, 500
            
    except Exception as e:
        return {
            "status": "❌ ERRO CRÍTICO",
            "error": str(e),
            "env_info": env_info if 'env_info' in locals() else {},
            "message": "Erro na execução do health check"
        }, 500

@app.route('/')
def index():
    try:
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))
    except Exception as e:
        print(f"Erro na rota index: {e}")
        return f"Erro interno: {str(e)}", 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        
        if not username or not password or not name:
            flash('Todos os campos são obrigatórios!', 'error')
            return render_template('register.html')
        
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor()
                # Verificar se usuário já existe
                placeholder = get_param_placeholder()
                cursor.execute(f"SELECT id FROM users WHERE username = {placeholder}", (username,))
                if cursor.fetchone():
                    flash('Nome de usuário já existe!', 'error')
                    return render_template('register.html')
                
                # Criar novo usuário
                hashed_password = generate_password_hash(password)
                placeholder = get_param_placeholder()
                print(f"🔍 Tentando cadastrar usuário: {username}")
                cursor.execute(f"INSERT INTO users (username, password_hash, name) VALUES ({placeholder}, {placeholder}, {placeholder})", (username, hashed_password, name))
                connection.commit()
                print(f"✅ Usuário {username} cadastrado com sucesso!")
                cursor.close()
                connection.close()
                
                flash('Usuário cadastrado com sucesso! Faça login agora.', 'success')
                return redirect(url_for('login'))
                
            except Exception as e:
                flash(f'Erro ao cadastrar usuário: {str(e)}', 'error')
                return render_template('register.html')
        else:
            flash('Erro de conexão com o banco de dados!', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            placeholder = get_param_placeholder()
            cursor.execute(f"SELECT id, username, name, password_hash FROM users WHERE username = {placeholder}", (username,))
            user_row = cursor.fetchone()
            
            print(f"🔍 Login attempt - User: {username}")
            print(f"🔍 User found in DB: {bool(user_row)}")
            
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
                if user_row:
                    flash('Senha incorreta! Tente: princesa123 🚫', 'error')
                else:
                    flash(f'Usuário "{username}" não encontrado! Use o botão de cadastro. 🚫', 'error')
                
            cursor.close()
            connection.close()
        else:
            flash('Erro de conexão com o banco de dados! Verifique os logs.', 'error')
    
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
        placeholder = get_param_placeholder()
        cursor.execute(f"""
            SELECT * FROM tasks 
            WHERE user_id = {placeholder} AND completed = {'0' if USING_SQLITE else 'FALSE'} 
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
        
        placeholder = get_param_placeholder()
        cursor.execute(f"""
            SELECT * FROM routines 
            WHERE user_id = {placeholder} AND active = {'1' if USING_SQLITE else 'TRUE'} 
            AND days_of_week LIKE {placeholder}
            ORDER BY time_schedule ASC
        """, (session['user_id'], f'%{today_pt}%'))
        today_routines = cursor_to_dict_list(cursor, cursor.fetchall())
        
        cursor.close()
        connection.close()
    
    return render_template('dashboard.html', 
                         tasks=tasks_pending, 
                         routines=today_routines,
                         user_name=session.get('name', ''))

@app.route('/tasks')
@login_required
def tasks():
    connection = get_db_connection()
    tasks = []
    
    if connection:
        cursor = connection.cursor()
        placeholder = get_param_placeholder()
        cursor.execute(f"""
            SELECT * FROM tasks 
            WHERE user_id = {placeholder} 
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
        placeholder = get_param_placeholder()
        print(f"🔍 Adicionando tarefa: {title} para usuário {session['user_id']}")
        cursor.execute(f"""
            INSERT INTO tasks (user_id, title, description, priority, due_date)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        """, (session['user_id'], title, description, priority, due_date))
        print(f"✅ Tarefa adicionada com sucesso!")
        connection.commit()
        cursor.close()
        connection.close()
        flash('Tarefa adicionada com sucesso! ✨', 'success')
    
    return redirect(url_for('tasks'))

@app.route('/toggle_task/<int:task_id>')
@login_required
def toggle_task(task_id):
    connection = get_db_connection()
    success = False
    
    if connection:
        cursor = connection.cursor()
        placeholder = get_param_placeholder()
        print(f"🔄 Alternando status da tarefa {task_id}")
        cursor.execute(f"""
            UPDATE tasks SET completed = NOT completed 
            WHERE id = {placeholder} AND user_id = {placeholder}
        """, (task_id, session['user_id']))
        connection.commit()
        cursor.close()
        connection.close()
        success = True
        flash('Status da tarefa atualizada! 👑', 'success')
    
    # Se for uma requisição AJAX, retornar JSON
    if request.headers.get('Content-Type') == 'application/json':
        return jsonify({'success': success})
    
    return redirect(url_for('tasks'))

@app.route('/delete_task/<int:task_id>')
@login_required
def delete_task(task_id):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        placeholder = get_param_placeholder()
        cursor.execute(f"DELETE FROM tasks WHERE id = {placeholder} AND user_id = {placeholder}", (task_id, session['user_id']))
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
        placeholder = get_param_placeholder()
        cursor.execute(f"""
            SELECT * FROM routines 
            WHERE user_id = {placeholder} 
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
        placeholder = get_param_placeholder()
        print(f"🔍 Adicionando rotina: {title} para usuário {session['user_id']}")
        cursor.execute(f"""
            INSERT INTO routines (user_id, title, description, time_schedule, days_of_week)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        """, (session['user_id'], title, description, time_schedule or None, days_of_week))
        print(f"✅ Rotina adicionada com sucesso!")
        connection.commit()
        cursor.close()
        connection.close()
        flash('Rotina adicionada com sucesso! 📅', 'success')
    
    return redirect(url_for('routines'))

@app.route('/toggle_routine/<int:routine_id>')
@login_required
def toggle_routine(routine_id):
    connection = get_db_connection()
    success = False
    
    if connection:
        cursor = connection.cursor()
        placeholder = get_param_placeholder()
        print(f"🔄 Alternando status da rotina {routine_id}")
        cursor.execute(f"""
            UPDATE routines SET active = NOT active 
            WHERE id = {placeholder} AND user_id = {placeholder}
        """, (routine_id, session['user_id']))
        connection.commit()
        cursor.close()
        connection.close()
        success = True
        flash('Status da rotina atualizada! ⚡', 'success')
    
    # Se for uma requisição AJAX, retornar JSON
    if request.headers.get('Content-Type') == 'application/json':
        return jsonify({'success': success})
    
    return redirect(url_for('routines'))

@app.route('/delete_routine/<int:routine_id>')
@login_required
def delete_routine(routine_id):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        placeholder = get_param_placeholder()
        print(f"🗑️ Deletando rotina {routine_id}")
        cursor.execute(f"DELETE FROM routines WHERE id = {placeholder} AND user_id = {placeholder}", (routine_id, session['user_id']))
        connection.commit()
        cursor.close()
        connection.close()
        flash('Rotina removida! 🗑️', 'success')
    
    return redirect(url_for('routines'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin_password = request.form['admin_password']
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE username = 'admin'")
            admin_row = cursor.fetchone()
            
            # Converter para dict se necessário
            if admin_row:
                admin = cursor_to_dict(cursor, admin_row)
                
                if admin and check_password_hash(admin['password_hash'], admin_password):
                    session['is_admin'] = True
                    flash('Login de administrador realizado com sucesso! 👑', 'success')
                    cursor.close()
                    connection.close()
                    return redirect(url_for('admin_dashboard'))
                else:
                    flash('Senha de administrador incorreta! Use: admin2025', 'error')
            else:
                flash('Usuário admin não encontrado no banco!', 'error')
            
            cursor.close()
            connection.close()
        else:
            flash('Erro de conexão com banco!', 'error')
    
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
        users_raw = cursor_to_dict_list(cursor, cursor.fetchall())
        
        # Formatar datas para SQLite se necessário
        users = []
        for user in users_raw:
            user_dict = dict(user)
            if USING_SQLITE and user_dict.get('created_at'):
                # SQLite retorna string, vamos formatar para display
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(user_dict['created_at'].replace('Z', '+00:00'))
                    user_dict['created_at_formatted'] = dt.strftime('%d/%m/%Y às %H:%M')
                except:
                    user_dict['created_at_formatted'] = user_dict['created_at'][:19]  # Primeiro 19 chars
            users.append(user_dict)
        
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
        
        placeholder = get_param_placeholder()
        print(f"🔍 Alterando senha do usuário ID: {user_id}")
        cursor.execute(f"UPDATE users SET password_hash = {placeholder} WHERE id = {placeholder}", 
                      (hashed_password, user_id))
        
        rows_affected = cursor.rowcount
        connection.commit()
        print(f"✅ Senha alterada! Linhas afetadas: {rows_affected}")
        cursor.close()
        connection.close()
        flash('Senha alterada com sucesso! ✅', 'success')
    else:
        flash('Erro ao conectar com o banco de dados! ❌', 'error')
    
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