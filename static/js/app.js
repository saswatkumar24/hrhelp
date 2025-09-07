// HR Resume Analyzer - Main JavaScript

// Global variables
let currentSessionId = null;
let isProcessing = false;

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    console.log('Initializing HR Resume Analyzer...');
    
    // Set up drag and drop for file upload
    setupDragAndDrop();
    
    // Set up keyboard shortcuts
    setupKeyboardShortcuts();
    
    // Check for existing session
    checkInitialStatus();
}

// Drag and drop functionality
function setupDragAndDrop() {
    const fileInput = document.getElementById('fileInput');
    const uploadForm = document.getElementById('uploadForm');
    
    if (!fileInput || !uploadForm) return;
    
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadForm.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    // Highlight drop area when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadForm.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadForm.addEventListener(eventName, unhighlight, false);
    });
    
    // Handle dropped files
    uploadForm.addEventListener('drop', handleDrop, false);
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight(e) {
        uploadForm.classList.add('dragover');
    }
    
    function unhighlight(e) {
        uploadForm.classList.remove('dragover');
    }
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        fileInput.files = files;
        updateFileInputDisplay(files);
    }
}

// Keyboard shortcuts
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + Enter to send chat message
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            const messageInput = document.getElementById('messageInput');
            if (messageInput && !messageInput.disabled && messageInput.value.trim()) {
                document.getElementById('chatForm').dispatchEvent(new Event('submit'));
            }
        }
        
        // Escape to clear current input
        if (e.key === 'Escape') {
            const messageInput = document.getElementById('messageInput');
            if (messageInput) {
                messageInput.value = '';
                messageInput.blur();
            }
        }
    });
}

// File input display helper
function updateFileInputDisplay(files) {
    const fileInput = document.getElementById('fileInput');
    if (!fileInput) return;
    
    if (files && files.length > 0) {
        const fileNames = Array.from(files).map(file => file.name).join(', ');
        console.log(`Files selected: ${fileNames}`);
        
        // Create visual feedback for selected files
        showSelectedFiles(files);
    }
}

function showSelectedFiles(files) {
    const existingDisplay = document.getElementById('selectedFilesDisplay');
    if (existingDisplay) {
        existingDisplay.remove();
    }
    
    const fileInput = document.getElementById('fileInput');
    const display = document.createElement('div');
    display.id = 'selectedFilesDisplay';
    display.className = 'mt-2 p-3 bg-light rounded';
    
    let html = `<h6><i class="fas fa-files me-2"></i>Selected Files (${files.length}):</h6><ul class="mb-0">`;
    
    Array.from(files).forEach(file => {
        const sizeStr = formatFileSize(file.size);
        const icon = getFileIcon(file.name);
        html += `<li class="d-flex justify-content-between align-items-center mb-1">
            <span><i class="${icon} me-2"></i>${file.name}</span>
            <small class="text-muted">${sizeStr}</small>
        </li>`;
    });
    
    html += '</ul>';
    display.innerHTML = html;
    
    fileInput.parentNode.insertBefore(display, fileInput.nextSibling);
}

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    switch (ext) {
        case 'pdf':
            return 'fas fa-file-pdf text-danger';
        case 'doc':
        case 'docx':
            return 'fas fa-file-word text-primary';
        case 'zip':
        case 'rar':
            return 'fas fa-file-archive text-warning';
        default:
            return 'fas fa-file text-secondary';
    }
}

// Session management
function setSessionId(sessionId) {
    currentSessionId = sessionId;
    localStorage.setItem('hrAnalyzerSessionId', sessionId);
}

function getSessionId() {
    return currentSessionId || localStorage.getItem('hrAnalyzerSessionId');
}

function clearSessionId() {
    currentSessionId = null;
    localStorage.removeItem('hrAnalyzerSessionId');
}

// Status checking
async function checkInitialStatus() {
    try {
        const response = await fetch('/status');
        const result = await response.json();
        
        if (result.success && result.session_active) {
            currentSessionId = result.session_id;
            console.log(`Found existing session: ${result.resumes_loaded} resumes loaded`);
        }
    } catch (error) {
        console.log('No existing session found');
    }
}

// Enhanced error handling
function handleError(error, context = '') {
    console.error(`Error in ${context}:`, error);
    
    let message = 'An unexpected error occurred.';
    
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
        message = 'Unable to connect to the server. Please check your connection.';
    } else if (error.message) {
        message = error.message;
    }
    
    showAlert(message, 'danger');
}

