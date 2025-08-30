// ClasifiCode - Main JavaScript Application

class ClasifiCodeApp {
    constructor() {
        this.apiBaseUrl = '/api';
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupAjaxDefaults();
        this.initializeComponents();
    }

    setupEventListeners() {
        // Form submissions
        document.addEventListener('submit', this.handleFormSubmit.bind(this));
        
        // Dynamic content loading
        document.addEventListener('click', this.handleDynamicClicks.bind(this));
        
        // Auto-save functionality
        this.setupAutoSave();
        
        // Search functionality
        this.setupSearch();
        
        // Modal handling
        this.setupModals();
    }

    setupAjaxDefaults() {
        // Add CSRF token to all AJAX requests
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        if (csrfToken) {
            $.ajaxSetup({
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });
        }
    }

    initializeComponents() {
        // Initialize tooltips
        if (typeof bootstrap !== 'undefined') {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }

        // Initialize popovers
        if (typeof bootstrap !== 'undefined') {
            const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
            popoverTriggerList.map(function (popoverTriggerEl) {
                return new bootstrap.Popover(popoverTriggerEl);
            });
        }

        // Initialize charts if Chart.js is available
        this.initializeCharts();
    }

    // Form handling
    handleFormSubmit(event) {
        const form = event.target;
        const formType = form.dataset.formType;

        switch (formType) {
            case 'classification':
                this.handleClassificationForm(event);
                break;
            case 'case':
                this.handleCaseForm(event);
                break;
            case 'login':
                this.handleLoginForm(event);
                break;
            case 'register':
                this.handleRegisterForm(event);
                break;
            default:
                // Default form handling
                break;
        }
    }

    async handleClassificationForm(event) {
        event.preventDefault();
        const form = event.target;
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;

        try {
            // Show loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="loading"></span> Clasificando...';

            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());

            const response = await fetch(`${this.apiBaseUrl}/classify`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                this.displayClassificationResults(result);
                this.showNotification('Clasificación completada exitosamente', 'success');
            } else {
                throw new Error(result.message || 'Error en la clasificación');
            }
        } catch (error) {
            console.error('Classification error:', error);
            this.showNotification(error.message, 'error');
        } finally {
            // Restore button state
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    }

    async handleCaseForm(event) {
        event.preventDefault();
        const form = event.target;
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        try {
            const response = await fetch(`${this.apiBaseUrl}/cases`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                this.showNotification('Caso creado exitosamente', 'success');
                // Redirect to case detail or list
                window.location.href = `/cases/${result.id}`;
            } else {
                throw new Error(result.message || 'Error al crear el caso');
            }
        } catch (error) {
            console.error('Case creation error:', error);
            this.showNotification(error.message, 'error');
        }
    }

