// GSAP Animations for ImmoAnalytics
// Modern UI animations and interactions

class AnimationController {
    constructor() {
        this.isInitialized = false;
        this.timeline = null;
        this.init();
    }

    init() {
        // Wait for GSAP to be loaded
        if (typeof gsap === 'undefined') {
            console.warn('GSAP not loaded, waiting...');
            setTimeout(() => this.init(), 100);
            return;
        }

        // Register plugins
        if (typeof ScrollTrigger !== 'undefined') {
            gsap.registerPlugin(ScrollTrigger);
        }

        if (typeof TextPlugin !== 'undefined') {
            gsap.registerPlugin(TextPlugin);
        }

        this.isInitialized = true;
        this.setupAnimations();
        this.setupInteractions();
        this.setupScrollAnimations();
    }

    setupAnimations() {
        // Hero Section Animations
        this.animateHero();
        
        // Feature Cards Animation
        this.animateFeatureCards();
        
        // KPI Cards Animation
        this.animateKPICards();
        
        // Navigation Animation
        this.animateNavigation();
    }

    animateHero() {
        if (!this.isInitialized) return;

        // Hero title animation with gradient text effect
        gsap.fromTo('.hero-title', 
            {
                opacity: 0,
                y: 50,
                scale: 0.8
            },
            {
                opacity: 1,
                y: 0,
                scale: 1,
                duration: 1.2,
                ease: 'back.out(1.7)',
                delay: 0.2
            }
        );

        // Hero subtitle animation
        gsap.fromTo('.hero-subtitle',
            {
                opacity: 0,
                y: 30
            },
            {
                opacity: 1,
                y: 0,
                duration: 1,
                ease: 'power2.out',
                delay: 0.5
            }
        );

        // Hero description animation
        gsap.fromTo('.hero-description',
            {
                opacity: 0,
                y: 20
            },
            {
                opacity: 1,
                y: 0,
                duration: 0.8,
                ease: 'power2.out',
                delay: 0.8
            }
        );

        // Floating animation for hero elements
        gsap.to('.hero-title', {
            y: -10,
            duration: 3,
            ease: 'sine.inOut',
            yoyo: true,
            repeat: -1
        });
    }

    animateFeatureCards() {
        if (!this.isInitialized) return;

        // Stagger animation for feature cards
        gsap.fromTo('.feature-card',
            {
                opacity: 0,
                y: 50,
                scale: 0.9
            },
            {
                opacity: 1,
                y: 0,
                scale: 1,
                duration: 0.8,
                ease: 'back.out(1.7)',
                stagger: 0.15,
                delay: 1.2
            }
        );

        // Hover animations for feature cards
        document.querySelectorAll('.feature-card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                gsap.to(card, {
                    scale: 1.05,
                    y: -10,
                    duration: 0.3,
                    ease: 'power2.out'
                });

