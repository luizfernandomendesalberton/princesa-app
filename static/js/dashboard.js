/**
 * Dashboard JavaScript - Princesa Ana Paula
 * Funções específicas da página de dashboard
 */

function markRoutineExecuted(routineId) {
    // Implementar lógica para marcar rotina como executada
    const btn = event.target.closest('button');
    btn.innerHTML = '<i class="fas fa-check"></i> Feito!';
    btn.disabled = true;
    btn.classList.add('btn-success');
    
    // Aqui você pode adicionar uma requisição AJAX para salvar no banco
    setTimeout(() => {
        btn.closest('.routine-item').style.opacity = '0.6';
    }, 500);
}

// Inicialização específica do dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard carregado!');
});