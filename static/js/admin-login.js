// Admin login page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Foco automático no campo de senha
    const passwordField = document.getElementById('admin_password');
    if (passwordField) {
        passwordField.focus();
    }
    
    // Animação de entrada
    const card = document.querySelector('.admin-card');
    if (card) {
        card.style.opacity = '0';
        card.style.transform = 'translateY(-20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 100);
    }
});