                gsap.to(card.querySelector('.feature-icon'), {
                    rotateY: 360,
                    duration: 0.6,
                    ease: 'power2.out'
                });
            });

            card.addEventListener('mouseleave', () => {
                gsap.to(card, {
                    scale: 1,
                    y: 0,
                    duration: 0.3,
                    ease: 'power2.out'
                });
            });
        });
    }

    animateKPICards() {
        if (!this.isInitialized) return;

        // Animate KPI cards with counting effect
        const kpiObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const card = entry.target;
                    const valueElement = card.querySelector('.kpi-value');
                    
                    // Animate card entrance
                    gsap.fromTo(card,
                        {
                            opacity: 0,
                            y: 30,
                            scale: 0.9
                        },
                        {
                            opacity: 1,
                            y: 0,
                            scale: 1,
                            duration: 0.6,
                            ease: 'back.out(1.7)'
                        }
                    );

                    // Animate value counting
                    if (valueElement && !card.dataset.animated) {
                        card.dataset.animated = 'true';
                        const finalValue = parseInt(valueElement.textContent) || 0;
                        
                        gsap.fromTo({ value: 0 },
                            { value: 0 },
                            {
                                value: finalValue,
                                duration: 2,
                                ease: 'power2.out',
                                onUpdate: function() {
                                    valueElement.textContent = Math.round(this.targets()[0].value);
                                }
                            }
                        );
                    }
                }
            });
        });

        document.querySelectorAll('.kpi-card').forEach(card => {
            kpiObserver.observe(card);
        });
    }

    animateNavigation() {
        if (!this.isInitialized) return;

        // Animate navigation on scroll
        let lastScrollY = window.scrollY;
        
        window.addEventListener('scroll', () => {
            const currentScrollY = window.scrollY;
            const nav = document.querySelector('.glass-nav');
            
            if (currentScrollY > 100) {
                gsap.to(nav, {
                    background: 'rgba(255, 255, 255, 0.15)',
                    duration: 0.3
                });
            } else {
                gsap.to(nav, {
                    background: 'rgba(255, 255, 255, 0.1)',
                    duration: 0.3
                });
            }

            lastScrollY = currentScrollY;
        });

        // Animate navigation links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('mouseenter', () => {
                gsap.to(link, {
                    scale: 1.1,
                    duration: 0.2,
                    ease: 'power2.out'
                });
            });

            link.addEventListener('mouseleave', () => {
                gsap.to(link, {
                    scale: 1,
                    duration: 0.2,
                    ease: 'power2.out'
                });
            });
        });
    }

    setupInteractions() {
        // Button hover animations
        document.querySelectorAll('.glass-button').forEach(button => {
            button.addEventListener('mouseenter', () => {
                gsap.to(button, {
                    scale: 1.05,
                    duration: 0.2,
                    ease: 'power2.out'
                });
            });

            button.addEventListener('mouseleave', () => {
                gsap.to(button, {
                    scale: 1,
                    duration: 0.2,
                    ease: 'power2.out'
                });
            });
        });

        // Card hover animations
        document.querySelectorAll('.glass-card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                gsap.to(card, {
                    y: -5,
                    duration: 0.3,
                    ease: 'power2.out'
                });
            });

            card.addEventListener('mouseleave', () => {
                gsap.to(card, {
                    y: 0,
                    duration: 0.3,
                    ease: 'power2.out'
                });
            });
        });

        // Input focus animations
        document.querySelectorAll('.glass-input').forEach(input => {
            input.addEventListener('focus', () => {
                gsap.to(input, {
                    scale: 1.02,
                    duration: 0.2,
                    ease: 'power2.out'
                });
            });

            input.addEventListener('blur', () => {
                gsap.to(input, {
                    scale: 1,
                    duration: 0.2,
                    ease: 'power2.out'
                });
            });
        });

        // Loading animations
        this.setupLoadingAnimations();
    }

    setupLoadingAnimations() {
        // Spinner animation
        gsap.to('.spinner', {
            rotation: 360,
            duration: 1,
            ease: 'none',
            repeat: -1
        });

        // Pulse animation for loading states
        gsap.to('.pulse', {
            scale: 1.05,
            duration: 1.5,
            ease: 'sine.inOut',
            yoyo: true,
            repeat: -1
        });
    }

    setupScrollAnimations() {
        if (!this.isInitialized || typeof ScrollTrigger === 'undefined') return;

        // Feature cards scroll animation
        gsap.utils.toArray('.feature-card').forEach((card, index) => {
            gsap.fromTo(card,
                {
                    opacity: 0,
                    y: 50,
                    scale: 0.9
                },
                {
                    opacity: 1,
                    y: 0,
                    scale: 1,
                    duration: 0.8,
                    ease: 'back.out(1.7)',
                    scrollTrigger: {
                        trigger: card,
                        start: 'top 95%',
                        end: 'bottom 5%',
                        toggleActions: 'play none none reverse'
                    }
                }
            );
        });

        // Dashboard cards scroll animation
        gsap.utils.toArray('.dashboard-card').forEach(card => {
            gsap.fromTo(card,
                {
                    opacity: 0,
                    y: 30,
                    rotateX: -10
                },
                {
                    opacity: 1,
                    y: 0,
                    rotateX: 0,
                    duration: 0.6,
                    ease: 'power2.out',
                    scrollTrigger: {
                        trigger: card,
                        start: 'top 95%',
                        end: 'bottom 5%',
                        toggleActions: 'play none none reverse'
                    }
                }
            );
        });

        // Parallax effect for background elements
        gsap.to('.animated-bg::before', {
            yPercent: -50,
            ease: 'none',
            scrollTrigger: {
                trigger: 'body',
                start: 'top bottom',
                end: 'bottom top',
                scrub: true
            }
        });
    }

    // Utility methods for custom animations
    animateElement(element, animation = 'fadeIn') {
        if (!this.isInitialized) return;

        const animations = {
            fadeIn: {
                from: { opacity: 0, y: 20 },
                to: { opacity: 1, y: 0, duration: 0.8, ease: 'power2.out' }
            },
            slideInLeft: {
                from: { opacity: 0, x: -100 },
                to: { opacity: 1, x: 0, duration: 0.8, ease: 'power2.out' }
            },
            slideInRight: {
                from: { opacity: 0, x: 100 },
                to: { opacity: 1, x: 0, duration: 0.8, ease: 'power2.out' }
            },
            bounceIn: {
                from: { opacity: 0, scale: 0.3 },
                to: { opacity: 1, scale: 1, duration: 1, ease: 'back.out(1.7)' }
            },
            flipIn: {
                from: { opacity: 0, rotateY: -90 },
                to: { opacity: 1, rotateY: 0, duration: 0.8, ease: 'power2.out' }
            }
        };

        const config = animations[animation] || animations.fadeIn;
        gsap.fromTo(element, config.from, config.to);
    }

    animateCounter(element, finalValue, duration = 2) {
        if (!this.isInitialized) return;

        gsap.fromTo({ value: 0 },
            { value: 0 },
            {
                value: finalValue,
                duration: duration,
                ease: 'power2.out',
                onUpdate: function() {
                    element.textContent = Math.round(this.targets()[0].value);
                }
            }
        );
    }

    showNotification(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                ${message}
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        gsap.fromTo(notification,
            { x: 400, opacity: 0 },
            { x: 0, opacity: 1, duration: 0.3, ease: 'power2.out' }
        );
        
        // Auto remove
        setTimeout(() => {
            gsap.to(notification, {
                x: 400,
                opacity: 0,
                duration: 0.3,
                ease: 'power2.in',
                onComplete: () => notification.remove()
            });
        }, duration);
    }

    // Modal animations
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;

        gsap.to(modal, {
            opacity: 1,
            visibility: 'visible',
            duration: 0.3,
            ease: 'power2.out'
        });

        gsap.fromTo(modal.querySelector('.modal-content'),
            { scale: 0.8, y: 50, opacity: 0 },
            { scale: 1, y: 0, opacity: 1, duration: 0.4, ease: 'back.out(1.7)', delay: 0.1 }
        );
    }

    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;

        gsap.to(modal.querySelector('.modal-content'), {
            scale: 0.8,
            y: 50,
            opacity: 0,
            duration: 0.3,
            ease: 'power2.in'
        });

        gsap.to(modal, {
            opacity: 0,
            visibility: 'hidden',
            duration: 0.3,
            ease: 'power2.in',
            delay: 0.1
        });
    }

    // Page transition animations
    pageTransition(callback) {
        const overlay = document.createElement('div');
        overlay.className = 'page-transition-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            z-index: 10000;
            opacity: 0;
            pointer-events: none;
        `;
        
        document.body.appendChild(overlay);
        
        gsap.timeline()
            .to(overlay, { opacity: 1, duration: 0.3, ease: 'power2.out' })
            .call(callback)
            .to(overlay, { opacity: 0, duration: 0.3, ease: 'power2.in' })
            .call(() => overlay.remove());
    }
}

// Particle system for background effects
class ParticleSystem {
    constructor(container) {
        this.container = container;
        this.particles = [];
        this.canvas = null;
        this.ctx = null;
        this.animationId = null;
        this.init();
    }

    init() {
        this.canvas = document.createElement('canvas');
        this.ctx = this.canvas.getContext('2d');
        this.canvas.style.position = 'absolute';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.pointerEvents = 'none';
        this.canvas.style.zIndex = '1';
        
        this.container.style.position = 'relative';
        this.container.appendChild(this.canvas);
        
        this.resize();
        this.createParticles();
        this.animate();
        
        window.addEventListener('resize', () => this.resize());
    }

    resize() {
        this.canvas.width = this.container.offsetWidth;
        this.canvas.height = this.container.offsetHeight;
    }

    createParticles() {
        const particleCount = Math.floor((this.canvas.width * this.canvas.height) / 15000);
        
        for (let i = 0; i < particleCount; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                size: Math.random() * 2 + 1,
                opacity: Math.random() * 0.5 + 0.2
            });
        }
    }

    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.particles.forEach(particle => {
            // Update position
            particle.x += particle.vx;
            particle.y += particle.vy;
            
            // Wrap around edges
            if (particle.x < 0) particle.x = this.canvas.width;
            if (particle.x > this.canvas.width) particle.x = 0;
            if (particle.y < 0) particle.y = this.canvas.height;
            if (particle.y > this.canvas.height) particle.y = 0;
            
            // Draw particle
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
            this.ctx.fillStyle = `rgba(255, 215, 0, ${particle.opacity})`;
            this.ctx.fill();
        });
        
        this.animationId = requestAnimationFrame(() => this.animate());
    }

    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        if (this.canvas && this.canvas.parentNode) {
            this.canvas.parentNode.removeChild(this.canvas);
        }
    }
}

// Initialize animations when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize animation controller
    window.animationController = new AnimationController();
    
    // Add particle system to hero section
    const heroSection = document.querySelector('.hero-section');
    if (heroSection) {
        window.particleSystem = new ParticleSystem(heroSection);
    }
    
    // Add smooth scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Add loading state management
    window.addEventListener('beforeunload', () => {
        document.body.classList.add('loading');
    });
    
    // Add intersection observer for animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    document.querySelectorAll('.fade-in, .slide-in-left, .slide-in-right, .slide-in-up').forEach(el => {
        observer.observe(el);
    });
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.particleSystem) {
        window.particleSystem.destroy();
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AnimationController, ParticleSystem };
}