    async handleLoginForm(event) {
        event.preventDefault();
        const form = event.target;
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        try {
            const response = await fetch(`${this.apiBaseUrl}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                this.showNotification('Inicio de sesión exitoso', 'success');
                // Redirect to dashboard
                window.location.href = '/dashboard';
            } else {
                throw new Error(result.message || 'Error en el inicio de sesión');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showNotification(error.message, 'error');
        }
    }

    async handleRegisterForm(event) {
        event.preventDefault();
        const form = event.target;
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        // Validate password confirmation
        if (data.password !== data.confirm_password) {
            this.showNotification('Las contraseñas no coinciden', 'error');
            return;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                this.showNotification('Registro exitoso', 'success');
                // Redirect to login
                window.location.href = '/login';
            } else {
                throw new Error(result.message || 'Error en el registro');
            }
        } catch (error) {
            console.error('Registration error:', error);
            this.showNotification(error.message, 'error');
        }
    }

    // Dynamic content handling
    handleDynamicClicks(event) {
        const target = event.target;

        // Handle candidate selection
        if (target.classList.contains('select-candidate')) {
            this.selectCandidate(target.dataset.candidateId);
        }

        // Handle case status changes
        if (target.classList.contains('change-status')) {
            this.changeCaseStatus(target.dataset.caseId, target.dataset.status);
        }

        // Handle pagination
        if (target.classList.contains('page-link')) {
            event.preventDefault();
            this.loadPage(target.href);
        }

        // Handle search
        if (target.classList.contains('search-btn')) {
            event.preventDefault();
            this.performSearch();
        }
    }

    // Classification results display
    displayClassificationResults(result) {
        const resultsContainer = document.getElementById('classification-results');
        if (!resultsContainer) return;

        const html = `
            <div class="classification-result">
                <div class="row">
                    <div class="col-md-8">
                        <h3>Mejor Candidato</h3>
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">${result.best_candidate.hs_code}</h5>
                                <p class="card-text">${result.best_candidate.description}</p>
                                <div class="confidence-bar">
                                    <div class="confidence-fill" style="width: ${result.best_candidate.confidence_score}%"></div>
                                </div>
                                <p class="mt-2">Confianza: ${result.best_candidate.confidence_score}%</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <h4>Estadísticas</h4>
                        <div class="stats-card">
                            <div class="number">${result.statistics.total_candidates}</div>
                            <div class="label">Candidatos</div>
                        </div>
                        <div class="stats-card">
                            <div class="number">${result.statistics.processing_time}ms</div>
                            <div class="label">Tiempo</div>
                        </div>
                    </div>
                </div>
                
                <h4 class="mt-4">Todos los Candidatos</h4>
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>Código HS</th>
                                <th>Descripción</th>
                                <th>Confianza</th>
                                <th>Método</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${result.candidates.map(candidate => `
                                <tr>
                                    <td><strong>${candidate.hs_code}</strong></td>
                                    <td>${candidate.description}</td>
                                    <td>
                                        <div class="progress">
                                            <div class="progress-bar" style="width: ${candidate.confidence_score}%">
                                                ${candidate.confidence_score}%
                                            </div>
                                        </div>
                                    </td>
                                    <td><span class="badge bg-info">${candidate.classification_method}</span></td>
                                    <td>
                                        <button class="btn btn-sm btn-primary select-candidate" 
                                                data-candidate-id="${candidate.id}">
                                            Seleccionar
                                        </button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        resultsContainer.innerHTML = html;
        resultsContainer.style.display = 'block';
    }

    // Auto-save functionality
    setupAutoSave() {
        const forms = document.querySelectorAll('form[data-auto-save]');
        forms.forEach(form => {
            const inputs = form.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                input.addEventListener('change', () => {
                    this.autoSaveForm(form);
                });
            });
        });
    }

    async autoSaveForm(form) {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        const formId = form.dataset.formId;

        try {
            await fetch(`${this.apiBaseUrl}/auto-save`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    form_id: formId,
                    data: data
                })
            });
        } catch (error) {
            console.error('Auto-save error:', error);
        }
    }

    // Search functionality
    setupSearch() {
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.performSearch(e.target.value);
                }, 500);
            });
        }
    }

    async performSearch(query = null) {
        const searchInput = document.getElementById('search-input');
        const searchTerm = query || searchInput?.value;

        if (!searchTerm) return;

        try {
            const response = await fetch(`${this.apiBaseUrl}/search?q=${encodeURIComponent(searchTerm)}`);
            const results = await response.json();

            this.displaySearchResults(results);
        } catch (error) {
            console.error('Search error:', error);
            this.showNotification('Error en la búsqueda', 'error');
        }
    }

    displaySearchResults(results) {
        const resultsContainer = document.getElementById('search-results');
        if (!resultsContainer) return;

        if (results.length === 0) {
            resultsContainer.innerHTML = '<p class="text-muted">No se encontraron resultados</p>';
            return;
        }

        const html = results.map(result => `
            <div class="card mb-3">
                <div class="card-body">
                    <h5 class="card-title">${result.title}</h5>
                    <p class="card-text">${result.description}</p>
                    <a href="${result.url}" class="btn btn-primary btn-sm">Ver más</a>
                </div>
            </div>
        `).join('');

        resultsContainer.innerHTML = html;
    }

    // Modal handling
    setupModals() {
        const modalTriggers = document.querySelectorAll('[data-bs-toggle="modal"]');
        modalTriggers.forEach(trigger => {
            trigger.addEventListener('click', (e) => {
                const modalId = trigger.dataset.bsTarget;
                const modal = document.querySelector(modalId);
                if (modal) {
                    const modalInstance = new bootstrap.Modal(modal);
                    modalInstance.show();
                }
            });
        });
    }

    // Utility functions
    showNotification(message, type = 'info') {
        const alertClass = `alert-${type}`;
        const alertHtml = `
            <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;

        const container = document.getElementById('notifications') || document.body;
        const alertElement = document.createElement('div');
        alertElement.innerHTML = alertHtml;
        container.appendChild(alertElement.firstElementChild);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = container.querySelector('.alert');
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    }

    async loadPage(url) {
        try {
            const response = await fetch(url);
            const html = await response.text();
            
            // Update the main content area
            const mainContent = document.querySelector('main') || document.getElementById('main-content');
            if (mainContent) {
                mainContent.innerHTML = html;
            }
            
            // Update URL without page reload
            window.history.pushState({}, '', url);
        } catch (error) {
            console.error('Page load error:', error);
            this.showNotification('Error al cargar la página', 'error');
        }
    }

    // Chart initialization
    initializeCharts() {
        if (typeof Chart === 'undefined') return;

        // Dashboard charts
        this.initializeDashboardCharts();
        
        // Classification charts
        this.initializeClassificationCharts();
    }

    initializeDashboardCharts() {
        const ctx = document.getElementById('casesChart');
        if (ctx) {
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
                    datasets: [{
                        label: 'Casos Procesados',
                        data: [12, 19, 3, 5, 2, 3],
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
    }

    initializeClassificationCharts() {
        const ctx = document.getElementById('confidenceChart');
        if (ctx) {
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Alta', 'Media', 'Baja'],
                    datasets: [{
                        data: [70, 20, 10],
                        backgroundColor: [
                            'rgb(75, 192, 192)',
                            'rgb(255, 205, 86)',
                            'rgb(255, 99, 132)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
    }

    // API helper methods
    async apiCall(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            }
        };

        const finalOptions = { ...defaultOptions, ...options };

        try {
            const response = await fetch(`${this.apiBaseUrl}${endpoint}`, finalOptions);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'API Error');
            }

            return data;
        } catch (error) {
            console.error('API call error:', error);
            throw error;
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.clasifiCodeApp = new ClasifiCodeApp();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ClasifiCodeApp;
}
