// Funções gerais do Princesa App
console.log('🌸 Carregando Princesa App...');

// PWA Detection
if (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true) {
    console.log('🏰 PWA: Rodando como aplicativo instalado!');
    document.body.classList.add('pwa-mode');
}

// PWA Install functionality
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    
    // Criar botão de instalação se não existir
    if (!document.getElementById('installBtn')) {
        const installBtn = document.createElement('button');
        installBtn.id = 'installBtn';
        installBtn.innerHTML = '<i class="fas fa-download"></i> Instalar App';
        installBtn.className = 'btn btn-sm btn-outline-light install-btn';
        installBtn.style.cssText = 'position:fixed;top:10px;right:10px;z-index:9999;opacity:0.8;';
        
        installBtn.addEventListener('click', async () => {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                const { outcome } = await deferredPrompt.userChoice;
                if (outcome === 'accepted') {
                    console.log('🌸 PWA: App instalado!');
                    installBtn.style.display = 'none';
                }
                deferredPrompt = null;
            }
        });
        
        document.body.appendChild(installBtn);
        
        // Auto-hide após 10 segundos
        setTimeout(() => {
            if (installBtn && installBtn.parentNode) {
                installBtn.style.opacity = '0.3';
            }
        }, 10000);
    }
});

// Service Worker Registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('🌸 SW: Service Worker registrado!', registration);
            })
            .catch(error => {
                console.log('❌ SW: Falha no registro', error);
            });
    });
}

// Toast notification system
function showToast(message, type = 'info') {
    // Criar toast notification
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} toast-notification`;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255,255,255,0.2);
        max-width: 350px;
        animation: slideIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        font-weight: 500;
    `;
    toast.innerHTML = `
        <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-info-circle'}"></i>
        ${message}
    `;
    
    document.body.appendChild(toast);
    
    // Remover após 4 segundos
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 4000);
}

// Hearts animation for princess theme
function createHearts() {
    const heartsContainer = document.createElement('div');
    heartsContainer.className = 'princess-hearts';
    heartsContainer.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 1;
        overflow: hidden;
    `;
    
    for (let i = 0; i < 6; i++) {
        const heart = document.createElement('div');
        heart.className = 'heart';
        heart.innerHTML = '💖';
        heart.style.cssText = `
            position: absolute;
            left: ${Math.random() * 100}%;
            animation-delay: ${Math.random() * 3}s;
            animation-duration: ${3 + Math.random() * 2}s;
        `;
        heartsContainer.appendChild(heart);
    }
    
    document.body.appendChild(heartsContainer);
    
    // Remove after animation
    setTimeout(() => {
        if (heartsContainer.parentNode) {
            heartsContainer.parentNode.removeChild(heartsContainer);
        }
    }, 8000);
}

// Add floating hearts on certain actions
document.addEventListener('DOMContentLoaded', function() {
    // Add hearts on successful actions
    const successAlerts = document.querySelectorAll('.alert-success');
    if (successAlerts.length > 0) {
        setTimeout(createHearts, 500);
    }
});

// AJAX form helpers
function toggleTask(taskId) {
    fetch(`/toggle_task/${taskId}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload(); // Refresh to show updated status
            showToast('✨ Status atualizado!', 'success');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        showToast('❌ Erro ao atualizar', 'error');
    });
}

function toggleRoutine(routineId) {
    fetch(`/toggle_routine/${routineId}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload(); // Refresh to show updated status
            showToast('⚡ Rotina atualizada!', 'success');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        showToast('❌ Erro ao atualizar', 'error');
    });
}

// Form validation helpers
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePassword(password) {
    return password.length >= 8 && /[A-Za-z]/.test(password) && /[0-9]/.test(password);
}