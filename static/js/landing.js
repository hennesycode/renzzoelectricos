/**
 * JavaScript para la Landing Page de Renzzo Eléctricos
 * Funciones: Parallax, modal de contacto, animaciones
 */

/* ============================================
   CLASE PRINCIPAL - LandingPage
   ============================================ */
class LandingPage {
    constructor() {
        this.init();
    }

    /**
     * Inicializa todos los módulos de la landing page
     */
    init() {
        this.initContactButton();
        this.initParallaxEffect();
        console.log('Landing Page inicializada correctamente');
    }

    /**
     * Configura el botón de contacto
     */
    initContactButton() {
        const contactBtn = document.querySelector('a[href="#contacto"]');
        
        if (contactBtn) {
            contactBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.showContactModal();
            });
        }
    }

    /**
     * Muestra modal de información de contacto
     */
    showContactModal() {
        alert(
            'Próximamente: Formulario de contacto\n\n' +
            'Email: info@renzzoelectricos.com\n' +
            'Teléfono: +57 300 123 4567\n' +
            'Ubicación: Villavicencio, Meta - Colombia'
        );
    }

    /**
     * Inicializa el efecto parallax para elementos decorativos
     */
    initParallaxEffect() {
        const decorations = document.querySelectorAll('.decoration');
        
        if (decorations.length === 0) return;

        document.addEventListener('mousemove', (e) => {
            this.handleParallax(e, decorations);
        });
    }

    /**
     * Maneja el efecto parallax basado en la posición del mouse
     * @param {MouseEvent} e - Evento del mouse
     * @param {NodeList} decorations - Elementos decorativos
     */
    handleParallax(e, decorations) {
        const mouseX = e.clientX / window.innerWidth;
        const mouseY = e.clientY / window.innerHeight;
        
        decorations.forEach((decoration, index) => {
            const speed = (index + 1) * 20;
            const x = (mouseX * speed) - (speed / 2);
            const y = (mouseY * speed) - (speed / 2);
            decoration.style.transform = `translate(${x}px, ${y}px)`;
        });
    }
}

/* ============================================
   UTILIDADES
   ============================================ */

/**
 * Objeto con funciones utilitarias
 */
const LandingUtils = {
    /**
     * Smooth scroll hacia un elemento
     * @param {string} selector - Selector CSS del elemento
     */
    smoothScrollTo(selector) {
        const element = document.querySelector(selector);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth' });
        }
    },

    /**
     * Valida formato de email
     * @param {string} email - Email a validar
     * @returns {boolean}
     */
    isValidEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },

    /**
     * Formatea número de teléfono colombiano
     * @param {string} phone - Número de teléfono
     * @returns {string}
     */
    formatColombianPhone(phone) {
        const cleaned = phone.replace(/\D/g, '');
        const match = cleaned.match(/^(\d{3})(\d{3})(\d{4})$/);
        if (match) {
            return `${match[1]} ${match[2]} ${match[3]}`;
        }
        return phone;
    }
};

/* ============================================
   INICIALIZACIÓN
   ============================================ */

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new LandingPage();
});
