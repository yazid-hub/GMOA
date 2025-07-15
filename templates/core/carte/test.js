function createEquipmentFromForm() {
    if (!pendingEquipment) return;
    
    // Récupérer les données du formulaire
    const formData = {
        type: document.getElementById('equipment-type').value,
        name: document.getElementById('equipment-name').value,
        reference: document.getElementById('equipment-reference').value,
        brand: document.getElementById('equipment-brand').value,
        model: document.getElementById('equipment-model').value,
        location: document.getElementById('equipment-location').value,
        latitude: parseFloat(document.getElementById('equipment-lat').value),
        longitude: parseFloat(document.getElementById('equipment-lng').value),
        fibers_total: document.getElementById('equipment-fibers-total').value,
        fibers_used: document.getElementById('equipment-fibers-used').value,
        connector: document.getElementById('equipment-connector').value,
        status: document.getElementById('equipment-status').value,
        criticality: document.getElementById('equipment-criticality').value,
        service_date: document.getElementById('equipment-service-date').value,
        warranty_end: document.getElementById('equipment-warranty-end').value,
        notes: document.getElementById('equipment-notes').value
    };
    
    console.log('📊 Données équipement:', formData);
    
    // Créer le marqueur temporaire sur la carte
    const tempMarker = createTemporaryMarker(formData);
    
    // Sauvegarder en base de données
    saveEquipmentToDB(formData, tempMarker);
    
    // Fermer le formulaire
    closeEquipmentForm();
    
    // Désactiver le mode outil
    deactivateToolMode();
}

function createTemporaryMarker(formData) {
    const marker = L.marker(pendingEquipment.latlng, {
        icon: L.divIcon({
            html: `<div style="background: ${pendingEquipment.color}; border: 2px solid white; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                     <i class="${pendingEquipment.iconClass}" style="color: white; font-size: 12px;"></i>
                   </div>`,
            className: 'ftth-equipment-marker',
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        })
    });
    
    // Stocker les données complètes
    marker.equipmentData = {
        ...formData,
        id: Date.now(), // ID temporaire
        latlng: pendingEquipment.latlng,
        color: pendingEquipment.color,
        iconClass: pendingEquipment.iconClass,
        saved: false // Marqueur non sauvegardé
    };
    
    // Popup temporaire
    marker.bindPopup(`
        <div style="text-align: center;">
            <h4>${formData.name}</h4>
            <p><strong>Type:</strong> ${formData.type}</p>
            <p><strong>Statut:</strong> En cours de sauvegarde...</p>
            <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mx-auto mt-2"></div>
        </div>
    `);
    
    // Gestion des clics pour câblage
    marker.on('click', function(e) {
        if (currentToolMode === 'cable') {
            e.originalEvent.stopPropagation();
            marker.closePopup();
            addEquipmentToCable(marker);
            return false;
        }
    });
    
    drawingLayer.addLayer(marker);
    return marker;
}

// Fonction de sauvegarde en base de données
function saveEquipmentToDB(formData, tempMarker) {
    const equipmentData = {
        type: formData.type,
        name: formData.name,
        reference: formData.reference || formData.name,
        brand: formData.brand,
        model: formData.model,
        latitude: formData.latitude,
        longitude: formData.longitude,
        status: formData.status,
        criticality: formData.criticality,
        address: formData.location,
        fibers: parseInt(formData.fibers_total) || null,
        fibers_used: parseInt(formData.fibers_used) || 0,
        connector: formData.connector,
        service_date: formData.service_date,
        warranty_end: formData.warranty_end,
        notes: formData.notes
    };
    
    console.log('💾 Sauvegarde en cours...', equipmentData);
    
    // Appel AJAX vers Django
    fetch('/api/ftth/equipment/create/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(equipmentData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Sauvegarde réussie
            console.log('✅ Équipement sauvegardé:', data);
            
            // Mettre à jour le marqueur
            tempMarker.equipmentData.id = data.asset_id;
            tempMarker.equipmentData.saved = true;
            
            // Mettre à jour la popup
            updateEquipmentPopup(tempMarker, formData, data.asset_id);
            
            // Notification de succès
            showNotification('success', `Équipement ${formData.name} créé avec succès`);
            
        } else {
            // Erreur de sauvegarde
            console.error('❌ Erreur sauvegarde:', data.error);
            showNotification('error', `Erreur: ${data.error}`);
            
            // Marquer comme erreur
            tempMarker.equipmentData.saved = false;
            tempMarker.equipmentData.error = data.error;
            
            // Popup d'erreur
            tempMarker.bindPopup(`
                <div style="text-align: center;">
                    <h4>${formData.name}</h4>
                    <p style="color: red;"><strong>Erreur:</strong> ${data.error}</p>
                    <div style="margin-top: 8px;">
                        <button onclick="retryEquipmentSave(${tempMarker.equipmentData.id})" style="background: #f59e0b; color: white; padding: 4px 8px; border: none; border-radius: 4px; cursor: pointer; margin: 2px;">
                            🔄 Réessayer
                        </button>
                        <button onclick="deleteTemporaryEquipment(${tempMarker.equipmentData.id})" style="background: #ef4444; color: white; padding: 4px 8px; border: none; border-radius: 4px; cursor: pointer; margin: 2px;">
                            🗑️ Supprimer
                        </button>
                    </div>
                </div>
            `);
        }
    })
    .catch(error => {
        console.error('❌ Erreur réseau:', error);
        showNotification('error', 'Erreur de connexion au serveur');
        
        tempMarker.equipmentData.saved = false;
        tempMarker.equipmentData.error = 'Erreur réseau';
        
        tempMarker.bindPopup(`
            <div style="text-align: center;">
                <h4>${formData.name}</h4>
                <p style="color: red;"><strong>Erreur réseau</strong></p>
                <button onclick="retryEquipmentSave(${tempMarker.equipmentData.id})" style="background: #f59e0b; color: white; padding: 4px 8px; border: none; border-radius: 4px; cursor: pointer;">
                    🔄 Réessayer
                </button>
            </div>
        `);
    });
}

function updateEquipmentPopup(marker, formData, assetId) {
    const fibersInfo = formData.fibers_total ? 
        `<p><strong>Fibres:</strong> ${formData.fibers_used || 0}/${formData.fibers_total}</p>` : '';
    
    const popup = `
        <div style="text-align: center;">
            <h4>${formData.name}</h4>
            <p><strong>Type:</strong> ${formData.type}</p>
            <p><strong>Statut:</strong> ${formData.status}</p>
            ${fibersInfo}
            <div style="margin-top: 8px;">
                <button onclick="editEquipment(${assetId})" style="background: #3b82f6; color: white; padding: 4px 8px; border: none; border-radius: 4px; cursor: pointer; margin: 2px;">
                    ✏️ Modifier
                </button>
                <button onclick="deleteEquipment(${assetId})" style="background: #ef4444; color: white; padding: 4px 8px; border: none; border-radius: 4px; cursor: pointer; margin: 2px;">
                    🗑️ Supprimer
                </button>
            </div>
        </div>
    `;
    
    marker.bindPopup(popup);
}

