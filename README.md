# 🌸 Projeto Princesa Ana Paula 💖

Um sistema personalizado de gerenciamento de tarefas e rotinas criado especialmente para a Princesa Ana Paula Schlickmann Michels.

## ✨ Funcionalidades

### 🔐 Sistema de Login Seguro
- Login personalizado com senha
- Sessão protegida
- Interface de princesa com temas cor-de-rosa

### 📋 Gerenciamento de Tarefas
- ➕ Criar, editar e excluir tarefas
- ✅ Marcar tarefas como concluídas com animações
- 🏷️ Definir prioridades (Alta, Média, Baixa)
- 📅 Definir datas de vencimento
- 🔔 Notificações para tarefas em atraso

### 📅 Sistema de Rotinas
- 🕐 Criar rotinas com horários específicos
- 📆 Definir dias da semana para cada rotina
- 🔄 Ativar/desativar rotinas facilmente
- ✨ Marcar execução de rotinas
- 🏠 Dashboard com rotinas do dia atual

### 🎨 Design Especial
- 💖 Interface temática de princesa
- 🌸 Cores rosa, roxo e dourado
- ✨ Animações suaves e efeitos especiais
- 📱 Responsivo para celular e desktop
- 🎭 Corações flutuantes e sparkles

## 🛠️ Tecnologias Utilizadas

- **Backend**: Python + Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **Database**: MySQL
- **Framework CSS**: Bootstrap 5
- **Ícones**: Font Awesome
- **Tipografia**: Google Fonts (Dancing Script + Poppins)

## 📦 Instalação

### Pré-requisitos
1. **Python 3.8+** instalado
2. **MySQL Server** instalado e rodando
3. **Git** (opcional)

### Passo a Passo

#### 1. Clone ou baixe o projeto
```bash
git clone [seu-repositorio]
cd princesa
```

#### 2. Execute a configuração automática
```bash
python setup.py
```

O script irá:
- ✅ Instalar todas as dependências
- 🗄️ Criar o banco de dados
- 👤 Criar usuário padrão
- 📋 Inserir tarefas de exemplo
- 📅 Inserir rotinas de exemplo

#### 3. Inicie o servidor
```bash
# Windows
run.bat

# Linux/Mac
./run.sh

# Ou manualmente
python back-end/sever.py
```

#### 4. Acesse a aplicação
Abra seu navegador e vá para: `http://localhost:5000`

### 🔑 Login Padrão
- **Usuário**: `ana_paula`
- **Senha**: `princesa123`

## �️ Estrutura do Banco de Dados

O sistema utiliza **MySQL** com 4 tabelas principais:

