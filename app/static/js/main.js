// Main JavaScript file for Student Project Platform

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // File upload handling
    setupFileUpload();

    // Form validation
    setupFormValidation();

    // Search functionality
    setupSearch();
});

// File Upload Functionality
function setupFileUpload() {
    const fileUploadAreas = document.querySelectorAll('.file-upload-area');

    fileUploadAreas.forEach(function(area) {
        const fileInput = area.querySelector('input[type="file"]');

        if (fileInput) {
            // Click to upload
            area.addEventListener('click', function() {
                fileInput.click();
            });

            // Drag and drop
            area.addEventListener('dragover', function(e) {
                e.preventDefault();
                area.classList.add('dragover');
            });

            area.addEventListener('dragleave', function(e) {
                e.preventDefault();
                area.classList.remove('dragover');
            });

            area.addEventListener('drop', function(e) {
                e.preventDefault();
                area.classList.remove('dragover');

                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    fileInput.files = files;
                    handleFileSelect(files[0], area);
                }
            });

            // File input change
            fileInput.addEventListener('change', function(e) {
                if (e.target.files.length > 0) {
                    handleFileSelect(e.target.files[0], area);
                }
            });
        }
    });
}

function handleFileSelect(file, area) {
    const fileName = file.name;
    const fileSize = (file.size / 1024 / 1024).toFixed(2); // MB

    // Update UI to show selected file
    area.innerHTML = `
        <div class="text-success">
            <i class="fas fa-check-circle fa-2x mb-2"></i>
            <div><strong>${fileName}</strong></div>
            <div class="text-muted">${fileSize} MB</div>
        </div>
    `;
}

// Form Validation
function setupFormValidation() {
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

// Search Functionality
function setupSearch() {
    const searchInputs = document.querySelectorAll('.search-input');

    searchInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            const searchTerm = input.value.toLowerCase();
            const searchableItems = document.querySelectorAll('.searchable-item');

            searchableItems.forEach(function(item) {
                const text = item.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    });
}

// Utility Functions
function showLoading() {
    const loadingOverlay = document.createElement('div');
    loadingOverlay.className = 'spinner-overlay';
    loadingOverlay.innerHTML = `
        <div class="spinner-border spinner-border-lg text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
    `;
    document.body.appendChild(loadingOverlay);
}

function hideLoading() {
    const loadingOverlay = document.querySelector('.spinner-overlay');
    if (loadingOverlay) {
        loadingOverlay.remove();
    }
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(notification);

    // Auto-remove after 5 seconds
    setTimeout(function() {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// AJAX Helper Functions
function makeRequest(url, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        }
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    return fetch(url, options)
        .then(response => response.json())
        .catch(error => {
            console.error('Request failed:', error);
            throw error;
        });
}

// Project Management Functions
function claimProject(projectId) {
    showLoading();

    makeRequest(`/student/claim-project/${projectId}`, 'POST')
        .then(data => {
            hideLoading();
            if (data.success) {
                showNotification('Project claimed successfully!', 'success');
                location.reload();
            } else {
                showNotification(data.error || 'Failed to claim project', 'danger');
            }
        })
        .catch(error => {
            hideLoading();
            showNotification('An error occurred', 'danger');
        });
}

function approveProject(projectId, action) {
    const adminNotes = prompt('Add admin notes (optional):');

    showLoading();

    const formData = new FormData();
    formData.append('action', action);
    formData.append('admin_notes', adminNotes || '');

    fetch(`/admin/approve-project/${projectId}`, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        hideLoading();
        if (response.ok) {
            showNotification(`Project ${action}d successfully!`, 'success');
            location.reload();
        } else {
            showNotification('Failed to process request', 'danger');
        }
    })
    .catch(error => {
        hideLoading();
        showNotification('An error occurred', 'danger');
    });
}

// Real-time Updates (if needed)
function startRealTimeUpdates() {
    // This would connect to WebSocket or use Server-Sent Events
    // for real-time notifications and updates
    console.log('Real-time updates would be implemented here');
}

// Export functions for use in other scripts
window.StudentPlatform = {
    showLoading,
    hideLoading,
    showNotification,
    makeRequest,
    claimProject,
    approveProject
};
