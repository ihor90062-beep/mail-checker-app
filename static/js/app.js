// Advanced Email & Proxy Checker - Client-side JavaScript

// Global application state
const App = {
    currentUser: null,
    activeChecks: new Map(),
    config: {
        autoRefresh: true,
        refreshInterval: 5000
    }
};

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize form validation
    initializeFormValidation();
    
    // Setup auto-refresh for dashboard
    if (window.location.pathname === '/dashboard' && App.config.autoRefresh) {
        setupAutoRefresh();
    }
    
    // Setup real-time notifications
    setupNotifications();
    
    console.log('Email & Proxy Checker initialized');
}

// Form validation helpers
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}

// Email validation helper
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Proxy validation helper
function isValidProxy(host, port) {
    const hostRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$|^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$/;
    const portNum = parseInt(port);
    
    return hostRegex.test(host) && portNum >= 1 && portNum <= 65535;
}

// Password strength indicator
function updatePasswordStrength(password, indicatorElement) {
    const strength = calculatePasswordStrength(password);
    const indicator = document.getElementById(indicatorElement);
    
    if (!indicator) return;
    
    indicator.className = 'progress-bar';
    
    if (strength < 25) {
        indicator.classList.add('bg-danger');
        indicator.style.width = '25%';
        indicator.textContent = 'Weak';
    } else if (strength < 50) {
        indicator.classList.add('bg-warning');
        indicator.style.width = '50%';
        indicator.textContent = 'Fair';
    } else if (strength < 75) {
        indicator.classList.add('bg-info');
        indicator.style.width = '75%';
        indicator.textContent = 'Good';
    } else {
        indicator.classList.add('bg-success');
        indicator.style.width = '100%';
        indicator.textContent = 'Strong';
    }
}

function calculatePasswordStrength(password) {
    let strength = 0;
    
    if (password.length >= 8) strength += 25;
    if (/[a-z]/.test(password)) strength += 15;
    if (/[A-Z]/.test(password)) strength += 15;
    if (/[0-9]/.test(password)) strength += 15;
    if (/[^A-Za-z0-9]/.test(password)) strength += 30;
    
    return Math.min(strength, 100);
}

// Notification system
function setupNotifications() {
    // Check if browser supports notifications
    if ('Notification' in window) {
        // Request permission if not already granted
        if (Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }
}

function showNotification(title, message, type = 'info') {
    // Browser notification
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, {
            body: message,
            icon: '/static/favicon.ico',
            tag: 'email-proxy-checker'
        });
    }
    
    // In-app toast notification
    showToast(title, message, type);
}

function showToast(title, message, type = 'info') {
    const toastContainer = getOrCreateToastContainer();
    
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="fas fa-${getToastIcon(type)} text-${type} me-2"></i>
                <strong class="me-auto">${title}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    
    toast.show();
    
    // Remove toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

function getOrCreateToastContainer() {
    let container = document.getElementById('toast-container');
    
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1055';
        document.body.appendChild(container);
    }
    
    return container;
}

function getToastIcon(type) {
    const icons = {
        'success': 'check-circle',
        'danger': 'exclamation-triangle',
        'warning': 'exclamation-circle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// Auto-refresh functionality for dashboard
function setupAutoRefresh() {
    if (!App.config.autoRefresh) return;
    
    setInterval(function() {
        refreshDashboardStats();
    }, App.config.refreshInterval);
}

async function refreshDashboardStats() {
    try {
        // This would typically fetch updated statistics
        // For demo purposes, we'll just update the timestamp
        const timestamp = document.querySelector('.last-updated');
        if (timestamp) {
            timestamp.textContent = 'Last updated: ' + new Date().toLocaleTimeString();
        }
    } catch (error) {
        console.error('Failed to refresh dashboard:', error);
    }
}

// Utility functions
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString();
}

function formatDuration(milliseconds) {
    const seconds = Math.floor(milliseconds / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
        return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
        return `${minutes}m ${seconds % 60}s`;
    } else {
        return `${seconds}s`;
    }
}

function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(function() {
            showToast('Success', 'Copied to clipboard', 'success');
        }).catch(function(err) {
            console.error('Failed to copy: ', err);
            fallbackCopyToClipboard(text);
        });
    } else {
        fallbackCopyToClipboard(text);
    }
}

function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.top = '0';
    textArea.style.left = '0';
    textArea.style.position = 'fixed';
    
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showToast('Success', 'Copied to clipboard', 'success');
        } else {
            showToast('Error', 'Failed to copy to clipboard', 'danger');
        }
    } catch (err) {
        console.error('Fallback copy failed: ', err);
        showToast('Error', 'Failed to copy to clipboard', 'danger');
    }
    
    document.body.removeChild(textArea);
}

// Export/Import functionality
function exportResults(results, filename) {
    const dataStr = JSON.stringify(results, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = filename || 'check-results.json';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function importFromFile(input, callback) {
    const file = input.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            const data = JSON.parse(e.target.result);
            callback(data);
        } catch (error) {
            showToast('Error', 'Invalid file format', 'danger');
        }
    };
    reader.readAsText(file);
}

// Loading state management
function setLoadingState(element, loading = true) {
    if (loading) {
        element.disabled = true;
        const originalText = element.textContent;
        element.dataset.originalText = originalText;
        element.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
    } else {
        element.disabled = false;
        element.textContent = element.dataset.originalText || 'Submit';
    }
}

// Progress tracking
function updateProgress(progressBar, percentage, text = '') {
    progressBar.style.width = percentage + '%';
    progressBar.setAttribute('aria-valuenow', percentage);
    
    if (text) {
        progressBar.textContent = text;
    }
}

// Form data helpers
function serializeFormData(form) {
    const formData = new FormData(form);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    return data;
}

function populateForm(form, data) {
    Object.keys(data).forEach(key => {
        const field = form.querySelector(`[name="${key}"]`);
        if (field) {
            field.value = data[key];
        }
    });
}

// Debug helpers
function debugLog(message, data = null) {
    if (window.location.hostname === 'localhost' || window.location.hostname.includes('replit')) {
        console.log(`[Debug] ${message}`, data);
    }
}

// Global error handler
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    
    // Show user-friendly error message
    showToast('Error', 'An unexpected error occurred. Please try again.', 'danger');
});

// Expose useful functions globally
window.EmailProxyChecker = {
    showNotification,
    showToast,
    copyToClipboard,
    exportResults,
    importFromFile,
    setLoadingState,
    updateProgress,
    isValidEmail,
    isValidProxy,
    debugLog
};

console.log('Email & Proxy Checker JavaScript loaded successfully');
