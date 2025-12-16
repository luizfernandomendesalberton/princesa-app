// Profile page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Verificar status das notificações
    checkNotificationStatus();
    checkPWAStatus();
});

function checkNotificationStatus() {
    const pushStatus = document.getElementById('push-status');
    if (!pushStatus) return;
    
    if ('Notification' in window) {
        if (Notification.permission === 'granted') {
            pushStatus.innerHTML = '<span class="status-badge status-active">✅ Ativadas</span>';
        } else if (Notification.permission === 'denied') {
            pushStatus.innerHTML = '<span class="status-badge status-inactive">❌ Bloqueadas</span>';
        } else {
            pushStatus.innerHTML = '<span class="status-badge" style="background: #fff3cd; color: #856404;">⏳ Pendente</span>';
        }
    } else {
        pushStatus.innerHTML = '<span class="status-badge status-inactive">❌ Não suportadas</span>';
    }
}

function checkPWAStatus() {
    const pwaStatus = document.getElementById('pwa-status');
    if (!pwaStatus) return;
    
    if (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true) {
        pwaStatus.innerHTML = '<span class="status-badge status-active">✅ Instalado</span>';
    } else {
        pwaStatus.innerHTML = '<span class="status-badge" style="background: #fff3cd; color: #856404;">📱 Pode instalar</span>';
    }
}