import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from functools import wraps
import secrets
import re
from urllib.parse import quote, unquote
import logging
from werkzeug.middleware.proxy_fix import ProxyFix
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import threading

# Carregar variáveis de ambiente
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Variáveis de ambiente carregadas")
except ImportError:
    print("⚠️ python-dotenv não disponível, usando variáveis do sistema")

# Variável global para tipo de banco
USING_SQLITE = False

# Configuração de logging para segurança
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
security_logger = logging.getLogger('security')

def log_security_event(event_type, user_id=None, details=None, ip_address=None):
    """Log de eventos de segurança"""
    log_message = f'Security Event: {event_type}'
    if user_id:
        log_message += f' | User ID: {user_id}'
    if ip_address:
        log_message += f' | IP: {ip_address}'
    if details:
        log_message += f' | Details: {details}'
    
    security_logger.info(log_message)

# Sistema de rate limiting simples
rate_limit_storage = {}

def is_rate_limited(ip_address, max_attempts=5, window_minutes=15):
    """Verifica se um IP está sendo limitado por rate limiting"""
    current_time = datetime.now()
    cleanup_time = current_time - timedelta(minutes=window_minutes)
    
    # Limpar registros antigos
    if ip_address in rate_limit_storage:
        rate_limit_storage[ip_address] = [
            attempt for attempt in rate_limit_storage[ip_address] 
            if attempt > cleanup_time
        ]
        
        # Verificar se excedeu o limite
        if len(rate_limit_storage[ip_address]) >= max_attempts:
            return True
    
    return False

def add_rate_limit_attempt(ip_address):
    """Adiciona uma tentativa de rate limiting para um IP"""
    current_time = datetime.now()
    
    if ip_address not in rate_limit_storage:
        rate_limit_storage[ip_address] = []
    
    rate_limit_storage[ip_address].append(current_time)

def record_login_attempt(ip_address):
    """Registra uma tentativa de login para rate limiting"""
    add_rate_limit_attempt(ip_address)

def is_protected_user(user_id):
    """Verifica se um usuário está protegido contra exclusão"""
    protected_users = [1, 2]  # IDs dos usuários admin e ana_paula
    return user_id in protected_users

def audit_user_operation(operation_type, user_id, admin_id, details=None):
    """Sistema de auditoria para operações de usuários"""
    log_security_event(f'USER_AUDIT_{operation_type}', 
                      user_id=admin_id, 
                      details=f'Target User ID: {user_id}, Operation: {operation_type}, Details: {details or "N/A"}')

