// Smooth scroll for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
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

// Animated counter for stats
function animateCounter(element, target, duration = 2000) {
    const start = 0;
    const increment = target / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        
        if (target >= 1000000) {
            element.textContent = formatNumber(current);
        } else if (target >= 1000) {
            element.textContent = Math.floor(current).toLocaleString();
        } else if (target % 1 !== 0) {
            element.textContent = current.toFixed(1);
        } else {
            element.textContent = Math.floor(current);
        }
    }, 16);
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(0) + 'K';
    }
    return num.toString();
}

// Intersection Observer for stats animation
const statsObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const counters = entry.target.querySelectorAll('.stat-number');
            counters.forEach(counter => {
                const target = parseFloat(counter.dataset.target);
                if (target) {
                    animateCounter(counter, target);
                }
            });
            statsObserver.disconnect();
        }
    });
}, {
    threshold: 0.3
});

const statsSection = document.querySelector('.stats');
if (statsSection) {
    statsObserver.observe(statsSection);
}

// Navbar scroll effect
const navbar = document.querySelector('.navbar');
window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
        navbar.style.background = 'rgba(2, 2, 3, 0.95)';
        navbar.style.backdropFilter = 'blur(30px)';
    } else {
        navbar.style.background = 'rgba(2, 2, 3, 0.8)';
        navbar.style.backdropFilter = 'blur(20px)';
    }
});

// Mobile menu toggle (if needed)
// const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
// const navLinks = document.querySelector('.nav-links');

// mobileMenuBtn?.addEventListener('click', () => {
//     navLinks.classList.toggle('active');
// });

// Feature card hover animation enhancement
const featureCards = document.querySelectorAll('.feature-card');
featureCards.forEach(card => {
    card.addEventListener('mouseenter', () => {
        card.style.transform = 'translateY(-8px) scale(1.02)';
    });
    card.addEventListener('mouseleave', () => {
        card.style.transform = 'translateY(0) scale(1)';
    });
});

// Tech item hover animation
const techItems = document.querySelectorAll('.tech-item');
techItems.forEach(item => {
    item.addEventListener('mouseenter', () => {
        item.style.transform = 'translateX(8px) scale(1.02)';
    });
    item.addEventListener('mouseleave', () => {
        item.style.transform = 'translateX(0) scale(1)';
    });
});

// Button ripple effect
document.querySelectorAll('.btn').forEach(button => {
    button.addEventListener('click', function(e) {
        const rect = this.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const ripple = document.createElement('span');
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.classList.add('ripple');
        
        this.appendChild(ripple);
        
        setTimeout(() => {
            ripple.remove();
        }, 600);
    });
});

