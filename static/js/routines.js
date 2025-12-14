/**
 * Routines JavaScript - Princesa Ana Paula
 * Funções específicas da página de rotinas
 */

function toggleRoutine(routineId) {
    fetch(`/routines/toggle/${routineId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const routineCard = document.querySelector(`[data-routine-id="${routineId}"]`);
            const toggle = routineCard.querySelector('input[type="checkbox"]');
            
            if (toggle.checked) {
                routineCard.classList.add('active');
                routineCard.classList.remove('inactive');
            } else {
                routineCard.classList.remove('active');
                routineCard.classList.add('inactive');
            }
        }
    })
    .catch(error => {
        console.error('Erro:', error);
    });
}

function markRoutineExecuted(routineId) {
    const btn = event.target.closest('button');
    btn.innerHTML = '<i class="fas fa-check"></i> Executada!';
    btn.disabled = true;
    btn.classList.remove('princess-btn-success');
    btn.classList.add('btn-success');
    
    // Efeito de sparkles
    showSparkles(btn);
    
    // Aqui você pode adicionar lógica para salvar a execução no banco
    setTimeout(() => {
        btn.innerHTML = '<i class="fas fa-check"></i> Executar';
        btn.disabled = false;
        btn.classList.add('princess-btn-success');
        btn.classList.remove('btn-success');
    }, 3000);
}

function editRoutine(routineId) {
    // Implementar funcionalidade de edição
    alert('Funcionalidade de edição será implementada em breve!');
}

function deleteRoutine(routineId) {
    if (confirm('Tem certeza que deseja excluir esta rotina?')) {
        // Implementar exclusão
        alert('Funcionalidade de exclusão será implementada em breve!');
    }
}

function showSparkles(element) {
    const rect = element.getBoundingClientRect();
    const sparkleContainer = document.createElement('div');
    sparkleContainer.style.position = 'fixed';
    sparkleContainer.style.left = rect.left + 'px';
    sparkleContainer.style.top = rect.top + 'px';
    sparkleContainer.style.width = rect.width + 'px';
    sparkleContainer.style.height = rect.height + 'px';
    sparkleContainer.style.pointerEvents = 'none';
    sparkleContainer.style.zIndex = '9999';
    
    const sparkles = ['✨', '💫', '⭐', '🌟'];
    
    for (let i = 0; i < 10; i++) {
        const sparkle = document.createElement('div');
        sparkle.textContent = sparkles[Math.floor(Math.random() * sparkles.length)];
        sparkle.style.position = 'absolute';
        sparkle.style.left = Math.random() * rect.width + 'px';
        sparkle.style.top = Math.random() * rect.height + 'px';
        sparkle.style.animationDuration = '2s';
        sparkle.style.animationName = 'sparkle-burst';
        sparkle.style.fontSize = '1.5rem';
        
        sparkleContainer.appendChild(sparkle);
    }
    
    document.body.appendChild(sparkleContainer);
    
    setTimeout(() => {
        document.body.removeChild(sparkleContainer);
    }, 2000);
}

// Inicialização específica das rotinas
document.addEventListener('DOMContentLoaded', function() {
    // Adicionar CSS para animação dos sparkles
    const sparkleStyle = document.createElement('style');
    sparkleStyle.textContent = `
        @keyframes sparkle-burst {
            0% {
                transform: scale(0) rotate(0deg);
                opacity: 1;
            }
            50% {
                transform: scale(1.5) rotate(180deg);
                opacity: 0.8;
            }
            100% {
                transform: scale(0) rotate(360deg);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(sparkleStyle);
    
    console.log('Página de rotinas carregada!');
});