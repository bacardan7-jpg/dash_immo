// Animation Controller - ImmoAnalytics
// GSAP-based animations with performance optimizations

class AnimationController {
    constructor() {
        this.isInitialized = false;
        this.timelines = new Map();
        this.observers = new Map();
        this.particleSystems = new Map();
        
        this.init();
    }

    init() {
        // Load GSAP with error handling
        this.loadGSAP().then(() => {
            this.setupAnimations();
            this.setupScrollAnimations();
            this.setupObservers();
            this.setupInteractions();
            this.setupParticleSystems();
            this.isInitialized = true;
            console.log('AnimationController initialized');
        }).catch(error => {
            console.warn('GSAP not available:', error);
            this.setupFallbackAnimations();
        });
    }

    async loadGSAP() {
        return new Promise((resolve, reject) => {
            if (typeof gsap !== 'undefined') {
                // Register plugins
                if (typeof ScrollTrigger !== 'undefined') {
                    gsap.registerPlugin(ScrollTrigger);
                }
                if (typeof TextPlugin !== 'undefined') {
                    gsap.registerPlugin(TextPlugin);
                }
                if (typeof MotionPathPlugin !== 'undefined') {
                    gsap.registerPlugin(MotionPathPlugin);
                }
                resolve();
                return;
            }

            // Dynamic load GSAP if not present
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js';
            script.onload = () => {
                // Load plugins
                const plugins = [
                    'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/ScrollTrigger.min.js',
                    'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/TextPlugin.min.js'
                ];

                Promise.all(
                    plugins.map(url => {
                        return new Promise((resolve) => {
                            const pluginScript = document.createElement('script');
                            pluginScript.src = url;
                            pluginScript.onload = resolve;
                            document.head.appendChild(pluginScript);
                        });
                    })
                ).then(() => {
                    if (typeof ScrollTrigger !== 'undefined') {
                        gsap.registerPlugin(ScrollTrigger);
                    }
                    if (typeof TextPlugin !== 'undefined') {
                        gsap.registerPlugin(TextPlugin);
                    }
                    resolve();
                });
            };
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    setupAnimations() {
        // Hero animations
        this.animateHero();
        
        // Feature cards
        this.animateFeatureCards();
        
        // KPI cards
        this.animateKPICards();
        
        // Tech items
        this.animateTechItems();
    }

    animateHero() {
        if (!this.isInitialized) return;

        const heroTimeline = gsap.timeline();
        
        heroTimeline
            .fromTo('.hero-title',
                { opacity: 0, y: 50, scale: 0.8 },
                { opacity: 1, y: 0, scale: 1, duration: 1.2, ease: 'back.out(1.7)' }
            )
            .fromTo('.hero-subtitle',
                { opacity: 0, y: 30 },
                { opacity: 1, y: 0, duration: 1, ease: 'power2.out' },
                '-=0.8'
            )
            .fromTo('.hero-description',
                { opacity: 0, y: 20 },
                { opacity: 1, y: 0, duration: 0.8, ease: 'power2.out' },
                '-=0.6'
            )
            .fromTo('.hero-actions .glass-button',
                { opacity: 0, y: 30, scale: 0.9 },
                { opacity: 1, y: 0, scale: 1, duration: 0.6, ease: 'back.out(1.7)', stagger: 0.1 },
                '-=0.4'
            );

        // Floating animation
        gsap.to('.hero-title', {
            y: -5,
            duration: 4,
            ease: 'sine.inOut',
            yoyo: true,
            repeat: -1
        });

        this.timelines.set('hero', heroTimeline);
    }

    animateFeatureCards() {
        if (!this.isInitialized || typeof ScrollTrigger === 'undefined') return;

        gsap.utils.toArray('.feature-card').forEach((card, index) => {
            // Parallax effect
            gsap.to(card, {
                y: (i, el) => -ScrollTrigger.maxScroll(window) * 0.5 * (el.dataset.speed || 0.5),
                ease: 'none',
                scrollTrigger: {
                    trigger: card,
                    start: 'top bottom',
                    end: 'bottom top',
                    scrub: true
                }
            });

            // Entrance animation
            gsap.fromTo(card,
                { opacity: 0, y: 50, scale: 0.9 },
                {
                    opacity: 1,
                    y: 0,
                    scale: 1,
                    duration: 0.8,
                    ease: 'back.out(1.7)',
                    scrollTrigger: {
                        trigger: card,
                        start: 'top 85%',
                        end: 'bottom 15%',
                        toggleActions: 'play none none reverse'
                    }
                }
            );
        });
    }

    animateKPICards() {
        if (!this.isInitialized || typeof ScrollTrigger === 'undefined') return;

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const card = entry.target;
                    const valueElement = card.querySelector('.kpi-value[data-count]');
                    
                    if (valueElement && !card.dataset.animated) {
                        card.dataset.animated = 'true';
                        const finalValue = parseInt(valueElement.dataset.count) || 0;
                        
                        gsap.to(card, {
                            scale: 1.02,
                            duration: 0.2,
                            ease: 'power2.out',
                            yoyo: true,
                            repeat: 1
                        });
                        
                        this.animateCounter(valueElement, finalValue);
                    }
                }
            });
        }, { threshold: 0.5 });

        document.querySelectorAll('.kpi-card').forEach(card => observer.observe(card));
    }

    animateTechItems() {
        if (!this.isInitialized) return;

        gsap.fromTo('.tech-item',
            { opacity: 0, scale: 0.8, y: 30 },
            {
                opacity: 1,
                scale: 1,
                y: 0,
                duration: 0.6,
                ease: 'back.out(1.7)',
                stagger: 0.05,
                delay: 0.5
            }
        );
    }

    setupScrollAnimations() {
        if (!this.isInitialized || typeof ScrollTrigger === 'undefined') return;

        // Parallax background
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

        // Dashboard cards
        gsap.utils.toArray('.dashboard-card').forEach(card => {
            gsap.fromTo(card,
                { opacity: 0, y: 30, rotateX: -10 },
                {
                    opacity: 1,
                    y: 0,
                    rotateX: 0,
                    duration: 0.6,
                    ease: 'power2.out',
                    scrollTrigger: {
                        trigger: card,
                        start: 'top 85%',
                        toggleActions: 'play none none reverse'
                    }
                }
            );
        });
    }

    setupObservers() {
        // Intersection Observer for performance
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

        document.querySelectorAll('.fade-in, .slide-in-left, .slide-in-right, .slide-in-up').forEach(el => {
            observer.observe(el);
        });
    }

    setupInteractions() {
        // Button interactions
        document.querySelectorAll('.glass-button:not(:disabled)').forEach(button => {
            button.addEventListener('mouseenter', () => {
                gsap.to(button, { scale: 1.05, duration: 0.2, ease: 'power2.out' });
            });

            button.addEventListener('mouseleave', () => {
                gsap.to(button, { scale: 1, duration: 0.2, ease: 'power2.out' });
            });

            button.addEventListener('mousedown', () => {
                gsap.to(button, { scale: 0.95, duration: 0.1, ease: 'power2.in' });
            });

            button.addEventListener('mouseup', () => {
                gsap.to(button, { scale: 1.05, duration: 0.2, ease: 'back.out(1.7)' });
            });
        });

        // Card interactions
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

        // Input interactions
        document.querySelectorAll('.glass-input').forEach(input => {
            input.addEventListener('focus', () => {
                gsap.to(input, { scale: 1.02, duration: 0.2, ease: 'power2.out' });
            });

            input.addEventListener('blur', () => {
                gsap.to(input, { scale: 1, duration: 0.2, ease: 'power2.out' });
            });
        });

        // Mobile menu toggle
        const navToggle = document.querySelector('.nav-toggle');
        const navCollapse = document.querySelector('.nav-collapse');
        
        if (navToggle && navCollapse) {
            navToggle.addEventListener('click', () => {
                const isExpanded = navToggle.getAttribute('aria-expanded') === 'true';
                navToggle.setAttribute('aria-expanded', !isExpanded);
                navCollapse.classList.toggle('show');
                
                gsap.fromTo(navCollapse,
                    { opacity: 0, y: -20 },
                    { opacity: 1, y: 0, duration: 0.3, ease: 'power2.out' }
                );
            });
        }
    }

    setupParticleSystems() {
        document.querySelectorAll('.particle-container').forEach(container => {
            const system = new ParticleSystem(container);
            this.particleSystems.set(container, system);
        });
    }

    animateCounter(element, finalValue, duration = 2) {
        if (!this.isInitialized) {
            element.textContent = finalValue;
            return;
        }

        const obj = { value: 0 };
        gsap.to(obj, {
            value: finalValue,
            duration: duration,
            ease: 'power2.out',
            onUpdate: () => {
                element.textContent = Math.round(obj.value);
            },
            onComplete: () => {
                element.textContent = finalValue;
            }
        });
    }

    showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span>${message}</span>
                <button class="notification-close" aria-label="Fermer">&times;</button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Close button
        notification.querySelector('.notification-close').addEventListener('click', () => {
            this.hideNotification(notification);
        });
        
        // Animate in
        if (this.isInitialized) {
            gsap.fromTo(notification,
                { x: 400, opacity: 0 },
                { x: 0, opacity: 1, duration: 0.3, ease: 'back.out(1.7)' }
            );
            
            // Auto hide
            setTimeout(() => this.hideNotification(notification), duration);
        } else {
            notification.style.transform = 'translateX(0)';
            notification.style.opacity = '1';
            setTimeout(() => notification.remove(), duration);
        }
    }

    hideNotification(notification) {
        if (this.isInitialized) {
            gsap.to(notification, {
                x: 400,
                opacity: 0,
                duration: 0.3,
                ease: 'power2.in',
                onComplete: () => notification.remove()
            });
        } else {
            notification.remove();
        }
    }

    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;

        modal.classList.add('show');
        
        if (this.isInitialized) {
            gsap.to(modal, { opacity: 1, duration: 0.3, ease: 'power2.out' });
            
            const modalContent = modal.querySelector('.modal-content');
            gsap.fromTo(modalContent,
                { scale: 0.8, y: 50, opacity: 0 },
                { scale: 1, y: 0, opacity: 1, duration: 0.4, ease: 'back.out(1.7)', delay: 0.1 }
            );
        }
    }

    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;

        if (this.isInitialized) {
            const modalContent = modal.querySelector('.modal-content');
            gsap.to(modalContent, {
                scale: 0.8,
                y: 50,
                opacity: 0,
                duration: 0.3,
                ease: 'power2.in'
            });
            
            gsap.to(modal, {
                opacity: 0,
                duration: 0.3,
                ease: 'power2.in',
                delay: 0.1,
                onComplete: () => modal.classList.remove('show')
            });
        } else {
            modal.classList.remove('show');
        }
    }

    setupFallbackAnimations() {
        // Fallback CSS animations if GSAP fails
        document.querySelectorAll('.fade-in').forEach(el => {
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        });
        
        document.querySelectorAll('.kpi-value[data-count]').forEach(el => {
            el.textContent = el.dataset.count;
        });
        
        console.log('Fallback animations applied');
    }

    destroy() {
        // Cleanup
        this.timelines.forEach(tl => tl.kill());
        this.particleSystems.forEach(system => system.destroy());
        if (typeof ScrollTrigger !== 'undefined') {
            ScrollTrigger.getAll().forEach(st => st.kill());
        }
    }
}

