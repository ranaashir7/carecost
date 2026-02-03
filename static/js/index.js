// Index page specific functionality
document.addEventListener('DOMContentLoaded', function() {
    // Add any index-page specific functionality here
    
    // Auto-focus on symptom input
    const symptomInput = document.getElementById('symptom');
    if (symptomInput) {
        symptomInput.focus();
    }

    // Add typing animation effect
    const heroTitle = document.querySelector('.hero-title');
    if (heroTitle) {
        // Add entrance animation
        setTimeout(() => {
            heroTitle.style.opacity = '1';
            heroTitle.style.transform = 'translateY(0)';
        }, 100);
    }

    // Add staggered animation to feature items
    const featureItems = document.querySelectorAll('.feature-item');
    featureItems.forEach((item, index) => {
        setTimeout(() => {
            item.style.opacity = '1';
            item.style.transform = 'translateY(0)';
        }, 300 + (index * 100));
    });

    // Add animation to steps
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observe step elements
    const steps = document.querySelectorAll('.step');
    steps.forEach(step => {
        step.style.opacity = '0';
        step.style.transform = 'translateY(20px)';
        step.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(step);
    });

    // Add form validation feedback
    const symptomForm = document.getElementById('symptomForm');
    const symptomInputField = document.getElementById('symptom');
    
    if (symptomInputField) {
        symptomInputField.addEventListener('input', function() {
            const value = this.value.trim();
            const submitBtn = symptomForm.querySelector('button[type="submit"]');
            
            if (value.length > 2) {
                submitBtn.style.transform = 'scale(1.02)';
                submitBtn.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.3)';
            } else {
                submitBtn.style.transform = 'scale(1)';
                submitBtn.style.boxShadow = '';
            }
        });
    }

    // Add subtle hover effects to nav links
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-1px)';
        });
        
        link.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    // Add parallax effect to hero section (subtle)
    window.addEventListener('scroll', function() {
        const scrolled = window.pageYOffset;
        const heroSection = document.querySelector('.hero-section');
        
        if (heroSection && scrolled < window.innerHeight) {
            const speed = scrolled * 0.5;
            heroSection.style.transform = `translateY(${speed}px)`;
        }
    });

    // Initialize initial animations
    initializeAnimations();
});

function initializeAnimations() {
    // Set initial states for animated elements
    const heroTitle = document.querySelector('.hero-title');
    const featureItems = document.querySelectorAll('.feature-item');
    
    if (heroTitle) {
        heroTitle.style.opacity = '0';
        heroTitle.style.transform = 'translateY(20px)';
        heroTitle.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
    }

    featureItems.forEach(item => {
        item.style.opacity = '0';
        item.style.transform = 'translateY(20px)';
        item.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    });
}
