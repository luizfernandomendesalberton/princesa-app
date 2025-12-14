# Script de Configuração Inicial - Projeto Princesa Ana Paula
# Execute este arquivo para configurar o ambiente

import mysql.connector
import sys
import subprocess
import os

def install_requirements():
    """Instala as dependências Python necessárias"""
    print("📦 Instalando dependências...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependências instaladas com sucesso!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Erro ao instalar dependências")
        return False

def setup_database():
    """Configura o banco de dados MySQL"""
    print("🗄️ Configurando banco de dados...")
    
    # Configurações padrão - ALTERE CONFORME NECESSÁRIO
    host = "localhost"
    user = input("Digite o usuário do MySQL (padrão: root): ") or "root"
    password = input("Digite a senha do MySQL (deixe em branco se não tiver): ")
    
    try:
        # Conectar ao MySQL (sem especificar database)
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        
        cursor = connection.cursor()
        
        # Criar database
        cursor.execute("CREATE DATABASE IF NOT EXISTS princesa_db")
        print("✅ Database 'princesa_db' criada!")
        
        # Usar a database
        cursor.execute("USE princesa_db")
        
        # Criar tabelas
        print("📋 Criando tabelas...")
        
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
        
        # Tabela de execuções de rotinas
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
        
        # Criar usuário padrão
        from werkzeug.security import generate_password_hash
        hashed_password = generate_password_hash('princesa123')
        
        cursor.execute("""
            INSERT IGNORE INTO users (username, password_hash, name) 
            VALUES ('ana_paula', %s, 'Ana Paula Schlickmann Michels')
        """, (hashed_password,))
        
        # Inserir algumas tarefas de exemplo
        cursor.execute("SELECT id FROM users WHERE username = 'ana_paula'")
        user_result = cursor.fetchone()
        
        if user_result:
            user_id = user_result[0]
            
            # Tarefas de exemplo
            example_tasks = [
                (user_id, "Beber 2L de água por dia", "Manter hidratação adequada", "alta", "2024-12-15"),
                (user_id, "Fazer skincare matinal", "Limpeza, tônico e hidratante", "media", None),
                (user_id, "Exercitar-se por 30 min", "Caminhada, yoga ou academia", "alta", "2024-12-14"),
                (user_id, "Ler 20 páginas de um livro", "Momento de relaxamento e aprendizado", "baixa", None),
                (user_id, "Organizar o quarto", "Arrumar cama e organizar roupas", "media", "2024-12-13")
            ]
            
            for task in example_tasks:
                cursor.execute("""
                    INSERT IGNORE INTO tasks (user_id, title, description, priority, due_date)
                    VALUES (%s, %s, %s, %s, %s)
                """, task)
            
            # Rotinas de exemplo
            example_routines = [
                (user_id, "Skincare Matinal", "Limpeza facial + tônico + hidratante + protetor solar", "08:00", "segunda,terca,quarta,quinta,sexta,sabado,domingo"),
                (user_id, "Exercícios", "30 minutos de atividade física", "07:00", "segunda,quarta,sexta"),
                (user_id, "Skincare Noturno", "Demaquilante + limpeza + hidratante noturno", "22:00", "segunda,terca,quarta,quinta,sexta,sabado,domingo"),
                (user_id, "Meditação", "10 minutos de mindfulness", "21:00", "segunda,terca,quarta,quinta,sexta,sabado,domingo"),
                (user_id, "Leitura", "30 minutos de leitura relaxante", "20:00", "segunda,terca,quarta,quinta,sexta,sabado,domingo")
            ]
            
            for routine in example_routines:
                cursor.execute("""
                    INSERT IGNORE INTO routines (user_id, title, description, time_schedule, days_of_week)
                    VALUES (%s, %s, %s, %s, %s)
                """, routine)
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("✅ Banco de dados configurado com sucesso!")
        print("👤 Usuário padrão criado: ana_paula / princesa123")
        print("📋 Tarefas de exemplo adicionadas!")
        print("📅 Rotinas de exemplo adicionadas!")
        
        # Salvar configurações
        with open('.env', 'w') as f:
            f.write(f"DB_HOST={host}\n")
            f.write(f"DB_USER={user}\n")
            f.write(f"DB_PASSWORD={password}\n")
            f.write("DB_NAME=princesa_db\n")
        
        return True
        
    except mysql.connector.Error as err:
        print(f"❌ Erro no banco de dados: {err}")
        if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            print("Verifique se o usuário e senha estão corretos")
        elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            print("Database não existe")
        return False

def create_run_script():
    """Cria script para executar a aplicação"""
    print("📄 Criando script de execução...")
    
    # Script para Windows
    with open('run.bat', 'w') as f:
        f.write('''@echo off
echo 🌸 Iniciando Projeto Princesa Ana Paula 💖
echo.
echo Aguarde enquanto o servidor é iniciado...
echo.
cd /d "%~dp0"
python back-end/sever.py
pause
''')
    
    # Script para Linux/Mac
    with open('run.sh', 'w') as f:
        f.write('''#!/bin/bash
echo "🌸 Iniciando Projeto Princesa Ana Paula 💖"
echo ""
echo "Aguarde enquanto o servidor é iniciado..."
echo ""
cd "$(dirname "$0")"
python3 back-end/sever.py
''')
    
    # Tornar executável no Linux/Mac
    try:
        os.chmod('run.sh', 0o755)
    except:
        pass
    
    print("✅ Scripts de execução criados!")
    print("   Windows: run.bat")
    print("   Linux/Mac: ./run.sh")

def main():
    print("=" * 50)
    print("🌸 CONFIGURAÇÃO INICIAL - PROJETO PRINCESA 💖")
    print("=" * 50)
    print()
    
    # Verificar se o MySQL está instalado
    print("🔍 Verificando MySQL...")
    try:
        import mysql.connector
        print("✅ MySQL Connector encontrado!")
    except ImportError:
        print("❌ MySQL Connector não encontrado!")
        print("Instale com: pip install mysql-connector-python")
        return
    
    # Instalar dependências
    if not install_requirements():
        return
    
    print()
    
    # Configurar banco de dados
    if not setup_database():
        return
    
    print()
    
    # Criar scripts de execução
    create_run_script()
    
    print()
    print("=" * 50)
    print("✅ CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 50)
    print()
    print("📋 PRÓXIMOS PASSOS:")
    print("1. Execute 'python back-end/sever.py' ou use o script 'run.bat'/'run.sh'")
    print("2. Abra http://localhost:5000 no navegador")
    print("3. Faça login com: ana_paula / princesa123")
    print()
    print("💖 Divirta-se criando tarefas e rotinas para sua princesa!")
    print()

if __name__ == "__main__":
    main()