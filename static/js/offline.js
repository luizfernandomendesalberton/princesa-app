// Offline page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const statusElement = document.getElementById('connectionStatus');
    const statusText = document.getElementById('statusText');
    
    // Verificar status de conexão
    function updateConnectionStatus() {
        if (navigator.onLine) {
            statusElement.classList.remove('offline');
            statusElement.classList.add('online');
            statusText.textContent = 'Conectado! Redirecionando...';
            
            // Redirecionar quando voltar online
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 2000);
        } else {
            statusElement.classList.remove('online');
            statusElement.classList.add('offline');
            statusText.textContent = 'Sem conexão';
        }
    }
    
    // Monitorar mudanças de conexão
    window.addEventListener('online', updateConnectionStatus);
    window.addEventListener('offline', updateConnectionStatus);
    
    // Verificação inicial
    updateConnectionStatus();
    
    // Verificar periodicamente
    setInterval(updateConnectionStatus, 5000);
});