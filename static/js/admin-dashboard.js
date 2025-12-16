// Admin Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Animação de entrada dos cards
    const cards = document.querySelectorAll('.user-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
    
    // Confirmação antes de alterar senha
    const forms = document.querySelectorAll('form[action*="change_password"]');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const passwordInput = this.querySelector('input[name="new_password"]');
            const password = passwordInput.value;
            
            if (password.length < 6) {
                e.preventDefault();
                alert('A senha deve ter pelo menos 6 caracteres!');
                passwordInput.focus();
                return;
            }
            
            const userName = this.closest('.user-card').querySelector('h5').textContent.trim();
            if (!confirm(`Tem certeza que deseja alterar a senha de ${userName}?`)) {
                e.preventDefault();
            }
        });
    });
    
    // Auto-limpar campos após sucesso
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('success') === 'password_changed') {
        const inputs = document.querySelectorAll('input[name="new_password"]');
        inputs.forEach(input => input.value = '');
    }
});