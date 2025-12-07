// Main JavaScript - ImmoAnalytics
// Utility functions and event handlers

class ImmoAnalytics {
    constructor() {
        this.config = {
            apiBaseUrl: window.location.origin,
            timeout: 10000,
            retryAttempts: 3
        };
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupFormValidation();
        this.setupThemeManagement();
        this.setupServiceWorker();
        this.setupErrorHandling();
        this.setupAccessibility();
    }

    setupEventListeners() {
        // Global click handlers
        document.addEventListener('click', (e) => {
            // Handle data-action attributes
            const action = e.target.dataset.action;
            if (action) {
                e.preventDefault();
                this.handleAction(action, e.target);
            }
        });

        // Handle form submissions
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.classList.contains('ajax-form')) {
                e.preventDefault();
                this.submitForm(form);
            }
        });

        // Handle visibility change for performance
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseNonCriticalAnimations();
            } else {
                this.resumeNonCriticalAnimations();
            }
        });

        // Handle online/offline
        window.addEventListener('online', () => this.handleOnline());
        window.addEventListener('offline', () => this.handleOffline());
    }

    setupFormValidation() {
        // Real-time validation
        document.querySelectorAll('input[required]').forEach(input => {
            input.addEventListener('blur', () => this.validateField(input));
            input.addEventListener('input', () => this.clearFieldError(input));
        });

        // Password match validation
        const confirmPassword = document.getElementById('confirm_password');
        const password = document.getElementById('password');
        
        if (confirmPassword && password) {
            confirmPassword.addEventListener('input', () => {
                if (confirmPassword.value !== password.value) {
                    this.showFieldError(confirmPassword, 'Les mots de passe ne correspondent pas');
                } else {
                    this.clearFieldError(confirmPassword);
                }
            });
        }
    }

    validateField(field) {
        const value = field.value.trim();
        
        // Required validation
        if (field.hasAttribute('required') && !value) {
            this.showFieldError(field, 'Ce champ est obligatoire');
            return false;
        }
        
        // Email validation
        if (field.type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                this.showFieldError(field, 'Email invalide');
                return false;
            }
        }
        
        // Username validation
        if (field.id === 'username' && value) {
            const usernameRegex = /^[a-zA-Z0-9_-]{3,20}$/;
            if (!usernameRegex.test(value)) {
                this.showFieldError(field, "3-20 caractères alphanumériques, - ou _");
                return false;
            }
        }
        
        // Password strength
        if (field.id === 'password' && value) {
            const strength = this.checkPasswordStrength(value);
            if (strength < 2) {
                this.showFieldError(field, 'Mot de passe trop faible');
                return false;
            }
        }
        
        this.clearFieldError(field);
        return true;
    }

    showFieldError(field, message) {
        field.setCustomValidity(message);
        field.style.borderColor = '#dc3545';
        
        // Show error message
        let errorElement = field.parentNode.querySelector('.field-error');
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'field-error text-danger small mt-1';
            field.parentNode.appendChild(errorElement);
        }
        errorElement.textContent = message;
    }

    clearFieldError(field) {
        field.setCustomValidity('');
        field.style.borderColor = '';
        
        const errorElement = field.parentNode.querySelector('.field-error');
        if (errorElement) {
            errorElement.remove();
        }
    }

    checkPasswordStrength(password) {
        let strength = 0;
        if (password.length >= 8) strength++;
        if (password.length >= 12) strength++;
        if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
        if (/\d/.test(password)) strength++;
        if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength++;
        return strength;
    }

    setupThemeManagement() {
        // Theme toggle
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }

        // Load saved theme
        const savedTheme = localStorage.getItem('theme') || 'auto';
        document.documentElement.setAttribute('data-theme', savedTheme);
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 
                        currentTheme === 'light' ? 'auto' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        // Show notification
        if (window.animationController) {
            const themeName = newTheme === 'auto' ? 'automatique' : 
                            newTheme === 'dark' ? 'sombre' : 'clair';
            window.animationController.showNotification(
                `Thème ${themeName} activé`,
                'info',
                2000
            );
        }
    }

    setupServiceWorker() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/static/js/sw.js')
                .then(registration => {
                    console.log('SW registered:', registration);
                })
                .catch(error => {
                    console.log('SW registration failed:', error);
                });
        }
    }

    setupErrorHandling() {
        // Global error handler
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);
            this.logError(event.error);
        });
        
        // Unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            this.logError(event.reason);
        });
    }

    logError(error) {
        // In production, send to error tracking service
        if (window.location.hostname !== 'localhost') {
            // Example: Sentry, LogRocket, etc.
            console.log('Error logged:', error);
        }
    }

    setupAccessibility() {
        // Skip to content link
        const skipLink = document.querySelector('.visually-hidden-focusable');
        if (skipLink) {
            skipLink.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(skipLink.getAttribute('href'));
                if (target) {
                    target.setAttribute('tabindex', '-1');
                    target.focus();
                    target.scrollIntoView();
                }
            });
        }

        // Focus management for modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                // Close any open modals
                document.querySelectorAll('.modal.show').forEach(modal => {
                    if (window.animationController) {
                        window.animationController.hideModal(modal.id);
                    }
                });
            }
        });

        // Announce dynamic content changes
        if ('AriaLive' in window) {
            this.ariaLive = new AriaLive();
        }
    }

    pauseNonCriticalAnimations() {
        document.body.classList.add('animations-paused');
        if (window.animationController) {
            gsap.globalTimeline.pause();
        }
    }

    resumeNonCriticalAnimations() {
        document.body.classList.remove('animations-paused');
        if (window.animationController) {
            gsap.globalTimeline.resume();
        }
    }

    handleOnline() {
        document.body.classList.remove('offline');
        if (window.animationController) {
            window.animationController.showNotification(
                'Connexion rétablie',
                'success'
            );
        }
    }

    handleOffline() {
        document.body.classList.add('offline');
        if (window.animationController) {
            window.animationController.showNotification(
                'Mode hors ligne - Certaines fonctionnalités peuvent être limitées',
                'warning'
            );
        }
    }

    handleAction(action, element) {
        const actions = {
            'toggle-theme': () => this.toggleTheme(),
            'show-modal': () => {
                const modalId = element.dataset.modal;
                if (modalId && window.animationController) {
                    window.animationController.showModal(modalId);
                }
            },
            'hide-modal': () => {
                const modalId = element.dataset.modal;
                if (modalId && window.animationController) {
                    window.animationController.hideModal(modalId);
                }
            },
            'copy-text': () => {
                const text = element.dataset.text;
                navigator.clipboard.writeText(text).then(() => {
                    if (window.animationController) {
                        window.animationController.showNotification(
                            'Copié dans le presse-papier',
                            'success',
                            2000
                        );
                    }
                });
            }
        };

        if (actions[action]) {
            actions[action]();
        }
    }

    async submitForm(form) {
        const formData = new FormData(form);
        const submitButton = form.querySelector('button[type="submit"]');
        
        // Disable button and show loading
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Chargement...';
        
        try {
            const response = await fetch(form.action, {
                method: form.method,
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Success handling
                if (window.animationController) {
                    window.animationController.showNotification(
                        result.message || 'Opération réussie',
                        'success'
                    );
                }
                
                if (result.redirect) {
                    setTimeout(() => {
                        window.location.href = result.redirect;
                    }, 1000);
                }
            } else {
                // Error handling
                if (window.animationController) {
                    window.animationController.showNotification(
                        result.message || 'Une erreur est survenue',
                        'error'
                    );
                }
                
                // Show field errors
                if (result.errors) {
                    Object.entries(result.errors).forEach(([field, message]) => {
                        const fieldElement = form.querySelector(`[name="${field}"]`);
                        if (fieldElement) {
                            this.showFieldError(fieldElement, message);
                        }
                    });
                }
            }
        } catch (error) {
            console.error('Form submission error:', error);
            if (window.animationController) {
                window.animationController.showNotification(
                    'Erreur de connexion au serveur',
                    'error'
                );
            }
        } finally {
            // Re-enable button
            submitButton.disabled = false;
            submitButton.innerHTML = submitButton.dataset.originalText || 'Soumettre';
        }
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.ImmoAnalytics = new ImmoAnalytics();
});

// Utility functions
const utils = {
    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    throttle: (func, limit) => {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func(...args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
    
    formatNumber: (num) => {
        return new Intl.NumberFormat('fr-FR').format(num);
    },
    
    formatPrice: (price) => {
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: 'EUR'
        }).format(price);
    },
    
    formatDate: (date) => {
        return new Intl.DateTimeFormat('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(new Date(date));
    }
};

// ARIA Live helper
class AriaLive {
    constructor() {
        this.element = document.createElement('div');
        this.element.setAttribute('aria-live', 'polite');
        this.element.setAttribute('aria-atomic', 'true');
        this.element.className = 'visually-hidden';
        document.body.appendChild(this.element);
    }

    announce(message) {
        this.element.textContent = '';
        setTimeout(() => {
            this.element.textContent = message;
        }, 100);
    }
}

// Export utilities
window.utils = utils;