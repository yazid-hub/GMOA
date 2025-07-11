// Gestionnaire des médias pour l'exécution d'intervention

class MediaManager {
    constructor() {
        this.mediaRecorder = null;
        this.recordedBlobs = [];
        this.currentStream = null;
        this.audioRecorder = null;
        this.audioChunks = [];
        this.currentPointId = null;
        this.ordreTravailiId = null;
        this.csrfToken = null;
        this.allowedTypes = {
            image: ['jpg', 'jpeg', 'png', 'gif', 'webp'],
            video: ['mp4', 'avi', 'mov', 'wmv'],
            audio: ['mp3', 'wav', 'aac', 'm4a'],
            document: ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx']
        };
        this.uploadQueue = [];
        this.compressionWorker = new Worker('/static/js/workers/compression_worker.js');
        this.maxFileSize = 50 * 1024 * 1024; // 50MB
        
        this.init();
    }
    
    init() {
        // Récupérer les données depuis le DOM
        const metaData = document.getElementById('intervention-meta-data');
        if (metaData) {
            this.ordreTravailiId = metaData.dataset.ordreId;
            this.csrfToken = metaData.dataset.csrfToken;
        }
        
        // Initialiser les événements
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Gestionnaire global pour fermer les modals avec Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeMediaModal();
                this.closeViewModal();
            }
        });
    }
    
    // ========================================
    // CAPTURE PHOTO
    // ========================================
    
    capturePhoto(pointId) {
        this.currentPointId = pointId;
        this.showModal('Prendre une photo');
        
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                this.currentStream = stream;
                const video = document.getElementById('preview-video');
                
                if (!video) {
                    throw new Error('Élément video introuvable');
                }
                
                video.srcObject = stream;
                
                const captureBtn = document.getElementById('capture-btn');
                if (captureBtn) {
                    captureBtn.onclick = () => this.takePhoto(video);
                }
            })
            .catch(error => {
                console.error('Erreur accès caméra:', error);
                this.showError('Impossible d\'accéder à la caméra');
                this.closeMediaModal();
            });
    }
    
    takePhoto(video) {
        const canvas = document.getElementById('preview-canvas');
        if (!canvas) {
            this.showError('Canvas introuvable');
            return;
        }
        
        const context = canvas.getContext('2d');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0);
        
        canvas.toBlob(blob => {
            if (blob) {
                const filename = `photo_${Date.now()}.jpg`;
                this.uploadMedia(blob, this.currentPointId, 'PHOTO', filename);
                this.closeMediaModal();
            } else {
                this.showError('Erreur lors de la capture');
            }
        }, 'image/jpeg', 0.8);
    }
    
    // ========================================
    // CAPTURE VIDÉO
    // ========================================
    
    captureVideo(pointId) {
        this.currentPointId = pointId;
        this.showModal('Enregistrer une vidéo');
        
        navigator.mediaDevices.getUserMedia({ video: true, audio: true })
            .then(stream => {
                this.currentStream = stream;
                const video = document.getElementById('preview-video');
                
                if (!video) {
                    throw new Error('Élément video introuvable');
                }
                
                video.srcObject = stream;
                
                this.recordedBlobs = [];
                this.mediaRecorder = new MediaRecorder(stream);
                
                this.mediaRecorder.ondataavailable = event => {
                    if (event.data && event.data.size > 0) {
                        this.recordedBlobs.push(event.data);
                    }
                };
                
                this.mediaRecorder.onstop = () => {
                    const blob = new Blob(this.recordedBlobs, { type: 'video/webm' });
                    const filename = `video_${Date.now()}.webm`;
                    this.uploadMedia(blob, this.currentPointId, 'VIDEO', filename);
                    this.closeMediaModal();
                };
                
                this.setupVideoControls();
            })
            .catch(error => {
                console.error('Erreur accès caméra/micro:', error);
                this.showError('Impossible d\'accéder à la caméra/microphone');
                this.closeMediaModal();
            });
    }
    
    setupVideoControls() {
        const captureBtn = document.getElementById('capture-btn');
        if (!captureBtn) return;
        
        captureBtn.innerHTML = '<i class="fas fa-circle mr-2"></i>Commencer';
        captureBtn.onclick = () => {
            if (this.mediaRecorder.state === 'inactive') {
                this.mediaRecorder.start();
                captureBtn.innerHTML = '<i class="fas fa-stop mr-2"></i>Arrêter';
                captureBtn.classList.remove('bg-blue-500', 'hover:bg-blue-600');
                captureBtn.classList.add('bg-red-500', 'hover:bg-red-600');
            } else {
                this.mediaRecorder.stop();
            }
        };
    }
    
    // ========================================
    // ENREGISTREMENT AUDIO
    // ========================================
    
    toggleAudioRecording(pointId) {
        const button = document.getElementById(`audio-btn-${pointId}`);
        if (!button) return;
        
        if (!this.audioRecorder || this.audioRecorder.state === 'inactive') {
            this.startAudioRecording(pointId, button);
        } else {
            this.stopAudioRecording(button);
        }
    }
    
    startAudioRecording(pointId, button) {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                this.audioChunks = [];
                this.audioRecorder = new MediaRecorder(stream);
                
                this.audioRecorder.ondataavailable = event => {
                    this.audioChunks.push(event.data);
                };
                
                this.audioRecorder.onstop = () => {
                    const blob = new Blob(this.audioChunks, { type: 'audio/wav' });
                    const filename = `audio_${Date.now()}.wav`;
                    this.uploadMedia(blob, pointId, 'AUDIO', filename);
                    stream.getTracks().forEach(track => track.stop());
                    
                    button.classList.remove('bg-red-100');
                    button.innerHTML = '<i class="fas fa-microphone mr-2 text-red-600"></i>Enregistrer audio';
                };
                
                this.audioRecorder.start();
                button.classList.add('bg-red-100');
                button.innerHTML = '<i class="fas fa-stop mr-2 text-red-600"></i>Arrêter';
            })
            .catch(error => {
                console.error('Erreur accès microphone:', error);
                this.showError('Impossible d\'accéder au microphone');
            });
    }
    
    stopAudioRecording(button) {
        if (this.audioRecorder) {
            this.audioRecorder.stop();
        }
    }
    
    // ========================================
    // GESTION FICHIERS
    // ========================================
    
    handleFileUpload(input, pointId) {
        const files = Array.from(input.files);
        
        if (files.length === 0) return;
        
        files.forEach(file => {
            this.uploadMedia(file, pointId, 'DOCUMENT', file.name);
        });
        
        // Reset input
        input.value = '';
    }
    
    // ========================================
    // UPLOAD MÉDIA
    // ========================================
    
    uploadMedia(blob, pointId, type, filename) {
        if (!this.ordreTravailiId || !this.csrfToken) {
            this.showError('Données manquantes pour l\'upload');
            return;
        }
        
        const formData = new FormData();
        formData.append('fichier', blob, filename);
        formData.append('point_id', pointId);
        formData.append('type_fichier', type);
        formData.append('ordre_travail_id', this.ordreTravailiId);
        formData.append('csrfmiddlewaretoken', this.csrfToken);
        
        this.showUploadProgress(pointId);
        
        const xhr = new XMLHttpRequest();
        
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                this.updateUploadProgress(pointId, percentComplete);
            }
        });
        
        xhr.onload = () => {
            this.hideUploadProgress(pointId);
            
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        this.addMediaToGallery(pointId, response.media);
                        this.showSuccess('Média ajouté avec succès');
                    } else {
                        this.showError(`Erreur: ${response.error}`);
                    }
                } catch (e) {
                    this.showError('Erreur lors du traitement de la réponse');
                }
            } else {
                console.error('Erreur HTTP:', xhr.status, xhr.responseText);
                this.showError(`Erreur lors de l'upload (Status: ${xhr.status})`);
            }
        };
        
        xhr.onerror = () => {
            this.hideUploadProgress(pointId);
            this.showError('Erreur de connexion lors de l\'upload');
        };
        
        xhr.open('POST', '/ajax/upload-media-simple/');
        xhr.send(formData);
    }
    
    // ========================================
    // GESTION GALERIE
    // ========================================
    
    addMediaToGallery(pointId, media) {
        const gallery = document.getElementById(`media-gallery-${pointId}`);
        if (!gallery) {
            console.error('Galerie introuvable pour le point:', pointId);
            return;
        }
        
        const mediaElement = this.createMediaElement(media, pointId);
        gallery.appendChild(mediaElement);
        console.log('Média ajouté à la galerie:', media);
    }
    
    createMediaElement(media, pointId) {
        const div = document.createElement('div');
        div.className = 'relative group';
        div.setAttribute('data-media-id', media.id);
        
        let mediaContent = '';
        
        if (this.isImage(media)) {
            mediaContent = this.createImageContent(media);
        } else if (this.isVideo(media)) {
            mediaContent = this.createVideoContent(media);
        } else if (this.isAudio(media)) {
            mediaContent = this.createAudioContent(media);
        } else {
            mediaContent = this.createFileContent(media);
        }
        
        div.innerHTML = `
            ${mediaContent}
            <button type="button" 
                    class="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                    onclick="mediaManager.deleteMedia('${media.id}', '${pointId}')"
                    title="Supprimer">
                <i class="fas fa-times"></i>
            </button>
            <div class="absolute bottom-0 left-0 right-0 bg-black bg-opacity-75 text-white text-xs p-1 opacity-0 group-hover:opacity-100 transition-opacity">
                ${this.truncateText(media.nom_original, 15)}
            </div>
        `;
        
        return div;
    }
    
    createImageContent(media) {
        return `
            <div class="w-24 h-24 rounded-lg overflow-hidden border border-gray-200 cursor-pointer"
                 onclick="mediaManager.viewMedia('${media.url}', '${media.type_mime || 'image/jpeg'}', '${media.nom_original}')">
                <img src="${media.url}" alt="${media.nom_original}" 
                     class="w-full h-full object-cover" 
                     onerror="this.parentElement.innerHTML='<div class=\\'w-full h-full bg-gray-200 flex items-center justify-center\\'>❌</div>';">
            </div>`;
    }
    
    createVideoContent(media) {
        return `
            <div class="w-24 h-24 rounded-lg overflow-hidden border border-gray-200 bg-gray-100 flex items-center justify-center cursor-pointer"
                 onclick="mediaManager.viewMedia('${media.url}', '${media.type_mime || 'video/mp4'}', '${media.nom_original}')">
                <i class="fas fa-video text-2xl text-blue-500"></i>
            </div>`;
    }
    
    createAudioContent(media) {
        return `
            <div class="w-24 h-24 rounded-lg border border-gray-200 bg-green-50 flex flex-col items-center justify-center p-2 cursor-pointer"
                 onclick="mediaManager.toggleAudioPlayer('audio-${media.id}')">
                <i class="fas fa-music text-2xl text-green-600 mb-1"></i>
                <span class="text-xs text-center text-green-800">${this.truncateText(media.nom_original, 10)}</span>
                <audio id="audio-${media.id}" class="hidden w-full mt-1" controls>
                    <source src="${media.url}" type="${media.type_mime || 'audio/mpeg'}">
                    Votre navigateur ne supporte pas l'audio.
                </audio>
            </div>`;
    }
    
    createFileContent(media) {
        const ext = (media.extension || 'FILE').toUpperCase();
        return `
            <div class="w-24 h-24 rounded-lg overflow-hidden border border-gray-200 bg-gray-50 flex flex-col items-center justify-center p-2 cursor-pointer"
                 onclick="window.open('${media.url}', '_blank')">
                <i class="fas fa-file text-2xl text-gray-400 mb-1"></i>
                <span class="text-xs text-gray-600 text-center">${ext}</span>
            </div>`;
    }
    
    // ========================================
    // VISUALISATION MÉDIAS
    // ========================================
    
    viewMedia(url, mimeType, nomOriginal) {
        const modal = document.getElementById('media-view-modal');
        const content = document.getElementById('view-content');
        
        if (!modal || !content) {
            this.showError('Modal de visualisation introuvable');
            return;
        }
        
        if (mimeType.startsWith('image/')) {
            content.innerHTML = `
                <div class="max-w-full max-h-screen">
                    <img src="${url}" alt="${nomOriginal}" class="max-w-full max-h-screen object-contain">
                </div>`;
        } else if (mimeType.startsWith('video/')) {
            content.innerHTML = `
                <div class="max-w-full max-h-screen">
                    <video controls class="max-w-full max-h-screen" autoplay>
                        <source src="${url}" type="${mimeType}">
                        Votre navigateur ne supporte pas la vidéo.
                    </video>
                </div>`;
        } else if (mimeType.startsWith('audio/')) {
            content.innerHTML = `
                <div class="p-8 bg-gradient-to-br from-green-400 to-blue-500 text-white text-center min-w-96">
                    <i class="fas fa-music text-6xl mb-4"></i>
                    <h3 class="text-xl font-bold mb-4">${nomOriginal}</h3>
                    <audio controls class="w-full" autoplay>
                        <source src="${url}" type="${mimeType}">
                        Votre navigateur ne supporte pas l'audio.
                    </audio>
                    <div class="mt-4">
                        <a href="${url}" target="_blank" class="bg-white text-blue-600 px-4 py-2 rounded hover:bg-gray-100">
                            <i class="fas fa-download mr-2"></i>Télécharger
                        </a>
                    </div>
                </div>`;
        } else {
            content.innerHTML = `
                <div class="p-8 text-center min-w-96">
                    <i class="fas fa-file text-6xl text-gray-400 mb-4"></i>
                    <h3 class="text-xl font-bold text-gray-700 mb-4">${nomOriginal}</h3>
                    <p class="text-gray-600 mb-4">Fichier non prévisualisable</p>
                    <a href="${url}" target="_blank" class="bg-blue-500 text-white px-6 py-3 rounded hover:bg-blue-600">
                        <i class="fas fa-external-link-alt mr-2"></i>Ouvrir le fichier
                    </a>
                </div>`;
        }
        
        modal.classList.remove('hidden');
    }
    
    // ========================================
    // SUPPRESSION MÉDIAS
    // ========================================
    
    deleteMedia(mediaId, pointId) {
        if (!confirm('Êtes-vous sûr de vouloir supprimer ce média ?')) {
            return;
        }
        
        fetch('/ajax/delete-media-simple/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.csrfToken,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ media_id: mediaId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const mediaElement = document.querySelector(`[data-media-id="${mediaId}"]`);
                if (mediaElement) {
                    mediaElement.remove();
                }
                this.showSuccess('Média supprimé');
            } else {
                this.showError('Erreur lors de la suppression');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            this.showError('Erreur de connexion');
        });
    }
    
    // ========================================
    // GESTION MODALS
    // ========================================
    
    showModal(title) {
        const modal = document.getElementById('media-capture-modal');
        const titleElement = document.getElementById('modal-title');
        
        if (modal && titleElement) {
            titleElement.textContent = title;
            modal.classList.remove('hidden');
        }
    }
    
    closeMediaModal() {
        const modal = document.getElementById('media-capture-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
        
        if (this.currentStream) {
            this.currentStream.getTracks().forEach(track => track.stop());
            this.currentStream = null;
        }
        
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }
    }
    
    closeViewModal() {
        const modal = document.getElementById('media-view-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
        
        // Arrêter tous les médias en cours
        const videos = modal.querySelectorAll('video');
        const audios = modal.querySelectorAll('audio');
        
        videos.forEach(video => {
            video.pause();
            video.currentTime = 0;
        });
        
        audios.forEach(audio => {
            audio.pause();
            audio.currentTime = 0;
        });
    }
    
    // ========================================
    // AUDIO PLAYER
    // ========================================
    
    toggleAudioPlayer(audioId) {
        const audio = document.getElementById(audioId);
        if (!audio) return;
        
        const allAudios = document.querySelectorAll('audio');
        
        // Arrêter tous les autres audios
        allAudios.forEach(a => {
            if (a.id !== audioId) {
                a.pause();
                a.classList.add('hidden');
            }
        });
        
        // Toggle l'audio courant
        if (audio.classList.contains('hidden')) {
            audio.classList.remove('hidden');
            audio.play();
        } else {
            audio.classList.add('hidden');
            audio.pause();
        }
    }
    
    // ========================================
    // GESTION PROGRESSION
    // ========================================
    
    showUploadProgress(pointId) {
        const progressElement = document.getElementById(`upload-progress-${pointId}`);
        if (progressElement) {
            progressElement.classList.remove('hidden');
        }
    }
    
    updateUploadProgress(pointId, percentage) {
        const percentElement = document.getElementById(`upload-percentage-${pointId}`);
        const barElement = document.getElementById(`upload-bar-${pointId}`);
        
        if (percentElement) {
            percentElement.textContent = Math.round(percentage) + '%';
        }
        if (barElement) {
            barElement.style.width = percentage + '%';
        }
    }
    
    hideUploadProgress(pointId) {
        const progressElement = document.getElementById(`upload-progress-${pointId}`);
        if (progressElement) {
            progressElement.classList.add('hidden');
        }
    }
    
    // ========================================
    // UTILITAIRES
    // ========================================
    
    isImage(media) {
        if (media.is_image) return true;
        const ext = (media.extension || '').toLowerCase();
        return ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext);
    }
    
    isVideo(media) {
        if (media.is_video) return true;
        const ext = (media.extension || '').toLowerCase();
        return ['mp4', 'avi', 'mov', 'webm'].includes(ext);
    }
    
    isAudio(media) {
        if (media.is_audio) return true;
        const ext = (media.extension || '').toLowerCase();
        return ['mp3', 'wav', 'aac', 'm4a'].includes(ext);
    }
    
    truncateText(text, length) {
        if (!text || text.length <= length) return text;
        return text.substring(0, length - 3) + '...';
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
    
    showMessage(message, type) {
        const messageDiv = document.createElement('div');
        const bgColor = type === 'success' ? 'bg-green-500' : 'bg-red-500';
        const icon = type === 'success' ? 'fa-check' : 'fa-exclamation-triangle';
        
        messageDiv.className = `fixed top-4 right-4 ${bgColor} text-white px-4 py-2 rounded-md shadow-lg z-50`;
        messageDiv.innerHTML = `<i class="fas ${icon} mr-2"></i>${message}`;
        
        document.body.appendChild(messageDiv);
        
        setTimeout(() => {
            messageDiv.remove();
        }, 3000);
    }
}

// Initialiser le gestionnaire de médias
let mediaManager;

document.addEventListener('DOMContentLoaded', function() {
    mediaManager = new MediaManager();
});

// Fonctions globales pour compatibilité avec le template
function capturePhoto(pointId) {
    mediaManager.capturePhoto(pointId);
}

function captureVideo(pointId) {
    mediaManager.captureVideo(pointId);
}

function toggleAudioRecording(pointId) {
    mediaManager.toggleAudioRecording(pointId);
}

function handleFileUpload(input, pointId) {
    mediaManager.handleFileUpload(input, pointId);
}

function deleteMedia(mediaId, pointId) {
    mediaManager.deleteMedia(mediaId, pointId);
}

function closeMediaModal() {
    mediaManager.closeMediaModal();
}

function closeViewModal() {
    mediaManager.closeViewModal();
}

function viewMedia(url, mimeType, nomOriginal) {
    mediaManager.viewMedia(url, mimeType, nomOriginal);
}

function toggleAudioPlayer(audioId) {
    mediaManager.toggleAudioPlayer(audioId);
}