# Sistema de Email
def send_email_notification(to_email, subject, message, notification_type='info'):
    """Envia notificação por email de forma assíncrona"""
    def send_async_email():
        try:
            # Configurações SMTP (usando Gmail como exemplo)
            smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.environ.get('SMTP_PORT', '587'))
            smtp_username = os.environ.get('SMTP_USERNAME', 'princesa.app.notifications@gmail.com')
            smtp_password = os.environ.get('SMTP_PASSWORD', '')
            
            if not smtp_password:
                print("⚠️ Email não configurado - SMTP_PASSWORD não definida")
                return False
            
            # Criar mensagem
            msg = MIMEMultipart('alternative')
            msg['From'] = f'Princesa App <{smtp_username}>'
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Template HTML lindinho
            html_template = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #ffeef8 0%, #f8e8ff 100%); }}
                    .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 15px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #ff69b4, #9c27b0); padding: 30px; text-align: center; color: white; }}
                    .header h1 {{ margin: 0; font-size: 28px; }}
                    .content {{ padding: 30px; }}
                    .notification {{ padding: 20px; border-radius: 10px; margin: 20px 0; }}
                    .routine {{ background: linear-gradient(135deg, #e8f5e8, #f0fff0); border-left: 4px solid #28a745; }}
                    .task {{ background: linear-gradient(135deg, #fff8e1, #fefefe); border-left: 4px solid #ffc107; }}
                    .footer {{ text-align: center; padding: 20px; color: #666; font-size: 14px; }}
                    .princess-icon {{ font-size: 24px; margin-right: 10px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>👑 Princesa App</h1>
                        <p>Suas Notificações Chegaram!</p>
                    </div>
                    <div class="content">
                        <div class="notification {notification_type}">
                            {message}
                        </div>
                        <p>Acesse o app para gerenciar suas tarefas e rotinas:</p>
                        <p><a href="https://princesa-app.onrender.com" style="color: #ff69b4; text-decoration: none; font-weight: bold;">🌸 Abrir Princesa App</a></p>
                    </div>
                    <div class="footer">
                        <p>💎 Enviado com amor pelo seu Princesa App</p>
                        <p>Para parar de receber notificações, acesse as configurações do app.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Anexar HTML
            html_part = MIMEText(html_template, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Enviar email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            log_security_event('EMAIL_SENT', details=f'Email sent to: {to_email}, Subject: {subject}')
            print(f"✉️ Email enviado para {to_email}: {subject}")
            return True
            
        except Exception as e:
            log_security_event('EMAIL_ERROR', details=f'Failed to send email to {to_email}: {str(e)}')
            print(f"❌ Erro ao enviar email: {e}")
            return False
    
    # Executar em thread separada para não bloquear o app
    email_thread = threading.Thread(target=send_async_email)
    email_thread.daemon = True
    email_thread.start()
    
def validate_input(input_str, max_length=255, allow_empty=True, input_type='text'):
    """Valida e limpa entrada do usuário com sanitização avançada"""
    if input_str is None:
        return "" if allow_empty else None
    
    # Converter para string e remover espaços
    cleaned = str(input_str).strip()
    
    # Verificar se vazio quando não permitido
    if not allow_empty and not cleaned:
        return None
    
    # Verificar tamanho máximo
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    
    # Sanitização baseada no tipo de input
    if input_type == 'username':
        # Username: apenas alfanuméricos e underscore
        import re
        cleaned = re.sub(r'[^a-zA-Z0-9_]', '', cleaned)
    elif input_type == 'email':
        # Email: validação básica
        if '@' not in cleaned or '.' not in cleaned.split('@')[-1]:
            return None if not allow_empty else ""
    elif input_type == 'text':
        # Sanitizar caracteres perigosos para XSS e SQL injection
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\n', '\r', '\t', ';', '--', '/*', '*/', 'script', 'javascript']
        for char in dangerous_chars:
            cleaned = cleaned.replace(char, '')
    
    # Verificação adicional para SQL injection
    sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'EXEC', 'UNION', 'SCRIPT']
    cleaned_upper = cleaned.upper()
    for keyword in sql_keywords:
        if keyword in cleaned_upper:
            # Log tentativa de SQL injection
            log_security_event('POTENTIAL_SQL_INJECTION', details=f'Input contained: {keyword}')
            cleaned = cleaned.replace(keyword.lower(), '').replace(keyword.upper(), '')
    
    return cleaned

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

# Configuração segura para produção
app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_urlsafe(32)

# Configurações básicas para produção
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024
)

# Middleware para proxy reverso (Render)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Headers de segurança
@app.after_request
def add_security_headers(response):
    """Adiciona headers de segurança aprimorados em todas as respostas"""
    # Content Security Policy mais restritivo
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )
    
    response.headers.update({
        'Content-Security-Policy': csp,
        'X-Frame-Options': 'DENY',
        'X-Content-Type-Options': 'nosniff',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=63072000; includeSubDomains; preload',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=(), payment=(), usb=()',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'X-Permitted-Cross-Domain-Policies': 'none',
        'Cross-Origin-Embedder-Policy': 'require-corp',
        'Cross-Origin-Opener-Policy': 'same-origin',
        'Cross-Origin-Resource-Policy': 'same-origin'
    })
    
    return response

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

def create_example_data_for_user(cursor, user_id):
    """Cria dados de exemplo para um usuário novo"""
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
                email TEXT,
                email_notifications BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Adicionar colunas email se não existirem (migração)
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
            print("📧 Coluna email adicionada")
        except:
            pass  # Coluna já existe
            
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN email_notifications BOOLEAN DEFAULT 1")
            print("🔔 Coluna email_notifications adicionada")
        except:
            pass  # Coluna já existe
        
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
        
        # Criar usuários padrão apenas se não existirem (preservar senhas alteradas)
        
        # Verificar se admin existe
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        admin_exists = cursor.fetchone()[0] > 0
        
        if not admin_exists:
            admin_password = generate_password_hash('admin2025')
            cursor.execute("INSERT INTO users (username, password_hash, name) VALUES (?, ?, ?)",
                         ('admin', admin_password, 'Administrador'))
            print("👑 Admin SQLite criado")
        else:
            print("👑 Admin SQLite já existe - preservando senha atual")
        
        # Verificar se Ana Paula existe
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'ana_paula'")
        user_exists = cursor.fetchone()[0] > 0
        
        if not user_exists:
            user_password = generate_password_hash('princesa123')
            cursor.execute("INSERT INTO users (username, password_hash, name) VALUES (?, ?, ?)",
                         ('ana_paula', user_password, 'Ana Paula Schlickmann Michels'))
            print("✅ Ana Paula SQLite criada")
        else:
            print("✅ Ana Paula SQLite já existe - preservando senha atual")
        
        # Proteger usuários críticos contra exclusão acidental
        protected_users = ['admin', 'ana_paula']
        for username in protected_users:
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_row = cursor.fetchone()
            if user_row:
                log_security_event('PROTECTED_USER_VERIFIED', details=f'User {username} (ID: {user_row[0]}) protected against deletion')
        
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
                email VARCHAR(255),
                email_notifications BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Adicionar colunas email se não existirem (migração)
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR(255)")
            print("📧 Coluna email adicionada")
        except:
            pass  # Coluna já existe
            
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN email_notifications BOOLEAN DEFAULT TRUE")
            print("🔔 Coluna email_notifications adicionada")
        except:
            pass  # Coluna já existe
        
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
        
        # Verificar e criar usuário ana_paula apenas se não existir (preservar senha)
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'ana_paula'")
        user_exists = cursor.fetchone()[0] > 0
        
        if not user_exists:
            # Criar usuário ana_paula apenas se não existir
            hashed_password = generate_password_hash('princesa123')
            cursor.execute("""
                INSERT INTO users (username, password_hash, name) 
                VALUES ('ana_paula', %s, 'Ana Paula Schlickmann Michels')
                RETURNING id
            """, (hashed_password,))
            
            # Inserir dados de exemplo apenas para usuário novo
            user_id = cursor.fetchone()[0]
            print(f"✅ Usuário ana_paula criado com ID: {user_id}")
            
            # Criar dados de exemplo apenas para usuário novo
            create_example_data_for_user(cursor, user_id)
        else:
            print("✅ Usuário ana_paula já existe - preservando senha atual")
            # Não inserir dados de exemplo se usuário já existe
            return True

        
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
        # Verificar se usuário está logado
        if 'user_id' not in session:
            log_security_event('UNAUTHORIZED_ACCESS', details=f'Attempted access to {request.endpoint}')
            return redirect(url_for('login'))
        
        # Verificar expiração da sessão
        if 'login_time' in session:
            login_time = datetime.fromisoformat(session['login_time'])
            if datetime.now() - login_time > app.config['PERMANENT_SESSION_LIFETIME']:
                session.clear()
                log_security_event('SESSION_EXPIRED', user_id=session.get('user_id'))
                flash('Sua sessão expirou. Faça login novamente.', 'warning')
                return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'is_admin' not in session:
            log_security_event('UNAUTHORIZED_ADMIN_ACCESS', user_id=session.get('user_id'))
            return redirect(url_for('admin_login'))
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
        ip_address = request.remote_addr
        
        # Validar e sanitizar input com validação aprimorada
        username = validate_input(request.form.get('username', ''), max_length=50, input_type='username')
        password = request.form.get('password', '')
        name = validate_input(request.form.get('name', ''), max_length=100, input_type='text')
        
        # Validações de segurança
        if not username or not password or not name:
            flash('Todos os campos são obrigatórios!', 'error')
            return render_template('register.html')
        
        if len(username) < 3:
            flash('Nome de usuário deve ter pelo menos 3 caracteres!', 'error')
            return render_template('register.html')
        
        if len(password) < 8:
            flash('Senha deve ter pelo menos 8 caracteres!', 'error')
            return render_template('register.html')
        
        # Verificar complexidade da senha
        if not re.search(r'[A-Za-z]', password) or not re.search(r'[0-9]', password):
            flash('Senha deve conter pelo menos uma letra e um número!', 'error')
            return render_template('register.html')
        
        if len(name) < 2:
            flash('Nome deve ter pelo menos 2 caracteres!', 'error')
            return render_template('register.html')
        
        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor()
                # Verificar se usuário já existe
                placeholder = get_param_placeholder()
                cursor.execute(f"SELECT id FROM users WHERE username = {placeholder}", (username,))
                if cursor.fetchone():
                    log_security_event('REGISTRATION_DUPLICATE_USERNAME', details=f'Username: {username}', ip_address=ip_address)
                    flash('Nome de usuário já existe!', 'error')
                    return render_template('register.html')
                
                # Criar novo usuário com senha forte
                hashed_password = generate_password_hash(password, method='pbkdf2:sha256:100000')
                
                log_security_event('USER_REGISTRATION_ATTEMPT', details=f'Username: {username}, Name: {name}', ip_address=ip_address)
                cursor.execute(f"INSERT INTO users (username, password_hash, name) VALUES ({placeholder}, {placeholder}, {placeholder})", (username, hashed_password, name))
                connection.commit()
                
                log_security_event('SUCCESSFUL_REGISTRATION', details=f'Username: {username}', ip_address=ip_address)
                print(f"✅ Usuário {username} cadastrado com sucesso!")
                cursor.close()
                connection.close()
                
                flash('Usuário cadastrado com sucesso! Faça login agora.', 'success')
                return redirect(url_for('login'))
                
            except Exception as e:
                log_security_event('REGISTRATION_ERROR', details=f'Error: {str(e)}', ip_address=ip_address)
                flash('Erro ao cadastrar usuário. Tente novamente.', 'error')
                return render_template('register.html')
        else:
            flash('Erro de conexão com o banco de dados!', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        ip_address = request.remote_addr
        
        # Verificar rate limiting
        if is_rate_limited(ip_address):
            log_security_event('RATE_LIMITED_LOGIN', ip_address=ip_address)
            flash('Muitas tentativas de login. Tente novamente em 15 minutos.', 'error')
            return render_template('login.html'), 429
        
        # Validar e sanitizar input com validação aprimorada
        username = validate_input(request.form.get('username', ''), max_length=50, input_type='username')
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Usuário e senha são obrigatórios!', 'error')
            return render_template('login.html')
        
        if len(password) < 6:
            record_login_attempt(ip_address)
            flash('Senha deve ter pelo menos 6 caracteres!', 'error')
            return render_template('login.html')
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            placeholder = get_param_placeholder()
            cursor.execute(f"SELECT id, username, name, password_hash FROM users WHERE username = {placeholder}", (username,))
            user_row = cursor.fetchone()
            
            log_security_event('LOGIN_ATTEMPT', details=f'User: {username}', ip_address=ip_address)
            
            if user_row and check_password_hash(user_row[3], password):
                # Login bem-sucedido
                user = {
                    'id': user_row[0],
                    'username': user_row[1], 
                    'name': user_row[2],
                    'password_hash': user_row[3]
                }
                
                # Configurar sessão segura
                session.permanent = True
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['name'] = user['name']
                session['login_time'] = datetime.now().isoformat()
                session['login_ip'] = ip_address
                
                # Limpar tentativas de login para este IP
                if ip_address in rate_limit_storage:
                    del rate_limit_storage[ip_address]
                
                log_security_event('SUCCESSFUL_LOGIN', user_id=user['id'], ip_address=ip_address)
                flash('Login realizado com sucesso! Bem-vinda, Princesa! 👑', 'success')
                return redirect(url_for('dashboard'))
            else:
                # Login falhado
                record_login_attempt(ip_address)
                
                if user_row:
                    log_security_event('FAILED_LOGIN_WRONG_PASSWORD', details=f'User: {username}', ip_address=ip_address)
                    flash('Senha incorreta! 🚫', 'error')
                else:
                    log_security_event('FAILED_LOGIN_USER_NOT_FOUND', details=f'User: {username}', ip_address=ip_address)
                    flash(f'Usuário "{username}" não encontrado! 🚫', 'error')
                
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
    # Validar e sanitizar input
    title = validate_input(request.form.get('title', ''), max_length=255)
    description = validate_input(request.form.get('description', ''), max_length=1000)
    priority = request.form.get('priority', 'media')
    due_date = request.form.get('due_date')
    
    # Validações
    if not title or len(title.strip()) < 2:
        flash('Título da tarefa deve ter pelo menos 2 caracteres!', 'error')
        return redirect(url_for('tasks'))
    
    # Validar prioridade
    valid_priorities = ['baixa', 'media', 'alta']
    if priority not in valid_priorities:
        priority = 'media'
    
    # Validar data se fornecida
    if due_date:
        try:
            datetime.strptime(due_date, '%Y-%m-%d')
        except ValueError:
            flash('Formato de data inválido!', 'error')
            return redirect(url_for('tasks'))
    
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        placeholder = get_param_placeholder()
        
        log_security_event('TASK_CREATION', user_id=session['user_id'], details=f'Title: {title[:50]}')
        
        cursor.execute(f"""
            INSERT INTO tasks (user_id, title, description, priority, due_date)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
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
    # Validar e sanitizar input
    title = validate_input(request.form.get('title', ''), max_length=255)
    description = validate_input(request.form.get('description', ''), max_length=1000)
    time_schedule = request.form.get('time_schedule')
    days_of_week = ','.join(request.form.getlist('days_of_week'))
    
    # Validações
    if not title or len(title.strip()) < 2:
        flash('Título da rotina deve ter pelo menos 2 caracteres!', 'error')
        return redirect(url_for('routines'))
    
    # Validar horário se fornecido
    if time_schedule:
        try:
            datetime.strptime(time_schedule, '%H:%M')
        except ValueError:
            flash('Formato de horário inválido! Use HH:MM', 'error')
            return redirect(url_for('routines'))
    
    # Validar dias da semana
    valid_days = ['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo']
    selected_days = [day for day in request.form.getlist('days_of_week') if day in valid_days]
    days_of_week = ','.join(selected_days)
    
    if not selected_days:
        flash('Selecione pelo menos um dia da semana!', 'error')
        return redirect(url_for('routines'))
    
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        placeholder = get_param_placeholder()
        
        log_security_event('ROUTINE_CREATION', user_id=session['user_id'], details=f'Title: {title[:50]}')
        
        cursor.execute(f"""
            INSERT INTO routines (user_id, title, description, time_schedule, days_of_week)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
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
@admin_required
def admin_change_password():
    ip_address = request.remote_addr
    admin_id = session.get('user_id')
    
    # Validar e sanitizar input
    user_id = request.form.get('user_id')
    new_password = request.form.get('new_password', '')
    
    # Validações de segurança aprimoradas
    if not user_id or not user_id.isdigit():
        log_security_event('ADMIN_INVALID_USER_ID', user_id=admin_id, ip_address=ip_address)
        flash('ID de usuário inválido!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    user_id = int(user_id)
    
    # Validações de senha mais rigorosas
    if len(new_password) < 8:
        flash('A senha deve ter pelo menos 8 caracteres!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if len(new_password) > 128:
        flash('A senha não pode ter mais que 128 caracteres!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # Verificar complexidade da senha
    if not re.search(r'[A-Za-z]', new_password) or not re.search(r'[0-9]', new_password):
        flash('Senha deve conter pelo menos uma letra e um número!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # Verificar se contém caracteres especiais (recomendado)
    if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', new_password):
        flash('Recomendado: Use pelo menos um caractere especial para maior segurança!', 'warning')
    
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        
        # Verificar se usuário existe
        placeholder = get_param_placeholder()
        cursor.execute(f"SELECT username, name FROM users WHERE id = {placeholder}", (user_id,))
        user_row = cursor.fetchone()
        
        if not user_row:
            log_security_event('ADMIN_USER_NOT_FOUND', user_id=admin_id, details=f'Attempted to change password for non-existent user ID: {user_id}', ip_address=ip_address)
            flash('Usuário não encontrado!', 'error')
            cursor.close()
            connection.close()
            return redirect(url_for('admin_dashboard'))
        
        username = user_row[0] if isinstance(user_row, tuple) else user_row['username']
        name = user_row[1] if isinstance(user_row, tuple) else user_row['name']
        
        # Verificar se é um usuário protegido
        if is_protected_user(user_id):
            audit_user_operation('PASSWORD_CHANGE_PROTECTED', user_id, admin_id, f'Protected user: {username}')
        
        # Atualizar senha com hash ainda mais forte
        hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256:150000')
        cursor.execute(f"UPDATE users SET password_hash = {placeholder} WHERE id = {placeholder}", 
                      (hashed_password, user_id))
        
        rows_affected = cursor.rowcount
        connection.commit()
        
        # Log detalhado da operação
        log_security_event('ADMIN_PASSWORD_CHANGE', 
                         user_id=admin_id, 
                         details=f'Changed password for user: {username} ({name}) [ID: {user_id}] - Rows affected: {rows_affected}',
                         ip_address=ip_address)
        
        audit_user_operation('PASSWORD_CHANGE', user_id, admin_id, f'User: {username} ({name})')
        
        cursor.close()
        connection.close()
        flash(f'Senha alterada com sucesso para {name}! ✅', 'success')
    else:
        log_security_event('ADMIN_DB_CONNECTION_ERROR', user_id=admin_id, ip_address=ip_address)
        flash('Erro ao conectar com o banco de dados! ❌', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    """Função protegida para exclusão de usuários com múltiplas validações"""
    ip_address = request.remote_addr
    admin_id = session.get('user_id')
    
    # Verificar se é um usuário protegido
    if is_protected_user(user_id):
        log_security_event('PROTECTED_USER_DELETE_ATTEMPT', 
                         user_id=admin_id, 
                         details=f'Attempted to delete protected user ID: {user_id}',
                         ip_address=ip_address)
        flash('❌ Usuário protegido! Não é possível excluir usuários críticos do sistema.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # Verificar se não está tentando se auto-excluir
    if user_id == admin_id:
        log_security_event('SELF_DELETE_ATTEMPT', user_id=admin_id, ip_address=ip_address)
        flash('❌ Você não pode excluir sua própria conta!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        placeholder = get_param_placeholder()
        
        # Verificar se usuário existe e obter informações
        cursor.execute(f"SELECT username, name FROM users WHERE id = {placeholder}", (user_id,))
        user_row = cursor.fetchone()
        
        if not user_row:
            flash('❌ Usuário não encontrado!', 'error')
            cursor.close()
            connection.close()
            return redirect(url_for('admin_dashboard'))
        
        username = user_row[0] if isinstance(user_row, tuple) else user_row['username']
        name = user_row[1] if isinstance(user_row, tuple) else user_row['name']
        
        # Executar exclusão
        cursor.execute(f"DELETE FROM users WHERE id = {placeholder}", (user_id,))
        rows_affected = cursor.rowcount
        connection.commit()
        
        # Log da exclusão
        audit_user_operation('DELETE', user_id, admin_id, f'Deleted user: {username} ({name})')
        log_security_event('USER_DELETED', 
                         user_id=admin_id, 
                         details=f'Deleted user: {username} ({name}) [ID: {user_id}] - Rows affected: {rows_affected}',
                         ip_address=ip_address)
        
        cursor.close()
        connection.close()
        flash(f'✅ Usuário {name} excluído com sucesso!', 'success')
    else:
        flash('❌ Erro ao conectar com o banco de dados!', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/backup_users')
@admin_required  
def admin_backup_users():
    """Criar backup dos usuários para recuperação"""
    connection = get_db_connection()
    backup_data = []
    
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id, username, name, created_at FROM users ORDER BY id")
        users = cursor_to_dict_list(cursor, cursor.fetchall())
        
        # Log do backup
        log_security_event('USER_BACKUP_CREATED', 
                         user_id=session.get('user_id'),
                         details=f'Backup created with {len(users)} users')
        
        cursor.close()
        connection.close()
        
        # Retornar JSON do backup
        from flask import jsonify
        return jsonify({
            'status': 'success',
            'backup_time': datetime.now().isoformat(),
            'user_count': len(users),
            'users': users
        })
    
    return jsonify({'status': 'error', 'message': 'Database connection failed'})

@app.route('/admin/logout')
def admin_logout():
    log_security_event('ADMIN_LOGOUT', user_id=session.get('user_id'), ip_address=request.remote_addr)
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

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Página de configurações do perfil do usuário"""
    if request.method == 'POST':
        # Validar e sanitizar input
        email = validate_input(request.form.get('email', ''), max_length=255, input_type='email')
        email_notifications = request.form.get('email_notifications') == 'on'
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            placeholder = get_param_placeholder()
            
            # Atualizar email e preferências
            cursor.execute(f"""
                UPDATE users 
                SET email = {placeholder}, email_notifications = {placeholder}
                WHERE id = {placeholder}
            """, (email or None, email_notifications, session['user_id']))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            log_security_event('PROFILE_UPDATE', 
                             user_id=session['user_id'], 
                             details=f'Email: {email}, Notifications: {email_notifications}')
            
            flash('💖 Perfil atualizado com sucesso!', 'success')
            
            # Enviar email de teste se configurado
            if email and email_notifications:
                send_email_notification(
                    email, 
                    '👑 Princesa App - Email Configurado!',
                    '<h2>🎉 Parabéns!</h2><p>Seu email foi configurado com sucesso! Você receberá notificações sobre suas tarefas e rotinas.</p>',
                    'routine'
                )
                flash('📧 Email de teste enviado!', 'info')
    
    # Buscar dados atuais do usuário
    connection = get_db_connection()
    user_data = {'email': '', 'email_notifications': True}
    
    if connection:
        cursor = connection.cursor()
        placeholder = get_param_placeholder()
        cursor.execute(f"SELECT email, email_notifications FROM users WHERE id = {placeholder}", (session['user_id'],))
        user_row = cursor.fetchone()
        
        if user_row:
            user_data = {
                'email': user_row[0] or '',
                'email_notifications': bool(user_row[1]) if user_row[1] is not None else True
            }
        
        cursor.close()
        connection.close()
    
    return render_template('profile.html', user=user_data)

@app.route('/api/check_notifications')
@login_required
def check_notifications():
    """Verifica rotinas e tarefas que precisam de notificação"""
    from datetime import datetime, time as dt_time
    
    connection = get_db_connection()
    notifications = []
    
    if connection:
        cursor = connection.cursor()
        placeholder = get_param_placeholder()
        
        # Verificar rotinas do dia atual
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
        current_time = datetime.now().time()
        
        # Buscar rotinas ativas para hoje
        cursor.execute(f"""
            SELECT * FROM routines 
            WHERE user_id = {placeholder} AND active = {'1' if USING_SQLITE else 'TRUE'} 
            AND days_of_week LIKE {placeholder}
        """, (session['user_id'], f'%{today_pt}%'))
        
        routines = cursor_to_dict_list(cursor, cursor.fetchall())
        
        for routine in routines:
            if routine['time_schedule']:
                try:
                    # Converter horário da rotina
                    if isinstance(routine['time_schedule'], str):
                        routine_time = datetime.strptime(routine['time_schedule'], '%H:%M').time()
                    else:
                        routine_time = routine['time_schedule']
                    
                    # Verificar se está na hora (com margem de 1 minuto)
                    current_minutes = current_time.hour * 60 + current_time.minute
                    routine_minutes = routine_time.hour * 60 + routine_time.minute
                    
                    if abs(current_minutes - routine_minutes) <= 1:
                        notifications.append({
                            'id': f"routine_{routine['id']}",
                            'type': 'routine',
                            'title': '🌸 Hora da Rotina!',
                            'message': f"{routine['title']}",
                            'description': routine.get('description', ''),
                            'time': routine['time_schedule'],
                            'priority': 'normal'
                        })
                        
                        # Enviar email se configurado
                        cursor.execute(f"SELECT email, email_notifications FROM users WHERE id = {placeholder}", (session['user_id'],))
                        user_email_data = cursor.fetchone()
                        
                        if user_email_data and user_email_data[0] and user_email_data[1]:
                            email_subject = f"🌸 Hora da Rotina: {routine['title']}"
                            description_text = f'<p><strong>📝 Descrição:</strong> {routine.get("description", "")}</p>' if routine.get('description') else ''
                            email_message = f"""
                            <h2>🔔 É hora da sua rotina!</h2>
                            <h3>🌸 {routine['title']}</h3>
                            <p><strong>⏰ Horário:</strong> {routine['time_schedule']}</p>
                            {description_text}
                            <p>👑 Sua rotina de princesa te espera!</p>
                            """
                            
                            send_email_notification(
                                user_email_data[0],
                                email_subject,
                                email_message,
                                'routine'
                            )
                except Exception as e:
                    print(f"Erro ao processar rotina {routine['id']}: {e}")
        
        # Verificar tarefas com prazo próximo (hoje e amanhã)
        from datetime import date, timedelta
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        cursor.execute(f"""
            SELECT * FROM tasks 
            WHERE user_id = {placeholder} AND completed = {'0' if USING_SQLITE else 'FALSE'}
            AND due_date IN ({placeholder}, {placeholder})
            ORDER BY due_date ASC, priority DESC
        """, (session['user_id'], today.strftime('%Y-%m-%d'), tomorrow.strftime('%Y-%m-%d')))
        
        tasks = cursor_to_dict_list(cursor, cursor.fetchall())
        
        for task in tasks:
            if task['due_date']:
                task_date = task['due_date']
                if isinstance(task_date, str):
                    task_date = datetime.strptime(task_date, '%Y-%m-%d').date()
                
                priority_icons = {'alta': '🔴', 'media': '🟡', 'baixa': '🟢'}
                priority_icon = priority_icons.get(task.get('priority', 'media'), '🟡')
                
                if task_date == today:
                    notifications.append({
                        'id': f"task_{task['id']}",
                        'type': 'task',
                        'title': f'{priority_icon} Tarefa para Hoje!',
                        'message': f"{task['title']}",
                        'description': task.get('description', ''),
                        'priority': task.get('priority', 'media'),
                        'due_date': task_date.strftime('%d/%m/%Y')
                    })
                    
                    # Enviar email para tarefas de hoje
                    cursor.execute(f"SELECT email, email_notifications FROM users WHERE id = {placeholder}", (session['user_id'],))
                    user_email_data = cursor.fetchone()
                    
                    if user_email_data and user_email_data[0] and user_email_data[1]:
                        priority_names = {'alta': 'Alta Prioridade', 'media': 'Média Prioridade', 'baixa': 'Baixa Prioridade'}
                        priority_name = priority_names.get(task.get('priority', 'media'), 'Média Prioridade')
                        
                        email_subject = f"{priority_icon} Tarefa para Hoje: {task['title']}"
                        description_text = f'<p><strong>📝 Descrição:</strong> {task.get("description", "")}</p>' if task.get('description') else ''
                        email_message = f"""
                        <h2>📅 Tarefa para Hoje!</h2>
                        <h3>{priority_icon} {task['title']}</h3>
                        <p><strong>🎨 Prioridade:</strong> {priority_name}</p>
                        <p><strong>📅 Prazo:</strong> {task_date.strftime('%d/%m/%Y')}</p>
                        {description_text}
                        <p>💪 Você consegue, Princesa!</p>
                        """
                        
                        send_email_notification(
                            user_email_data[0],
                            email_subject,
                            email_message,
                            'task'
                        )
                        
                elif task_date == tomorrow:
                    notifications.append({
                        'id': f"task_{task['id']}",
                        'type': 'task',
                        'title': f'{priority_icon} Tarefa para Amanhã!',
                        'message': f"{task['title']}",
                        'description': task.get('description', ''),
                        'priority': task.get('priority', 'media'),
                        'due_date': task_date.strftime('%d/%m/%Y')
                    })
        
        cursor.close()
        connection.close()
    
    return jsonify({
        'notifications': notifications,
        'count': len(notifications),
        'timestamp': datetime.now().isoformat()
    })



@app.route('/api/mark_notification_seen/<notification_id>')
@login_required
def mark_notification_seen(notification_id):
    """Marca uma notificação como vista"""
    log_security_event('NOTIFICATION_SEEN', 
                     user_id=session['user_id'], 
                     details=f'Notification ID: {notification_id}')
    
    return jsonify({'status': 'success'})



@app.route('/test')
def test():
    """Rota de teste simples"""
    return "✅ Aplicação Princesa funcionando!"

# Inicialização do banco de dados
try:
    print("🌸 Inicializando aplicação Princesa...")
    init_db()
    print("✅ Banco de dados inicializado com sucesso!")
except Exception as e:
    print(f"❌ Erro ao inicializar banco: {e}")
    # Em produção, continua mesmo com erro de DB para debugging

# Para execução local
if __name__ == '__main__':
    print("🌸 Modo desenvolvimento - iniciando servidor local")
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    app.run(debug=debug, host='0.0.0.0', port=port)
else:
    print("🌸 Aplicação carregada para produção")