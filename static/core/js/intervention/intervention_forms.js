// static/js/intervention/intervention_forms.js
// Gestionnaire des formulaires pour l'exécution d'intervention

class InterventionForms {
    constructor() {
        this.formData = new Map();
        this.validators = new Map();
        this.isDirty = false;
        
        this.init();
    }
    
    init() {
        this.setupFormValidation();
        this.setupFieldListeners();
        this.setupSubmitHandlers();
        this.calculateInitialProgress();
    }
    
    // ========================================
    // VALIDATION DES FORMULAIRES
    // ========================================
    
    setupFormValidation() {
        // Règles de validation par type de champ
        this.validators.set('NUMBER', {
            validate: (value, field) => {
                if (!value) return { valid: true };
                const num = parseFloat(value);
                return {
                    valid: !isNaN(num),
                    message: 'Veuillez saisir un nombre valide'
                };
            }
        });
        
        this.validators.set('SELECT', {
            validate: (value, field) => {
                const isRequired = field.closest('.border-l-4')?.querySelector('label')?.textContent?.includes('*');
                if (isRequired && !value) {
                    return {
                        valid: false,
                        message: 'Veuillez sélectionner une option'
                    };
                }
                return { valid: true };
            }
        });
        
        this.validators.set('BOOLEAN', {
            validate: (value, field) => {
                const isRequired = field.closest('.border-l-4')?.querySelector('label')?.textContent?.includes('*');
                if (isRequired && !value) {
                    return {
                        valid: false,
                        message: 'Veuillez faire un choix'
                    };
                }
                return { valid: true };
            }
        });
        
        this.validators.set('TEXT', {
            validate: (value, field) => {
                const isRequired = field.closest('.border-l-4')?.querySelector('label')?.textContent?.includes('*');
                if (isRequired && (!value || value.trim() === '')) {
                    return {
                        valid: false,
                        message: 'Ce champ est obligatoire'
                    };
                }
                
                // Validation de longueur si spécifiée
                const maxLength = field.getAttribute('maxlength');
                if (maxLength && value && value.length > parseInt(maxLength)) {
                    return {
                        valid: false,
                        message: `Maximum ${maxLength} caractères autorisés`
                    };
                }
                
                return { valid: true };
            }
        });
        
        this.validators.set('TEXTAREA', {
            validate: (value, field) => {
                return this.validators.get('TEXT').validate(value, field);
            }
        });
        
        this.validators.set('DATE', {
            validate: (value, field) => {
                if (!value) return { valid: true };
                
                const date = new Date(value);
                if (isNaN(date.getTime())) {
                    return {
                        valid: false,
                        message: 'Date invalide'
                    };
                }
                
                return { valid: true };
            }
        });
        
        this.validators.set('TIME', {
            validate: (value, field) => {
                if (!value) return { valid: true };
                
                const timeRegex = /^([01]?[0-9]|2[0-3]):[0-5][0-9]$/;
                if (!timeRegex.test(value)) {
                    return {
                        valid: false,
                        message: 'Format d\'heure invalide (HH:MM)'
                    };
                }
                
                return { valid: true };
            }
        });
    }
    
    validateField(field) {
        const fieldType = this.getFieldType(field);
        const validator = this.validators.get(fieldType);
        
        if (!validator) {
            return { valid: true };
        }
        
        const value = this.getFieldValue(field);
        const result = validator.validate(value, field);
        
        this.showFieldValidation(field, result);
        
        return result;
    }
    
    validateAllFields() {
        const fields = document.querySelectorAll('#execution-form input, #execution-form select, #execution-form textarea');
        let allValid = true;
        let firstInvalidField = null;
        
        fields.forEach(field => {
            const result = this.validateField(field);
            if (!result.valid) {
                allValid = false;
                if (!firstInvalidField) {
                    firstInvalidField = field;
                }
            }
        });
        
        return { valid: allValid, firstInvalidField };
    }
    
