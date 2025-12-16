// Sistema de Notificações da Princesa - Versão Limpa
console.log('🔔 Carregando sistema de notificações...');

class PrincessNotifications {
    constructor() {
        this.permission = 'default';
        this.checkInterval = null;
        this.seenNotifications = new Set();
        this.isActive = false;
        this.init();
    }
    
    async init() {
        console.log('🔔 Inicializando sistema...');
        
        if (!('Notification' in window)) {
            console.log('⚠️ Notificações não suportadas');
            return;
        }
        
        this.permission = Notification.permission;
        this.isActive = false; // Sempre começar desativado
        
        console.log('✅ Sistema inicializado');
    }
    
    async requestPermission() {
        try {
            this.permission = await Notification.requestPermission();
            return this.permission === 'granted';
        } catch (error) {
            console.error('Erro ao solicitar permissão:', error);
            return false;
        }
    }
    
    startChecking() {
        if (this.checkInterval) return;
        
        this.checkInterval = setInterval(() => {
            this.checkForNotifications();
        }, 30000);
        
        this.checkForNotifications();
        this.isActive = true;
        console.log('🔔 Verificação ativada');
    }
    
    stopChecking() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
            this.checkInterval = null;
        }
        this.isActive = false;
        console.log('🔕 Verificação desativada');
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
        
        const notification = new Notification(notif.title, {
            body: notif.message,
            icon: '/static/icons/icon-192x192.png',
            badge: '/static/icons/icon-72x72.png'
        });
        
        notification.onclick = () => {
            window.focus();
            notification.close();
            fetch(`/api/mark_notification_seen/${notif.id}`, { method: 'POST' });
        };
        
        setTimeout(() => notification.close(), 10000);
    }
    
    toggle() {
        if (this.isActive) {
            this.stopChecking();
            return false;
        } else {
            if (this.permission === 'granted') {
                this.startChecking();
                return true;
            } else {
                this.requestPermission().then(granted => {
                    if (granted) {
                        this.startChecking();
                        updateNotificationButton(true);
                    }
                });
                return false;
            }
        }
    }
}

// Função global para toggle de notificações
function toggleNotifications() {
    console.log('🔔 Toggle notificações');
    
    if (!window.princessNotifications) {
        console.log('⚠️ Sistema não inicializado');
        return;
    }
    
    const isActive = window.princessNotifications.toggle();
    updateNotificationButton(isActive);
    
    if (isActive) {
        showToast('🔔 Notificações ativadas!', 'success');
    } else {
        showToast('🔕 Notificações pausadas', 'info');
    }
}

// Função para atualizar botão de notificações
function updateNotificationButton(isActive) {
    const icon = document.getElementById('notificationIcon');
    const status = document.getElementById('notificationStatus');
    
    if (icon && status) {
        if (isActive) {
            icon.className = 'fas fa-bell';
            status.textContent = '🔔';
            status.className = 'notification-status active';
        } else {
            icon.className = 'fas fa-bell-slash';
            status.textContent = '🔕';
            status.className = 'notification-status inactive';
        }
    }
}

// Função para mostrar toast
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type}`;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 3000);
}

// Inicializar quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    console.log('🌸 Inicializando Princesa Notifications...');
    window.princessNotifications = new PrincessNotifications();
    
    // Atualizar botão inicial
    setTimeout(() => {
        updateNotificationButton(false);
    }, 500);
});

console.log('✅ Arquivo notifications.js carregado');