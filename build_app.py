import os
import shutil
import json
from pathlib import Path

class PrincessAppBuilder:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.www_dir = self.project_root / 'www'
        self.static_dir = self.project_root / 'static'
        self.templates_dir = self.project_root / 'templates'
        
    def clean_www(self):
        """Limpa o diretório www"""
        if self.www_dir.exists():
            shutil.rmtree(self.www_dir)
        self.www_dir.mkdir()
        print("🧹 Diretório www limpo")
    
    def copy_static_files(self):
        """Copia arquivos estáticos"""
        if self.static_dir.exists():
            shutil.copytree(self.static_dir, self.www_dir / 'static')
        print("📁 Arquivos estáticos copiados")
    
    def generate_static_html(self):
        """Gera versões estáticas dos templates para o app"""
        
        # Template base simplificado para o app
        base_html = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>Princesa Ana Paula</title>
    
    <!-- Capacitor Core -->
    <script type="module" src="static/js/capacitor-core.js"></script>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Dancing+Script:wght@400;500;600;700&family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <!-- CSS Principal -->
    <link rel="stylesheet" href="static/css/princess-style.css">
    <link rel="stylesheet" href="static/css/app-mobile.css">
    
    <style>
        /* Ajustes para app nativo */
        body {
            padding-top: env(safe-area-inset-top);
            padding-bottom: env(safe-area-inset-bottom);
            -webkit-user-select: none;
            -webkit-touch-callout: none;
            -webkit-tap-highlight-color: transparent;
        }
        
        .navbar {
            padding-top: calc(env(safe-area-inset-top) + 10px);
        }
        
        .app-container {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .content-area {
            flex: 1;
            padding: 20px;
        }
    </style>
</head>
<body>
    <div class="app-container" id="app">
        <!-- Splash Screen -->
        <div id="splash" class="splash-screen">
            <div class="splash-content">
                <div class="princess-crown">👑</div>
                <h1>Princesa Ana Paula</h1>
                <div class="loading-hearts">
                    <div class="heart">💖</div>
                    <div class="heart">💕</div>
                    <div class="heart">💖</div>
                </div>
            </div>
        </div>
        
        <!-- App Content -->
        <div id="mainContent" style="display: none;">
            <!-- Navigation -->
            <nav class="navbar navbar-expand-lg princess-navbar">
                <div class="container-fluid">
                    <a class="navbar-brand" href="#" onclick="navigateTo('dashboard')">
                        <i class="fas fa-crown"></i> Princesa
                    </a>
                    <div class="navbar-nav ms-auto">
                        <a class="nav-link" href="#" onclick="showProfile()">
                            <i class="fas fa-user-crown"></i> Ana Paula
                        </a>
                    </div>
                </div>
            </nav>
            
            <!-- Content Area -->
            <div class="content-area">
                <div id="pageContent">
                    <!-- Conteúdo dinâmico será carregado aqui -->
                </div>
            </div>
            
            <!-- Bottom Navigation -->
            <nav class="bottom-nav">
                <button onclick="navigateTo('dashboard')" class="nav-btn active">
                    <i class="fas fa-home"></i>
                    <span>Home</span>
                </button>
                <button onclick="navigateTo('tasks')" class="nav-btn">
                    <i class="fas fa-tasks"></i>
                    <span>Tarefas</span>
                </button>
                <button onclick="navigateTo('routines')" class="nav-btn">
                    <i class="fas fa-calendar-alt"></i>
                    <span>Rotinas</span>
                </button>
                <button onclick="showProfile()" class="nav-btn">
                    <i class="fas fa-user"></i>
                    <span>Perfil</span>
                </button>
            </nav>
        </div>
    </div>
    
    <!-- Scripts -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="static/js/princess-app-native.js"></script>
</body>
</html>'''
        
        # Salvar index.html
        with open(self.www_dir / 'index.html', 'w', encoding='utf-8') as f:
            f.write(base_html)
        
        print("📄 HTML principal gerado")
    
    def create_capacitor_js(self):
        """Cria arquivo JavaScript para integração com Capacitor"""
        
        capacitor_js = '''// Capacitor Core Import
import { CapacitorHttp, CapacitorCookies } from '@capacitor/core';
import { LocalNotifications } from '@capacitor/local-notifications';
import { Haptics, ImpactStyle } from '@capacitor/haptics';
import { StatusBar, Style } from '@capacitor/status-bar';
import { SplashScreen } from '@capacitor/splash-screen';
import { Storage } from '@capacitor/storage';
import { Network } from '@capacitor/network';
import { Device } from '@capacitor/device';

// Configurar Capacitor quando app carrega
document.addEventListener('DOMContentLoaded', async function() {
    console.log('🌸 Princesa App: Inicializando...');
    
    // Configurar status bar
    await StatusBar.setStyle({ style: Style.Dark });
    await StatusBar.setBackgroundColor({ color: '#ff1493' });
    
    // Esconder splash screen após animação
    setTimeout(async () => {
        await SplashScreen.hide();
        document.getElementById('splash').style.display = 'none';
        document.getElementById('mainContent').style.display = 'block';
    }, 2000);
    
    // Verificar conexão
    const status = await Network.getStatus();
    console.log('📡 Status da rede:', status);
    
    // Pedir permissões para notificações
    await LocalNotifications.requestPermissions();
    
    // Carregar dados salvos
    await loadUserData();
    
    // Navegar para dashboard
    navigateTo('dashboard');
});

// Dados locais do app
let appData = {
    user: null,
    tasks: [],
    routines: [],
    isOnline: true
};

// Armazenamento local
async function saveData(key, value) {
    await Storage.set({
        key: key,
        value: JSON.stringify(value)
    });
}

async function loadData(key) {
    const result = await Storage.get({ key: key });
    return result.value ? JSON.parse(result.value) : null;
}

// Carregar dados do usuário
async function loadUserData() {
    const userData = await loadData('user');
    if (userData) {
        appData.user = userData;
    }
    
    const tasks = await loadData('tasks');
    if (tasks) {
        appData.tasks = tasks;
    }
    
    const routines = await loadData('routines');
    if (routines) {
        appData.routines = routines;
    }
}

// Navegação entre telas
function navigateTo(page) {
    // Vibração leve
    Haptics.impact({ style: ImpactStyle.Light });
    
    // Atualizar navegação ativa
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    event.target.closest('.nav-btn').classList.add('active');
    
    // Carregar conteúdo da página
    loadPageContent(page);
}

function loadPageContent(page) {
    const content = document.getElementById('pageContent');
    
    switch(page) {
        case 'dashboard':
            content.innerHTML = getDashboardHTML();
            break;
        case 'tasks':
            content.innerHTML = getTasksHTML();
            break;
        case 'routines':
            content.innerHTML = getRoutinesHTML();
            break;
        default:
            content.innerHTML = getDashboardHTML();
    }
}

// Templates de páginas
function getDashboardHTML() {
    return `
        <div class="dashboard-container">
            <div class="princess-welcome">
                <h1>Bem-vinda, Princesa! 👑</h1>
                <p class="princess-quote">"Cada dia é uma nova oportunidade de brilhar!"</p>
            </div>
            
            <div class="quick-stats">
                <div class="stat-card">
                    <div class="stat-icon">📋</div>
                    <div class="stat-info">
                        <h3>${appData.tasks.filter(t => !t.completed).length}</h3>
                        <p>Tarefas Pendentes</p>
                    </div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-icon">✅</div>
                    <div class="stat-info">
                        <h3>${appData.tasks.filter(t => t.completed).length}</h3>
                        <p>Concluídas</p>
                    </div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-icon">📅</div>
                    <div class="stat-info">
                        <h3>${appData.routines.length}</h3>
                        <p>Rotinas</p>
                    </div>
                </div>
            </div>
            
            <div class="quick-actions">
                <button class="action-btn primary" onclick="addQuickTask()">
                    <i class="fas fa-plus"></i> Nova Tarefa
                </button>
                <button class="action-btn secondary" onclick="navigateTo('routines')">
                    <i class="fas fa-calendar"></i> Ver Rotinas
                </button>
            </div>
            
            <div class="todays-tasks">
                <h3>Tarefas de Hoje</h3>
                <div id="todayTasksList">
                    ${renderTodayTasks()}
                </div>
            </div>
        </div>
    `;
}

function getTasksHTML() {
    return `
        <div class="tasks-container">
            <div class="tasks-header">
                <h2><i class="fas fa-tasks"></i> Minhas Tarefas</h2>
                <button class="btn-add" onclick="showAddTaskModal()">
                    <i class="fas fa-plus"></i>
                </button>
            </div>
            
            <div class="tasks-filter">
                <button class="filter-btn active" onclick="filterTasks('all')">Todas</button>
                <button class="filter-btn" onclick="filterTasks('pending')">Pendentes</button>
                <button class="filter-btn" onclick="filterTasks('completed')">Concluídas</button>
            </div>
            
            <div id="tasksList">
                ${renderTasks()}
            </div>
        </div>
    `;
}

function getRoutinesHTML() {
    return `
        <div class="routines-container">
            <div class="routines-header">
                <h2><i class="fas fa-calendar-alt"></i> Minhas Rotinas</h2>
                <button class="btn-add" onclick="showAddRoutineModal()">
                    <i class="fas fa-plus"></i>
                </button>
            </div>
            
            <div id="routinesList">
                ${renderRoutines()}
            </div>
        </div>
    `;
}

// Funções auxiliares de renderização
function renderTodayTasks() {
    const todayTasks = appData.tasks.filter(task => !task.completed).slice(0, 3);
    
    if (todayTasks.length === 0) {
        return '<p class="no-tasks">Nenhuma tarefa para hoje! 🎉</p>';
    }
    
    return todayTasks.map(task => `
        <div class="task-item-mini">
            <div class="task-checkbox" onclick="toggleTask(${task.id})">
                <i class="far fa-square"></i>
            </div>
            <div class="task-content">
                <h4>${task.title}</h4>
                <p class="task-priority priority-${task.priority}">${task.priority}</p>
            </div>
        </div>
    `).join('');
}

function renderTasks() {
    if (appData.tasks.length === 0) {
        return '<p class="no-items">Nenhuma tarefa cadastrada ainda.</p>';
    }
    
    return appData.tasks.map(task => `
        <div class="task-item ${task.completed ? 'completed' : ''}">
            <div class="task-checkbox" onclick="toggleTask(${task.id})">
                <i class="fa${task.completed ? 's fa-check-square' : 'r fa-square'}"></i>
            </div>
            <div class="task-content">
                <h4>${task.title}</h4>
                <p>${task.description || ''}</p>
                <div class="task-meta">
                    <span class="task-priority priority-${task.priority}">${task.priority}</span>
                    ${task.due_date ? `<span class="task-date">${task.due_date}</span>` : ''}
                </div>
            </div>
            <button class="task-delete" onclick="deleteTask(${task.id})">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `).join('');
}

function renderRoutines() {
    if (appData.routines.length === 0) {
        return '<p class="no-items">Nenhuma rotina cadastrada ainda.</p>';
    }
    
    return appData.routines.map(routine => `
        <div class="routine-item ${routine.active ? 'active' : 'inactive'}">
            <div class="routine-header">
                <h4>${routine.title}</h4>
                <div class="routine-toggle" onclick="toggleRoutine(${routine.id})">
                    <i class="fas fa-toggle-${routine.active ? 'on' : 'off'}"></i>
                </div>
            </div>
            <p>${routine.description || ''}</p>
            <div class="routine-schedule">
                <span class="routine-time">${routine.time_schedule || '--:--'}</span>
                <span class="routine-days">${routine.days_of_week || 'Todos os dias'}</span>
            </div>
        </div>
    `).join('');
}

// Ações de tarefas
async function toggleTask(taskId) {
    await Haptics.impact({ style: ImpactStyle.Medium });
    
    const task = appData.tasks.find(t => t.id === taskId);
    if (task) {
        task.completed = !task.completed;
        await saveData('tasks', appData.tasks);
        
        // Atualizar UI
        loadPageContent('tasks');
        
        // Notificação de sucesso
        if (task.completed) {
            await LocalNotifications.schedule({
                notifications: [{
                    title: "Parabéns, Princesa! 👑",
                    body: "Tarefa concluída com sucesso!",
                    id: Date.now(),
                    sound: 'success.wav'
                }]
            });
        }
    }
}

async function addQuickTask() {
    const title = prompt("Nova tarefa:");
    if (title) {
        const newTask = {
            id: Date.now(),
            title: title,
            description: '',
            completed: false,
            priority: 'media',
            created_at: new Date().toISOString()
        };
        
        appData.tasks.push(newTask);
        await saveData('tasks', appData.tasks);
        
        // Vibração de sucesso
        await Haptics.impact({ style: ImpactStyle.Light });
        
        // Atualizar dashboard
        loadPageContent('dashboard');
    }
}

function showProfile() {
    alert('Perfil da Princesa Ana Paula 👑\\n\\nEm breve, mais funcionalidades!');
}

// Inicializar dados de exemplo se não existirem
if (appData.tasks.length === 0) {
    appData.tasks = [
        {
            id: 1,
            title: "💄 Rotina de skincare matinal",
            description: "Limpeza, hidratante e protetor solar",
            completed: false,
            priority: "alta"
        },
        {
            id: 2,
            title: "👗 Escolher look do dia",
            description: "Combinar roupas e acessórios lindos",
            completed: false,
            priority: "media"
        }
    ];
}

if (appData.routines.length === 0) {
    appData.routines = [
        {
            id: 1,
            title: "☀️ Acordar como uma princesa",
            description: "Levantar cedo e começar o dia com energia",
            time_schedule: "07:00",
            active: true,
            days_of_week: "Todos os dias"
        },
        {
            id: 2,
            title: "🌙 Skincare noturno",
            description: "Rotina de cuidados noturnos",
            time_schedule: "21:30",
            active: true,
            days_of_week: "Todos os dias"
        }
    ];
}

export { navigateTo, toggleTask, addQuickTask, showProfile };'''
        
        # Salvar arquivo JavaScript
        with open(self.www_dir / 'static' / 'js' / 'capacitor-core.js', 'w', encoding='utf-8') as f:
            f.write(capacitor_js)
        
        print("📱 JavaScript do Capacitor criado")
    
    def create_mobile_css(self):
        """Cria CSS otimizado para mobile"""
        
        mobile_css = '''/* CSS Mobile Nativo - Princesa App */

/* Reset e base */
* {
    box-sizing: border-box;
    -webkit-tap-highlight-color: transparent;
}

body {
    margin: 0;
    padding: 0;
    font-family: 'Poppins', sans-serif;
    background: linear-gradient(135deg, #ff69b4, #ff1493);
    min-height: 100vh;
    overflow-x: hidden;
}

/* Splash Screen */
.splash-screen {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: linear-gradient(135deg, #ff69b4, #ff1493);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
}

.splash-content {
    text-align: center;
    color: white;
}

.princess-crown {
    font-size: 4rem;
    margin-bottom: 20px;
    animation: bounce 1s ease-in-out infinite alternate;
}

.splash-content h1 {
    font-family: 'Dancing Script', cursive;
    font-size: 2.5rem;
    margin-bottom: 30px;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.loading-hearts {
    display: flex;
    justify-content: center;
    gap: 10px;
}

.loading-hearts .heart {
    font-size: 1.5rem;
    animation: heartBeat 1.5s ease-in-out infinite;
}

.loading-hearts .heart:nth-child(2) {
    animation-delay: 0.3s;
}

.loading-hearts .heart:nth-child(3) {
    animation-delay: 0.6s;
}

/* Navegação inferior */
.bottom-nav {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    display: flex;
    justify-content: space-around;
    padding: 10px 0 calc(env(safe-area-inset-bottom) + 10px);
    box-shadow: 0 -2px 20px rgba(0,0,0,0.1);
    z-index: 100;
}

.nav-btn {
    background: none;
    border: none;
    display: flex;
    flex-direction: column;
    align-items: center;
    color: #999;
    transition: all 0.3s ease;
    padding: 8px 12px;
    border-radius: 12px;
    min-width: 60px;
}

.nav-btn.active {
    color: #ff1493;
    background: rgba(255, 20, 147, 0.1);
}

.nav-btn i {
    font-size: 1.2rem;
    margin-bottom: 4px;
}

.nav-btn span {
    font-size: 0.7rem;
    font-weight: 500;
}

/* Container principal */
.app-container {
    padding-bottom: 80px; /* Espaço para nav inferior */
}

.content-area {
    padding: 20px;
    min-height: calc(100vh - 160px);
}

/* Dashboard */
.dashboard-container {
    max-width: 500px;
    margin: 0 auto;
}

.princess-welcome {
    text-align: center;
    background: rgba(255, 255, 255, 0.9);
    border-radius: 20px;
    padding: 30px 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}

.princess-welcome h1 {
    font-family: 'Dancing Script', cursive;
    color: #ff1493;
    font-size: 2rem;
    margin-bottom: 10px;
}

.princess-quote {
    color: #666;
    font-style: italic;
    margin: 0;
}

/* Cards de estatísticas */
.quick-stats {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 15px;
    margin-bottom: 20px;
}

.stat-card {
    background: white;
    border-radius: 15px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 2px 15px rgba(0,0,0,0.1);
}

.stat-icon {
    font-size: 2rem;
    margin-bottom: 10px;
}

.stat-info h3 {
    color: #ff1493;
    font-size: 1.5rem;
    margin: 0;
    font-weight: 600;
}

.stat-info p {
    color: #666;
    font-size: 0.8rem;
    margin: 0;
}

/* Ações rápidas */
.quick-actions {
    display: flex;
    gap: 10px;
    margin-bottom: 25px;
}

.action-btn {
    flex: 1;
    border: none;
    border-radius: 12px;
    padding: 15px;
    font-weight: 500;
    transition: all 0.3s ease;
}

.action-btn.primary {
    background: linear-gradient(45deg, #ff69b4, #ff1493);
    color: white;
}

.action-btn.secondary {
    background: rgba(255, 255, 255, 0.9);
    color: #ff1493;
}

.action-btn:active {
    transform: scale(0.95);
}

/* Tarefas */
.tasks-container, .routines-container {
    max-width: 500px;
    margin: 0 auto;
}

.tasks-header, .routines-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(255, 255, 255, 0.9);
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 20px;
}

.tasks-header h2, .routines-header h2 {
    color: #ff1493;
    margin: 0;
    font-size: 1.3rem;
}

.btn-add {
    background: linear-gradient(45deg, #ff69b4, #ff1493);
    border: none;
    border-radius: 50%;
    width: 45px;
    height: 45px;
    color: white;
    font-size: 1.2rem;
}

/* Filtros */
.tasks-filter {
    display: flex;
    gap: 5px;
    margin-bottom: 20px;
    background: rgba(255, 255, 255, 0.9);
    border-radius: 12px;
    padding: 5px;
}

.filter-btn {
    flex: 1;
    background: transparent;
    border: none;
    padding: 10px;
    border-radius: 8px;
    color: #666;
    font-weight: 500;
    transition: all 0.3s ease;
}

.filter-btn.active {
    background: linear-gradient(45deg, #ff69b4, #ff1493);
    color: white;
}

/* Items de tarefa */
.task-item, .routine-item {
    background: white;
    border-radius: 15px;
    padding: 15px;
    margin-bottom: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    display: flex;
    align-items: center;
    gap: 15px;
}

.task-item.completed {
    opacity: 0.6;
}

.task-checkbox {
    color: #ff1493;
    font-size: 1.2rem;
    cursor: pointer;
}

.task-content {
    flex: 1;
}

.task-content h4 {
    margin: 0 0 5px 0;
    color: #333;
    font-size: 1rem;
}

.task-content p {
    margin: 0 0 5px 0;
    color: #666;
    font-size: 0.9rem;
}

.task-meta {
    display: flex;
    gap: 10px;
    align-items: center;
}

.task-priority {
    font-size: 0.7rem;
    padding: 2px 8px;
    border-radius: 10px;
    text-transform: uppercase;
    font-weight: 600;
}

.priority-alta {
    background: #ffe6e6;
    color: #e74c3c;
}

.priority-media {
    background: #fff4e6;
    color: #f39c12;
}

.priority-baixa {
    background: #e6f7e6;
    color: #27ae60;
}

.task-delete {
    background: none;
    border: none;
    color: #e74c3c;
    font-size: 1rem;
    padding: 5px;
}

/* Mini tarefas no dashboard */
.todays-tasks {
    background: rgba(255, 255, 255, 0.9);
    border-radius: 15px;
    padding: 20px;
}

.todays-tasks h3 {
    color: #ff1493;
    margin: 0 0 15px 0;
    font-size: 1.1rem;
}

.task-item-mini {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 0;
    border-bottom: 1px solid #f0f0f0;
}

.task-item-mini:last-child {
    border-bottom: none;
}

.no-tasks, .no-items {
    text-align: center;
    color: #999;
    padding: 40px 20px;
    font-style: italic;
}

/* Rotinas */
.routine-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
}

.routine-toggle {
    color: #ff1493;
    font-size: 1.5rem;
    cursor: pointer;
}

.routine-item.inactive {
    opacity: 0.5;
}

.routine-schedule {
    display: flex;
    gap: 15px;
    font-size: 0.8rem;
    color: #666;
    margin-top: 5px;
}

/* Animações */
@keyframes bounce {
    from { transform: translateY(0); }
    to { transform: translateY(-10px); }
}

@keyframes heartBeat {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.2); }
}

/* Responsivo */
@media (max-width: 480px) {
    .quick-stats {
        grid-template-columns: 1fr;
        gap: 10px;
    }
    
    .stat-card {
        display: flex;
        align-items: center;
        gap: 15px;
        text-align: left;
        padding: 15px;
    }
    
    .stat-icon {
        margin-bottom: 0;
        font-size: 1.5rem;
    }
}

/* Dark mode (futuro) */
@media (prefers-color-scheme: dark) {
    /* Estilos para modo escuro */
}'''
        
        # Salvar CSS mobile
        with open(self.www_dir / 'static' / 'css' / 'app-mobile.css', 'w', encoding='utf-8') as f:
            f.write(mobile_css)
        
        print("🎨 CSS Mobile criado")
    
    def create_android_resources(self):
        """Cria diretório para recursos Android"""
        resources_dir = self.project_root / 'android-resources'
        resources_dir.mkdir(exist_ok=True)
        
        # Criar estrutura de ícones
        icon_sizes = ['hdpi', 'mdpi', 'xhdpi', 'xxhdpi', 'xxxhdpi']
        for size in icon_sizes:
            (resources_dir / f'mipmap-{size}').mkdir(exist_ok=True)
        
        # Arquivo de instruções para ícones
        instructions = '''# 📱 RECURSOS ANDROID - ÍCONES

## 🎨 Criando Ícones da Princesa

### Tamanhos Necessários:

- **mdpi**: 48x48px
- **hdpi**: 72x72px  
- **xhdpi**: 96x96px
- **xxhdpi**: 144x144px
- **xxxhdpi**: 192x192px

### 🛠️ Ferramentas Recomendadas:

1. **Android Asset Studio**: https://romannurik.github.io/AndroidAssetStudio/
2. **App Icon Generator**: https://appicon.co/
3. **Capacitor Assets**: `npx @capacitor/assets generate`

### 📝 Instruções:

1. Criar logo da princesa 1024x1024px (PNG com fundo transparente)
2. Usar ferramenta para gerar todos os tamanhos
3. Colocar arquivos nas pastas correspondentes
4. Renomear para: `ic_launcher.png` e `ic_launcher_round.png`

### 🌈 Cores do App:

- **Primary**: #ff1493 (Deep Pink)
- **Secondary**: #ff69b4 (Hot Pink)  
- **Accent**: #ffc0cb (Light Pink)
- **Background**: #ffffff (White)
'''
        
        with open(resources_dir / 'ICON_INSTRUCTIONS.md', 'w', encoding='utf-8') as f:
            f.write(instructions)
        
        print("📁 Estrutura de recursos Android criada")
    
    def build(self):
        """Executa o build completo"""
        print("🌸 Iniciando build da Princesa App...")
        
        self.clean_www()
        self.copy_static_files()
        self.generate_static_html()
        self.create_capacitor_js()
        self.create_mobile_css()
        self.create_android_resources()
        
        print("✅ Build concluído com sucesso!")
        print("\n📱 Próximos passos:")
        print("1. npm install")
        print("2. npx cap add android")
        print("3. npm run android:build") 
        print("4. npm run android:open")

if __name__ == "__main__":
    builder = PrincessAppBuilder()
    builder.build()