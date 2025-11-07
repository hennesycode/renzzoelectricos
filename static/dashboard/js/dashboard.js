/**
 * DASHBOARD RENZZO ELÉCTRICOS - JavaScript
 * Funcionalidad para menú lateral colapsable y mejoras de UI
 */

document.addEventListener('DOMContentLoaded', function() {
    initSidebar();
    initUserDropdown();
    highlightActiveMenu();
});

/**
 * Inicializar sidebar colapsable
 */
function initSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    const mainContent = document.querySelector('.main-content');
    const sidebarOpenBtn = document.querySelector('.sidebar-open-btn');
    
    if (!sidebarToggle || !sidebar) return;
    
    // Cargar estado del sidebar desde localStorage
    const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    if (sidebarCollapsed) {
        sidebar.classList.add('collapsed');
    }

    // Función para sincronizar la visibilidad del botón externo
    function updateSidebarOpenBtnVisibility() {
        if (!sidebarOpenBtn) return;
        if (sidebar.classList.contains('collapsed')) {
            sidebarOpenBtn.style.display = 'flex';
        } else {
            sidebarOpenBtn.style.display = 'none';
        }
    }
    // Ejecutar al iniciar para dejar el estado correcto
    updateSidebarOpenBtnVisibility();
    
    // Toggle sidebar al hacer clic
    sidebarToggle.addEventListener('click', function() {
        sidebar.classList.toggle('collapsed');
        
        // Guardar estado en localStorage
        const isCollapsed = sidebar.classList.contains('collapsed');
        localStorage.setItem('sidebarCollapsed', isCollapsed);
        
        // Animación suave
        if (mainContent) {
            mainContent.style.transition = 'margin-left 0.3s ease';
        }

        // Actualizar visibilidad del botón externo tras el toggle
        updateSidebarOpenBtnVisibility();
    });

    // Si existe el botón externo (visible cuando está colapsada), enlazar su acción
    if (sidebarOpenBtn) {
        sidebarOpenBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            sidebar.classList.remove('collapsed');
            localStorage.setItem('sidebarCollapsed', 'false');
            // Asegurar que el botón externo se oculte inmediatamente
            updateSidebarOpenBtnVisibility();
        });
    }
    
    // En móviles, cerrar sidebar al hacer clic fuera
    if (window.innerWidth <= 768) {
        document.addEventListener('click', function(e) {
            if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
                sidebar.classList.add('collapsed');
            }
        });
    }
}

/**
 * Dropdown del usuario (opcional para futuro)
 */
function initUserDropdown() {
    const userElement = document.querySelector('.topbar-user');
    if (!userElement) return;
    
    userElement.addEventListener('click', function(e) {
        // Aquí se puede agregar un dropdown con opciones de usuario
        console.log('User clicked');
    });
}

/**
 * Resaltar menú activo según la URL actual
 */
function highlightActiveMenu() {
    const currentPath = window.location.pathname;
    const menuLinks = document.querySelectorAll('.menu-link');
    
    // Primero remover todas las clases active
    menuLinks.forEach(link => {
        link.classList.remove('active');
    });
    
    // Buscar coincidencia exacta primero (más específica)
    let exactMatch = null;
    menuLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && href === currentPath) {
            exactMatch = link;
        }
    });
    
    // Si hay coincidencia exacta, activarla y terminar
    if (exactMatch) {
        exactMatch.classList.add('active');
        return;
    }
    
    // Si no hay coincidencia exacta, buscar la más específica (más larga)
    let bestMatch = null;
    let longestMatch = 0;
    
    menuLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && href !== '/' && currentPath.startsWith(href)) {
            if (href.length > longestMatch) {
                longestMatch = href.length;
                bestMatch = link;
            }
        }
    });
    
    // Activar la mejor coincidencia
    if (bestMatch) {
        bestMatch.classList.add('active');
    }
}

/**
 * Confirmar acciones críticas
 */
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

/**
 * Mostrar notificación toast
 */
function showToast(message, type = 'success') {
    // Crear elemento toast
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 25px;
        background-color: ${type === 'success' ? '#40916c' : '#c9184a'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        z-index: 9999;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(toast);
    
    // Remover después de 3 segundos
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Agregar animaciones CSS para toast
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

/**
 * Formatear números como moneda
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'COP',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

/**
 * Formatear fechas
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('es-CO', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}