// Add CSS for ripple effect
const styleSheet = document.createElement('style');
styleSheet.textContent = `
    .btn {
        position: relative;
        overflow: hidden;
    }
    
    .ripple {
        position: absolute;
        width: 100px;
        height: 100px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: translate(-50%, -50%) scale(0);
        animation: ripple-animation 0.6s ease-out;
        pointer-events: none;
    }
    
    @keyframes ripple-animation {
        to {
            transform: translate(-50%, -50%) scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(styleSheet);

// Pricing card hover effect
const pricingCards = document.querySelectorAll('.pricing-card');
pricingCards.forEach(card => {
    card.addEventListener('mouseenter', () => {
        if (!card.classList.contains('popular')) {
            card.style.transform = 'translateY(-4px)';
        }
    });
    card.addEventListener('mouseleave', () => {
        if (!card.classList.contains('popular')) {
            card.style.transform = 'translateY(0)';
        }
    });
});

// Smooth reveal animation for sections
const sectionObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, {
    threshold: 0.1
});

document.querySelectorAll('section').forEach(section => {
    section.style.opacity = '0';
    section.style.transform = 'translateY(30px)';
    section.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
    sectionObserver.observe(section);
});

// Add hover effect to dashboard tabs
const dashboardTabs = document.querySelectorAll('.tab');
dashboardTabs.forEach(tab => {
    tab.addEventListener('click', function() {
        dashboardTabs.forEach(t => t.classList.remove('active'));
        this.classList.add('active');
    });
});

// Simulate test status update
function simulateTestUpdates() {
    const testItems = document.querySelectorAll('.test-item');
    const statuses = ['通过', '失败', '运行中'];
    
    setInterval(() => {
        const randomIndex = Math.floor(Math.random() * testItems.length);
        const testItem = testItems[randomIndex];
        const statusSpan = testItem.querySelector('.test-status');
        const currentStatus = statusSpan.textContent;
        
        let newStatus;
        do {
            newStatus = statuses[Math.floor(Math.random() * statuses.length)];
        } while (newStatus === currentStatus);
        
        statusSpan.textContent = newStatus;
        statusSpan.className = `test-status ${newStatus === '通过' ? 'success' : newStatus === '运行中' ? 'running' : 'warning'}`;
    }, 3000);
}

// Start simulation when dashboard is visible
const dashboardObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            simulateTestUpdates();
            dashboardObserver.disconnect();
        }
    });
}, {
    threshold: 0.5
});

const dashboardPreview = document.querySelector('.dashboard-preview');
if (dashboardPreview) {
    dashboardObserver.observe(dashboardPreview);
}

// Add typing animation to hero title
function typingEffect(element, text, speed = 100) {
    let index = 0;
    element.textContent = '';
    
    const timer = setInterval(() => {
        if (index < text.length) {
            element.textContent += text.charAt(index);
            index++;
        } else {
            clearInterval(timer);
        }
    }, speed);
}

// Initialize typing effect after page load
document.addEventListener('DOMContentLoaded', () => {
    const heroTitle = document.querySelector('.hero-title');
    if (heroTitle) {
        const originalText = heroTitle.innerHTML;
        const gradientPart = heroTitle.querySelector('.gradient-text');
        
        if (gradientPart) {
            gradientPart.textContent = '';
            setTimeout(() => {
                typingEffect(gradientPart, '多端UI自动化测试平台', 80);
            }, 500);
        }
    }
});

// Add particle effect to hero section
function createParticles() {
    const heroSection = document.querySelector('.hero');
    if (!heroSection) return;
    
    const particleContainer = document.createElement('div');
    particleContainer.className = 'particles-container';
    heroSection.appendChild(particleContainer);
    
    for (let i = 0; i < 20; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.top = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 5 + 's';
        particle.style.animationDuration = (10 + Math.random() * 10) + 's';
        particle.style.width = (2 + Math.random() * 4) + 'px';
        particle.style.height = particle.style.width;
        particleContainer.appendChild(particle);
    }
}

// Add particle CSS
const particleStyles = document.createElement('style');
particleStyles.textContent = `
    .particles-container {
        position: absolute;
        inset: 0;
        pointer-events: none;
        overflow: hidden;
        z-index: 0;
    }
    
    .particle {
        position: absolute;
        background: radial-gradient(circle, rgba(37, 99, 235, 0.6), transparent);
        border-radius: 50%;
        animation: particle-float linear infinite;
    }
    
    @keyframes particle-float {
        0% {
            transform: translateY(100vh) rotate(0deg);
            opacity: 0;
        }
        10% {
            opacity: 1;
        }
        90% {
            opacity: 1;
        }
        100% {
            transform: translateY(-100vh) rotate(720deg);
            opacity: 0;
        }
    }
