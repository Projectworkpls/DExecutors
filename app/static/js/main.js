document.addEventListener('DOMContentLoaded', function() {
    console.log('DExecutors app loaded successfully!');
    
    // Add smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
    
    // Add loading states to forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.textContent = 'Loading...';
                submitBtn.disabled = true;
            }
        });
    });
    
    // Add hover effects to project cards
    const projectCards = document.querySelectorAll('.project-card');
    projectCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Auto-hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.flash');
    flashMessages.forEach(flash => {
        setTimeout(() => {
            flash.style.opacity = '0';
            flash.style.transform = 'translateY(-20px)';
            setTimeout(() => {
                flash.remove();
            }, 300);
        }, 5000);
    });
    
    // Add click animation to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            let ripple = document.createElement('span');
            ripple.classList.add('ripple');
            this.appendChild(ripple);
            
            let x = e.clientX - e.target.offsetLeft;
            let y = e.clientY - e.target.offsetTop;
            
            ripple.style.left = `${x}px`;
            ripple.style.top = `${y}px`;
            
            setTimeout(() => {
                ripple.remove();
            }, 300);
        });
    });
    
    // Form validation
    const emailInputs = document.querySelectorAll('input[type="email"]');
    emailInputs.forEach(input => {
        input.addEventListener('blur', function() {
            const email = this.value;
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            
            if (email && !emailRegex.test(email)) {
                this.style.borderColor = '#dc3545';
                showTooltip(this, 'Please enter a valid email address');
            } else {
                this.style.borderColor = '#28a745';
                hideTooltip(this);
            }
        });
    });
    
    // Budget validation for project creation
    const budgetInput = document.querySelector('input[name="budget"]');
    if (budgetInput) {
        budgetInput.addEventListener('input', function() {
            const value = parseFloat(this.value);
            if (value > 5000) {
                this.style.borderColor = '#dc3545';
                showTooltip(this, 'Budget cannot exceed ₹5,000 for Level 1');
            } else if (value > 0) {
                this.style.borderColor = '#28a745';
                hideTooltip(this);
            }
        });
    }
    
    // Deadline validation
    const deadlineInput = document.querySelector('input[name="deadline"]');
    if (deadlineInput) {
        deadlineInput.addEventListener('change', function() {
            const selectedDate = new Date(this.value);
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            
            if (selectedDate < today) {
                this.style.borderColor = '#dc3545';
                showTooltip(this, 'Deadline cannot be in the past');
            } else {
                this.style.borderColor = '#28a745';
                hideTooltip(this);
            }
        });
    }
    
    // Helper functions
    function showTooltip(element, message) {
        hideTooltip(element); // Remove existing tooltip
        
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = message;
        tooltip.style.cssText = `
            position: absolute;
            background: #dc3545;
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 12px;
            z-index: 1000;
            margin-top: 5px;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        
        element.parentNode.appendChild(tooltip);
        element.setAttribute('data-tooltip', 'true');
        
        setTimeout(() => {
            tooltip.style.opacity = '1';
        }, 10);
    }
    
    function hideTooltip(element) {
        if (element.getAttribute('data-tooltip')) {
            const tooltip = element.parentNode.querySelector('.tooltip');
            if (tooltip) {
                tooltip.remove();
            }
            element.removeAttribute('data-tooltip');
        }
    }
    
    // Add search functionality for browse page
    const searchInput = document.querySelector('#project-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const projectCards = document.querySelectorAll('.project-card');
            
            projectCards.forEach(card => {
                const title = card.querySelector('h3').textContent.toLowerCase();
                const description = card.querySelector('.project-description').textContent.toLowerCase();
                
                if (title.includes(searchTerm) || description.includes(searchTerm)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }
    
    // Add progress bar for forms
    const progressForms = document.querySelectorAll('.project-form');
    progressForms.forEach(form => {
        const inputs = form.querySelectorAll('input[required], textarea[required]');
        const progressBar = document.createElement('div');
        progressBar.className = 'form-progress';
        progressBar.style.cssText = `
            height: 4px;
            background: #e9ecef;
            border-radius: 2px;
            margin-bottom: 1rem;
            overflow: hidden;
        `;
        
        const progressFill = document.createElement('div');
        progressFill.style.cssText = `
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            width: 0%;
            transition: width 0.3s ease;
        `;
        
        progressBar.appendChild(progressFill);
        form.insertBefore(progressBar, form.firstChild);
        
        function updateProgress() {
            let filledInputs = 0;
            inputs.forEach(input => {
                if (input.value.trim() !== '') {
                    filledInputs++;
                }
            });
            
            const progress = (filledInputs / inputs.length) * 100;
            progressFill.style.width = `${progress}%`;
        }
        
        inputs.forEach(input => {
            input.addEventListener('input', updateProgress);
        });
    });
});

// Add CSS for ripple effect
const style = document.createElement('style');
style.textContent = `
    .btn {
        position: relative;
        overflow: hidden;
    }
    
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.6);
        transform: scale(0);
        animation: ripple-animation 0.3s linear;
        pointer-events: none;
    }
    
    @keyframes ripple-animation {
        to {
            transform: scale(2);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style); 