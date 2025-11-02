/**
 * JavaScript para el Login de Renzzo Eléctricos
 * Maneja autenticación AJAX con SweetAlert2
 */

/* ============================================
   CLASE PRINCIPAL - LoginManager
   ============================================ */
class LoginManager {
    constructor() {
        this.form = document.getElementById('loginForm');
        this.loginButton = document.getElementById('loginButton');
        this.init();
    }

    /**
     * Inicializa el gestor de login
     */
    init() {
        if (!this.form) {
            console.error('Formulario de login no encontrado');
            return;
        }

        this.attachEventListeners();
        console.log('Login Manager inicializado correctamente');
    }

    /**
     * Adjunta event listeners al formulario
     */
    attachEventListeners() {
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    /**
     * Maneja el envío del formulario
     * @param {Event} e - Evento del formulario
     */
    async handleSubmit(e) {
        e.preventDefault();

        const formData = this.getFormData();
        
        // Validar datos
        if (!this.validateForm(formData)) {
            return;
        }

        // Procesar login
        await this.processLogin(formData);
    }

    /**
     * Obtiene los datos del formulario
     * @returns {Object} Datos del formulario
     */
    getFormData() {
        return {
            username: this.form.username.value.trim(),
            password: this.form.password.value,
            remember: this.form.remember.checked,
            csrftoken: document.querySelector('[name=csrfmiddlewaretoken]').value
        };
    }

    /**
     * Valida los datos del formulario
     * @param {Object} data - Datos a validar
     * @returns {boolean} True si es válido
     */
    validateForm(data) {
        if (!data.username || !data.password) {
            Swal.fire({
                icon: 'warning',
                title: 'Campos incompletos',
                text: 'Por favor ingresa tu usuario y contraseña',
                confirmButtonText: 'Entendido'
            });
            return false;
        }
        return true;
    }

    /**
     * Procesa el login mediante AJAX
     * @param {Object} data - Datos del formulario
     */
    async processLogin(data) {
        this.setLoadingState(true);

        try {
            const response = await this.sendLoginRequest(data);
            const result = await response.json();

            if (result.success) {
                await this.handleLoginSuccess(result);
            } else {
                this.handleLoginError(result);
            }
        } catch (error) {
            this.handleNetworkError(error);
        }
    }

    /**
     * Envía la petición AJAX de login
     * @param {Object} data - Datos del formulario
     * @returns {Promise<Response>}
     */
    async sendLoginRequest(data) {
        // Obtener la URL del formulario
        const loginUrl = this.form.action || window.location.href;

        return await fetch(loginUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': data.csrftoken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: new URLSearchParams({
                'username': data.username,
                'password': data.password,
                'remember': data.remember ? 'on' : ''
            })
        });
    }

    /**
     * Maneja login exitoso
     * @param {Object} result - Resultado del servidor
     */
    async handleLoginSuccess(result) {
        await Swal.fire({
            icon: 'success',
            title: '¡Bienvenido!',
            text: `Hola ${result.user.username}, accediendo al sistema...`,
            timer: 1500,
            showConfirmButton: false
        });

        // Redirigir al dashboard
        window.location.href = result.redirect_url;
    }

    /**
     * Maneja error de login
     * @param {Object} result - Resultado del servidor
     */
    handleLoginError(result) {
        this.setLoadingState(false);

        Swal.fire({
            icon: 'error',
            title: 'Error de autenticación',
            text: result.message || 'Usuario o contraseña incorrectos',
            confirmButtonText: 'Intentar de nuevo'
        });
    }

    /**
     * Maneja error de red
     * @param {Error} error - Error capturado
     */
    handleNetworkError(error) {
        console.error('Error de red:', error);
        this.setLoadingState(false);

        Swal.fire({
            icon: 'error',
            title: 'Error de conexión',
            text: 'No se pudo conectar con el servidor. Por favor intenta de nuevo.',
            confirmButtonText: 'Entendido'
        });
    }

    /**
     * Establece el estado de carga del botón
     * @param {boolean} isLoading - Si está cargando
     */
    setLoadingState(isLoading) {
        if (isLoading) {
            this.loginButton.disabled = true;
            this.loginButton.innerHTML = '<div class="spinner"></div> Verificando...';
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
}

/* ============================================
   UTILIDADES DE LOGIN
   ============================================ */
const LoginUtils = {
    /**
     * Valida fortaleza de contraseña
     * @param {string} password - Contraseña a validar
     * @returns {Object} Resultado de validación
     */
    validatePasswordStrength(password) {
        const minLength = 8;
        const hasUpperCase = /[A-Z]/.test(password);
        const hasLowerCase = /[a-z]/.test(password);
        const hasNumbers = /\d/.test(password);
        const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);

        return {
            isValid: password.length >= minLength,
            strength: hasUpperCase && hasLowerCase && hasNumbers && hasSpecialChar ? 'strong' : 'weak',
            length: password.length
        };
    },

    /**
     * Almacena credenciales en localStorage (solo username)
     * @param {string} username - Nombre de usuario
     */
    rememberUser(username) {
        if (username) {
            localStorage.setItem('remembered_user', username);
        }
    },

    /**
     * Obtiene usuario recordado
     * @returns {string|null}
     */
    getRememberedUser() {
        return localStorage.getItem('remembered_user');
    },

    /**
     * Limpia usuario recordado
     */
    clearRememberedUser() {
        localStorage.removeItem('remembered_user');
    }
};

/* ============================================
   INICIALIZACIÓN
   ============================================ */

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    new LoginManager();
    
    // Cargar usuario recordado si existe
    const rememberedUser = LoginUtils.getRememberedUser();
    if (rememberedUser) {
        const usernameInput = document.getElementById('username');
        if (usernameInput) {
            usernameInput.value = rememberedUser;
            document.getElementById('remember').checked = true;
        }
    }
});
