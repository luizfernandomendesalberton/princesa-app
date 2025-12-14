/**
 * Princess App - JavaScript Interativo
 * Sistema de Tarefas e Rotinas para Princesa Ana Paula
 */

class PrincessApp {
    constructor() {
        this.init();
        this.setupEventListeners();
        this.startAnimations();
    }

    init() {
        console.log('🌸 Princesa App inicializada! 💖');
        this.showWelcomeMessage();
        this.setupNotifications();
        this.loadUserPreferences();
    }

    setupEventListeners() {
        // Auto-save para formulários
        this.setupAutoSave();
        
        // Confirmações suaves
        this.setupSoftConfirmations();
        
        // Teclado shortcuts
        this.setupKeyboardShortcuts();
        
        // Drag & Drop para tarefas
        this.setupDragDrop();
        
        // Real-time validation
        this.setupFormValidation();
    }

    showWelcomeMessage() {
        const currentHour = new Date().getHours();
        let greeting;
        
        if (currentHour < 12) {
            greeting = "Bom dia, Princesa! ☀️";
        } else if (currentHour < 18) {
            greeting = "Boa tarde, Princesa! 🌸";
        } else {
            greeting = "Boa noite, Princesa! 🌙";
        }
        
        // Mostrar apenas se não for a página de login
        if (!window.location.pathname.includes('login')) {
            this.showToast(greeting, 'success', 3000);
        }
    }