// Fonction pour récupérer le token CSRF Django
function getCsrfToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return '';
}

// Système de notifications
function showNotification(type, message) {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 px-4 py-3 rounded-lg shadow-lg z-50 ${
        type === 'success' ? 'bg-green-500 text-white' : 
        type === 'error' ? 'bg-red-500 text-white' : 
        'bg-blue-500 text-white'
    }`;
    notification.innerHTML = `
        <div class="flex items-center">
            <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation-triangle' : 'info'} mr-2"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Fonctions utilitaires
function retryEquipmentSave(equipmentId) {
    // Retrouver le marqueur et réessayer la sauvegarde
    drawingLayer.eachLayer(function(layer) {
        if (layer.equipmentData && layer.equipmentData.id === equipmentId) {
            saveEquipmentToDB(layer.equipmentData, layer);
        }
    });
}

function deleteTemporaryEquipment(equipmentId) {
    drawingLayer.eachLayer(function(layer) {
        if (layer.equipmentData && layer.equipmentData.id === equipmentId) {
            drawingLayer.removeLayer(layer);
            console.log('🗑️ Équipement temporaire supprimé');
        }
    });
}

function editEquipment(assetId) {
    // TODO: Implémenter l'édition
    console.log('✏️ Édition équipement:', assetId);
    alert(`Édition équipement ID: ${assetId}`);
}

function deleteEquipment(assetId) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cet équipement ?')) {
        return;
    }
    
    fetch(`/api/ftth/equipment/${assetId}/delete/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('success', data.message);
            
            // Supprimer de la carte
            drawingLayer.eachLayer(function(layer) {
                if (layer.equipmentData && layer.equipmentData.id === assetId) {
                    drawingLayer.removeLayer(layer);
                }
            });
        } else {
            showNotification('error', data.error);
        }
    })
    .{% extends 'core/base.html' %}
{% load static %}

{% block title %}Carte FTTH - Assets{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<style>
#map {
    height: 100vh !important;
    width: 100% !important;
    min-height: 600px !important;
}

.ftth-tool-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    padding: 12px 8px;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    background: white;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 11px;
    font-weight: 500;
}

.ftth-tool-btn:hover {
    background: #f3f4f6;
    border-color: #3b82f6;
}

.ftth-tool-btn.active {
    background: #dbeafe;
    border-color: #3b82f6;
    color: #1d4ed8;
}

.ftth-tool-btn i {
    font-size: 16px;
}
</style>
{% endblock %}

{% block content %}
<div class="w-full h-screen overflow-hidden">
    <!-- Barre de recherche -->
    <div class="absolute top-4 left-1/2 transform -translate-x-1/2 z-50">
        <div class="relative">
            <input type="text" 
                   id="search-input"
                   placeholder="Rechercher un asset..."
                   class="w-96 px-4 py-3 bg-white border border-gray-300 rounded-lg shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
            <div id="search-results" class="absolute top-full left-0 right-0 bg-white border border-gray-300 border-t-0 rounded-b-lg max-h-60 overflow-y-auto z-50 hidden"></div>
        </div>
    </div>

    <!-- Statistiques -->
    <div class="absolute top-4 left-4 bg-white p-4 rounded-lg shadow-lg z-40 min-w-48">
        <h3 class="font-bold text-gray-800 mb-2 flex items-center">
            <i class="fas fa-chart-bar mr-2 text-blue-600"></i>
            Stats
        </h3>
        <div class="space-y-1 text-sm">
            <div class="flex justify-between">
                <span>Total:</span>
                <span class="font-semibold">{{ stats.total_assets|default:0 }}</span>
            </div>
            <div class="flex justify-between">
                <span class="text-green-600">Service:</span>
                <span class="font-semibold">{{ stats.en_service|default:0 }}</span>
            </div>
            <div class="flex justify-between">
                <span class="text-red-600">Panne:</span>
                <span class="font-semibold">{{ stats.en_panne|default:0 }}</span>
            </div>
        </div>
    </div>

    <!-- Boutons -->
    <div class="absolute top-4 right-4 space-x-2 z-40">
        <button onclick="toggleSidebar()" class="bg-blue-600 text-white px-4 py-2 rounded-lg shadow-lg hover:bg-blue-700">
            <i class="fas fa-info-circle"></i>
        </button>
        <button onclick="centrerSurAssets()" class="bg-green-600 text-white px-4 py-2 rounded-lg shadow-lg hover:bg-green-700">
            🎯 Centrer
        </button>
    </div>

    <!-- Palette d'outils FTTH -->
    <div id="ftth-tools-palette" class="absolute top-20 right-4 bg-white p-4 rounded-lg shadow-lg z-40 min-w-48">
        <h4 class="font-bold text-gray-800 mb-3 flex items-center">
            <i class="fas fa-drafting-compass mr-2 text-blue-600"></i>
            Outils FTTH
        </h4>
        
        <div class="grid grid-cols-2 gap-2">
            <button onclick="activateToolMode('nro')" class="ftth-tool-btn" data-tool="nro">
                <i class="fas fa-server" style="color: #dc2626;"></i>
                <span>NRO</span>
            </button>
            
            <button onclick="activateToolMode('pm')" class="ftth-tool-btn" data-tool="pm">
                <i class="fas fa-network-wired" style="color: #ea580c;"></i>
                <span>PM</span>
            </button>
            
            <button onclick="activateToolMode('pb')" class="ftth-tool-btn" data-tool="pb">
                <i class="fas fa-cube" style="color: #ca8a04;"></i>
                <span>PB</span>
            </button>
            
            <button onclick="activateToolMode('pto')" class="ftth-tool-btn" data-tool="pto">
                <i class="fas fa-home" style="color: #16a34a;"></i>
                <span>PTO</span>
            </button>
            
            <button onclick="activateToolMode('cable')" class="ftth-tool-btn" data-tool="cable">
                <i class="fas fa-minus" style="color: #7c3aed;"></i>
                <span>Câble</span>
            </button>
            
            <button onclick="activateToolMode('measure')" class="ftth-tool-btn" data-tool="measure">
                <i class="fas fa-ruler" style="color: #6b7280;"></i>
                <span>Mesure</span>
            </button>
            
            <button onclick="clearDrawings()" class="ftth-tool-btn col-span-2">
                <i class="fas fa-eraser" style="color: #ef4444;"></i>
                <span>Effacer</span>
            </button>
        </div>
    </div>

    <!-- Légende -->
    <div class="absolute bottom-4 left-4 bg-white p-4 rounded-lg shadow-lg z-40">
        <h4 class="font-bold text-gray-800 mb-2">Statuts</h4>
        <div class="space-y-2 text-sm">
            <div class="flex items-center">
                <div class="w-4 h-4 bg-green-500 rounded-full mr-2"></div>
                <span>En service</span>
            </div>
            <div class="flex items-center">
                <div class="w-4 h-4 bg-red-500 rounded-full mr-2"></div>
                <span>En panne</span>
            </div>
            <div class="flex items-center">
                <div class="w-4 h-4 bg-yellow-500 rounded-full mr-2"></div>
                <span>Maintenance</span>
            </div>
        </div>
    </div>

    <!-- Carte -->
    <div id="map" style="height: 100vh; width: 100vw; position: absolute; top: 0; left: 0; z-index: 10;"></div>

    <!-- Sidebar -->
    <div id="sidebar" class="fixed top-0 right-0 w-80 h-full bg-white shadow-xl transform translate-x-full transition-transform duration-300 z-50">
        <div class="p-6 h-full overflow-y-auto">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-xl font-bold">Détails Asset</h2>
                <button onclick="closeSidebar()" class="text-gray-500 hover:text-gray-700">
                    <i class="fas fa-times text-xl"></i>
                </button>
            </div>
            <div id="sidebar-content">
                <p class="text-gray-500">Sélectionnez un asset sur la carte.</p>
            </div>
        </div>
    </div>

    <!-- Formulaire de création d'équipement -->
    <div id="equipment-form-sidebar" class="fixed top-0 right-0 w-96 h-full bg-white shadow-xl transform translate-x-full transition-transform duration-300 z-50 border-l-4 border-blue-500">
        <div class="p-6 h-full overflow-y-auto">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-xl font-bold text-blue-600">
                    <i class="fas fa-plus-circle mr-2"></i>
                    Nouvel Équipement FTTH
                </h2>
                <button onclick="closeEquipmentForm()" class="text-gray-500 hover:text-gray-700">
                    <i class="fas fa-times text-xl"></i>
                </button>
            </div>
            
            <form id="equipment-form" class="space-y-4">
                <!-- Type d'équipement -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Type d'équipement *</label>
                    <select id="equipment-type" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" required>
                        <option value="">Sélectionner...</option>
                        <option value="NRO">NRO - Nœud de Raccordement Optique</option>
                        <option value="PM">PM - Point de Mutualisation</option>
                        <option value="PB">PB - Point de Branchement</option>
                        <option value="PTO">PTO - Prise Terminale Optique</option>
                    </select>
                </div>

                <!-- Nom -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Nom *</label>
                    <input type="text" id="equipment-name" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Ex: NRO-PARIS-01" required>
                </div>

                <!-- Référence -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Référence</label>
                    <input type="text" id="equipment-reference" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Référence technique">
                </div>

                <!-- Marque et Modèle -->
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Marque</label>
                        <input type="text" id="equipment-brand" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Ex: Huawei">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Modèle</label>
                        <input type="text" id="equipment-model" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Ex: MA5608T">
                    </div>
                </div>

                <!-- Localisation -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Localisation</label>
                    <input type="text" id="equipment-location" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Ex: Armoire rue de la Paix">
                </div>

                <!-- Coordonnées GPS -->
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Latitude *</label>
                        <input type="number" id="equipment-lat" step="0.000001" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" readonly>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Longitude *</label>
                        <input type="number" id="equipment-lng" step="0.000001" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" readonly>
                    </div>
                </div>

                <!-- Champs techniques FTTH -->
                <div id="technical-fields" class="space-y-3 hidden">
                    <div class="border-t pt-3">
                        <h4 class="font-medium text-gray-800 mb-2">Spécifications techniques</h4>
                        
                        <div class="grid grid-cols-2 gap-3">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">Nombre de fibres total</label>
                                <input type="number" id="equipment-fibers-total" min="1" max="288" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Ex: 48">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">Fibres utilisées</label>
                                <input type="number" id="equipment-fibers-used" min="0" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Ex: 12">
                            </div>
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Type de connecteur</label>
                            <select id="equipment-connector" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                                <option value="">Sélectionner...</option>
                                <option value="SC">SC</option>
                                <option value="LC">LC</option>
                                <option value="FC">FC</option>
                                <option value="ST">ST</option>
                                <option value="E2000">E2000</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- Statut -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Statut *</label>
                    <select id="equipment-status" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" required>
                        <option value="EN_SERVICE">En service</option>
                        <option value="EN_MAINTENANCE">En maintenance</option>
                        <option value="EN_PANNE">En panne</option>
                        <option value="HORS_SERVICE">Hors service</option>
                    </select>
                </div>

                <!-- Criticité -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Criticité *</label>
                    <select id="equipment-criticality" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" required>
                        <option value="FAIBLE">Faible</option>
                        <option value="MOYENNE" selected>Moyenne</option>
                        <option value="HAUTE">Haute</option>
                        <option value="CRITIQUE">Critique</option>
                    </select>
                </div>

                <!-- Dates -->
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Mise en service</label>
                        <input type="date" id="equipment-service-date" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Fin de garantie</label>
                        <input type="date" id="equipment-warranty-end" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                    </div>
                </div>

                <!-- Notes -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                    <textarea id="equipment-notes" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" rows="3" placeholder="Informations complémentaires..."></textarea>
                </div>

                <!-- Boutons -->
                <div class="flex space-x-3 pt-4">
                    <button type="submit" class="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors">
                        <i class="fas fa-save mr-2"></i>
                        Créer l'équipement
                    </button>
                    <button type="button" onclick="closeEquipmentForm()" class="flex-1 bg-gray-500 text-white py-2 px-4 rounded-md hover:bg-gray-600 transition-colors">
                        <i class="fas fa-times mr-2"></i>
                        Annuler
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<script>
// Variables globales
let map = null;
let assetsLayer = null;
let drawingLayer = null;
let currentToolMode = null;
let cablePoints = [];
let currentCableLine = null;
let measurePoints = [];

// Données
const DEFAULT_LAT = 48.8566;
const DEFAULT_LNG = 2.3522;
let assetsData = null;
let centerLat = DEFAULT_LAT;
let centerLng = DEFAULT_LNG;

// Récupération des données Django
try {
    const rawData = {{ assets_geojson|safe }};
    if (rawData && rawData.features) {
        assetsData = rawData;
    } else {
        assetsData = { type: "FeatureCollection", features: [] };
    }
} catch (e) {
    console.error('Erreur données assets:', e);
    assetsData = { type: "FeatureCollection", features: [] };
}

// Centre de la carte
try {
    const backendLat = parseFloat("{{ center_lat|default:'' }}");
    const backendLng = parseFloat("{{ center_lng|default:'' }}");
    
    if (!isNaN(backendLat) && !isNaN(backendLng)) {
        centerLat = backendLat;
        centerLng = backendLng;
    }
} catch (e) {
    console.log('Utilisation centre par défaut');
}

// Initialisation carte
function initMap() {
    try {
        // Créer la carte
        map = L.map('map').setView([centerLat, centerLng], 10);
        
        // Initialiser le layer de dessin
        drawingLayer = L.layerGroup().addTo(map);

        // Ajouter les tuiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap'
        }).addTo(map);

        // Ajouter les assets
        addAssets();
        
        // Redimensionner
        setTimeout(() => {
            map.invalidateSize();
        }, 100);
        
    } catch (error) {
        console.error('Erreur init carte:', error);
    }
}

// Ajout des assets
function addAssets() {
    try {
        if (!assetsData || !assetsData.features || assetsData.features.length === 0) {
            return;
        }

        const validFeatures = assetsData.features.filter(feature => {
            if (!feature.geometry || !feature.geometry.coordinates) return false;
            const coords = feature.geometry.coordinates;
            return Array.isArray(coords) && coords.length === 2 && 
                   !isNaN(coords[0]) && !isNaN(coords[1]);
        });

        if (validFeatures.length === 0) return;

        assetsLayer = L.geoJSON({ 
            type: "FeatureCollection", 
            features: validFeatures 
        }, {
            pointToLayer: function(feature, latlng) {
                const props = feature.properties || {};
                const color = getStatusColor(props.statut);
                
                return L.circleMarker(latlng, {
                    radius: 8,
                    fillColor: color,
                    color: '#fff',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.8
                });
            },
            onEachFeature: function(feature, layer) {
                const props = feature.properties || {};
                
                const popup = `
                    <div class="p-2">
                        <h3 class="font-bold">${props.nom || 'Asset'}</h3>
                        <p class="text-sm">Statut: ${props.statut || 'Inconnu'}</p>
                        <button onclick="showDetails(${props.id || 0})" class="mt-2 bg-blue-500 text-white px-2 py-1 rounded text-xs">
                            Détails
                        </button>
                    </div>
                `;
                
                layer.bindPopup(popup);
                
                layer.on('click', function() {
                    if (props.id) {
                        showDetails(props.id);
                    }
                });
            }
        }).addTo(map);
        
    } catch (error) {
        console.error('Erreur ajout assets:', error);
    }
}

// Fonctions utilitaires
function getStatusColor(statut) {
    switch ((statut || '').toLowerCase()) {
        case 'en service': return '#10b981';
        case 'en panne': return '#ef4444';
        case 'en maintenance': return '#f59e0b';
        default: return '#6b7280';
    }
}

// Outils FTTH
function activateToolMode(toolType) {
    document.querySelectorAll('.ftth-tool-btn').forEach(btn => btn.classList.remove('active'));
    
    const btn = document.querySelector(`[data-tool="${toolType}"]`);
    if (btn) btn.classList.add('active');
    
    currentToolMode = toolType;
    map.getContainer().style.cursor = 'crosshair';
    
    // Désactiver les popups des équipements en mode câble
    if (toolType === 'cable') {
        disableEquipmentPopups();
        console.log('🔧 Mode câble: popups désactivées, cliquez sur les équipements pour les relier');
    } else {
        enableEquipmentPopups();
    }
    
    map.off('click', onMapClick);
    map.on('click', onMapClick);
}

function onMapClick(e) {
    if (!currentToolMode) return;
    
    const latlng = e.latlng;
    
    switch(currentToolMode) {
        case 'nro':
            addEquipment(latlng, 'NRO', '#dc2626', 'fas fa-server');
            break;
        case 'pm':
            addEquipment(latlng, 'PM', '#ea580c', 'fas fa-network-wired');
            break;
        case 'pb':
            addEquipment(latlng, 'PB', '#ca8a04', 'fas fa-cube');
            break;
        case 'pto':
            addEquipment(latlng, 'PTO', '#16a34a', 'fas fa-home');
            break;
        case 'cable':
            addCablePoint(latlng);
            break;
        case 'measure':
            measureDistance(latlng);
            break;
    }
}

function addEquipment(latlng, type, color, iconClass) {
    // Ouvrir le formulaire au lieu de créer directement
    openEquipmentForm(latlng, type, color, iconClass);
}

// Variables globales pour le formulaire
let pendingEquipment = null;

function openEquipmentForm(latlng, type, color, iconClass) {
    // Stocker les données temporaires
    pendingEquipment = {
        latlng: latlng,
        type: type,
        color: color,
        iconClass: iconClass
    };
    
    // Remplir le formulaire
    document.getElementById('equipment-type').value = type;
    document.getElementById('equipment-lat').value = latlng.lat.toFixed(6);
    document.getElementById('equipment-lng').value = latlng.lng.toFixed(6);
    document.getElementById('equipment-name').value = `${type}-${Date.now()}`;
    
    // Afficher les champs techniques selon le type
    const technicalFields = document.getElementById('technical-fields');
    if (['NRO', 'PM', 'PB'].includes(type)) {
        technicalFields.classList.remove('hidden');
    } else {
        technicalFields.classList.add('hidden');
    }
    
    // Ouvrir le formulaire
    const formSidebar = document.getElementById('equipment-form-sidebar');
    formSidebar.classList.remove('translate-x-full');
    
    console.log(`📝 Formulaire ouvert pour ${type} à:`, latlng);
}

function closeEquipmentForm() {
    const formSidebar = document.getElementById('equipment-form-sidebar');
    formSidebar.classList.add('translate-x-full');
    
    // Reset
    document.getElementById('equipment-form').reset();
    pendingEquipment = null;
}

// Gestion du formulaire
document.addEventListener('DOMContentLoaded', function() {
    const equipmentForm = document.getElementById('equipment-form');
    if (equipmentForm) {
        equipmentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            createEquipmentFromForm();
        });
    }
    
    // Afficher/masquer champs techniques selon le type
    const typeSelect = document.getElementById('equipment-type');
    if (typeSelect) {
        typeSelect.addEventListener('change', function() {
            const technicalFields = document.getElementById('technical-fields');
            if (['NRO', 'PM', 'PB'].includes(this.value)) {
                technicalFields.classList.remove('hidden');
            } else {
                technicalFields.classList.add('hidden');
            }
        });
    }
});

function createEquipmentFromForm() {
    if (!pendingEquipment) return;
    
    // Récupérer les données du formulaire
    const formData = {
        type: document.getElementById('equipment-type').value,
        name: document.getElementById('equipment-name').value,
        address: document.getElementById('equipment-address').value,
        latitude: parseFloat(document.getElementById('equipment-lat').value),
        longitude: parseFloat(document.getElementById('equipment-lng').value),
        fibers: document.getElementById('equipment-fibers').value,
        connector: document.getElementById('equipment-connector').value,
        status: document.getElementById('equipment-status').value,
        criticality: document.getElementById('equipment-criticality').value,
        notes: document.getElementById('equipment-notes').value
    };
    
    console.log('📊 Données équipement:', formData);
    
    // Créer le marqueur sur la carte
    const marker = L.marker(pendingEquipment.latlng, {
        icon: L.divIcon({
            html: `<div style="background: ${pendingEquipment.color}; border: 2px solid white; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                     <i class="${pendingEquipment.iconClass}" style="color: white; font-size: 12px;"></i>
                   </div>`,
            className: 'ftth-equipment-marker',
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        })
    });
    
    // Stocker les données complètes
    marker.equipmentData = {
        ...formData,
        id: Date.now(),
        latlng: pendingEquipment.latlng,
        color: pendingEquipment.color,
        iconClass: pendingEquipment.iconClass
    };
    
    // Créer la popup mais ne pas l'attacher tout de suite
    const popupContent = `
        <div style="text-align: center;">
            <h4>${formData.name}</h4>
            <p><strong>Type:</strong> ${formData.type}</p>
            <p><strong>Statut:</strong> ${formData.status}</p>
            ${formData.fibers ? `<p><strong>Fibres:</strong> ${formData.fibers}</p>` : ''}
            <div style="margin-top: 8px;">
                <button onclick="saveEquipmentToDB(${marker.equipmentData.id})" style="background: #16a34a; color: white; padding: 4px 8px; border: none; border-radius: 4px; cursor: pointer; margin: 2px;">
                    💾 Sauvegarder
                </button>
                <button onclick="editEquipment(${marker.equipmentData.id})" style="background: #3b82f6; color: white; padding: 4px 8px; border: none; border-radius: 4px; cursor: pointer; margin: 2px;">
                    ✏️ Modifier
                </button>
            </div>
        </div>
    `;
    
    marker.bindPopup(popupContent);
    
    // Gestion intelligente des clics selon le mode
    marker.on('click', function(e) {
        if (currentToolMode === 'cable') {
            // Mode câble : empêcher la popup et faire le raccordement
            e.originalEvent.stopPropagation();
            marker.closePopup(); // Fermer si ouverte
            addEquipmentToCable(marker);
            return false;
        } else {
            // Mode normal : popup normale
            // La popup s'ouvrira automatiquement
        }
    });
    
    drawingLayer.addLayer(marker);
    
    // Fermer le formulaire
    closeEquipmentForm();
    
    // Désactiver le mode outil
    deactivateToolMode();
    
    console.log(`✅ Équipement ${formData.name} créé sur la carte`);
}

// Variables pour l'édition avancée
let cableSegments = [];
let currentSegment = null;
let proximityAlerts = [];
let snapDistance = 50; // Distance en mètres pour la détection

function addCablePoint(latlng) {
    // Vérifier la proximité avec des équipements existants
    const nearbyEquipments = findNearbyEquipments(latlng, snapDistance);
    
    if (nearbyEquipments.length > 0 && !isPointNearExistingSegment(latlng)) {
        showProximityAlert(latlng, nearbyEquipments);
        return;
    }
    
    // Si on a déjà un équipement sélectionné, on relie au point libre
    if (cableEquipments.length === 1) {
        const equipmentPoint = cableEquipments[0].equipmentData.latlng;
        const points = [equipmentPoint, latlng];
        
        createCableSegment(points, {
            startType: 'equipment',
            startRef: cableEquipments[0].equipmentData.name,
            endType: 'free',
            endRef: 'Point libre'
        });
        
        resetCableSelection();
        return;
    }
    
    // Logique de tracé libre avec segments
    if (!currentSegment) {
        // Démarrer un nouveau segment
        currentSegment = {
            points: [latlng],
            startType: 'free',
            endType: 'free',
            id: Date.now()
        };
        
        // Marqueur de départ
        const startMarker = L.circleMarker(latlng, {
            radius: 4,
            color: '#7c3aed',
            fillColor: '#7c3aed',
            fillOpacity: 1
        }).addTo(drawingLayer);
        
        console.log('🔌 Nouveau segment démarré - ID:', currentSegment.id);
    } else {
        // Continuer le segment actuel
        currentSegment.points.push(latlng);
        
        // Redessiner la ligne
        if (currentCableLine) {
            drawingLayer.removeLayer(currentCableLine);
        }
        
        currentCableLine = L.polyline(currentSegment.points, {
            color: '#7c3aed',
            weight: 3,
            opacity: 0.8
        }).addTo(drawingLayer);
        
        // Popup d'édition du segment
        const distance = calculateDistance(currentSegment.points);
        
        currentCableLine.bindPopup(`
            <div>
                <h4>📏 Segment ${currentSegment.id}</h4>
                <p><strong>Points:</strong> ${currentSegment.points.length}</p>
                <p><strong>Longueur:</strong> ${distance.toFixed(2)} m</p>
                <div style="margin-top: 10px;">
                    <button onclick="finalizeSegment()" style="background: #16a34a; color: white; padding: 4px 8px; border: none; border-radius: 4px; cursor: pointer; margin: 2px;">
                        ✅ Finaliser
                    </button>
                    <button onclick="editSegment(${currentSegment.id})" style="background: #3b82f6; color: white; padding: 4px 8px; border: none; border-radius: 4px; cursor: pointer; margin: 2px;">
                        ✏️ Éditer
                    </button>
                    <button onclick="continueSegment()" style="background: #f59e0b; color: white; padding: 4px 8px; border: none; border-radius: 4px; cursor: pointer; margin: 2px;">
                        ➕ Continuer
                    </button>
                    <button onclick="cancelSegment()" style="background: #ef4444; color: white; padding: 4px 8px; border: none; border-radius: 4px; cursor: pointer; margin: 2px;">
                        ❌ Annuler
                    </button>
                </div>
            </div>
        `);
    }
}

function findNearbyEquipments(latlng, maxDistance) {
    const nearby = [];
    
    // Vérifier dans les équipements créés
    if (drawingLayer) {
        drawingLayer.eachLayer(function(layer) {
            if (layer.equipmentData) {
                const distance = latlng.distanceTo(layer.equipmentData.latlng);
                if (distance <= maxDistance) {
                    nearby.push({
                        marker: layer,
                        distance: distance,
                        data: layer.equipmentData
                    });
                }
            }
        });
    }
    
    // Vérifier dans les assets existants
    if (assetsLayer) {
        assetsLayer.eachLayer(function(layer) {
            if (layer.feature && layer.feature.geometry) {
                const coords = layer.feature.geometry.coordinates;
                const assetLatLng = L.latLng(coords[1], coords[0]);
                const distance = latlng.distanceTo(assetLatLng);
                if (distance <= maxDistance) {
                    nearby.push({
                        marker: layer,
                        distance: distance,
                        data: layer.feature.properties
                    });
                }
            }
        });
    }
    
    return nearby.sort((a, b) => a.distance - b.distance);
}

function showProximityAlert(latlng, nearbyEquipments) {
    const alertPopup = L.popup({
        closeButton: false,
        autoClose: false,
        closeOnClick: false,
        className: 'proximity-alert-popup'
    });
    
    const nearestEquipment = nearbyEquipments[0];
    
    const alertContent = `
        <div style="text-align: center; min-width: 200px;">
            <h4 style="color: #f59e0b; margin: 0 0 10px 0;">
                ⚠️ Équipement proche détecté !
            </h4>
            <p style="margin: 5px 0;">
                <strong>${nearestEquipment.data.name || nearestEquipment.data.nom}</strong><br>
                À ${nearestEquipment.distance.toFixed(1)} m
            </p>
            <div style="margin-top: 15px;">
                <button onclick="snapToEquipment(${nearestEquipment.data.id || nearestEquipment.data.latitude}, ${nearestEquipment.data.longitude || nearestEquipment.data.longitude})" 
                        style="background: #16a34a; color: white; padding: 6px 12px; border: none; border-radius: 4px; cursor: pointer; margin: 2px;">
                    🔌 Raccorder
                </button>
                <button onclick="ignoreProximity(${latlng.lat}, ${latlng.lng})" 
                        style="background: #6b7280; color: white; padding: 6px 12px; border: none; border-radius: 4px; cursor: pointer; margin: 2px;">
                    ➡️ Ignorer
                </button>
            </div>
        </div>
    `;
    
    alertPopup.setLatLng(latlng).setContent(alertContent).openOn(map);
    
    // Stocker pour nettoyage
    proximityAlerts.push(alertPopup);
    
    console.log(`⚠️ Alerte proximité: ${nearestEquipment.data.name || nearestEquipment.data.nom} à ${nearestEquipment.distance.toFixed(1)}m`);
}

function snapToEquipment(equipmentId, lng) {
    // Fermer les alertes
    proximityAlerts.forEach(popup => map.closePopup(popup));
    proximityAlerts = [];
    
    // Trouver l'équipement et s'y raccorder
    const equipment = findEquipmentById(equipmentId);
    if (equipment) {
        console.log('🔌 Raccordement automatique à:', equipment.name || equipment.nom);
        
        if (currentSegment && currentSegment.points.length > 0) {
            // Finaliser le segment vers l'équipement
            currentSegment.points.push(equipment.latlng);
            currentSegment.endType = 'equipment';
            currentSegment.endRef = equipment.name || equipment.nom;
            
            finalizeSegment();
        } else {
            // Créer un nouveau segment vers l'équipement
            addEquipmentToCable(equipment.marker);
        }
    }
}

function ignoreProximity(lat, lng) {
    // Fermer les alertes et continuer normalement
    proximityAlerts.forEach(popup => map.closePopup(popup));
    proximityAlerts = [];
    
    const latlng = L.latLng(lat, lng);
    
    // Continuer le tracé normal
    if (!currentSegment) {
        currentSegment = {
            points: [latlng],
            startType: 'free',
            endType: 'free',
            id: Date.now()
        };
        
        const startMarker = L.circleMarker(latlng, {
            radius: 4,
            color: '#7c3aed',
            fillColor: '#7c3aed',
            fillOpacity: 1
        }).addTo(drawingLayer);
    } else {
        currentSegment.points.push(latlng);
        
        if (currentCableLine) {
            drawingLayer.removeLayer(currentCableLine);
        }
        
        currentCableLine = L.polyline(currentSegment.points, {
            color: '#7c3aed',
            weight: 3,
            opacity: 0.8
        }).addTo(drawingLayer);
    }
    
    console.log('➡️ Proximité ignorée, tracé libre continué');
}

function isPointNearExistingSegment(latlng) {
    // Vérifier si le point est près d'un segment existant
    return cableSegments.some(segment => {
        return segment.points.some(point => {
            return latlng.distanceTo(point) < 10; // 10 mètres
        });
    });
}

function findEquipmentById(id) {
    // Chercher dans les équipements créés
    let found = null;
    
    if (drawingLayer) {
        drawingLayer.eachLayer(function(layer) {
            if (layer.equipmentData && layer.equipmentData.id === id) {
                found = {
                    marker: layer,
                    ...layer.equipmentData
                };
            }
        });
    }
    
    // Chercher dans les assets existants
    if (!found && assetsLayer) {
        assetsLayer.eachLayer(function(layer) {
            if (layer.feature && layer.feature.properties && layer.feature.properties.id === id) {
                const coords = layer.feature.geometry.coordinates;
                found = {
                    marker: layer,
                    id: id,
                    name: layer.feature.properties.nom,
                    latlng: L.latLng(coords[1], coords[0])
                };
            }
        });
    }
    
    return found;
}

function createCableSegment(points, metadata) {
    const segment = {
        id: Date.now(),
        points: points,
        ...metadata,
        distance: calculateDistance(points),
        createdAt: new Date()
    };
    
    const segmentLine = L.polyline(points, {
        color: '#7c3aed',
        weight: 3,
        opacity: 0.8
    }).addTo(drawingLayer);
    
    segmentLine.bindPopup(`
        <div>
            <h4>📏 Segment ${segment.id}</h4>
            <p><strong>De:</strong> ${segment.startRef}</p>
            <p><strong>Vers:</strong> ${segment.endRef}</p>
            <p><strong>Longueur:</strong> ${segment.distance.toFixed(2)} m</p>
            <div style="margin-top: 10px;">
                <button onclick="editSegment(${segment.id})" style="background: #3b82f6; color: white; padding: 4px 8px; border: none; border-radius: 4px; cursor: pointer; margin: 2px;">
                    ✏️ Éditer
                </button>
                <button onclick="duplicateSegment(${segment.id})" style="background: #f59e0b; color: white; padding: 4px 8px; border: none; border-radius: 4px; cursor: pointer; margin: 2px;">
                    📋 Dupliquer
                </button>
                <button onclick="deleteSegment(${segment.id})" style="background: #ef4444; color: white; padding: 4px 8px; border: none; border-radius: 4px; cursor: pointer; margin: 2px;">
                    🗑️ Supprimer
                </button>
            </div>
        </div>
    `);
    
    segment.layer = segmentLine;
    cableSegments.push(segment);
    
    console.log(`✅ Segment ${segment.id} créé: ${segment.startRef} → ${segment.endRef} (${segment.distance.toFixed(2)}m)`);
    
    return segment;
}

function finalizeSegment() {
    if (!currentSegment) return;
    
    const segment = createCableSegment(currentSegment.points, {
        startType: currentSegment.startType,
        endType: currentSegment.endType,
        startRef: currentSegment.startRef || 'Point libre',
        endRef: currentSegment.endRef || 'Point libre'
    });
    
    // Nettoyer
    if (currentCableLine) {
        drawingLayer.removeLayer(currentCableLine);
    }
    
    currentSegment = null;
    currentCableLine = null;
    cablePoints = [];
    
    console.log('✅ Segment finalisé');
}

function editSegment(segmentId) {
    const segment = cableSegments.find(s => s.id === segmentId);
    if (!segment) return;
    
    console.log('✏️ Édition du segment:', segmentId);
    
    // Créer une interface d'édition
    const editContent = `
        <div style="min-width: 250px;">
            <h4>✏️ Édition Segment ${segmentId}</h4>
            <div style="margin: 10px 0;">
                <label style="display: block; margin: 5px 0;">Nom du segment:</label>
                <input type="text" id="segment-name-${segmentId}" value="Segment ${segmentId}" style="width: 100%; padding: 4px;">
            </div>
            <div style="margin: 10px 0;">
                <label style="display: block; margin: 5px 0;">Type de câble:</label>
                <select id="cable-type-${segmentId}" style="width: 100%; padding: 4px;">
                    <option value="fibre">Fibre optique</option>
                    <option value="coaxial">Coaxial</option>
                    <option value="twisted">Paire torsadée</option>
                </select>
            </div>
            <div style="margin: 10px 0;">
                <label style="display: block; margin: 5px 0;">Nombre de fibres:</label>
                <input type="number" id="fiber-count-${segmentId}" value="12" min="1" max="288" style="width: 100%; padding: 4px;">
            </div>
            <div style="margin: 15px 0;">
                <button onclick="saveSegmentEdit(${segmentId})" style="background: #16a34a; color: white; padding: 6px 12px; border: none; border-radius: 4px; cursor: pointer; margin: 2px;">
                    💾 Sauvegarder
                </button>
                <button onclick="addSegmentPoint(${segmentId})" style="background: #3b82f6; color: white; padding: 6px 12px; border: none; border-radius: 4px; cursor: pointer; margin: 2px;">
                    ➕ Ajouter point
                </button>
                <button onclick="cancelSegmentEdit(${segmentId})" style="background: #6b7280; color: white; padding: 6px 12px; border: none; border-radius: 4px; cursor: pointer; margin: 2px;">
                    ❌ Annuler
                </button>
            </div>
        </div>
    `;
    
    segment.layer.bindPopup(editContent).openPopup();
}

function saveSegmentEdit(segmentId) {
    const segment = cableSegments.find(s => s.id === segmentId);
    if (!segment) return;
    
    const name = document.getElementById(`segment-name-${segmentId}`).value;
    const cableType = document.getElementById(`cable-type-${segmentId}`).value;
    const fiberCount = document.getElementById(`fiber-count-${segmentId}`).value;
    
    segment.name = name;
    segment.cableType = cableType;
    segment.fiberCount = parseInt(fiberCount);
    
    console.log('💾 Segment sauvegardé:', segment);
    
    // Mettre à jour la popup
    segment.layer.bindPopup(`
        <div>
            <h4>📏 ${segment.name}</h4>
            <p><strong>Type:</strong> ${segment.cableType}</p>
            <p><strong>Fibres:</strong> ${segment.fiberCount}</p>
            <p><strong>Longueur:</strong> ${segment.distance.toFixed(2)} m</p>
            <div style="margin-top: 10px;">
                <button onclick="editSegment(${segment.id})" style="background: #3b82f6; color: white; padding: 4px 8px; border: none; border-radius: 4px; cursor: pointer; margin: 2px;">
                    ✏️ Éditer
                </button>
                <button onclick="deleteSegment(${segment.id})" style="background: #ef4444; color: white; padding: 4px 8px; border: none; border-radius: 4px; cursor: pointer; margin: 2px;">
                    🗑️ Supprimer
                </button>
            </div>
        </div>
    `);
}

function addSegmentPoint(segmentId) {
    const segment = cableSegments.find(s => s.id === segmentId);
    if (!segment) return;
    
    console.log('➕ Mode ajout de point pour segment:', segmentId);
    
    // Activer le mode ajout de point
    map.getContainer().style.cursor = 'copy';
    
    const onPointAdd = function(e) {
        // Insérer le point au milieu du segment
        const midIndex = Math.floor(segment.points.length / 2);
        segment.points.splice(midIndex, 0, e.latlng);
        
        // Recalculer la distance
        segment.distance = calculateDistance(segment.points);
        
        // Redessiner la ligne
        segment.layer.setLatLngs(segment.points);
        
        // Nettoyer
        map.getContainer().style.cursor = '';
        map.off('click', onPointAdd);
        
        console.log('✅ Point ajouté au segment:', segmentId);
    };
    
    map.on('click', onPointAdd);
}

function deleteSegment(segmentId) {
    const segmentIndex = cableSegments.findIndex(s => s.id === segmentId);
    if (segmentIndex === -1) return;
    
    const segment = cableSegments[segmentIndex];
    
    // Supprimer de la carte
    if (segment.layer) {
        drawingLayer.removeLayer(segment.layer);
    }
    
    // Supprimer du tableau
    cableSegments.splice(segmentIndex, 1);
    
    console.log('🗑️ Segment supprimé:', segmentId);
}

function continueSegment() {
    if (currentCableLine) {
        currentCableLine.closePopup();
    }
    console.log('➕ Continuez le tracé du segment');
}

function cancelSegment() {
    if (currentCableLine) {
        drawingLayer.removeLayer(currentCableLine);
    }
    currentSegment = null;
    currentCableLine = null;
    cablePoints = [];
    console.log('❌ Segment annulé');
}

// Nouvelle fonction pour raccorder des équipements
let cableEquipments = [];

function addEquipmentToCable(equipmentMarker) {
    // WORKFLOW 1: Si on a un segment en cours, on s'y connecte
    if (currentSegment && currentSegment.points.length > 0) {
        const equipmentPoint = equipmentMarker.equipmentData.latlng;
        
        // Finaliser le segment vers l'équipement
        currentSegment.points.push(equipmentPoint);
        currentSegment.endType = 'equipment';
        currentSegment.endRef = equipmentMarker.equipmentData.name;
        
        // Créer le segment final
        const segment = createCableSegment(currentSegment.points, {
            startType: currentSegment.startType,
            endType: 'equipment',
            startRef: currentSegment.startRef || 'Point libre',
            endRef: equipmentMarker.equipmentData.name
        });
        
        // Nettoyer
        if (currentCableLine) {
            drawingLayer.removeLayer(currentCableLine);
        }
        
        currentSegment = null;
        currentCableLine = null;
        cablePoints = [];
        
        console.log(`✅ Segment créé depuis tracé libre vers ${equipmentMarker.equipmentData.name}`);
        return;
    }
    
    // WORKFLOW 2: Si on a des points libres en cours (ancienne logique)
    if (cablePoints.length > 0) {
        const lastPoint = cablePoints[cablePoints.length - 1];
        const equipmentPoint = equipmentMarker.equipmentData.latlng;
        
        // Supprimer la ligne temporaire s'il y en a une
        if (currentCableLine) {
            drawingLayer.removeLayer(currentCableLine);
        }
        
        // Créer le segment final vers l'équipement
        const finalPoints = [...cablePoints, equipmentPoint];
        const segment = createCableSegment(finalPoints, {
            startType: 'free',
            endType: 'equipment',
            startRef: 'Point libre',
            endRef: equipmentMarker.equipmentData.name
        });
        
        console.log(`✅ Câble créé depuis tracé libre vers ${equipmentMarker.equipmentData.name}`);
        
        // Réinitialiser
        cablePoints = [];
        currentCableLine = null;
        return;
    }
    
    // WORKFLOW 3: Logique équipement → équipement (existante)
    cableEquipments.push(equipmentMarker);
    
    // Changer l'apparence pour montrer la sélection
    const equipment = equipmentMarker.equipmentData;
    equipmentMarker.setIcon(L.divIcon({
        html: `<div style="background: ${equipment.color}; border: 4px solid #3b82f6; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                 <i class="${equipment.iconClass || 'fas fa-server'}" style="color: white; font-size: 12px;"></i>
               </div>`,
        className: 'ftth-equipment-marker-selected',
        iconSize: [28, 28],
        iconAnchor: [14, 14]
    }));
    
    // Fermer la popup si elle est ouverte
    if (equipmentMarker.isPopupOpen()) {
        equipmentMarker.closePopup();
    }
    
    console.log(`📡 Équipement ${equipment.type || equipment.name} sélectionné (${cableEquipments.length})`);
    
    if (cableEquipments.length === 1) {
        console.log('👆 Cliquez sur un autre équipement pour créer le câble');
    } else if (cableEquipments.length >= 2) {
        createCableBetweenEquipments();
    }
}

function createCableBetweenEquipments() {
    if (cableEquipments.length < 2) return;
    
    // Créer la ligne entre tous les équipements sélectionnés
    const points = cableEquipments.map(marker => marker.equipmentData.latlng);
    
    const segment = createCableSegment(points, {
        startType: 'equipment',
        endType: 'equipment',
        startRef: cableEquipments[0].equipmentData.name,
        endRef: cableEquipments[cableEquipments.length - 1].equipmentData.name
    });
    
    console.log(`✅ Câble créé entre ${cableEquipments.length} équipements`);
    
    // Réinitialiser
    resetCableSelection();
}

function resetCableSelection() {
    // Remettre l'apparence normale des équipements
    cableEquipments.forEach(marker => {
        const equipment = marker.equipmentData;
        marker.setIcon(L.divIcon({
            html: `<div style="background: ${equipment.color}; border: 2px solid white; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                     <i class="${equipment.iconClass || 'fas fa-server'}" style="color: white; font-size: 12px;"></i>
                   </div>`,
            className: 'ftth-equipment-marker',
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        }));
    });
    
    // Réinitialiser toutes les variables
    cableEquipments = [];
    cablePoints = [];
    currentCableLine = null;
}

// Gestion des popups d'équipements selon le mode
function disableEquipmentPopups() {
    console.log('🚫 Désactivation des popups en mode câble');
    
    // Désactiver les popups des assets existants
    if (assetsLayer) {
        assetsLayer.eachLayer(function(layer) {
            layer.closePopup();
            layer.off('click');
            layer.on('click', function(e) {
                if (currentToolMode === 'cable') {
                    e.originalEvent.stopPropagation();
                    e.preventDefault();
                    console.log('🔌 Asset existant sélectionné pour câblage');
                    return false;
                }
            });
        });
    }
    
    // Désactiver les popups des nouveaux équipements
    if (drawingLayer) {
        drawingLayer.eachLayer(function(layer) {
            if (layer.equipmentData) {
                layer.closePopup();
                // Marquer comme désactivé pour les popups
                layer._popupWasDisabled = true;
            }
        });
    }
}

function enableEquipmentPopups() {
    console.log('✅ Réactivation des popups - mode normal');
    
    // Réactiver les popups des assets existants
    if (assetsLayer) {
        assetsLayer.eachLayer(function(layer) {
            layer.off('click');
            layer.on('click', function() {
                if (currentToolMode !== 'cable' && layer.feature && layer.feature.properties && layer.feature.properties.id) {
                    showDetails(layer.feature.properties.id);
                }
            });
        });
    }
    
    // Les nouveaux équipements gardent leur gestion intelligente dans createEquipmentFromForm
}

function measureDistance(latlng) {
    measurePoints.push(latlng);
    
    if (measurePoints.length === 1) {
        const startMarker = L.circleMarker(latlng, {
            radius: 3,
            color: '#6b7280',
            fillColor: '#6b7280',
            fillOpacity: 1
        }).addTo(drawingLayer);
    } else if (measurePoints.length === 2) {
        const distance = calculateDistance(measurePoints);
        
        const measureLine = L.polyline(measurePoints, {
            color: '#6b7280',
            weight: 2,
            dashArray: '5, 5'
        }).addTo(drawingLayer);
        
        measureLine.bindPopup(`Distance: ${distance.toFixed(2)} m`).openPopup();
        
        measurePoints = [];
        deactivateToolMode();
    }
}

function calculateDistance(points) {
    let totalDistance = 0;
    for (let i = 1; i < points.length; i++) {
        totalDistance += points[i-1].distanceTo(points[i]);
    }
    return totalDistance;
}

function finalizeCable() {
    console.log('Câble finalisé:', cablePoints);
    cablePoints = [];
    currentCableLine = null;
    deactivateToolMode();
}

function clearDrawings() {
    if (drawingLayer) {
        drawingLayer.clearLayers();
    }
    cablePoints = [];
    measurePoints = [];
    currentCableLine = null;
    cableEquipments = [];
    deactivateToolMode();
}

function deactivateToolMode() {
    currentToolMode = null;
    if (map) {
        map.getContainer().style.cursor = '';
        map.off('click', onMapClick);
    }
    document.querySelectorAll('.ftth-tool-btn').forEach(btn => btn.classList.remove('active'));
    
    // Réactiver les popups normales
    enableEquipmentPopups();
    resetCableSelection();
}

// Fonctions de sauvegarde (à implémenter côté Django)
function saveEquipmentToDB(type, lat, lng) {
    console.log(`💾 Sauvegarde ${type} en base:`, { type, lat, lng });
    // TODO: Appel AJAX vers Django pour créer l'asset
    alert(`Équipement ${type} à sauvegarder\nLat: ${lat}\nLng: ${lng}`);
}

function saveCableToDB() {
    console.log('💾 Sauvegarde câble en base');
    // TODO: Appel AJAX vers Django pour créer le câble
    alert('Câble à sauvegarder en base de données');
}

function removeTemporaryEquipment(equipmentId) {
    console.log('🗑️ Suppression équipement temporaire:', equipmentId);
    // Logique de suppression
}

function removeCable() {
    console.log('🗑️ Suppression câble');
    // Logique de suppression
}

// Sidebar
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.classList.toggle('translate-x-full');
    }
}

function closeSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.classList.add('translate-x-full');
    }
}

function showDetails(assetId) {
    if (!assetId) return;
    
    const content = document.getElementById('sidebar-content');
    if (!content) return;
    
    const asset = findAssetById(assetId);
    if (asset) {
        content.innerHTML = `
            <div>
                <h3 class="text-lg font-bold mb-2">${asset.nom || 'Asset'}</h3>
                <div class="space-y-2 text-sm">
                    <p><strong>Référence:</strong> ${asset.reference || 'N/A'}</p>
                    <p><strong>Catégorie:</strong> ${asset.categorie || 'N/A'}</p>
                    <p><strong>Statut:</strong> ${asset.statut || 'N/A'}</p>
                    <p><strong>Localisation:</strong> ${asset.localisation || 'N/A'}</p>
                </div>
            </div>
        `;
    } else {
        content.innerHTML = '<p class="text-red-500">Asset non trouvé</p>';
    }
    
    toggleSidebar();
}

function findAssetById(id) {
    if (!assetsData || !assetsData.features) return null;
    
    const feature = assetsData.features.find(f => 
        f.properties && f.properties.id == id
    );
    
    return feature ? feature.properties : null;
}

function centrerSurAssets() {
    if (!assetsData || !assetsData.features || assetsData.features.length === 0) {
        return;
    }
    
    let minLat = 90, maxLat = -90, minLng = 180, maxLng = -180;
    
    assetsData.features.forEach(feature => {
        const coords = feature.geometry.coordinates;
        const lat = coords[1];
        const lng = coords[0];
        
        minLat = Math.min(minLat, lat);
        maxLat = Math.max(maxLat, lat);
        minLng = Math.min(minLng, lng);
        maxLng = Math.max(maxLng, lng);
    });
    
    const bounds = [[minLat, minLng], [maxLat, maxLng]];
    map.fitBounds(bounds, { padding: [50, 50] });
}

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        try {
            initMap();
        } catch (error) {
            console.error('Erreur fatale:', error);
        }
    }, 100);
});
</script>
{% endblock %}