// Loading state management
function setLoadingState(element, isLoading) {
    if (!element) return;
    
    if (isLoading) {
        element.disabled = true;
        element.classList.add('loading');
        
        // Add spinner to button if it's a button
        if (element.tagName === 'BUTTON') {
            const originalText = element.innerHTML;
            element.setAttribute('data-original-text', originalText);
            element.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
        }
    } else {
        element.disabled = false;
        element.classList.remove('loading');
        
        // Restore original button text
        if (element.tagName === 'BUTTON' && element.getAttribute('data-original-text')) {
            element.innerHTML = element.getAttribute('data-original-text');
            element.removeAttribute('data-original-text');
        }
    }
}

// Enhanced alert system with auto-dismiss and positioning
function showAlert(message, type = 'info', autoDismiss = true) {
    const alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) return;
    
    const alertId = 'alert_' + Date.now();
    const alertDiv = document.createElement('div');
    alertDiv.id = alertId;
    alertDiv.className = `alert alert-${type} alert-dismissible fade show slide-up`;
    alertDiv.style.position = 'relative';
    alertDiv.style.zIndex = '1050';
    
    const icon = getAlertIcon(type);
    alertDiv.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="${icon} me-2"></i>
            <div class="flex-grow-1">${message}</div>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    alertContainer.appendChild(alertDiv);
    
    // Auto-dismiss after delay
    if (autoDismiss) {
        const dismissDelay = type === 'danger' ? 8000 : 5000;
        setTimeout(() => {
            if (alertDiv && alertDiv.parentNode) {
                alertDiv.classList.remove('show');
                setTimeout(() => {
                    if (alertDiv.parentNode) {
                        alertDiv.remove();
                    }
                }, 150);
            }
        }, dismissDelay);
    }
    
    return alertId;
}

function getAlertIcon(type) {
    switch (type) {
        case 'success':
            return 'fas fa-check-circle';
        case 'danger':
        case 'error':
            return 'fas fa-exclamation-triangle';
        case 'warning':
            return 'fas fa-exclamation-circle';
        case 'info':
            return 'fas fa-info-circle';
        default:
            return 'fas fa-bell';
    }
}

// Chat message formatting
function formatMessage(text) {
    // Convert newlines to <br> tags
    text = text.replace(/\n/g, '<br>');
    
    // Make URLs clickable
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    text = text.replace(urlRegex, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');
    
    // Format code blocks
    text = text.replace(/`([^`]+)`/g, '<code class="bg-light px-1 rounded">$1</code>');
    
    // Format bold text
    text = text.replace(/\*\*([^\*]+)\*\*/g, '<strong>$1</strong>');
    
    return text;
}

// Performance monitoring
function measurePerformance(name, fn) {
    return async function(...args) {
        const startTime = performance.now();
        try {
            const result = await fn.apply(this, args);
            const endTime = performance.now();
            console.log(`${name} took ${(endTime - startTime).toFixed(2)} milliseconds`);
            return result;
        } catch (error) {
            const endTime = performance.now();
            console.log(`${name} failed after ${(endTime - startTime).toFixed(2)} milliseconds`);
            throw error;
        }
    };
}

// Local storage utilities
function saveToStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
        return true;
    } catch (error) {
        console.warn('Failed to save to localStorage:', error);
        return false;
    }
}

function loadFromStorage(key, defaultValue = null) {
    try {
        const data = localStorage.getItem(key);
        return data ? JSON.parse(data) : defaultValue;
    } catch (error) {
        console.warn('Failed to load from localStorage:', error);
        return defaultValue;
    }
}

// Debounce utility for input handling
function debounce(func, wait, immediate = false) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}

// Copy text to clipboard
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showAlert('Copied to clipboard!', 'success');
        return true;
    } catch (error) {
        console.warn('Failed to copy to clipboard:', error);
        
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            textArea.remove();
            showAlert('Copied to clipboard!', 'success');
            return true;
        } catch (err) {
            textArea.remove();
            showAlert('Failed to copy to clipboard', 'warning');
            return false;
        }
    }
}

// Export functions for use in templates
window.hrAnalyzer = {
    showAlert,
    copyToClipboard,
    formatMessage,
    setLoadingState,
    handleError,
    formatFileSize,
    getFileIcon
};