// Particle System using Canvas
class ParticleSystem {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            particleCount: options.particleCount || Math.floor((window.innerWidth * window.innerHeight) / 20000),
            particleSize: options.particleSize || [1, 4],
            speed: options.speed || 0.5,
            color: options.color || '255, 215, 0',
            opacity: options.opacity || 0.3,
            ...options
        };
        
        this.canvas = null;
        this.ctx = null;
        this.particles = [];
        this.animationId = null;
        this.resizeHandler = null;
        
        this.init();
    }

    init() {
        this.canvas = document.createElement('canvas');
        this.ctx = this.canvas.getContext('2d');
        
        this.canvas.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 1;
        `;
        
        this.container.style.position = 'relative';
        this.container.insertBefore(this.canvas, this.container.firstChild);
        
        this.resize();
        this.createParticles();
        this.animate();
        
        this.resizeHandler = () => this.resize();
        window.addEventListener('resize', this.resizeHandler);
    }

    resize() {
        this.canvas.width = this.canvas.offsetWidth * window.devicePixelRatio;
        this.canvas.height = this.canvas.offsetHeight * window.devicePixelRatio;
        this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
    }

    createParticles() {
        this.particles = [];
        const { particleCount, particleSize, speed, color, opacity } = this.options;
        
        for (let i = 0; i < particleCount; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.offsetWidth,
                y: Math.random() * this.canvas.offsetHeight,
                vx: (Math.random() - 0.5) * speed,
                vy: (Math.random() - 0.5) * speed,
                size: Math.random() * (particleSize[1] - particleSize[0]) + particleSize[0],
                opacity: Math.random() * opacity,
                color: color
            });
        }
    }

    animate() {
        this.ctx.clearRect(0, 0, this.canvas.offsetWidth, this.canvas.offsetHeight);
        
        this.particles.forEach(particle => {
            // Update position
            particle.x += particle.vx;
            particle.y += particle.vy;
            
            // Wrap around edges
            if (particle.x < 0) particle.x = this.canvas.offsetWidth;
            if (particle.x > this.canvas.offsetWidth) particle.x = 0;
            if (particle.y < 0) particle.y = this.canvas.offsetHeight;
            if (particle.y > this.canvas.offsetHeight) particle.y = 0;
            
            // Draw particle
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
            this.ctx.fillStyle = `rgba(${particle.color}, ${particle.opacity})`;
            this.ctx.fill();
        });
        
        this.animationId = requestAnimationFrame(() => this.animate());
    }

    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        
        if (this.resizeHandler) {
            window.removeEventListener('resize', this.resizeHandler);
        }
        
        if (this.canvas && this.canvas.parentNode) {
            this.canvas.parentNode.removeChild(this.canvas);
        }
    }
}

/* Mobile menu toggle */
class MobileMenu {
    constructor() {
        this.toggle = document.querySelector('.nav-toggle');
        this.menu = document.querySelector('.nav-collapse');
        this.sidebar = document.querySelector('.glass-sidebar');
        
        this.init();
    }

    init() {
        if (!this.toggle) return;
        
        this.toggle.addEventListener('click', () => this.toggleMenu());
        
        // Close on outside click
        document.addEventListener('click', (e) => {
            if (!this.toggle.contains(e.target) && !this.menu.contains(e.target)) {
                this.closeMenu();
            }
        });
        
        // Swipe gestures
        let touchStartX = 0;
        let touchEndX = 0;
        
        document.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        });
        
        document.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            this.handleSwipe(touchStartX, touchEndX);
        });
    }

    toggleMenu() {
        const isOpen = this.toggle.getAttribute('aria-expanded') === 'true';
        
        if (isOpen) {
            this.closeMenu();
        } else {
            this.openMenu();
        }
    }

    openMenu() {
        this.toggle.setAttribute('aria-expanded', 'true');
        this.menu.classList.add('show');
        
        gsap.fromTo(this.menu,
            { opacity: 0, y: -20 },
            { opacity: 1, y: 0, duration: 0.3, ease: 'power2.out' }
        );
    }

    closeMenu() {
        this.toggle.setAttribute('aria-expanded', 'false');
        
        gsap.to(this.menu, {
            opacity: 0,
            y: -20,
            duration: 0.3,
            ease: 'power2.in',
            onComplete: () => this.menu.classList.remove('show')
        });
    }

    handleSwipe(startX, endX) {
        const swipeThreshold = 50;
        const diff = startX - endX;
        
        // Swipe left to open sidebar on mobile
        if (diff < -swipeThreshold && window.innerWidth <= 768) {
            this.openSidebar();
        }
        // Swipe right to close sidebar
        else if (diff > swipeThreshold && this.sidebar?.classList.contains('show')) {
            this.closeSidebar();
        }
    }

    openSidebar() {
        if (!this.sidebar) return;
        
        this.sidebar.classList.add('show');
        gsap.fromTo(this.sidebar,
            { x: '-100%' },
            { x: '0%', duration: 0.3, ease: 'power2.out' }
        );
    }

    closeSidebar() {
        if (!this.sidebar) return;
        
        gsap.to(this.sidebar, {
            x: '-100%',
            duration: 0.3,
            ease: 'power2.in',
            onComplete: () => this.sidebar.classList.remove('show')
        });
    }
}

/* Performance utilities */
class PerformanceMonitor {
    constructor() {
        this.metrics = {
            fps: 0,
            frameTime: 0,
            memory: 0
        };
        
        this.init();
    }

    init() {
        if ('requestIdleCallback' in window) {
            requestIdleCallback(() => this.collectMetrics());
        }
    }

    collectMetrics() {
        // FPS monitoring
        let lastTime = performance.now();
        let frames = 0;
        
        const measureFPS = (currentTime) => {
            frames++;
            
            if (currentTime >= lastTime + 1000) {
                this.metrics.fps = Math.round((frames * 1000) / (currentTime - lastTime));
                frames = 0;
                lastTime = currentTime;
            }
            
            requestAnimationFrame(measureFPS);
        };
        
        requestAnimationFrame(measureFPS);
        
        // Memory monitoring (if available)
        if ('memory' in performance) {
            setInterval(() => {
                this.metrics.memory = Math.round(performance.memory.usedJSHeapSize / 1048576);
            }, 5000);
        }
    }

    getMetrics() {
        return this.metrics;
    }
}

/* Initialize on DOM load */
document.addEventListener('DOMContentLoaded', () => {
    // Initialize animation controller
    window.animationController = new AnimationController();
    
    // Initialize mobile menu
    window.mobileMenu = new MobileMenu();
    
    // Initialize performance monitor (dev mode)
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        window.performanceMonitor = new PerformanceMonitor();
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
    
    // Add beforeunload handler
    window.addEventListener('beforeunload', () => {
        if (window.animationController) {
            window.animationController.destroy();
        }
    });
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AnimationController, ParticleSystem, MobileMenu, PerformanceMonitor };
}