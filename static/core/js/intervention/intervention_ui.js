// static/core/js/intervention/intervention_ui.js
// Gestionnaire de l'interface utilisateur pour l'exécution d'intervention

class InterventionUI {
    constructor() {
        this.autoSaveTimer = null;
        this.autoSaveInterval = 30000; // 30 secondes
        this.ordreTravailiId = null;
        this.csrfToken = null;
        this.isDirty = false;
        
        this.init();
    }
    
    init() {
        // Récupérer les données depuis le DOM
        const metaData = document.getElementById('intervention-meta-data');
        if (metaData) {
            this.ordreTravailiId = metaData.dataset.ordreId;
            this.csrfToken = metaData.dataset.csrfToken;
        }
        
        this.setupEventListeners();
        this.initializeCollapses();
        this.setupAutoSave();
        this.loadPersistedData();
        this.updateProgress();
    }
    
    setupEventListeners() {
        // Écouter les changements dans le formulaire pour l'auto-save
        const formInputs = document.querySelectorAll('#execution-form input, #execution-form select, #execution-form textarea');
        
        formInputs.forEach(input => {
            input.addEventListener('change', () => {
                this.isDirty = true;
                this.triggerAutoSave();
                this.updateProgress();
            });
            input.addEventListener('input', () => {
                this.isDirty = true;
                this.triggerAutoSave();
            });
        });
        
        // Validation avant finalisation
        const finaliseButton = document.querySelector('button[onclick="showConfirmModal()"]');
        if (finaliseButton) {
            finaliseButton.addEventListener('click', (e) => {
                if (!this.validateRequiredFields()) {
                    e.preventDefault();
                    e.stopPropagation();
                    return false;
                }
            });
        }
        
        // Drag & Drop pour les fichiers
        this.setupDragAndDrop();
        
        // Gestionnaire pour fermer les modals avec Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
        });
    }
    
    // ========================================
    // GESTION DES COLLAPSES
    // ========================================
    
    initializeCollapses() {
        // Auto-collapse des opérations sauf la première
        const operations = document.querySelectorAll('[id^="operation-content-"]');
        operations.forEach((op, index) => {
            if (index > 0) {
                this.collapseElement(op.id);
            }
        });
    }
    
    toggleCollapse(elementId) {
        const element = document.getElementById(elementId);
        const chevron = document.getElementById('chevron-' + elementId);
        
        if (element && chevron) {
            const isHidden = element.style.display === 'none' || element.classList.contains('hidden');
            
            if (isHidden) {
                this.expandElement(elementId);
            } else {
                this.collapseElement(elementId);
            }
        }
    }
    
    expandElement(elementId) {
        const element = document.getElementById(elementId);
        const chevron = document.getElementById('chevron-' + elementId);
        
        if (element) {
            element.style.display = 'block';
            element.classList.remove('hidden');
        }
        if (chevron) {
            chevron.style.transform = 'rotate(180deg)';
        }
    }
    
    collapseElement(elementId) {
        const element = document.getElementById(elementId);
        const chevron = document.getElementById('chevron-' + elementId);
        
        if (element) {
            element.style.display = 'none';
            element.classList.add('hidden');
        }
        if (chevron) {
            chevron.style.transform = 'rotate(0deg)';
        }
    }
    
    // ========================================
    // AUTO-SAVE
    // ========================================
    
    setupAutoSave() {
        // Démarrer l'auto-save si configuré
        if (this.autoSaveInterval > 0) {
            this.triggerAutoSave();
        }
    }
    
    triggerAutoSave() {
        // Annuler le timer précédent
        if (this.autoSaveTimer) {
            clearTimeout(this.autoSaveTimer);
        }
        
        // Programmer la sauvegarde
        this.autoSaveTimer = setTimeout(() => {
            this.performAutoSave();
        }, this.autoSaveInterval);
    }
    
    performAutoSave() {
        if (!this.isDirty || !this.ordreTravailiId) {
            return;
        }
        
        const formData = this.collectFormData();
        
        // Sauvegarder localement
        this.saveToLocalStorage(formData);
        
        // Optionnel: sauvegarder sur le serveur
        this.saveToServer(formData);
    }
    
    collectFormData() {
        const form = document.getElementById('execution-form');
        if (!form) return {};
        
        const formData = new FormData(form);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }
        
        return data;
    }
    
    saveToLocalStorage(data) {
        try {
            const storageKey = `intervention_draft_${this.ordreTravailiId}`;
            const storageData = {
                data: data,
                timestamp: new Date().toISOString(),
                progress: this.calculateProgress()
            };
            localStorage.setItem(storageKey, JSON.stringify(storageData));
        } catch (e) {
            console.warn('Impossible de sauvegarder en local:', e);
        }
    }
    
    loadPersistedData() {
        try {
            const storageKey = `intervention_draft_${this.ordreTravailiId}`;
            const savedData = localStorage.getItem(storageKey);
            
            if (savedData) {
                const parsedData = JSON.parse(savedData);
                this.restoreFormData(parsedData.data);
                this.updateProgress();
            }
        } catch (e) {
            console.warn('Impossible de charger les données sauvegardées:', e);
        }
    }
    
    restoreFormData(data) {
        if (!data) return;
        
        Object.keys(data).forEach(key => {
            const field = document.querySelector(`[name="${key}"]`);
            if (field) {
                if (field.type === 'checkbox') {
                    field.checked = !!data[key];
                } else {
                    field.value = data[key];
                }
            }
        });
    }
    
    saveToServer(data) {
        const metaData = document.getElementById('intervention-meta-data');
        const saveUrl = metaData?.dataset?.autoSaveUrl;
        
        if (!saveUrl) return;
        
        fetch(saveUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.csrfToken,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                this.showConnectionStatus('online');
                this.isDirty = false;
            }
        })
        .catch(error => {
            console.warn('Erreur sauvegarde serveur:', error);
            this.showConnectionStatus('offline');
        });
    }
    
    // ========================================
    // PROGRESSION
    // ========================================
    
    updateProgress() {
        const progress = this.calculateProgress();
        this.displayProgress(progress);
    }
    
    calculateProgress() {
        const allFields = document.querySelectorAll('[data-point-id]');
        let totalFields = 0;
        let completedFields = 0;
        
        allFields.forEach(container => {
            const inputs = container.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                totalFields++;
                if (this.isFieldCompleted(input)) {
                    completedFields++;
                }
            });
        });
        
        return {
            total: totalFields,
            completed: completedFields,
            percentage: totalFields > 0 ? (completedFields / totalFields) * 100 : 0
        };
    }
    
    isFieldCompleted(field) {
        if (field.type === 'checkbox') {
            return true; // Les checkboxes sont toujours considérées comme complétées
        }
        
        const value = field.value?.trim();
        return value && value !== '';
    }
    
    displayProgress(progress) {
        // Barre de progression
        const progressBar = document.getElementById('progress-bar');
        const progressText = document.getElementById('progress-text');
        const completionStatus = document.getElementById('completion-status');
        
        if (progressBar) {
            progressBar.style.width = progress.percentage + '%';
        }
        
        if (progressText) {
            progressText.textContent = Math.round(progress.percentage) + '%';
        }
        
        if (completionStatus) {
            completionStatus.textContent = `${progress.completed} sur ${progress.total} points complétés`;
        }
    }
    
    // ========================================
    // VALIDATION
    // ========================================
    
    validateRequiredFields() {
        const requiredFields = document.querySelectorAll('[required]');
        const errors = [];
        
        requiredFields.forEach(field => {
            if (!this.isFieldValid(field)) {
                const label = this.getFieldLabel(field);
                errors.push(label || 'Champ requis');
                this.highlightFieldError(field);
            } else {
                this.clearFieldError(field);
            }
        });
        
        if (errors.length > 0) {
            this.showValidationErrors(errors);
            return false;
        }
        
        return true;
    }
    
    isFieldValid(field) {
        if (field.type === 'checkbox') {
            return true; // Les checkboxes requises sont gérées différemment
        }
        
        const value = field.value?.trim();
        return value && value !== '';
    }
    
    getFieldLabel(field) {
        const container = field.closest('[data-point-id]');
        if (container) {
            const label = container.querySelector('label');
            return label?.textContent?.replace('*', '').trim();
        }
        return null;
    }
    
    highlightFieldError(field) {
        field.classList.add('border-red-500', 'bg-red-50');
    }
    
    clearFieldError(field) {
        field.classList.remove('border-red-500', 'bg-red-50');
    }
    
    showValidationErrors(errors) {
        const message = `Veuillez remplir les champs requis :\n• ${errors.join('\n• ')}`;
        this.showToast(message, 'error');
    }
    
    // ========================================
    // DRAG & DROP
    // ========================================
    
    setupDragAndDrop() {
        const form = document.getElementById('execution-form');
        if (!form) return;
        
        form.addEventListener('dragover', (e) => {
            e.preventDefault();
            form.classList.add('drag-over');
        });
        
        form.addEventListener('dragleave', (e) => {
            e.preventDefault();
            form.classList.remove('drag-over');
        });
        
        form.addEventListener('drop', (e) => {
            e.preventDefault();
            form.classList.remove('drag-over');
            
            const files = Array.from(e.dataTransfer.files);
            if (files.length > 0) {
                this.handleDroppedFiles(files, e.target);
            }
        });
    }
    
    handleDroppedFiles(files, target) {
        // Trouver le point de contrôle le plus proche
        const pointContainer = target.closest('[data-point-id]');
        if (pointContainer) {
            const pointId = pointContainer.dataset.pointId;
            if (window.mediaManager && window.mediaManager.handleFileUpload) {
                files.forEach(file => {
                    window.mediaManager.processDroppedFile(file, pointId);
                });
            }
        }
    }
    
    // ========================================
    // STATUT DE CONNEXION
    // ========================================
    
    showConnectionStatus(status) {
        const statusElement = document.getElementById('connection-status');
        if (!statusElement) return;
        
        statusElement.classList.remove('bg-green-100', 'text-green-800', 'bg-red-100', 'text-red-800');
        
        const statusText = statusElement.querySelector('span');
        const statusDot = statusElement.querySelector('div');
        
        if (status === 'online') {
            statusElement.classList.add('bg-green-100', 'text-green-800');
            if (statusText) statusText.textContent = 'En ligne';
            if (statusDot) statusDot.classList.add('animate-pulse');
        } else {
            statusElement.classList.add('bg-red-100', 'text-red-800');
            if (statusText) statusText.textContent = 'Hors ligne';
            if (statusDot) statusDot.classList.remove('animate-pulse');
        }
    }
    
    // ========================================
    // MODALS
    // ========================================
    
    closeAllModals() {
        const modals = document.querySelectorAll('[id$="-modal"]');
        modals.forEach(modal => {
            modal.classList.add('hidden');
        });
    }
    
    // ========================================
    // NOTIFICATIONS
    // ========================================
    
    showToast(message, type = 'info') {
        // Utiliser la fonction globale showToast si disponible
        if (window.showToast) {
            window.showToast(message, type);
            return;
        }
        
        // Fallback simple
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 transform transition-all duration-300`;
        
        const colors = {
            'success': 'bg-green-500 text-white',
            'error': 'bg-red-500 text-white',
            'info': 'bg-blue-500 text-white',
            'warning': 'bg-yellow-500 text-white'
        };
        
        toast.className += ' ' + (colors[type] || colors['info']);
        toast.innerHTML = `<div class="flex items-center"><span>${message}</span></div>`;
        
        document.body.appendChild(toast);
        
        setTimeout(() => toast.remove(), 5000);
    }
    
    // ========================================
    // NETTOYAGE
    // ========================================
    
    destroy() {
        if (this.autoSaveTimer) {
            clearTimeout(this.autoSaveTimer);
        }
        
        // Sauvegarder une dernière fois si nécessaire
        if (this.isDirty) {
            this.performAutoSave();
        }
    }
}

// ========================================
// INITIALISATION ET FONCTIONS GLOBALES
// ========================================

// Instance globale
let interventionUI;

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    interventionUI = new InterventionUI();
});

// Fonctions globales pour compatibilité avec le template
window.toggleCollapse = function(elementId) {
    if (interventionUI) {
        interventionUI.toggleCollapse(elementId);
    }
};

window.updateProgress = function() {
    if (interventionUI) {
        interventionUI.updateProgress();
    }
};

window.validateForm = function() {
    if (interventionUI) {
        return interventionUI.validateRequiredFields();
    }
    return true;
};

// Nettoyage lors de la fermeture de la page
window.addEventListener('beforeunload', function(e) {
    if (interventionUI) {
        interventionUI.destroy();
        
        // Avertir si des modifications non sauvegardées
        if (interventionUI.isDirty) {
            e.preventDefault();
            e.returnValue = 'Des modifications non sauvegardées pourraient être perdues.';
            return e.returnValue;
        }
    }
});