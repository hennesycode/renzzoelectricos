/**
 * Login Manager - Renzzo Eléctricos
 * Sistema de autenticación AJAX moderno con cache y "recordarme"
 * Optimizado para UX móvil y desktop
 */

/* ============================================
   CLASE PRINCIPAL - LoginManager
   ============================================ */
class LoginManager {
    constructor() {
        this.form = document.getElementById('loginForm');
        this.loginButton = document.getElementById('loginButton');
        
        // Buscar inputs usando los IDs generados por Django
        this.usernameInput = document.querySelector('input[name="username"]');
        this.passwordInput = document.querySelector('input[name="password"]');
        this.rememberCheckbox = document.querySelector('input[name="remember_me"]');
        
        // Cache keys para localStorage
        this.cacheKeys = {
            username: 'renzzoelectricos_saved_username',
            lastLogin: 'renzzoelectricos_last_login',
            userPreferences: 'renzzoelectricos_user_prefs'
        };
        
        this.init();
    }

    /**
     * Inicializa el sistema de login
     */
    init() {
        this.bindEvents();
        this.setupFormValidation();
        this.loadCachedCredentials();
        this.setupAutoComplete();
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
        
        // Guardar username cuando cambia (para cache)
        this.usernameInput.addEventListener('input', () => this.saveTempUsername());
        
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
        
        // Manejar cambios en "recordarme"
        this.rememberCheckbox.addEventListener('change', (e) => {
            const isChecked = e.target.checked;
            this.saveUserPreference('rememberMe', isChecked);
            
            if (isChecked) {
                console.log('✅ Recordarme activado - guardará último usuario');
            } else {
                console.log('ℹ️ Recordarme desactivado - no guardará usuario');
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
     * Carga credenciales guardadas desde localStorage y cookies.
     * Sincroniza cookie (servidor) con localStorage (cliente) dando prioridad
     * a la cookie si difieren, ya que el servidor tiene la verdad absoluta.
     */
    loadCachedCredentials() {
        try {
            // Cargar desde localStorage
            const savedUsername = localStorage.getItem(this.cacheKeys.username);
            const userPrefs = this.getUserPreferences();
            
            // Cargar desde cookie (si existe) - fuente de verdad del servidor
            const cookieUsername = this.getCookieValue('saved_username');
            
            // Sincronización: cookie tiene prioridad sobre localStorage
            let usernameToLoad = null;
            
            if (cookieUsername) {
                // Cookie existe: usarla y sincronizar localStorage si difiere
                usernameToLoad = cookieUsername;
                if (savedUsername !== cookieUsername) {
                    console.log(`🔄 Sincronizando cache: '${savedUsername}' → '${cookieUsername}'`);
                    localStorage.setItem(this.cacheKeys.username, cookieUsername);
                }
            } else if (savedUsername) {
                // Solo localStorage existe: usarlo pero cookie puede haber expirado
                usernameToLoad = savedUsername;
                console.log('⚠️ Cookie ausente, usando localStorage');
            }
            
            if (usernameToLoad) {
                this.usernameInput.value = usernameToLoad;
                this.usernameInput.classList.add('success');
                
                // Marcar "recordarme" si tiene preferencia guardada
                if (userPrefs.rememberMe !== false) {
                    this.rememberCheckbox.checked = true;
                }
                
                // Enfocar contraseña si hay usuario guardado
                setTimeout(() => {
                    this.passwordInput.focus();
                }, 100);
                
                console.log(`✅ Credenciales cargadas: ${usernameToLoad}`);
            } else {
                console.log('ℹ️ No hay credenciales guardadas');
            }
        } catch (error) {
            console.warn('⚠️ Error al cargar credenciales desde cache:', error);
        }
    }

    /**
     * Configura detección de tipo de input (email vs username).
     * NO crea dropdown ni autocompletado - solo guarda el último usuario.
     */
    setupAutoComplete() {
        // Solo detectar email vs username para cambiar placeholder
        this.usernameInput.addEventListener('input', (e) => {
            const value = e.target.value;
            if (value.includes('@')) {
                this.usernameInput.setAttribute('type', 'email');
                this.usernameInput.setAttribute('placeholder', 'Ingrese su email');
            } else {
                this.usernameInput.setAttribute('type', 'text');
                this.usernameInput.setAttribute('placeholder', 'Ingrese su usuario o email');
            }
        });
        
        console.log('✅ Detección de tipo de input configurada (sin dropdown)');
    }

    /**
     * Guarda username temporalmente mientras el usuario escribe
     */
    saveTempUsername() {
        const username = this.usernameInput.value.trim();
        if (username.length >= 3) {
            // Guardar temporalmente SOLO si el usuario tiene activa la
            // preferencia 'rememberMe'. Evita sobreescribir el valor
            // permanente sin que el usuario confirme el login con la
            // palomilla marcada.
            const prefs = this.getUserPreferences();
            if (prefs.rememberMe) {
                localStorage.setItem(this.cacheKeys.username, username);
            }
        }
    }

    /**
     * Guarda preferencias de usuario
     */
    saveUserPreference(key, value) {
        try {
            let prefs = this.getUserPreferences();
            prefs[key] = value;
            localStorage.setItem(this.cacheKeys.userPreferences, JSON.stringify(prefs));
        } catch (error) {
            console.warn('Error al guardar preferencias:', error);
        }
    }

    /**
     * Obtiene preferencias de usuario
     */
    getUserPreferences() {
        try {
            const prefs = localStorage.getItem(this.cacheKeys.userPreferences);
            return prefs ? JSON.parse(prefs) : {};
        } catch (error) {
            console.warn('Error al obtener preferencias:', error);
            return {};
        }
    }

    /**
     * Obtiene valor de cookie
     */
    getCookieValue(name) {
        const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
        return match ? decodeURIComponent(match[2]) : null;
    }

    /**
     * Limpia TODOS los datos relacionados con "recordarme".
     * Útil para resetear el sistema de cache cuando el usuario
     * desactiva la opción o cambia de cuenta completamente.
     */
    clearRememberMeCache() {
        try {
            // Limpiar username guardado permanentemente
            localStorage.removeItem(this.cacheKeys.username);
            
            // Limpiar preferencias de usuario (rememberMe)
            const prefs = this.getUserPreferences();
            if (prefs.rememberMe !== undefined) {
                delete prefs.rememberMe;
                localStorage.setItem(this.cacheKeys.userPreferences, JSON.stringify(prefs));
            }
            
            // Desmarcar checkbox si está visible
            if (this.rememberCheckbox) {
                this.rememberCheckbox.checked = false;
            }
            
            console.log('🗑️ Cache de "recordarme" limpiado completamente');
        } catch (error) {
            console.warn('⚠️ Error al limpiar cache de recordarme:', error);
        }
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
        const username = this.usernameInput.value.trim();
        const password = this.passwordInput.value;
        const remember = this.rememberCheckbox.checked;
        
        return {
            username: username,
            password: password,
            remember_me: remember, // Cambiar a remember_me para coincidir con Django
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
        // Incluir credenciales same-origin para que el navegador acepte
        // la cabecera Set-Cookie que el servidor devuelve en respuesta AJAX.
        // Sin esto, la cookie 'saved_username' no se actualizará cuando
        // usamos fetch para autenticación AJAX y el valor anterior se mantiene.
        const response = await fetch('/accounts/login/', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': data.csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: new URLSearchParams({
                'username': data.username,
                'password': data.password,
                'remember_me': data.remember_me ? 'on' : ''
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    }

    /**
     * Maneja respuesta exitosa del login.
     * Sistema simple: guarda/actualiza/borra EXACTAMENTE lo que el usuario escribió.
     * SIN dropdown, SIN lista de recientes - solo el último valor ingresado.
     */
    async handleLoginResponse(result) {
        if (result.success) {
            // Guardar EXACTAMENTE lo que el usuario escribió en el campo
            // (puede ser username, email, teléfono, etc.)
            const inputValue = this.usernameInput.value.trim();
            const previousValue = localStorage.getItem(this.cacheKeys.username);
            
            // Guardar timestamp del último login
            localStorage.setItem(this.cacheKeys.lastLogin, Date.now().toString());

            // Si "recordarme" está marcado: guardar el valor ingresado
            if (result.remember_me) {
                // Log de cambio si es diferente
                if (previousValue && previousValue !== inputValue) {
                    console.log(`🔄 Actualizando: '${previousValue}' → '${inputValue}'`);
                }
                
                // GUARDAR: establecer el valor ingresado como único valor
                localStorage.setItem(this.cacheKeys.username, inputValue);
                this.saveUserPreference('rememberMe', true);
                
                console.log(`✅ Valor guardado: ${inputValue}`);
            } else {
                // "Recordarme" NO está activo: limpiar TODO
                console.log(`🗑️ Recordarme desactivado, limpiando cache`);
                
                // LIMPIAR: eliminar valor permanente guardado
                localStorage.removeItem(this.cacheKeys.username);
                this.saveUserPreference('rememberMe', false);
            }
            
            // Marcar campos como exitosos
            this.usernameInput.classList.add('success');
            this.passwordInput.classList.add('success');
            
            // Mostrar mensaje de éxito
            await Swal.fire({
                icon: 'success',
                title: '¡Bienvenido!',
                text: `Hola ${result.user?.full_name || result.user?.username || 'Usuario'}, accediendo al sistema...`,
                timer: 2000,
                timerProgressBar: true,
                showConfirmButton: false,
                allowOutsideClick: false
            });
            
            // Redirigir
            this.redirectToApp(result.redirect_url);
        } else {
            await this.handleLoginError({
                message: result.message || 'Credenciales incorrectas',
                errors: result.errors
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
            // Usar las clases del template
            const btnText = this.loginButton.querySelector('.btn-text');
            const loadingSpinner = this.loginButton.querySelector('.loading-spinner');
            
            if (btnText) btnText.style.display = 'none';
            if (loadingSpinner) loadingSpinner.style.display = 'flex';
        } else {
            this.loginButton.disabled = false;
            const btnText = this.loginButton.querySelector('.btn-text');
            const loadingSpinner = this.loginButton.querySelector('.loading-spinner');
            
            if (btnText) btnText.style.display = 'block';
            if (loadingSpinner) loadingSpinner.style.display = 'none';
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
