/**
 * Tasks JavaScript - Princesa Ana Paula
 * Funções específicas da página de tarefas
 */

function toggleTask(taskId) {
    fetch(`/toggle_task/${taskId}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (response.headers.get('content-type')?.includes('application/json')) {
            return response.json();
        } else {
            // Se não for JSON, recarregar a página
            location.reload();
            return null;
        }
    })
    .then(data => {
        if (data && data.success) {
            const taskCard = document.querySelector(`[data-task-id="${taskId}"]`);
            const checkbox = document.querySelector(`#task-${taskId}`);
            
            if (checkbox.checked) {
                taskCard.classList.add('completed');
                taskCard.classList.remove('pending');
                
                // Adicionar efeito de confetti
                showConfetti();
            } else {
                taskCard.classList.remove('completed');
                taskCard.classList.add('pending');
            }
        }
    })
    .catch(error => {
        console.error('Erro:', error);
    });
}

function deleteTask(taskId) {
    if (confirm('Tem certeza que deseja excluir esta tarefa?')) {
        fetch(`/delete_task/${taskId}`, {
            method: 'GET'
        })
        .then(() => {
            location.reload();
        })
        .catch(error => {
            console.error('Erro:', error);
        });
    }
}

function showConfetti() {
    // Simples efeito de confetti com emojis
    const confettiContainer = document.createElement('div');
    confettiContainer.style.position = 'fixed';
    confettiContainer.style.top = '0';
    confettiContainer.style.left = '0';
    confettiContainer.style.width = '100%';
    confettiContainer.style.height = '100%';
    confettiContainer.style.pointerEvents = 'none';
    confettiContainer.style.zIndex = '9999';
    
    const emojis = ['🎉', '✨', '💖', '🎊', '🌟'];
    
    for (let i = 0; i < 20; i++) {
        const confetti = document.createElement('div');
        confetti.textContent = emojis[Math.floor(Math.random() * emojis.length)];
        confetti.style.position = 'absolute';
        confetti.style.left = Math.random() * 100 + '%';
        confetti.style.animationDuration = '3s';
        confetti.style.animationName = 'confetti-fall';
        confetti.style.fontSize = '2rem';
        
        confettiContainer.appendChild(confetti);
    }
    
    document.body.appendChild(confettiContainer);
    
    setTimeout(() => {
        document.body.removeChild(confettiContainer);
    }, 3000);
}

// Inicialização específica das tarefas
document.addEventListener('DOMContentLoaded', function() {
    // Adicionar CSS para animação do confetti
    const style = document.createElement('style');
    style.textContent = `
        @keyframes confetti-fall {
            0% {
                transform: translateY(-100vh) rotate(0deg);
                opacity: 1;
            }
            100% {
                transform: translateY(100vh) rotate(360deg);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
    
    console.log('Página de tarefas carregada!');
});