### 1. 👤 Tabela `users` (Usuários)
```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. 📋 Tabela `tasks` (Tarefas)
```sql
CREATE TABLE tasks (
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
```

### 3. 📅 Tabela `routines` (Rotinas)
```sql
CREATE TABLE routines (
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
```

### 4. ✅ Tabela `routine_executions` (Execuções de Rotinas)
```sql
CREATE TABLE routine_executions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    routine_id INT,
    executed_date DATE,
    executed_time TIME,
    notes TEXT,
    FOREIGN KEY (routine_id) REFERENCES routines(id) ON DELETE CASCADE
);
```

### 🔧 Configuração Manual do Banco

Se precisar criar manualmente:

#### 1. **Criar o Database:**
```sql
CREATE DATABASE princesa_db;
USE princesa_db;
```

#### 2. **Executar as tabelas acima em ordem**

#### 3. **Criar usuário padrão:**
```sql
INSERT INTO users (username, password_hash, name) 
VALUES ('ana_paula', 'pbkdf2:sha256:600000$...', 'Ana Paula Schlickmann Michels');
```

### 🔑 **Configuração de Conexão:**
- **Host:** localhost
- **Database:** princesa_db  
- **Usuário:** root (ou seu usuário MySQL)
- **Senha:** (sua senha MySQL)
- **Porta:** 3306

## �📱 Como Usar

### Dashboard Principal
- 🏠 Visão geral das tarefas pendentes
- 📅 Rotinas do dia atual
- 🚀 Ações rápidas para criar tarefas/rotinas

### Gerenciar Tarefas
1. Clique em "Minhas Tarefas" no menu
2. Use o botão "+" para criar nova tarefa
3. Preencha título, descrição, prioridade e data
4. Marque como concluída clicando no checkbox
5. Delete tarefas desnecessárias

### Gerenciar Rotinas
1. Clique em "Minhas Rotinas" no menu
2. Use o botão "+" para criar nova rotina
3. Defina título, descrição, horário e dias
4. Use o toggle para ativar/desativar
5. Execute rotinas no dashboard

### 💡 Dicas Especiais
- **Ctrl + N**: Criar nova tarefa rapidamente
- **Ctrl + R**: Criar nova rotina rapidamente
- **ESC**: Fechar modais
- As tarefas vencidas ficam destacadas em vermelho
- Notificações aparecem automaticamente

## 🎨 Personalização

### Alterar Cores
Edite o arquivo `static/css/princess-style.css`:
```css
:root {
    --princess-pink: #sua-cor;
    --princess-purple: #sua-cor;
    /* ... outras variáveis */
}
```

### Configurar Banco de Dados
Edite o arquivo `back-end/sever.py`:
```python
DB_CONFIG = {
    'host': 'seu-host',
    'user': 'seu-usuario',
    'password': 'sua-senha',
    'database': 'princesa_db'
}
```

### Adicionar Novos Usuários
Execute no MySQL:
```sql
INSERT INTO users (username, password_hash, name) 
VALUES ('novo_usuario', 'hash_da_senha', 'Nome Completo');
```

## 📁 Estrutura do Projeto

```
princesa/
├── 📁 back-end/
│   └── 🐍 sever.py              # Servidor Flask principal
├── 📁 templates/
│   ├── 🌐 base.html             # Template base
│   ├── 🔐 login.html            # Página de login
│   ├── 🏠 dashboard.html        # Dashboard principal
│   ├── 📋 tasks.html            # Gerenciar tarefas
│   └── 📅 routines.html         # Gerenciar rotinas
├── 📁 static/
│   ├── 📁 css/
│   │   └── 🎨 princess-style.css # Estilos principais
│   └── 📁 js/
│       └── ⚡ princess-app.js    # JavaScript interativo
├── 📄 requirements.txt          # Dependências Python
├── 🔧 setup.py                  # Script de configuração
├── 🚀 run.bat                   # Executar no Windows
├── 🚀 run.sh                    # Executar no Linux/Mac
└── 📖 README.md                 # Este arquivo
```

## 🗄️ Banco de Dados

### Tabelas Criadas:
- **users**: Usuários do sistema
- **tasks**: Tarefas da princesa
- **routines**: Rotinas diárias
- **routine_executions**: Histórico de execuções

## 🔧 Desenvolvimento

### Executar em Modo Debug
```bash
# No arquivo sever.py, altere:
app.run(debug=True, host='0.0.0.0', port=5000)
```

### Adicionar Novas Funcionalidades
1. Crie novas rotas no `sever.py`
2. Adicione templates em `templates/`
3. Estilos em `static/css/`
4. JavaScript em `static/js/`

### Backup do Banco
```bash
mysqldump -u root -p princesa_db > backup.sql
```

## 🎯 Funcionalidades Futuras

- [ ] 📊 Relatórios de produtividade
- [ ] 🏆 Sistema de conquistas
- [ ] 📷 Upload de fotos nas tarefas
- [ ] 🔔 Notificações push
- [ ] 📱 App mobile
- [ ] 🌙 Modo noturno
- [ ] 👥 Compartilhar tarefas
- [ ] 📈 Gráficos de progresso

## 🆘 Problemas Comuns

### Erro de Conexão MySQL
```
Erro: Access denied for user 'root'@'localhost'
Solução: Verifique usuário e senha do MySQL
```

### Porta 5000 já em uso
```
Erro: Port 5000 is already in use
Solução: Altere a porta no sever.py ou pare outros serviços
```

### Erro de Módulo não Encontrado
```
Erro: ModuleNotFoundError: No module named 'flask'
Solução: Execute: pip install -r requirements.txt
```

## 💝 Mensagem Especial

Este projeto foi criado com muito amor e carinho especialmente para a Ana Paula. Cada detalhe foi pensado para tornar o gerenciamento de tarefas uma experiência mágica e divertida, digna de uma verdadeira princesa! 👑

Que este sistema ajude você a organizar seus dias com ainda mais brilho e elegância! ✨

---

💖 **Feito com amor para a Princesa Ana Paula** 💖

🌸 *\"Porque toda princesa merece um reino organizado!\"* 🌸