    showToast(message, type = 'info', duration = 3000) {
        // Remove toasts existentes
        const existingToasts = document.querySelectorAll('.princess-toast');
        existingToasts.forEach(toast => toast.remove());

        const toast = document.createElement('div');
        toast.className = `princess-toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <span class="toast-message">${message}</span>
                <button class="toast-close">&times;</button>
            </div>
        `;

        // Estilos inline para o toast
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            z-index: 10000;
            transform: translateX(400px);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            max-width: 350px;
            backdrop-filter: blur(10px);
        `;

        if (type === 'success') {
            toast.style.background = 'linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%)';
        } else if (type === 'error') {
            toast.style.background = 'linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%)';
        }

        document.body.appendChild(toast);

        // Animação de entrada
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 100);

        // Evento de fechar
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => this.hideToast(toast));

        // Auto-remover
        setTimeout(() => {
            this.hideToast(toast);
        }, duration);
    }

    hideToast(toast) {
        toast.style.transform = 'translateX(400px)';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }

    setupAutoSave() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            const inputs = form.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                input.addEventListener('input', () => {
                    this.saveFormData(form);
                });
            });
        });
    }

    saveFormData(form) {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);
        const formId = form.id || 'unnamed-form';
        
        localStorage.setItem(`princess-form-${formId}`, JSON.stringify(data));
        
        // Mostrar indicador visual de salvamento
        this.showSaveIndicator();
    }

    showSaveIndicator() {
        const indicator = document.createElement('div');
        indicator.innerHTML = '💾 Rascunho salvo';
        indicator.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 20px;
            background: rgba(108, 117, 125, 0.9);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            z-index: 9999;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;

        document.body.appendChild(indicator);

        setTimeout(() => {
            indicator.style.opacity = '1';
        }, 100);

        setTimeout(() => {
            indicator.style.opacity = '0';
            setTimeout(() => {
                if (indicator.parentNode) {
                    indicator.parentNode.removeChild(indicator);
                }
            }, 300);
        }, 2000);
    }

    setupSoftConfirmations() {
        // Substituir confirms nativos por modais bonitos
        const deleteButtons = document.querySelectorAll('[onclick*="delete"]');
        deleteButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const itemName = button.closest('.task-card, .routine-card')?.querySelector('h5, .task-title, .routine-title')?.textContent || 'este item';
                this.showConfirmModal(`Deseja realmente excluir "${itemName}"?`, () => {
                    // Executar a ação original
                    eval(button.getAttribute('onclick'));
                });
            });
        });
    }

    showConfirmModal(message, onConfirm, onCancel = null) {
        const modal = document.createElement('div');
        modal.className = 'princess-confirm-modal';
        modal.innerHTML = `
            <div class="confirm-overlay">
                <div class="confirm-dialog">
                    <div class="confirm-header">
                        <h5><i class="fas fa-question-circle"></i> Confirmação</h5>
                    </div>
                    <div class="confirm-body">
                        <p>${message}</p>
                    </div>
                    <div class="confirm-footer">
                        <button class="btn btn-secondary confirm-cancel">Cancelar</button>
                        <button class="btn princess-btn-primary confirm-ok">Confirmar</button>
                    </div>
                </div>
            </div>
        `;

        // Estilos inline
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 10001;
        `;

        const overlay = modal.querySelector('.confirm-overlay');
        overlay.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(5px);
        `;

        const dialog = modal.querySelector('.confirm-dialog');
        dialog.style.cssText = `
            background: white;
            border-radius: 20px;
            padding: 2rem;
            max-width: 400px;
            width: 90%;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            transform: scale(0.8);
            transition: transform 0.3s ease;
        `;

        document.body.appendChild(modal);

        // Animação de entrada
        setTimeout(() => {
            dialog.style.transform = 'scale(1)';
        }, 100);

        // Event listeners
        modal.querySelector('.confirm-cancel').addEventListener('click', () => {
            this.hideConfirmModal(modal);
            if (onCancel) onCancel();
        });

        modal.querySelector('.confirm-ok').addEventListener('click', () => {
            this.hideConfirmModal(modal);
            if (onConfirm) onConfirm();
        });

        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                this.hideConfirmModal(modal);
                if (onCancel) onCancel();
            }
        });
    }

    hideConfirmModal(modal) {
        const dialog = modal.querySelector('.confirm-dialog');
        dialog.style.transform = 'scale(0.8)';
        setTimeout(() => {
            if (modal.parentNode) {
                modal.parentNode.removeChild(modal);
            }
        }, 300);
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + N = Nova tarefa
            if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
                e.preventDefault();
                const addTaskBtn = document.querySelector('[data-bs-target="#addTaskModal"]');
                if (addTaskBtn) {
                    addTaskBtn.click();
                    this.showToast('Atalho: Ctrl+N para nova tarefa 📝', 'info', 2000);
                }
            }

            // Ctrl/Cmd + R = Nova rotina
            if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
                e.preventDefault();
                const addRoutineBtn = document.querySelector('[data-bs-target="#addRoutineModal"]');
                if (addRoutineBtn) {
                    addRoutineBtn.click();
                    this.showToast('Atalho: Ctrl+R para nova rotina 📅', 'info', 2000);
                }
            }

            // ESC = Fechar modais
            if (e.key === 'Escape') {
                const modals = document.querySelectorAll('.modal.show, .princess-confirm-modal');
                modals.forEach(modal => {
                    const closeBtn = modal.querySelector('.btn-close, .confirm-cancel');
                    if (closeBtn) closeBtn.click();
                });
            }
        });
    }

    setupDragDrop() {
        // Implementação futura para reordenar tarefas
        const taskCards = document.querySelectorAll('.task-card, .routine-card');
        taskCards.forEach(card => {
            card.style.cursor = 'move';
            // Implementação completa do drag & drop seria adicionada aqui
        });
    }

    setupFormValidation() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!this.validateForm(form)) {
                    e.preventDefault();
                    this.showToast('Por favor, verifique os campos obrigatórios 📝', 'error');
                }
            });
        });
    }

    validateForm(form) {
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;

        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                this.highlightField(field, false);
                isValid = false;
            } else {
                this.highlightField(field, true);
            }
        });

        return isValid;
    }

    highlightField(field, isValid) {
        field.style.borderColor = isValid ? '#28a745' : '#dc3545';
        field.style.boxShadow = `0 0 0 0.2rem ${isValid ? 'rgba(40, 167, 69, 0.25)' : 'rgba(220, 53, 69, 0.25)'}`;

        setTimeout(() => {
            field.style.borderColor = '';
            field.style.boxShadow = '';
        }, 3000);
    }

    setupNotifications() {
        // Verificar se há tarefas com prazo vencido
        this.checkOverdueTasks();
        
        // Verificar rotinas do dia
        this.checkTodayRoutines();
        
        // Configurar verificação periódica
        setInterval(() => {
            this.checkOverdueTasks();
        }, 300000); // A cada 5 minutos
    }

    checkOverdueTasks() {
        const taskCards = document.querySelectorAll('.task-card:not(.completed)');
        const today = new Date().toISOString().split('T')[0];
        
        taskCards.forEach(card => {
            const dateElement = card.querySelector('.task-date');
            if (dateElement) {
                const taskDate = dateElement.textContent.split('/').reverse().join('-');
                if (taskDate < today) {
                    card.style.borderColor = '#ff6b6b';
                    card.classList.add('overdue');
                }
            }
        });
    }

    checkTodayRoutines() {
        const now = new Date();
        const currentTime = now.toTimeString().slice(0, 5);
        const routineCards = document.querySelectorAll('.routine-card.active');
        
        routineCards.forEach(card => {
            const timeElement = card.querySelector('.routine-time');
            if (timeElement) {
                const routineTime = timeElement.textContent.trim().slice(-5);
                if (routineTime === currentTime) {
                    this.showToast('🔔 Hora da rotina: ' + card.querySelector('.routine-title').textContent, 'info', 5000);
                }
            }
        });
    }

    startAnimations() {
        // Animações de entrada para elementos
        this.animateOnScroll();
        
        // Efeitos de hover especiais
        this.setupHoverEffects();
        
        // Partículas flutuantes (opcional)
        this.createFloatingParticles();
    }

    animateOnScroll() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.animationPlayState = 'running';
                }
            });
        }, { threshold: 0.1 });

        const animatedElements = document.querySelectorAll('.task-card, .routine-card, .princess-card');
        animatedElements.forEach(el => {
            el.style.animation = 'fadeInUp 0.6s ease-out paused';
            observer.observe(el);
        });
    }

    setupHoverEffects() {
        const cards = document.querySelectorAll('.task-card, .routine-card');
        cards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                this.createSparkleEffect(card);
            });
        });
    }

    createSparkleEffect(element) {
        const sparkle = document.createElement('div');
        sparkle.innerHTML = '✨';
        sparkle.style.cssText = `
            position: absolute;
            top: 10px;
            right: 10px;
            font-size: 1.2rem;
            animation: sparkle-pop 1s ease-out;
            pointer-events: none;
            z-index: 10;
        `;

        element.style.position = 'relative';
        element.appendChild(sparkle);

        setTimeout(() => {
            if (sparkle.parentNode) {
                sparkle.parentNode.removeChild(sparkle);
            }
        }, 1000);
    }

    createFloatingParticles() {
        // Criar partículas sutis que flutuam pela tela
        const particleContainer = document.createElement('div');
        particleContainer.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: -1;
        `;

        for (let i = 0; i < 5; i++) {
            const particle = document.createElement('div');
            particle.innerHTML = ['💫', '✨', '🌟', '⭐', '💖'][Math.floor(Math.random() * 5)];
            particle.style.cssText = `
                position: absolute;
                font-size: 1.5rem;
                opacity: 0.3;
                animation: float-particle ${5 + Math.random() * 10}s linear infinite;
                left: ${Math.random() * 100}%;
                animation-delay: ${Math.random() * 10}s;
            `;
            
            particleContainer.appendChild(particle);
        }

        document.body.appendChild(particleContainer);
    }

