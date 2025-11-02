/**
 * Login Manager - Renzzo Eléctricos
 * Sistema de autenticación AJAX moderno y responsive
 * Optimizado para UX móvil y desktop
 */

/* ============================================
   CLASE PRINCIPAL - LoginManager
   ============================================ */
class LoginManager {
    constructor() {
        this.form = document.getElementById('loginForm');
        this.loginButton = document.getElementById('loginButton');
        this.usernameInput = document.getElementById('username');
        this.passwordInput = document.getElementById('password');
        this.rememberCheckbox = document.getElementById('remember');
        
        this.init();
    }

    /**
     * Inicializa el sistema de login
     */
    init() {
        this.bindEvents();
        this.setupFormValidation();
        console.log('Login Manager inicializado correctamente');
    }

    /**
     * Vincula eventos del formulario
     */
    bindEvents() {
        // Evento principal del formulario
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        
        // Validación en tiempo real
        this.usernameInput.addEventListener('input', () => this.validateField(this.usernameInput));
        this.passwordInput.addEventListener('input', () => this.validateField(this.passwordInput));
        
        // Enter key navigation
        this.usernameInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.passwordInput.focus();
            }
        });
        
        // Prevenir envío accidental
        this.passwordInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.form.dispatchEvent(new Event('submit'));
            }
        });
    }

    /**
     * Configura validación del formulario
     */
    setupFormValidation() {
        // Eliminar estados de error al hacer focus
        [this.usernameInput, this.passwordInput].forEach(input => {
            input.addEventListener('focus', () => {
                input.classList.remove('error');
                input.parentElement.classList.remove('error-shake');
            });
        });
    }

    /**
     * Maneja el envío del formulario
     */
    async handleSubmit(e) {
        e.preventDefault();
        
        const formData = this.getFormData();
        
        // Validación básica
        if (!this.validateForm(formData)) {
            return;
        }
        
        // Mostrar estado de carga
        this.setLoadingState(true);
        
        try {
            const result = await this.sendLoginRequest(formData);
            await this.handleLoginResponse(result);
        } catch (error) {
            console.error('Error en login:', error);
            await this.handleLoginError(error);
        } finally {
            this.setLoadingState(false);
        }
    }

    /**
     * Obtiene datos del formulario
     */
    getFormData() {
        return {
            username: this.usernameInput.value.trim(),
            password: this.passwordInput.value,
            remember: this.rememberCheckbox.checked,
            csrfToken: document.querySelector('[name=csrfmiddlewaretoken]').value
        };
    }

    /**
     * Valida el formulario
     */
    validateForm(data) {
        let isValid = true;
        
        // Validar usuario
        if (!data.username) {
            this.showFieldError(this.usernameInput, 'El usuario es requerido');
            isValid = false;
        } else if (data.username.length < 3) {
            this.showFieldError(this.usernameInput, 'Usuario debe tener al menos 3 caracteres');
            isValid = false;
        }
        
        // Validar contraseña
        if (!data.password) {
            this.showFieldError(this.passwordInput, 'La contraseña es requerida');
            isValid = false;
        } else if (data.password.length < 4) {
            this.showFieldError(this.passwordInput, 'Contraseña debe tener al menos 4 caracteres');
            isValid = false;
        }
        
        if (!isValid) {
            this.showValidationAlert();
        }
        
        return isValid;
    }

    /**
     * Valida campo individual
     */
    validateField(input) {
        const value = input.value.trim();
        
        if (value) {
            input.classList.remove('error');
            input.classList.add('success');
        } else {
            input.classList.remove('success');
        }
    }

    /**
     * Muestra error en campo específico
     */
    showFieldError(input, message) {
        input.classList.add('error');
        input.parentElement.classList.add('error-shake');
        
        // Remover shake después de la animación
        setTimeout(() => {
            input.parentElement.classList.remove('error-shake');
        }, 500);
        
        input.focus();
    }

    /**
     * Muestra alerta de validación
     */
    showValidationAlert() {
        Swal.fire({
            icon: 'warning',
            title: 'Campos incompletos',
            text: 'Por favor verifica que todos los campos estén correctamente completados',
            confirmButtonText: 'Entendido',
            timer: 3000,
            timerProgressBar: true
        });
    }

    /**
     * Envía petición de login
     */
    async sendLoginRequest(data) {
        const response = await fetch('/login/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': data.csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: new URLSearchParams({
                'username': data.username,
                'password': data.password,
                'remember': data.remember ? 'on' : ''
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    }

    /**
     * Maneja respuesta exitosa
     */
    async handleLoginResponse(result) {
        if (result.success) {
            // Marcar campos como exitosos
            this.usernameInput.classList.add('success');
            this.passwordInput.classList.add('success');
            
            // Mostrar mensaje de éxito
            await Swal.fire({
                icon: 'success',
                title: '¡Bienvenido!',
                text: `Hola ${result.user?.username || 'Usuario'}, accediendo al sistema...`,
                timer: 2000,
                timerProgressBar: true,
                showConfirmButton: false,
                allowOutsideClick: false
            });
            
            // Redirigir
            this.redirectToApp(result.redirect_url);
        } else {
            await this.handleLoginError({
                message: result.message || 'Credenciales incorrectas'
            });
        }
    }

    /**
     * Maneja errores de login
     */
    async handleLoginError(error) {
        // Marcar campos con error
        this.usernameInput.classList.add('error');
        this.passwordInput.classList.add('error');
        
        // Shake animation
        this.form.classList.add('error-shake');
        setTimeout(() => {
            this.form.classList.remove('error-shake');
        }, 500);
        
        // Mostrar error
        await Swal.fire({
            icon: 'error',
            title: 'Error de autenticación',
            text: error.message || 'No se pudo conectar con el servidor. Verifica tu conexión e intenta nuevamente.',
            confirmButtonText: 'Intentar de nuevo',
            allowOutsideClick: false
        });
        
        // Enfocar campo de usuario
        this.usernameInput.focus();
        this.passwordInput.value = ''; // Limpiar contraseña por seguridad
    }

    /**
     * Establece estado de carga
     */
    setLoadingState(loading) {
        if (loading) {
            this.loginButton.disabled = true;
            this.loginButton.innerHTML = `
                <div class="spinner"></div>
                Verificando...
            `;
        } else {
            this.loginButton.disabled = false;
            this.loginButton.innerHTML = `
                <svg viewBox="0 0 24 24">
                    <path d="M10 17l5-5-5-5v10z"/>
                    <path d="M3 3h8v2H5v14h6v2H3V3zm16 0v18h-2V3h2z"/>
                </svg>
                Iniciar Sesión
            `;
        }
    }

    /**
     * Redirección al sistema
     */
    redirectToApp(url) {
        const targetUrl = url || '/dashboard/';
        
        // Animación de salida
        document.body.style.opacity = '0';
        document.body.style.transition = 'opacity 0.5s ease';
        
        setTimeout(() => {
            window.location.href = targetUrl;
        }, 300);
    }
}

/* ============================================
   UTILIDADES DE LOGIN
   ============================================ */
const LoginUtils = {
    /**
     * Detecta si es un dispositivo móvil
     */
    isMobile() {
        return window.innerWidth <= 768;
    },

    /**
     * Valida formato de email (si se usa)
     */
    isValidEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },

    /**
     * Genera contraseña temporal (para testing)
     */
    generateTempPassword(length = 8) {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        let result = '';
        for (let i = 0; i < length; i++) {
            result += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return result;
    },

    /**
     * Formatear tiempo transcurrido
     */
    formatElapsedTime(startTime) {
        const elapsed = Date.now() - startTime;
        return `${(elapsed / 1000).toFixed(1)}s`;
    },

    /**
     * Detectar capacidades del dispositivo
     */
    getDeviceCapabilities() {
        return {
            touchSupport: 'ontouchstart' in window,
            webGL: !!window.WebGLRenderingContext,
            localStorage: !!window.localStorage,
            sessionStorage: !!window.sessionStorage,
            geolocation: !!navigator.geolocation,
            online: navigator.onLine
        };
    }
};

/* ============================================
   INICIALIZACIÓN
   ============================================ */
document.addEventListener('DOMContentLoaded', () => {
    // Inicializar Login Manager
    new LoginManager();
    
    // Log de información del dispositivo (solo en desarrollo)
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        console.log('🔧 Modo desarrollo - Renzzo Eléctricos');
        console.log('📱 Dispositivo móvil:', LoginUtils.isMobile());
        console.log('⚡ Capacidades:', LoginUtils.getDeviceCapabilities());
    }
    
    // Optimización para dispositivos táctiles
    if (LoginUtils.isMobile()) {
        document.body.classList.add('mobile-device');
        
        // Mejorar UX en móviles
        const inputs = document.querySelectorAll('.form-control');
        inputs.forEach(input => {
            input.addEventListener('focus', () => {
                // Scroll suave al input en móviles
                setTimeout(() => {
                    input.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center'
                    });
                }, 300);
            });
        });
    }
});

/* ============================================
   MANEJO DE ERRORES GLOBALES
   ============================================ */
window.addEventListener('error', (event) => {
    console.error('Error global capturado:', event.error);
    
    // Solo mostrar en desarrollo
    if (window.location.hostname === 'localhost') {
        console.error('Detalles del error:', {
            message: event.message,
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno
        });
    }
});

/* ============================================
   DETECCIÓN DE CONEXIÓN
   ============================================ */
window.addEventListener('online', () => {
    console.log('✅ Conexión restaurada');
});

window.addEventListener('offline', () => {
    console.log('❌ Sin conexión a internet');
    Swal.fire({
        icon: 'warning',
        title: 'Sin conexión',
        text: 'Verifica tu conexión a internet para continuar',
        confirmButtonText: 'Entendido'
    });
});
