// Sistema de Notificações da Princesa
class PrincessNotifications {
    constructor() {
        this.permission = 'default';
        this.checkInterval = null;
        this.seenNotifications = new Set();
        this.isActive = false;
        this.init();
    }
    
    async init() {
        console.log('🔔 Inicializando sistema de notificações...');
        
        if (!('Notification' in window)) {
            console.log('⚠️ Notificações não suportadas');
            return;
        }
        
        this.permission = Notification.permission;
        
        if (this.permission === 'granted') {
            this.isActive = false; // Iniciar desativado
            console.log('🔔 Sistema pronto');
        }
    }
    
    async requestPermission() {
        try {
            this.permission = await Notification.requestPermission();
            if (this.permission === 'granted') {
                this.showWelcomeNotification();
            }
        } catch (error) {
            console.error('Erro ao solicitar permissão:', error);
        }
    }
    
    showWelcomeNotification() {
        new Notification('👑 Princesa App', {
            body: 'Notificações ativadas! Você será avisada sobre suas rotinas e tarefas.',
            icon: '/static/icons/icon-192x192.png',
            badge: '/static/icons/icon-72x72.png'
        });
    }
    
    startChecking() {
        if (this.checkInterval) return;
        
        // Verificar a cada 30 segundos
        this.checkInterval = setInterval(() => {
            this.checkForNotifications();
        }, 30000);
        
        // Verificar imediatamente
        this.checkForNotifications();
        this.isActive = true;
    }
    
    stopChecking() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
            this.checkInterval = null;
        }
        this.isActive = false;
    }
    
    async checkForNotifications() {
        try {
            const response = await fetch('/api/check_notifications');
            const data = await response.json();
            
            if (data.notifications && data.notifications.length > 0) {
                data.notifications.forEach(notification => {
                    if (!this.seenNotifications.has(notification.id)) {
                        this.showNotification(notification);
                        this.seenNotifications.add(notification.id);
                    }
                });
            }
        } catch (error) {
            console.error('Erro ao verificar notificações:', error);
        }
    }
    
    showNotification(notif) {
        if (this.permission !== 'granted' || !this.isActive) return;
        
        const options = {
            body: notif.message,
            icon: '/static/icons/icon-192x192.png',
            badge: '/static/icons/icon-72x72.png',
            tag: notif.id,
            requireInteraction: true,
            data: notif
        };
        
        if (notif.type === 'routine') {
            options.body += `\n⏰ ${notif.time}`;
            if (notif.description) {
                options.body += `\n${notif.description}`;
            }
        } else if (notif.type === 'task') {
            options.body += `\n📅 Prazo: ${notif.due_date}`;
            if (notif.description) {
                options.body += `\n${notif.description}`;
            }
        }
        
        const notification = new Notification(notif.title, options);
        
        notification.onclick = () => {
            window.focus();
            if (notif.type === 'routine') {
                window.location.href = '/routines';
            } else if (notif.type === 'task') {
                window.location.href = '/tasks';
            }
            notification.close();
            
            // Marcar como vista
            fetch(`/api/mark_notification_seen/${notif.id}`);
        };
        
        // Auto-fechar após 10 segundos
        setTimeout(() => {
            notification.close();
        }, 10000);
    }
    
    toggle() {
        if (this.isActive) {
            this.stopChecking();
            this.isActive = false;
            console.log('🔕 Notificações desativadas');
            return false;
        } else {
            if (this.permission === 'granted') {
                this.startChecking();
                this.isActive = true;
                console.log('🔔 Notificações ativadas');
                return true;
            } else {
                console.log('⚠️ Permissão necessária para notificações');
                this.requestPermission();
                return false;
            }
        }
    }
}

// Inicializar sistema após DOM estar pronto
let princessNotifications = null;

document.addEventListener('DOMContentLoaded', function() {
    console.log('🌸 Inicializando sistema de notificações...');
    princessNotifications = new PrincessNotifications();
    window.princessNotifications = princessNotifications;
    
    // Atualizar botão inicial
    setTimeout(() => {
        updateNotificationButton(princessNotifications.isActive);
    }, 1000);
});

// Função para toggle de notificações - Corrigida
function toggleNotifications() {
    console.log('🔔 Botão de notificações clicado!');
    
    if (!window.princessNotifications) {
        console.log('⚠️ Sistema de notificações não inicializado ainda');
        showToast('⚠️ Aguarde, sistema carregando...', 'warning');
        return;
    }
    
    // Verificar permissão primeiro
    if (Notification.permission === 'default') {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                window.princessNotifications.permission = 'granted';
                const isActive = window.princessNotifications.toggle();
                updateNotificationButton(isActive);
                showToast('🔔 Notificações ativadas! Você será avisada sobre suas rotinas e tarefas.', 'success');
            } else {
                showToast('❌ Permissão negada. Ative nas configurações do navegador.', 'error');
            }
        });
        return;
    }
    
    if (Notification.permission === 'denied') {
        showToast('🙅 Notificações bloqueadas. Ative nas configurações do navegador.', 'warning');
        return;
    }
    
    // Toggle normal
    const isActive = window.princessNotifications.toggle();
    updateNotificationButton(isActive);
    
    if (isActive) {
        showToast('🔔 Notificações ativadas! Você será avisada sobre suas rotinas e tarefas.', 'success');
    } else {
        showToast('🔕 Notificações pausadas temporariamente.', 'info');
    }
}

function updateNotificationButton(isActive) {
    const icon = document.getElementById('notificationIcon');
    const status = document.getElementById('notificationStatus');
    const button = document.getElementById('notificationToggle');
    
    console.log('🎨 Atualizando botão:', isActive ? 'Ativo' : 'Inativo');
    
    if (icon && status) {
        if (isActive) {
            icon.className = 'fas fa-bell';
            status.textContent = '🔔';
            status.className = 'notification-status active';
            if (button) button.title = 'Desativar Notificações';
        } else {
            icon.className = 'fas fa-bell-slash';
            status.textContent = '🔕';
            status.className = 'notification-status inactive';
            if (button) button.title = 'Ativar Notificações';
        }
    } else {
        console.log('⚠️ Elementos do botão não encontrados');
    }
}