`;
document.head.appendChild(particleStyles);

createParticles();

// Add hover glow effect to CTA buttons
const ctaButtons = document.querySelectorAll('.cta .btn');
ctaButtons.forEach(button => {
    button.addEventListener('mouseenter', () => {
        button.style.boxShadow = '0 0 40px rgba(37, 99, 235, 0.4)';
    });
    button.addEventListener('mouseleave', () => {
        button.style.boxShadow = '';
    });
});

// Handle form submissions (if any forms are added later)
// document.addEventListener('submit', (e) => {
//     e.preventDefault();
//     // Handle form submission
// });

// Console welcome message
console.log('%c🚀 AutoTest Platform', 'font-size: 20px; font-weight: bold; color: #2563EB;');
console.log('%c智能驱动的多端UI自动化测试平台', 'font-size: 14px; color: #8A8F98;');

// Modal functionality
const Modal = {
    activeModal: null,
    
    open(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;
        
        if (this.activeModal) {
            this.close();
        }
        
        modal.classList.add('active');
        this.activeModal = modal;
        document.body.style.overflow = 'hidden';
        
        const firstInput = modal.querySelector('input, select, textarea');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 300);
        }
    },
    
    close() {
        if (!this.activeModal) return;
        
        this.activeModal.classList.remove('active');
        this.activeModal = null;
        document.body.style.overflow = '';
    },
    
    init() {
        document.querySelectorAll('[data-modal]').forEach(trigger => {
            trigger.addEventListener('click', (e) => {
                e.preventDefault();
                const modalId = trigger.dataset.modal;
                this.open(modalId);
            });
        });
        
        document.querySelectorAll('[data-close-modal]').forEach(trigger => {
            trigger.addEventListener('click', (e) => {
                e.preventDefault();
                this.close();
            });
        });
        
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal || e.target.classList.contains('modal-overlay')) {
                    this.close();
                }
            });
        });
        
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.activeModal) {
                this.close();
            }
        });
    }
};

Modal.init();

// Form handling
const FormHandler = {
    handleFormSubmit(formId, successMessage) {
        const form = document.getElementById(formId);
        if (!form) return;
        
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 提交中...';
            
            setTimeout(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
                
                form.reset();
                Modal.close();
                
                const successModal = document.getElementById('success-modal');
                const successMessageEl = document.getElementById('success-message');
                if (successMessageEl) {
                    successMessageEl.textContent = successMessage;
                }
                Modal.open('success-modal');
            }, 1500);
        });
    },
    
    init() {
        this.handleFormSubmit('login-form', '登录成功！欢迎回到 AutoTest。');
        this.handleFormSubmit('trial-form', '注册成功！我们已发送验证邮件到您的邮箱。');
        this.handleFormSubmit('journey-form', '提交成功！我们的专家将在24小时内与您联系。');
        this.handleFormSubmit('booking-form', '预约成功！我们已发送确认邮件到您的邮箱。');
        this.handleFormSubmit('contact-form', '提交成功！我们的销售团队将尽快与您联系。');
    }
};

FormHandler.init();

// Video modal functionality
const VideoModal = {
    init() {
        const videoTabs = document.querySelectorAll('.video-tab');
        const videoPlayButton = document.querySelector('.video-play-button');
        
        videoTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                videoTabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                const videoType = tab.dataset.video;
                this.updateVideoContent(videoType);
            });
        });
        
        videoPlayButton?.addEventListener('click', () => {
            alert('视频播放功能将在实际部署时接入真实视频源');
        });
    },
    
    updateVideoContent(videoType) {
        const videoInfo = document.querySelector('.video-info h3');
        const videoDesc = document.querySelector('.video-description');
        
        const videoData = {
            overview: {
                title: 'AutoTest 平台功能演示',
                duration: '时长：3分30秒',
                features: ['如何创建测试项目', '关键字驱动的测试用例编写', '多平台测试执行', '测试报告查看与分析']
            },
            android: {
                title: 'Android 自动化测试演示',
                duration: '时长：4分15秒',
                features: ['UiAutomator2 框架配置', 'Android 应用元素定位', '测试用例录制与回放', '性能监控与分析']
            },
            web: {
                title: 'Web 自动化测试演示',
                duration: '时长：3分45秒',
                features: ['Playwright 环境搭建', '多浏览器并行测试', '网络请求拦截', '页面性能测试']
            },
            advanced: {
                title: '高级功能演示',
                duration: '时长：5分20秒',
                features: ['PO 设计模式应用', '关键字自定义', '测试数据驱动', 'CI/CD 集成配置']
            }
        };
        
        const data = videoData[videoType];
        if (data && videoInfo && videoDesc) {
            videoInfo.textContent = data.title;
            videoInfo.nextElementSibling.textContent = data.duration;
            
            const featuresList = videoDesc.querySelector('ul');
            if (featuresList) {
                featuresList.innerHTML = data.features.map(f => `<li>${f}</li>`).join('');
            }
        }
    }
};

VideoModal.init();

// Date picker - set minimum date to today
const dateInputs = document.querySelectorAll('input[type="date"]');
dateInputs.forEach(input => {
    const today = new Date().toISOString().split('T')[0];
    input.setAttribute('min', today);
});

// Form validation visual feedback
const formInputs = document.querySelectorAll('.form-group input, .form-group select, .form-group textarea');
formInputs.forEach(input => {
    input.addEventListener('blur', () => {
        if (input.checkValidity()) {
            input.style.borderColor = '#22C55E';
        } else if (input.value) {
            input.style.borderColor = '#EF4444';
        }
    });
    
    input.addEventListener('input', () => {
        input.style.borderColor = '';
    });
});

// Checkbox group validation
const checkboxGroups = document.querySelectorAll('.checkbox-group');
checkboxGroups.forEach(group => {
    const checkboxes = group.querySelectorAll('input[type="checkbox"]');
    const form = group.closest('form');
    
    if (form) {
        form.addEventListener('submit', (e) => {
            const checked = Array.from(checkboxes).some(cb => cb.checked);
            if (checkboxes.length > 0 && !checked) {
                e.preventDefault();
                group.style.border = '1px solid #EF4444';
                group.style.borderRadius = '8px';
                group.style.padding = '0.5rem';
                
                setTimeout(() => {
                    group.style.border = '';
                    group.style.padding = '';
                }, 3000);
            }
        });
    }
});

// Password strength indicator
const passwordInputs = document.querySelectorAll('input[type="password"]');
passwordInputs.forEach(input => {
    input.addEventListener('input', () => {
        const value = input.value;
        let strength = 0;
        
        if (value.length >= 8) strength++;
        if (/[a-z]/.test(value)) strength++;
        if (/[A-Z]/.test(value)) strength++;
        if (/[0-9]/.test(value)) strength++;
        if (/[^a-zA-Z0-9]/.test(value)) strength++;
        
        const strengthIndicator = input.parentElement.querySelector('.password-strength');
        if (strengthIndicator) {
            const colors = ['#EF4444', '#F97316', '#FBBF24', '#84CC16', '#22C55E'];
            const labels = ['很弱', '弱', '中等', '强', '很强'];
            strengthIndicator.style.width = (strength * 20) + '%';
            strengthIndicator.style.backgroundColor = colors[strength - 1] || '#EF4444';
            strengthIndicator.nextElementSibling.textContent = labels[strength - 1] || '';
        }
    });
});

// Smooth modal switching
document.querySelectorAll('.modal-switch').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const targetModalId = link.dataset.modal;
        if (targetModalId) {
            Modal.close();
            setTimeout(() => {
                Modal.open(targetModalId);
            }, 300);
        }
    });
});

// Add loading state to buttons
document.querySelectorAll('.btn').forEach(button => {
    if (button.dataset.modal) {
        button.addEventListener('click', function() {
            const modalId = this.dataset.modal;
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.style.opacity = '0';
                setTimeout(() => {
                    modal.style.opacity = '1';
                }, 50);
            }
        });
    }
});

// Prevent form resubmission on page refresh
if (window.history.replaceState) {
    window.history.replaceState(null, null, window.location.href);
}