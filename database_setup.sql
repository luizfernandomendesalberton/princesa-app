-- ===================================================
-- 🌸 BANCO DE DADOS DO PROJETO PRINCESA ANA PAULA 💖
-- ===================================================
-- Script SQL para criação manual das tabelas
-- Execute este arquivo no seu MySQL Workbench ou cliente MySQL

-- 1. Criar o banco de dados
CREATE DATABASE IF NOT EXISTS princesa_db;
USE princesa_db;

-- ===================================================
-- 📋 CRIAÇÃO DAS TABELAS
-- ===================================================

-- 1. 👤 TABELA DE USUÁRIOS
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 📋 TABELA DE TAREFAS
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
);

-- 3. 📅 TABELA DE ROTINAS
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
);

-- 4. ✅ TABELA DE EXECUÇÃO DE ROTINAS
CREATE TABLE IF NOT EXISTS routine_executions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    routine_id INT,
    executed_date DATE,
    executed_time TIME,
    notes TEXT,
    FOREIGN KEY (routine_id) REFERENCES routines(id) ON DELETE CASCADE
);

-- ===================================================
-- 📝 INSERÇÃO DE DADOS PADRÃO
-- ===================================================

-- 1. 👑 Usuário padrão para Ana Paula
-- Senha: princesa123 (já hashada com Werkzeug)
INSERT IGNORE INTO users (username, password_hash, name) 
VALUES ('ana_paula', 'pbkdf2:sha256:600000$8YvkKzwRZa4M7Nxp$499ed0e7e52c37d02b172350e91b9b9fd5a1b30e5b7c0ad6ed8af2158e06c4b5', 'Ana Paula Schlickmann Michels');

-- 2. 📋 Tarefas de exemplo
INSERT IGNORE INTO tasks (user_id, title, description, priority, due_date) VALUES 
(1, '💄 Rotina de skincare matinal', 'Limpeza, hidratante e protetor solar', 'alta', CURDATE()),
(1, '👗 Escolher look do dia', 'Combinar roupas e acessórios lindos', 'media', CURDATE()),
(1, '📚 Estudar 30 minutos', 'Focar nos estudos importantes', 'alta', CURDATE()),
(1, '🥗 Preparar almoço saudável', 'Cozinhar algo nutritivo e gostoso', 'media', CURDATE()),
(1, '🧘‍♀️ Momento de relaxamento', '15 minutos de meditação ou respiração', 'baixa', CURDATE());

-- 3. 📅 Rotinas de exemplo  
INSERT IGNORE INTO routines (user_id, title, description, time_schedule, days_of_week, active) VALUES
(1, '☀️ Acordar como uma princesa', 'Levantar cedo e começar o dia com energia', '07:00:00', 'segunda,terca,quarta,quinta,sexta,sabado,domingo', TRUE),
(1, '💄 Skincare matinal', 'Rotina de cuidados com a pele pela manhã', '07:30:00', 'segunda,terca,quarta,quinta,sexta,sabado,domingo', TRUE),
(1, '🍎 Café da manhã nutritivo', 'Tomar um café da manhã saudável e saboroso', '08:00:00', 'segunda,terca,quarta,quinta,sexta,sabado,domingo', TRUE),
(1, '💪 Exercícios ou alongamento', '20 minutos de atividade física', '18:00:00', 'segunda,quarta,sexta', TRUE),
(1, '🌙 Skincare noturno', 'Rotina de cuidados noturnos', '21:30:00', 'segunda,terca,quarta,quinta,sexta,sabado,domingo', TRUE);

-- ===================================================
-- 🔍 CONSULTAS DE VERIFICAÇÃO
-- ===================================================

-- Verificar se as tabelas foram criadas
SHOW TABLES;

-- Verificar estrutura das tabelas
DESCRIBE users;
DESCRIBE tasks;
DESCRIBE routines;
DESCRIBE routine_executions;

-- Verificar dados inseridos
SELECT * FROM users;
SELECT * FROM tasks;
SELECT * FROM routines;

-- ===================================================
-- 📊 CONSULTAS ÚTEIS PARA DESENVOLVIMENTO
-- ===================================================

-- Buscar todas as tarefas de um usuário
SELECT t.*, u.name as user_name 
FROM tasks t 
JOIN users u ON t.user_id = u.id 
WHERE u.username = 'ana_paula';

-- Buscar rotinas ativas de hoje
SELECT * FROM routines 
WHERE active = TRUE 
AND FIND_IN_SET(
    CASE DAYOFWEEK(NOW())
        WHEN 1 THEN 'domingo'
        WHEN 2 THEN 'segunda' 
        WHEN 3 THEN 'terca'
        WHEN 4 THEN 'quarta'
        WHEN 5 THEN 'quinta'
        WHEN 6 THEN 'sexta'
        WHEN 7 THEN 'sabado'
    END, 
    days_of_week
) > 0;

-- Contar tarefas por status
SELECT 
    completed,
    COUNT(*) as total,
    CASE 
        WHEN completed = 1 THEN '✅ Concluídas'
        ELSE '⏳ Pendentes'
    END as status
FROM tasks 
GROUP BY completed;