// Adicionar interatividade ao fórum (ex.: confirmação de criação)
document.addEventListener('DOMContentLoaded', function() {
    const forumForm = document.getElementById('forumForm');
    if (forumForm) {
        forumForm.addEventListener('submit', function(e) {
            const titulo = document.getElementById('tituloForum').value;
            if (!confirm(`Deseja criar o fórum "${titulo}"?`)) {
                e.preventDefault();
            }
        });
    }
});