    showFieldValidation(field, result) {
        // Supprimer les messages d'erreur existants
        const existingError = field.parentNode.querySelector('.field-error-message');
        if (existingError) {
            existingError.remove();
        }
        
        // Réinitialiser le style
        field.classList.remove('border-red-500', 'border-green-500');
        
        if (result.valid) {
            if (field.value && field.value.trim() !== '') {
                field.classList.add('border-green-500');
            }
        } else {
            field.classList.add('border-red-500');
            
            // Ajouter le message d'erreur
            if (result.message) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'field-error-message text-red-600 text-xs mt-1';
                errorDiv.textContent = result.message;
                field.parentNode.appendChild(errorDiv);
            }
        }
    }
    
    // ========================================
    // GESTION DES CHAMPS
    // ========================================
    
    setupFieldListeners() {
        const fields = document.querySelectorAll('#execution-form input, #execution-form select, #execution-form textarea');
        
        fields.forEach(field => {
            // Validation en temps réel
            field.addEventListener('blur', () => {
                this.validateField(field);
                this.updateProgress();
            });
            
            field.addEventListener('change', () => {
                this.isDirty = true;
                this.validateField(field);
                this.updateProgress();
                this.saveFieldValue(field);
            });
            
            field.addEventListener('input', () => {
                this.isDirty = true;
                // Validation légère pendant la saisie (pas de message d'erreur)
                if (field.value && field.value.trim() !== '') {
                    field.classList.remove('border-red-500');
                    field.classList.add('border-green-500');
                }
                this.saveFieldValue(field);
            });
        });
    }
    
    getFieldType(field) {
        // Déterminer le type de champ à partir de l'attribut ou du type HTML
        const pointId = field.getAttribute('data-point-id');
        if (pointId) {
            // Le type peut être déterminé à partir du nom du champ ou d'autres attributs
            if (field.type === 'number') return 'NUMBER';
            if (field.type === 'date') return 'DATE';
            if (field.type === 'time') return 'TIME';
            if (field.type === 'datetime-local') return 'DATETIME';
            if (field.tagName === 'SELECT') return field.children.length <= 3 ? 'BOOLEAN' : 'SELECT';
            if (field.tagName === 'TEXTAREA') return 'TEXTAREA';
            return 'TEXT';
        }
        return 'TEXT';
    }
    
    getFieldValue(field) {
        if (field.type === 'checkbox') {
            return field.checked;
        }
        return field.value;
    }
    
    saveFieldValue(field) {
        const name = field.name;
        const value = this.getFieldValue(field);
        this.formData.set(name, value);
    }
    
    // ========================================
    // PROGRESSION
    // ========================================
    
    calculateInitialProgress() {
        // Calculer la progression initiale basée sur les champs remplis
        setTimeout(() => {
            this.updateProgress();
        }, 100);
    }
    
    updateProgress() {
        const totalFields = document.querySelectorAll('[data-point-id]').length;
        let completedFields = 0;
        
        document.querySelectorAll('[data-point-id]').forEach(field => {
            const value = this.getFieldValue(field);
            const pointId = field.getAttribute('data-point-id');
            
            if (value && value.toString().trim() !== '') {
                completedFields++;
                this.updateFieldValidationIndicator(pointId, true);
            } else {
                this.updateFieldValidationIndicator(pointId, false);
            }
        });
        
        const percentage = totalFields > 0 ? (completedFields / totalFields) * 100 : 0;
        
        // Mise à jour de la barre de progression
        const progressBar = document.getElementById('progress-bar');
        const progressPercentage = document.getElementById('progress-percentage');
        const completionStatus = document.getElementById('completion-status');
        
        if (progressBar) {
            progressBar.style.width = percentage + '%';
        }
        
        if (progressPercentage) {
            progressPercentage.textContent = Math.round(percentage) + '%';
        }
        
        if (completionStatus) {
            completionStatus.textContent = `${completedFields} sur ${totalFields} points complétés`;
        }
        
        // Mise à jour de la progression par opération
        this.updateOperationProgress();
        
        return { completed: completedFields, total: totalFields, percentage };
    }
    
    updateFieldValidationIndicator(pointId, isValid) {
        const indicator = document.getElementById(`validation-${pointId}`);
        if (!indicator) return;
        
        const icon = indicator.querySelector('i');
        
        if (isValid) {
            indicator.classList.remove('border-gray-300');
            indicator.classList.add('border-green-500', 'bg-green-50');
            if (icon) {
                icon.classList.remove('hidden');
            }
        } else {
            indicator.classList.remove('border-green-500', 'bg-green-50');
            indicator.classList.add('border-gray-300');
            if (icon) {
                icon.classList.add('hidden');
            }
        }
    }
    
    updateOperationProgress() {
        // Mettre à jour la progression pour chaque opération
        document.querySelectorAll('[id^="operation-progress-"]').forEach(element => {
            const operationId = element.id.replace('operation-progress-', '');
            const operationDiv = document.getElementById(`operation-${operationId}`);
            
            if (operationDiv) {
                const operationFields = operationDiv.querySelectorAll('[data-point-id]');
                let operationCompleted = 0;
                let operationTotal = operationFields.length;
                
                operationFields.forEach(field => {
                    const value = this.getFieldValue(field);
                    if (value && value.toString().trim() !== '') {
                        operationCompleted++;
                    }
                });
                
                element.textContent = `${operationCompleted}/${operationTotal} complété`;
                
                // Changer la couleur selon le statut
                if (operationCompleted === operationTotal && operationTotal > 0) {
                    element.className = 'text-green-600 font-bold';
                } else if (operationCompleted > 0) {
                    element.className = 'text-yellow-600 font-medium';
                } else {
                    element.className = 'text-gray-500 font-medium';
                }
            }
        });
    }
    
    // ========================================
    // SOUMISSION DU FORMULAIRE
    // ========================================
    
    setupSubmitHandlers() {
        const form = document.getElementById('execution-form');
        if (!form) return;
        
        form.addEventListener('submit', (e) => {
            const submitButton = e.submitter;
            const action = submitButton?.value;
            
            if (action === 'finaliser_intervention') {
                if (!this.validateBeforeSubmit()) {
                    e.preventDefault();
                    return false;
                }
            }
            
            // Afficher un indicateur de soumission
            this.showSubmissionIndicator(submitButton);
        });
    }
    
    validateBeforeSubmit() {
        const validation = this.validateAllFields();
        
        if (!validation.valid) {
            // Afficher un message d'erreur global
            this.showGlobalError('Veuillez corriger les erreurs dans le formulaire avant de continuer.');
            
            // Faire défiler vers le premier champ invalide
            if (validation.firstInvalidField) {
                validation.firstInvalidField.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center' 
                });
                validation.firstInvalidField.focus();
            }
            
            return false;
        }
        
        // Vérifier les champs obligatoires
        const requiredFields = document.querySelectorAll('[data-point-id]');
        const missingRequired = [];
        
        requiredFields.forEach(field => {
            const label = field.closest('.border-l-4')?.querySelector('label');
            if (label && label.textContent.includes('*')) {
                const value = this.getFieldValue(field);
                if (!value || value.toString().trim() === '') {
                    missingRequired.push(label.textContent.replace('*', '').trim());
                }
            }
        });
        
        if (missingRequired.length > 0) {
            this.showGlobalError(`Champs obligatoires manquants: ${missingRequired.join(', ')}`);
            return false;
        }
        
        return true;
    }
    
    showSubmissionIndicator(button) {
        if (!button) return;
        
        const originalText = button.innerHTML;
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Traitement...';
        
        // Réactiver après un délai (au cas où la soumission échoue côté serveur)
        setTimeout(() => {
            button.disabled = false;
            button.innerHTML = originalText;
        }, 10000);
    }
    
    // ========================================
    // SAUVEGARDE LOCALE
    // ========================================
    
    saveToLocalStorage() {
        const data = {};
        this.formData.forEach((value, key) => {
            data[key] = value;
        });
        
        const ordreId = document.getElementById('intervention-meta-data')?.dataset?.ordreId;
        if (ordreId) {
            localStorage.setItem(`form_data_${ordreId}`, JSON.stringify(data));
        }
    }
    
    loadFromLocalStorage() {
        const ordreId = document.getElementById('intervention-meta-data')?.dataset?.ordreId;
        if (!ordreId) return;
        
        const saved = localStorage.getItem(`form_data_${ordreId}`);
        if (saved) {
            try {
                const data = JSON.parse(saved);
                Object.keys(data).forEach(key => {
                    const field = document.querySelector(`[name="${key}"]`);
                    if (field) {
                        if (field.type === 'checkbox') {
                            field.checked = data[key];
                        } else {
                            field.value = data[key];
                        }
                        this.formData.set(key, data[key]);
                    }
                });
                
                // Mettre à jour la progression après le chargement
                setTimeout(() => {
                    this.updateProgress();
                }, 100);
            } catch (e) {
                console.error('Erreur lors du chargement des données locales:', e);
            }
        }
    }
    
    clearLocalStorage() {
        const ordreId = document.getElementById('intervention-meta-data')?.dataset?.ordreId;
        if (ordreId) {
            localStorage.removeItem(`form_data_${ordreId}`);
        }
    }
    
    // ========================================
    // UTILITAIRES
    // ========================================
    
    showGlobalError(message) {
        // Supprimer les messages d'erreur existants
        const existingError = document.querySelector('.global-error-message');
        if (existingError) {
            existingError.remove();
        }
        
        // Créer le nouveau message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'global-error-message fixed top-4 left-1/2 transform -translate-x-1/2 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 max-w-md';
        errorDiv.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-exclamation-circle mr-2"></i>
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-white hover:text-gray-200">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        document.body.appendChild(errorDiv);
        
        // Suppression automatique après 8 secondes
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 8000);
    }
    
    showGlobalSuccess(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'fixed top-4 left-1/2 transform -translate-x-1/2 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 max-w-md';
        successDiv.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-check-circle mr-2"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(successDiv);
        
        setTimeout(() => {
            if (successDiv.parentNode) {
                successDiv.remove();
            }
        }, 4000);
    }
    
    // ========================================
    // FONCTIONS SPÉCIALES POUR TYPES DE CHAMPS
    // ========================================
    
    setupConditionalFields() {
        // Gérer les champs conditionnels (qui dépendent d'autres champs)
        document.querySelectorAll('[data-depends-on]').forEach(field => {
            const dependsOn = field.getAttribute('data-depends-on');
            const condition = field.getAttribute('data-condition');
            const parentField = document.querySelector(`[name="${dependsOn}"]`);
            
            if (parentField) {
                const checkCondition = () => {
                    const parentValue = this.getFieldValue(parentField);
                    const shouldShow = this.evaluateCondition(parentValue, condition);
                    
                    const fieldContainer = field.closest('.border-l-4');
                    if (fieldContainer) {
                        fieldContainer.style.display = shouldShow ? 'block' : 'none';
                    }
                };
                
                parentField.addEventListener('change', checkCondition);
                checkCondition(); // Vérification initiale
            }
        });
    }
    
    evaluateCondition(value, condition) {
        if (!condition) return true;
        
        // Supporter différents types de conditions
        if (condition.startsWith('=')) {
            return value === condition.substring(1);
        } else if (condition.startsWith('>')) {
            return parseFloat(value) > parseFloat(condition.substring(1));
        } else if (condition.startsWith('<')) {
            return parseFloat(value) < parseFloat(condition.substring(1));
        } else {
            return value === condition;
        }
    }
    
    // ========================================
    // GESTION DES ERREURS DE SOUMISSION
    // ========================================
    
    handleSubmissionError(error) {
        console.error('Erreur de soumission:', error);
        this.showGlobalError('Erreur lors de la sauvegarde. Veuillez réessayer.');
        
        // Réactiver tous les boutons désactivés
        document.querySelectorAll('button[disabled]').forEach(button => {
            button.disabled = false;
        });
    }
    
    // ========================================
    // EXPORT/IMPORT DE DONNÉES
    // ========================================
    
    exportFormData() {
        const data = {};
        this.formData.forEach((value, key) => {
            data[key] = value;
        });
        
        return {
            formData: data,
            timestamp: new Date().toISOString(),
            progress: this.updateProgress()
        };
    }
    
    importFormData(data) {
        if (data.formData) {
            Object.keys(data.formData).forEach(key => {
                const field = document.querySelector(`[name="${key}"]`);
                if (field) {
                    if (field.type === 'checkbox') {
                        field.checked = data.formData[key];
                    } else {
                        field.value = data.formData[key];
                    }
                    this.formData.set(key, data.formData[key]);
                }
            });
            
            this.updateProgress();
        }
    }
    
    // ========================================
    // NETTOYAGE
    // ========================================
    
    destroy() {
        // Nettoyer les événements et les données
        this.formData.clear();
        this.validators.clear();
        
        // Sauvegarder les données avant destruction
        if (this.isDirty) {
            this.saveToLocalStorage();
        }
    }
}

// Initialiser le gestionnaire de formulaires
let interventionForms;

document.addEventListener('DOMContentLoaded', function() {
    interventionForms = new InterventionForms();
    
    // Charger les données sauvegardées
    interventionForms.loadFromLocalStorage();
    
    // Configurer les champs conditionnels
    interventionForms.setupConditionalFields();
});

// Fonctions globales pour compatibilité
function updateProgress() {
    if (interventionForms) {
        return interventionForms.updateProgress();
    }
}

function validateForm() {
    if (interventionForms) {
        return interventionForms.validateAllFields();
    }
    return { valid: true };
}

// Sauvegarde automatique avant fermeture
window.addEventListener('beforeunload', function(e) {
    if (interventionForms && interventionForms.isDirty) {
        interventionForms.saveToLocalStorage();
        
        // Afficher un avertissement si des modifications non sauvegardées existent
        e.preventDefault();
        e.returnValue = '';
        return '';
    }
});

