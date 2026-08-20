// Fonctions utilitaires globales
function formatTime(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleTimeString('fr-FR', { 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit'
    });
}

// Gestion des erreurs globales
window.addEventListener('error', function(e) {
    console.error('Erreur:', e.error);
});

// Service Worker pour PWA (optionnel)
if ('serviceWorker' in navigator) {
    // Pourrait être ajouté pour le mode hors-ligne
}