    loadUserPreferences() {
        // Carregar preferências salvas do usuário
        const preferences = JSON.parse(localStorage.getItem('princess-preferences') || '{}');
        
        // Aplicar tema se salvo
        if (preferences.theme) {
            document.body.classList.add(preferences.theme);
        }
        
        // Restaurar dados de formulários salvos
        this.restoreFormData();
    }

    restoreFormData() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            const formId = form.id || 'unnamed-form';
            const savedData = localStorage.getItem(`princess-form-${formId}`);
            
            if (savedData) {
                const data = JSON.parse(savedData);
                Object.entries(data).forEach(([name, value]) => {
                    const field = form.querySelector(`[name="${name}"]`);
                    if (field) {
                        field.value = value;
                    }
                });
            }
        });
    }
}

// Adicionar estilos para animações
const animationStyles = document.createElement('style');
animationStyles.textContent = `
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes sparkle-pop {
        0% {
            opacity: 0;
            transform: scale(0);
        }
        50% {
            opacity: 1;
            transform: scale(1.2);
        }
        100% {
            opacity: 0;
            transform: scale(0.8);
        }
    }
    
    @keyframes float-particle {
        0% {
            transform: translateY(100vh) rotate(0deg);
        }
        100% {
            transform: translateY(-100px) rotate(360deg);
        }
    }
    
    .overdue {
        animation: pulse-warning 2s ease-in-out infinite;
    }
    
    @keyframes pulse-warning {
        0%, 100% {
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
        }
        50% {
            box-shadow: 0 5px 15px rgba(255, 107, 107, 0.4);
        }
    }
`;
document.head.appendChild(animationStyles);

// Inicializar a aplicação quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', () => {
    new PrincessApp();
});

// Exportar para uso global se necessário
window.PrincessApp = PrincessApp;