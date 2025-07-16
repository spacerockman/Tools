/**
 * PDF Unlock Pro - Modern Web Application
 * Advanced JavaScript with 2025 UX patterns
 */

class PDFUnlockApp {
    constructor() {
        this.currentJobId = null;
        this.progressInterval = null;
        this.startTime = null;
        this.isProcessing = false;
        
        this.initializeElements();
        this.bindEvents();
        this.initializeAnimations();
    }

    initializeElements() {
        // Form elements
        this.uploadForm = document.getElementById('uploadForm');
        this.fileInput = document.getElementById('fileInput');
        this.fileUploadArea = document.getElementById('fileUploadArea');
        this.fileInfo = document.getElementById('fileInfo');
        this.fileName = document.getElementById('fileName');
        this.fileSize = document.getElementById('fileSize');
        this.removeFileBtn = document.getElementById('removeFile');
        this.submitBtn = document.getElementById('submitBtn');
        
        // Method selection
        this.methodRadios = document.querySelectorAll('input[name="method"]');
        this.passwordSection = document.getElementById('passwordSection');
        this.passwordInput = document.getElementById('passwordInput');
        this.togglePasswordBtn = document.getElementById('togglePassword');
        
        // Progress elements
        this.progressSection = document.getElementById('progressSection');
        this.progressStatus = document.getElementById('progressStatus');
        this.progressFill = document.getElementById('progressFill');
        this.progressPercentage = document.getElementById('progressPercentage');
        this.progressMessage = document.getElementById('progressMessage');
        this.elapsedTime = document.getElementById('elapsedTime');
        
        // Result elements
        this.resultSection = document.getElementById('resultSection');
        this.successResult = document.getElementById('successResult');
        this.errorResult = document.getElementById('errorResult');
        this.errorMessage = document.getElementById('errorMessage');
        this.downloadBtn = document.getElementById('downloadBtn');
        this.newFileBtn = document.getElementById('newFileBtn');
        this.retryBtn = document.getElementById('retryBtn');
    }

    bindEvents() {
        // File upload events
        this.fileUploadArea.addEventListener('click', () => this.fileInput.click());
        this.fileUploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
        this.fileUploadArea.addEventListener('dragleave', this.handleDragLeave.bind(this));
        this.fileUploadArea.addEventListener('drop', this.handleFileDrop.bind(this));
        this.fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        this.removeFileBtn.addEventListener('click', this.removeFile.bind(this));
        
        // Method selection
        this.methodRadios.forEach(radio => {
            radio.addEventListener('change', this.handleMethodChange.bind(this));
        });
        
        // Password toggle
        this.togglePasswordBtn.addEventListener('click', this.togglePasswordVisibility.bind(this));
        
        // Form submission
        this.uploadForm.addEventListener('submit', this.handleFormSubmit.bind(this));
        
        // Result actions
        this.downloadBtn.addEventListener('click', this.downloadFile.bind(this));
        this.newFileBtn.addEventListener('click', this.resetApp.bind(this));
        this.retryBtn.addEventListener('click', this.resetToUpload.bind(this));
        
        // Keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyboardShortcuts.bind(this));
    }

    initializeAnimations() {
        // Add entrance animations
        this.animateOnScroll();
        this.initializeParticles();
    }

    handleDragOver(e) {
        e.preventDefault();
        this.fileUploadArea.classList.add('drag-over');
    }

    handleDragLeave(e) {
        e.preventDefault();
        this.fileUploadArea.classList.remove('drag-over');
    }

    handleFileDrop(e) {
        e.preventDefault();
        this.fileUploadArea.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }

    handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            this.processFile(file);
        }
    }

    processFile(file) {
        // Validate file
        if (!file.type.includes('pdf')) {
            this.showNotification('Please select a PDF file', 'error');
            return;
        }

        if (file.size > 50 * 1024 * 1024) {
            this.showNotification('File size must be less than 50MB', 'error');
            return;
        }

        // Display file info
        this.fileName.textContent = file.name;
        this.fileSize.textContent = this.formatFileSize(file.size);
        this.fileUploadArea.style.display = 'none';
        this.fileInfo.style.display = 'block';
        this.submitBtn.disabled = false;

        // Add file to form data
        this.selectedFile = file;
        
        // Animate file info appearance
        this.fileInfo.style.opacity = '0';
        this.fileInfo.style.transform = 'translateY(20px)';
        setTimeout(() => {
            this.fileInfo.style.transition = 'all 0.3s ease';
            this.fileInfo.style.opacity = '1';
            this.fileInfo.style.transform = 'translateY(0)';
        }, 100);
    }

    removeFile() {
        this.selectedFile = null;
        this.fileInput.value = '';
        this.fileInfo.style.display = 'none';
        this.fileUploadArea.style.display = 'flex';
        this.submitBtn.disabled = true;
    }

    handleMethodChange(e) {
        const method = e.target.value;
        if (method === 'password') {
            this.passwordSection.style.display = 'block';
            this.passwordInput.focus();
        } else {
            this.passwordSection.style.display = 'none';
        }
    }

    togglePasswordVisibility() {
        const type = this.passwordInput.type === 'password' ? 'text' : 'password';
        this.passwordInput.type = type;
        
        const icon = this.togglePasswordBtn.querySelector('i');
        icon.className = type === 'password' ? 'fas fa-eye' : 'fas fa-eye-slash';
    }

    async handleFormSubmit(e) {
        e.preventDefault();
        
        if (!this.selectedFile || this.isProcessing) return;
        
        this.isProcessing = true;
        this.startTime = Date.now();
        
        // Prepare form data
        const formData = new FormData();
        formData.append('file', this.selectedFile);
        
        const method = document.querySelector('input[name="method"]:checked').value;
        formData.append('use_crack', method === 'crack' ? 'true' : 'false');
        
        if (method === 'password') {
            formData.append('password', this.passwordInput.value);
        }
        
        // Get advanced options
        const removeWatermark = document.querySelector('input[name="remove_watermark"]').checked;
        const optimizePdf = document.querySelector('input[name="optimize_pdf"]').checked;
        
        formData.append('remove_watermark', removeWatermark ? 'true' : 'false');
        formData.append('optimize_pdf', optimizePdf ? 'true' : 'false');
        
        // Show progress section
        this.showProgressSection();
        
        try {
            // Upload file
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.currentJobId = result.job_id;
                this.startProgressPolling();
            } else {
                throw new Error(result.error || 'Upload failed');
            }
        } catch (error) {
            this.showError(error.message);
        }
    }

    showProgressSection() {
        document.getElementById('uploadSection').style.display = 'none';
        this.progressSection.style.display = 'block';
        
        // Animate progress section
        this.progressSection.style.opacity = '0';
        this.progressSection.style.transform = 'translateY(30px)';
        setTimeout(() => {
            this.progressSection.style.transition = 'all 0.5s ease';
            this.progressSection.style.opacity = '1';
            this.progressSection.style.transform = 'translateY(0)';
        }, 100);
    }

    startProgressPolling() {
        this.updateElapsedTime();
        
        this.progressInterval = setInterval(async () => {
            try {
                const response = await fetch(`/status/${this.currentJobId}`);
                const status = await response.json();
                
                if (response.ok) {
                    this.updateProgress(status);
                    
                    if (status.status === 'completed') {
                        this.showSuccess();
                    } else if (status.status === 'failed') {
                        this.showError(status.error || 'Processing failed');
                    }
                } else {
                    throw new Error(status.error || 'Status check failed');
                }
            } catch (error) {
                this.showError(error.message);
            }
        }, 1000);
    }

    updateProgress(status) {
        const progress = status.progress || 0;
        const message = status.message || 'Processing...';
        
        // Update progress bar with animation
        this.progressFill.style.width = `${progress}%`;
        this.progressPercentage.textContent = `${progress}%`;
        this.progressMessage.textContent = message;
        this.progressStatus.textContent = this.getStatusText(status.status);
        
        // Add pulse effect for active processing
        if (status.status === 'processing') {
            this.progressFill.classList.add('pulse');
        } else {
            this.progressFill.classList.remove('pulse');
        }
    }

    updateElapsedTime() {
        const timeInterval = setInterval(() => {
            if (!this.isProcessing) {
                clearInterval(timeInterval);
                return;
            }
            
            const elapsed = Date.now() - this.startTime;
            const minutes = Math.floor(elapsed / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            this.elapsedTime.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }

    getStatusText(status) {
        const statusMap = {
            'queued': 'Queued',
            'processing': 'Processing',
            'completed': 'Completed',
            'failed': 'Failed'
        };
        return statusMap[status] || 'Unknown';
    }

    showSuccess() {
        this.stopProcessing();
        this.progressSection.style.display = 'none';
        this.resultSection.style.display = 'block';
        this.successResult.style.display = 'block';
        this.errorResult.style.display = 'none';
        
        // Animate success
        this.animateResult();
        this.showNotification('PDF successfully unlocked!', 'success');
    }

    showError(message) {
        this.stopProcessing();
        this.progressSection.style.display = 'none';
        this.resultSection.style.display = 'block';
        this.successResult.style.display = 'none';
        this.errorResult.style.display = 'block';
        this.errorMessage.textContent = message;
        
        // Animate error
        this.animateResult();
        this.showNotification(message, 'error');
    }

    animateResult() {
        this.resultSection.style.opacity = '0';
        this.resultSection.style.transform = 'scale(0.9)';
        setTimeout(() => {
            this.resultSection.style.transition = 'all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)';
            this.resultSection.style.opacity = '1';
            this.resultSection.style.transform = 'scale(1)';
        }, 100);
    }

    stopProcessing() {
        this.isProcessing = false;
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
    }

    async downloadFile() {
        if (!this.currentJobId) return;
        
        try {
            const response = await fetch(`/download/${this.currentJobId}`);
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `unlocked_${this.selectedFile.name}`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.showNotification('Download started!', 'success');
            } else {
                const error = await response.json();
                throw new Error(error.error || 'Download failed');
            }
        } catch (error) {
            this.showNotification(error.message, 'error');
        }
    }

    resetApp() {
        this.stopProcessing();
        this.currentJobId = null;
        this.removeFile();
        this.passwordInput.value = '';
        this.passwordSection.style.display = 'none';
        document.querySelector('input[name="method"][value="crack"]').checked = true;
        
        // Show upload section
        document.getElementById('uploadSection').style.display = 'block';
        this.progressSection.style.display = 'none';
        this.resultSection.style.display = 'none';
        
        // Animate return to upload
        document.getElementById('uploadSection').style.opacity = '0';
        setTimeout(() => {
            document.getElementById('uploadSection').style.transition = 'all 0.3s ease';
            document.getElementById('uploadSection').style.opacity = '1';
        }, 100);
    }

    resetToUpload() {
        this.resetApp();
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas ${this.getNotificationIcon(type)}"></i>
                <span>${message}</span>
            </div>
            <button class="notification-close">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        // Auto remove
        setTimeout(() => {
            this.removeNotification(notification);
        }, 5000);
        
        // Close button
        notification.querySelector('.notification-close').addEventListener('click', () => {
            this.removeNotification(notification);
        });
    }

    removeNotification(notification) {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }

    getNotificationIcon(type) {
        const icons = {
            'success': 'fa-check-circle',
            'error': 'fa-exclamation-circle',
            'warning': 'fa-exclamation-triangle',
            'info': 'fa-info-circle'
        };
        return icons[type] || icons.info;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + U for upload
        if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
            e.preventDefault();
            if (!this.isProcessing) {
                this.fileInput.click();
            }
        }
        
        // Escape to reset
        if (e.key === 'Escape' && !this.isProcessing) {
            this.resetApp();
        }
    }

    animateOnScroll() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, { threshold: 0.1 });

        document.querySelectorAll('.upload-card, .method-option, .result-card').forEach(el => {
            observer.observe(el);
        });
    }

    initializeParticles() {
        // Add subtle particle animation to background
        const canvas = document.createElement('canvas');
        canvas.id = 'particles';
        canvas.style.position = 'fixed';
        canvas.style.top = '0';
        canvas.style.left = '0';
        canvas.style.width = '100%';
        canvas.style.height = '100%';
        canvas.style.pointerEvents = 'none';
        canvas.style.zIndex = '-1';
        canvas.style.opacity = '0.3';
        
        document.body.appendChild(canvas);
        
        const ctx = canvas.getContext('2d');
        const particles = [];
        
        const resizeCanvas = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };
        
        const createParticle = () => ({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            vx: (Math.random() - 0.5) * 0.5,
            vy: (Math.random() - 0.5) * 0.5,
            size: Math.random() * 2 + 1,
            opacity: Math.random() * 0.5 + 0.2
        });
        
        const animate = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            particles.forEach(particle => {
                particle.x += particle.vx;
                particle.y += particle.vy;
                
                if (particle.x < 0 || particle.x > canvas.width) particle.vx *= -1;
                if (particle.y < 0 || particle.y > canvas.height) particle.vy *= -1;
                
                ctx.beginPath();
                ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(102, 126, 234, ${particle.opacity})`;
                ctx.fill();
            });
            
            requestAnimationFrame(animate);
        };
        
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);
        
        // Create particles
        for (let i = 0; i < 50; i++) {
            particles.push(createParticle());
        }
        
        animate();
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PDFUnlockApp();
});

// Add some global utility functions
window.PDFUnlockUtils = {
    // Smooth scroll to element
    scrollTo: (elementId) => {
        const element = document.getElementById(elementId);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth' });
        }
    },
    
    // Copy text to clipboard
    copyToClipboard: async (text) => {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            return false;
        }
    }
};