// static/js/intervention/intervention_ui.js
// Gestionnaire de l'interface utilisateur pour l'exécution d'intervention

class InterventionUI {
    constructor() {
        this.autoSaveTimer = null;
        this.autoSaveInterval = 30000; // 30 secondes
        this.ordreTravailiId = null;
        this.csrfToken = null;
        
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
    }
    
    setupEventListeners() {
        // Écouter les changements dans le formulaire pour l'auto-save
        const formInputs = document.querySelectorAll('#execution-form input, #execution-form select, #execution-form textarea');
        
        formInputs.forEach(input => {
            input.addEventListener('change', () => {
                this.triggerAutoSave();
            });
            input.addEventListener('input', () => {
                this.triggerAutoSave();
            });
        });
        
        // Validation avant finalisation
        const finaliseButton = document.querySelector('button[value="finaliser_intervention"]');
        if (finaliseButton) {
            finaliseButton.addEventListener('click', (e) => {
                if (!this.validateRequiredFields()) {
                    e.preventDefault();
                }
            });
        }
        
        // Drag & Drop pour les fichiers
        this.setupDragAndDrop();
    }
    
    // ========================================
    // GESTION DES COLLAPSES
    // ========================================
    
    initializeCollapses() {
        // Tous fermés par défaut
        document.querySelectorAll('[id^="operation-"]').forEach(element => {
            if (element.id.includes('operation-')) {
                element.style.display = 'none';
                const chevronId = 'chevron-' + element.id;
                const chevron = document.getElementById(chevronId);
                if (chevron) {
                    chevron.classList.add('rotate-180');
                }
            }
        });
    }
    
    toggleCollapse(elementId) {
        const element = document.getElementById(elementId);
        const chevron = document.getElementById('chevron-' + elementId);
        
        if (!element) return;
        
        if (element.style.display === 'none') {
            element.style.display = 'block';
            if (chevron) {
                chevron.classList.remove('rotate-180');
            }
        } else {
            element.style.display = 'none';
            if (chevron) {
                chevron.classList.add('rotate-180');
            }
        }
    }
    
    // ========================================
    // SAUVEGARDE AUTOMATIQUE
    // ========================================
    
    setupAutoSave() {
        // Sauvegarde avant fermeture de la page
        window.addEventListener('beforeunload', () => {
            this.saveDraft();
        });
    }
    
    triggerAutoSave() {
        clearTimeout(this.autoSaveTimer);
        this.autoSaveTimer = setTimeout(() => {
            this.saveDraft();
        }, 2000); // 2 secondes après la dernière modification
    }
    
