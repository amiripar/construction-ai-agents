// Global variables
let currentUser = null;
let authToken = null;
const API_BASE_URL = 'http://localhost:8000';

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if user is already logged in
    checkAuthStatus();
    
    // Setup form event listeners
    setupFormListeners();
    
    // Setup navigation
    setupNavigation();
});

// Authentication Status Check
function checkAuthStatus() {
    const token = sessionStorage.getItem('authToken');
    const user = sessionStorage.getItem('currentUser');
    
    if (token && user) {
        authToken = token;
        currentUser = JSON.parse(user);
        updateUIForLoggedInUser();
    }
}

// Update UI for logged in user
function updateUIForLoggedInUser() {
    const navAuth = document.querySelector('.nav-auth');
    if (navAuth && currentUser) {
        navAuth.innerHTML = `
            <span class="user-welcome">Hello ${currentUser.username}</span>
            <button class="btn-secondary" onclick="showDashboard()">Dashboard</button>
            <button class="btn-primary" onclick="logout()">Logout</button>
        `;
    }
}

// Setup Form Listeners
function setupFormListeners() {
    // Login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    // Register form
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
}

// Setup Navigation
function setupNavigation() {
    // Smooth scrolling for navigation links
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Modal Functions
function showLogin() {
    closeAllModals();
    document.getElementById('loginModal').style.display = 'block';
}

function showRegister() {
    closeAllModals();
    document.getElementById('registerModal').style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

function closeAllModals() {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.style.display = 'none';
    });
}

// Close modal when clicking outside
window.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
});

// Handle Login
async function handleLogin(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const loginData = {
        username: formData.get('username'),
        password: formData.get('password')
    };
    
    try {
        showLoading('loginForm');
        
        const response = await fetch(`${API_BASE_URL}/api/users/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(loginData)
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            // Store auth data
            authToken = result.data.access_token;
            currentUser = result.data.user;
            
            sessionStorage.setItem('authToken', authToken);
            sessionStorage.setItem('currentUser', JSON.stringify(currentUser));
            
            // Update UI
            updateUIForLoggedInUser();
            closeModal('loginModal');
            
            // Show success message
            showNotification('Login successful!', 'success');
            
            // Redirect to dashboard
            setTimeout(() => {
                showDashboard();
            }, 1000);
            
        } else {
            showNotification(result.message || 'Login error', 'error');
        }
        
    } catch (error) {
        console.error('Login error:', error);
        showNotification('Server connection error', 'error');
    } finally {
        hideLoading('loginForm');
    }
}

// Handle Register
async function handleRegister(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const password = formData.get('password');
    const confirmPassword = formData.get('confirmPassword');
    
    // Validate password confirmation
    if (password !== confirmPassword) {
        showNotification('Password and confirmation do not match', 'error');
        return;
    }
    
    const registerData = {
        first_name: formData.get('first_name'),
        last_name: formData.get('last_name'),
        username: formData.get('username'),
        email: formData.get('email'),
        phone: formData.get('phone') || null,
        role: formData.get('role'),
        password: password
    };
    
    try {
        showLoading('registerForm');
        
        const response = await fetch(`${API_BASE_URL}/api/users/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(registerData)
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            showNotification('Registration successful! Please log in.', 'success');
            closeModal('registerModal');
            
            // Show login modal
            setTimeout(() => {
                showLogin();
            }, 1000);
            
        } else {
            showNotification(result.message || 'Registration error', 'error');
        }
        
    } catch (error) {
        console.error('Register error:', error);
        showNotification('Server connection error', 'error');
    } finally {
        hideLoading('registerForm');
    }
}

// Logout
function logout() {
    authToken = null;
    currentUser = null;
    sessionStorage.removeItem('authToken');
    sessionStorage.removeItem('currentUser');
    
    // Reset navigation
    const navAuth = document.querySelector('.nav-auth');
    if (navAuth) {
        navAuth.innerHTML = `
            <button class="btn-secondary" onclick="showLogin()">Login</button>
            <button class="btn-primary" onclick="showRegister()">Register</button>
        `;
    }
    
    showNotification('Successfully logged out', 'success');
    
    // Redirect to home
    window.location.href = '#home';
}

// Show Dashboard
function showDashboard() {
    if (!currentUser) {
        showLogin();
        return;
    }
    
    // Create dashboard page
    window.location.href = '/static/dashboard.html';
}

// Show Demo
function showDemo() {
    showNotification('Demo will be available soon', 'info');
}

// Handle Start Free button click
function handleStartFree() {
    // Check if user is already logged in
    const token = localStorage.getItem('authToken');
    const user = localStorage.getItem('currentUser');
    
    if (token && user) {
        // User is logged in, redirect to dashboard
        showDashboard();
    } else {
        // User is not logged in, show register modal
        showRegister();
    }
}

// Loading Functions
function showLoading(formId) {
    const form = document.getElementById(formId);
    if (form) {
        form.classList.add('loading');
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        }
    }
}

function hideLoading(formId) {
    const form = document.getElementById(formId);
    if (form) {
        form.classList.remove('loading');
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = false;
            if (formId === 'loginForm') {
                submitBtn.innerHTML = 'Login';
            } else if (formId === 'registerForm') {
                submitBtn.innerHTML = 'Register';
            }
        }
    }
}

// Notification System
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => {
        notification.remove();
    });
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
        </div>
    `;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 3000;
        background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3'};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        animation: slideInRight 0.3s ease;
        max-width: 400px;
        word-wrap: break-word;
    `;
    
    // Add to document
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }
    }, 5000);
}

// Add notification animations to CSS
const notificationStyles = document.createElement('style');
notificationStyles.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .notification-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 10px;
    }
    
    .notification-close {
        background: none;
        border: none;
        color: white;
        font-size: 18px;
        cursor: pointer;
        padding: 0;
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .user-welcome {
        color: white;
        margin-left: 15px;
        font-weight: 500;
    }
`;
document.head.appendChild(notificationStyles);

// Mobile Menu Toggle
function toggleMenu() {
    const navMenu = document.getElementById('nav-menu');
    const hamburger = document.querySelector('.hamburger');
    
    navMenu.classList.toggle('active');
    hamburger.classList.toggle('active');
}

// Utility Functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0
    }).format(amount);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US').format(date);
}

// API Helper Functions
async function apiCall(endpoint, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    if (authToken) {
        defaultOptions.headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    const finalOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, finalOptions);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Request error');
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Export functions for use in other files
window.appFunctions = {
    showLogin,
    showRegister,
    closeModal,
    logout,
    showDashboard,
    showDemo,
    handleStartFree,
    showNotification,
    apiCall,
    formatCurrency,
    formatDate
};