// General JavaScript functions

// Flash message auto-hide
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.remove();
            }, 300);
        }, 5000);
    });
});

// Confirm delete actions
function confirmDelete(message = 'Are you sure you want to delete this item?') {
    return confirm(message);
}

// File upload validation
function validateFileUpload(input, allowedTypes = ['.pdf']) {
    const file = input.files[0];
    if (!file) return true;
    
    const fileName = file.name.toLowerCase();
    const isValidType = allowedTypes.some(type => fileName.endsWith(type));
    
    if (!isValidType) {
        alert(`Please select a valid file type: ${allowedTypes.join(', ')}`);
        input.value = '';
        return false;
    }
    
    const maxSize = 16 * 1024 * 1024; // 16MB
    if (file.size > maxSize) {
        alert('File size must be less than 16MB');
        input.value = '';
        return false;
    }
    
    return true;
}

// Add file validation to PDF upload inputs
document.addEventListener('DOMContentLoaded', function() {
    const pdfInputs = document.querySelectorAll('input[type="file"][accept=".pdf"]');
    pdfInputs.forEach(input => {
        input.addEventListener('change', function() {
            validateFileUpload(this, ['.pdf']);
        });
    });
});

// Quiz timer (optional feature)
class QuizTimer {
    constructor(duration, onTimeUp) {
        this.duration = duration; // in minutes
        this.onTimeUp = onTimeUp;
        this.timeLeft = duration * 60; // in seconds
        this.timer = null;
    }
    
    start() {
        this.timer = setInterval(() => {
            this.timeLeft--;
            this.updateDisplay();
            
            if (this.timeLeft <= 0) {
                this.stop();
                this.onTimeUp();
            }
        }, 1000);
    }
    
    stop() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }
    
    updateDisplay() {
        const minutes = Math.floor(this.timeLeft / 60);
        const seconds = this.timeLeft % 60;
        const display = document.getElementById('timer-display');
        if (display) {
            display.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
    }
}

// Export functions for use in templates
window.QuizTimer = QuizTimer;
window.confirmDelete = confirmDelete;
window.validateFileUpload = validateFileUpload;