    saveDraft() {
        const formData = new FormData(document.getElementById('execution-form'));
        const draftData = {};
        
        // Extraire seulement les données des points de contrôle
        for (let [key, value] of formData.entries()) {
            if (key.startsWith('point_')) {
                draftData[key] = value;
            }
        }
        
        this.showSaveIndicator();
        
        fetch(`/ordres-travail/${this.ordreTravailiId}/save-draft/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.csrfToken,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(draftData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.hideSaveIndicator();
                // Sauvegarder également en local pour persistance
                localStorage.setItem(`draft_${this.ordreTravailiId}`, JSON.stringify(draftData));
            }
        })
        .catch(error => {
            console.error('Erreur sauvegarde brouillon:', error);
        });
    }
    
    loadPersistedData() {
        // Charger les données de brouillon depuis le serveur
        fetch(`/ordres-travail/${this.ordreTravailiId}/load-draft/`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.draft) {
                    this.populateForm(data.draft);
                } else {
                    // Fallback vers le localStorage
                    const localDraft = localStorage.getItem(`draft_${this.ordreTravailiId}`);
                    if (localDraft) {
                        try {
                            const draftData = JSON.parse(localDraft);
                            this.populateForm(draftData);
                        } catch (e) {
                            console.error('Erreur parsing brouillon local:', e);
                        }
                    }
                }
            })
            .catch(error => {
                console.error('Erreur chargement brouillon:', error);
            });
    }
    
    populateForm(draftData) {
        Object.keys(draftData).forEach(key => {
            const element = document.querySelector(`[name="${key}"]`);
            if (element) {
                if (element.type === 'checkbox') {
                    element.checked = draftData[key];
                } else {
                    element.value = draftData[key];
                }
            }
        });
    }
    
    // ========================================
    // VALIDATION
    // ========================================
    
    validateRequiredFields() {
        const requiredFields = document.querySelectorAll('input[name^="point_"], select[name^="point_"], textarea[name^="point_"]');
        let hasError = false;
        let firstErrorField = null;
        
        requiredFields.forEach(field => {
            const label = field.closest('.border-l-4')?.querySelector('label');
            if (label && label.textContent.includes('*') && !field.value.trim()) {
                hasError = true;
                field.style.borderColor = '#ef4444';
                field.style.boxShadow = '0 0 0 3px rgba(239, 68, 68, 0.1)';
                
                if (!firstErrorField) {
                    firstErrorField = field;
                }
            } else {
                field.style.borderColor = '';
                field.style.boxShadow = '';
            }
        });
        
        if (hasError) {
            this.showError('Veuillez remplir tous les champs obligatoires avant de finaliser l\'intervention.');
            
            // Scroll vers le premier champ en erreur
            if (firstErrorField) {
                firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstErrorField.focus();
            }
            
            return false;
        }
        
        return true;
    }
    
    // ========================================
    // DRAG & DROP
    // ========================================
    
    setupDragAndDrop() {
        document.querySelectorAll('[id^="drop-zone-"]').forEach(dropZone => {
            const pointId = dropZone.id.replace('drop-zone-', '');
            
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.classList.add('dragover');
            });
            
            dropZone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                dropZone.classList.remove('dragover');
            });
            
            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.classList.remove('dragover');
                
                const files = Array.from(e.dataTransfer.files);
                files.forEach(file => {
                    if (window.mediaManager) {
                        window.mediaManager.uploadMedia(file, pointId, 'DOCUMENT', file.name);
                    }
                });
            });
        });
    }
    
    // ========================================
    // INDICATEURS VISUELS
    // ========================================
    
    showSaveIndicator() {
        const indicator = document.getElementById('save-indicator');
        if (indicator) {
            indicator.classList.remove('hidden');
        } else {
            // Créer l'indicateur s'il n'existe pas
            const newIndicator = document.createElement('div');
            newIndicator.id = 'save-indicator';
            newIndicator.className = 'fixed top-4 right-4 bg-yellow-100 border border-yellow-400 text-yellow-800 px-4 py-2 rounded-lg shadow-lg z-50 flex items-center space-x-2';
            newIndicator.innerHTML = `
                <i class="fas fa-save text-yellow-600"></i>
                <span class="text-sm font-medium">Sauvegarde automatique...</span>
                <div class="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
            `;
            document.body.appendChild(newIndicator);
        }
    }
    
    hideSaveIndicator() {
        const indicator = document.getElementById('save-indicator');
        if (indicator) {
            setTimeout(() => {
                indicator.classList.add('hidden');
            }, 2000);
        }
    }
    
    showOfflineIndicator() {
        const indicator = document.getElementById('offline-indicator');
        if (indicator) {
            indicator.classList.remove('hidden');
        } else {
            const newIndicator = document.createElement('div');
            newIndicator.id = 'offline-indicator';
            newIndicator.className = 'fixed top-16 right-4 bg-red-100 border border-red-400 text-red-800 px-4 py-2 rounded-lg shadow-lg z-50 flex items-center space-x-2';
            newIndicator.innerHTML = `
                <i class="fas fa-wifi-slash text-red-600"></i>
                <span class="text-sm font-medium">Mode hors ligne</span>
            `;
            document.body.appendChild(newIndicator);
        }
    }
    
    hideOfflineIndicator() {
        const indicator = document.getElementById('offline-indicator');
        if (indicator) {
            indicator.classList.add('hidden');
        }
    }
    
    // ========================================
    // GESTION HORS LIGNE
    // ========================================
    
    setupOfflineDetection() {
        window.addEventListener('online', () => {
            this.hideOfflineIndicator();
            this.syncOfflineData();
        });
        
        window.addEventListener('offline', () => {
            this.showOfflineIndicator();
        });
        
        // Vérification initiale
        if (!navigator.onLine) {
            this.showOfflineIndicator();
        }
    }
    
    syncOfflineData() {
        // Synchroniser les données sauvegardées hors ligne
        const offlineData = localStorage.getItem(`offline_data_${this.ordreTravailiId}`);
        if (offlineData) {
            try {
                const data = JSON.parse(offlineData);
                // Envoyer les données au serveur
                this.sendOfflineDataToServer(data);
                localStorage.removeItem(`offline_data_${this.ordreTravailiId}`);
            } catch (e) {
                console.error('Erreur sync données hors ligne:', e);
            }
        }
    }
    
    sendOfflineDataToServer(data) {
        fetch('/ajax/sync-offline/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.csrfToken,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                offline_data: data,
                ordre_travail_id: this.ordreTravailiId
            })
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                this.showSuccess('Données synchronisées avec succès');
            }
        })
        .catch(error => {
            console.error('Erreur synchronisation:', error);
        });
    }
    
    // ========================================
    // MESSAGES
    // ========================================
    
    showSuccess(message) {
        this.showMessage(message, 'success');
    }
    
    showError(message) {
        this.showMessage(message, 'error');
    }
    
    showInfo(message) {
        this.showMessage(message, 'info');
    }
    
    showMessage(message, type = 'info') {
        const messageDiv = document.createElement('div');
        
        let bgColor, textColor, icon;
        switch (type) {
            case 'success':
                bgColor = 'bg-green-500';
                textColor = 'text-white';
                icon = 'fa-check-circle';
                break;
            case 'error':
                bgColor = 'bg-red-500';
                textColor = 'text-white';
                icon = 'fa-exclamation-circle';
                break;
            case 'info':
            default:
                bgColor = 'bg-blue-500';
                textColor = 'text-white';
                icon = 'fa-info-circle';
                break;
        }
        
        messageDiv.className = `fixed top-4 left-1/2 transform -translate-x-1/2 ${bgColor} ${textColor} px-6 py-3 rounded-lg shadow-lg z-50 flex items-center space-x-2 min-w-96`;
        messageDiv.innerHTML = `
            <i class="fas ${icon}"></i>
            <span class="font-medium">${message}</span>
        `;
        
        document.body.appendChild(messageDiv);
        
        // Animation d'entrée
        setTimeout(() => {
            messageDiv.style.transform = 'translateX(-50%) translateY(0)';
        }, 10);
        
        // Suppression automatique
        setTimeout(() => {
            messageDiv.style.opacity = '0';
            messageDiv.style.transform = 'translateX(-50%) translateY(-20px)';
            setTimeout(() => {
                if (messageDiv.parentNode) {
                    messageDiv.parentNode.removeChild(messageDiv);
                }
            }, 300);
        }, 4000);
    }
    
    // ========================================
    // PROGRESSION
    // ========================================
    
    updateProgress() {
        const totalPoints = document.querySelectorAll('[data-point-id]').length;
        let completedPoints = 0;
        
        document.querySelectorAll('[data-point-id]').forEach(element => {
            const pointId = element.getAttribute('data-point-id');
            const value = element.value || element.checked;
            const validation = document.getElementById('validation-' + pointId);
            
            if (value && value.toString().trim() !== '') {
                completedPoints++;
                if (validation) {
                    validation.classList.remove('border-gray-300');
                    validation.classList.add('border-green-500', 'bg-green-50');
                    const icon = validation.querySelector('i');
                    if (icon) {
                        icon.classList.remove('hidden');
                    }
                }
            } else {
                if (validation) {
                    validation.classList.remove('border-green-500', 'bg-green-50');
                    validation.classList.add('border-gray-300');
                    const icon = validation.querySelector('i');
                    if (icon) {
                        icon.classList.add('hidden');
                    }
                }
            }
        });
        
        const percentage = totalPoints > 0 ? (completedPoints / totalPoints) * 100 : 0;
        
        // Mise à jour de la barre de progression principale
        const progressBar = document.getElementById('progress-bar');
        const progressPercentage = document.getElementById('progress-percentage');
        
        if (progressBar) {
            progressBar.style.width = percentage + '%';
        }
        if (progressPercentage) {
            progressPercentage.textContent = Math.round(percentage) + '%';
        }
        
        // Mise à jour du statut de completion
        const completionStatus = document.getElementById('completion-status');
        if (completionStatus) {
            completionStatus.textContent = `${completedPoints} sur ${totalPoints} points complétés`;
        }
    }
    
    // ========================================
    // NETTOYAGE
    // ========================================
    
    destroy() {
        if (this.autoSaveTimer) {
            clearTimeout(this.autoSaveTimer);
        }
    }
}

// Initialiser l'interface utilisateur
let interventionUI;

document.addEventListener('DOMContentLoaded', function() {
    interventionUI = new InterventionUI();
});

// Fonctions globales pour compatibilité avec le template
function toggleCollapse(elementId) {
    if (interventionUI) {
        interventionUI.toggleCollapse(elementId);
    }
}

function updateProgress() {
    if (interventionUI) {
        interventionUI.updateProgress();
    }
}

// Nettoyage lors de la fermeture de la page
window.addEventListener('beforeunload', function() {
    if (interventionUI) {
        interventionUI.destroy();
    }
});