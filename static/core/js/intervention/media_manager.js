// static/core/js/intervention/media_manager.js
// Gestionnaire complet des médias pour l'exécution d'intervention

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
        this.isRecording = false;
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
        this.showMediaModal('Prendre une photo');
        
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                this.currentStream = stream;
                this.setupPhotoCapture();
            })
            .catch(error => {
                console.error('Erreur accès caméra:', error);
                this.showError('Impossible d\'accéder à la caméra');
                this.closeMediaModal();
            });
    }
    
    setupPhotoCapture() {
        const modal = document.getElementById('media-modal');
        const content = document.getElementById('media-modal-content');
        
        content.innerHTML = `
            <video id="camera-preview" class="w-full max-w-md rounded-lg mb-4" autoplay muted></video>
            <canvas id="photo-canvas" class="hidden"></canvas>
            <div class="flex space-x-3 justify-center">
                <button id="take-photo-btn" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                    <i class="fas fa-camera mr-2"></i>
                    Prendre la photo
                </button>
                <button onclick="closeMediaModal()" class="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200">
                    Annuler
                </button>
            </div>
        `;
        
        const video = document.getElementById('camera-preview');
        const takePhotoBtn = document.getElementById('take-photo-btn');
        
        video.srcObject = this.currentStream;
        
        takePhotoBtn.onclick = () => {
            this.takePhoto();
        };
    }
    
    takePhoto() {
        const video = document.getElementById('camera-preview');
        const canvas = document.getElementById('photo-canvas');
        const context = canvas.getContext('2d');
        
        // Ajuster la taille du canvas à la vidéo
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        // Capturer l'image
        context.drawImage(video, 0, 0);
        
        // Convertir en blob
        canvas.toBlob((blob) => {
            const filename = `photo_${Date.now()}.jpg`;
            this.uploadMedia(blob, this.currentPointId, 'PHOTO', filename);
            
            // Nettoyer
            this.stopCurrentStream();
            this.closeMediaModal();
        }, 'image/jpeg', 0.8);
    }
    
    // ========================================
    // CAPTURE VIDÉO
    // ========================================
    
    captureVideo(pointId) {
        this.currentPointId = pointId;
        this.showMediaModal('Enregistrer une vidéo');
        
        navigator.mediaDevices.getUserMedia({ video: true, audio: true })
            .then(stream => {
                this.currentStream = stream;
                this.setupVideoCapture();
            })
            .catch(error => {
                console.error('Erreur accès caméra/micro:', error);
                this.showError('Impossible d\'accéder à la caméra/microphone');
                this.closeMediaModal();
            });
    }
    
    setupVideoCapture() {
        const content = document.getElementById('media-modal-content');
        
        content.innerHTML = `
            <video id="video-preview" class="w-full max-w-md rounded-lg mb-4" autoplay muted></video>
            <div class="flex space-x-3 justify-center">
                <button id="record-video-btn" class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700">
                    <i class="fas fa-circle mr-2"></i>
                    Commencer l'enregistrement
                </button>
                <button onclick="closeMediaModal()" class="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200">
                    Annuler
                </button>
            </div>
            <div id="recording-timer" class="hidden text-center mt-2">
                <span class="text-red-600 font-mono text-lg">00:00</span>
            </div>
        `;
        
        const video = document.getElementById('video-preview');
        const recordBtn = document.getElementById('record-video-btn');
        
        video.srcObject = this.currentStream;
        
        recordBtn.onclick = () => {
            if (!this.isRecording) {
                this.startVideoRecording();
            } else {
                this.stopVideoRecording();
            }
        };
    }
    
    startVideoRecording() {
        this.recordedBlobs = [];
        this.isRecording = true;
        
        try {
            this.mediaRecorder = new MediaRecorder(this.currentStream, {
                mimeType: 'video/webm;codecs=vp9'
            });
        } catch (e) {
            try {
                this.mediaRecorder = new MediaRecorder(this.currentStream, {
                    mimeType: 'video/webm'
                });
            } catch (e) {
                this.mediaRecorder = new MediaRecorder(this.currentStream);
            }
        }
        
        this.mediaRecorder.ondataavailable = (event) => {
            if (event.data && event.data.size > 0) {
                this.recordedBlobs.push(event.data);
            }
        };
        
        this.mediaRecorder.onstop = () => {
            const blob = new Blob(this.recordedBlobs, { type: 'video/webm' });
            const filename = `video_${Date.now()}.webm`;
            this.uploadMedia(blob, this.currentPointId, 'VIDEO', filename);
            
            this.stopCurrentStream();
            this.closeMediaModal();
        };
        
        this.mediaRecorder.start();
        this.updateRecordingUI(true);
        this.startRecordingTimer();
    }
    
    stopVideoRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.stopRecordingTimer();
        }
    }
    
    updateRecordingUI(recording) {
        const recordBtn = document.getElementById('record-video-btn');
        const timer = document.getElementById('recording-timer');
        
        if (recording) {
            recordBtn.innerHTML = '<i class="fas fa-stop mr-2"></i>Arrêter l\'enregistrement';
            recordBtn.classList.remove('bg-red-600', 'hover:bg-red-700');
            recordBtn.classList.add('bg-gray-600', 'hover:bg-gray-700');
            timer.classList.remove('hidden');
        } else {
            recordBtn.innerHTML = '<i class="fas fa-circle mr-2"></i>Commencer l\'enregistrement';
            recordBtn.classList.remove('bg-gray-600', 'hover:bg-gray-700');
            recordBtn.classList.add('bg-red-600', 'hover:bg-red-700');
            timer.classList.add('hidden');
        }
    }
    
    startRecordingTimer() {
        this.recordingStartTime = Date.now();
        this.recordingTimer = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.recordingStartTime) / 1000);
            const minutes = Math.floor(elapsed / 60).toString().padStart(2, '0');
            const seconds = (elapsed % 60).toString().padStart(2, '0');
            
            const timerElement = document.querySelector('#recording-timer span');
            if (timerElement) {
                timerElement.textContent = `${minutes}:${seconds}`;
            }
        }, 1000);
    }
    
    stopRecordingTimer() {
        if (this.recordingTimer) {
            clearInterval(this.recordingTimer);
            this.recordingTimer = null;
        }
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
            this.stopAudioRecording(pointId, button);
        }
    }
    
    startAudioRecording(pointId, button) {
        this.currentPointId = pointId;
        
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
                    
                    // Arrêter le stream
                    stream.getTracks().forEach(track => track.stop());
                    
                    // Réinitialiser le bouton
                    this.resetAudioButton(button);
                };
                
                this.audioRecorder.start();
                this.updateAudioButton(button, true);
            })
            .catch(error => {
                console.error('Erreur accès microphone:', error);
                this.showError('Impossible d\'accéder au microphone');
                this.resetAudioButton(button);
            });
    }
    
    stopAudioRecording(pointId, button) {
        if (this.audioRecorder && this.audioRecorder.state === 'recording') {
            this.audioRecorder.stop();
        }
    }
    
    updateAudioButton(button, recording) {
        if (recording) {
            button.innerHTML = '<i class="fas fa-stop mr-2 text-red-600"></i>Arrêter';
            button.classList.add('bg-red-50', 'border-red-300');
        }
    }
    
    resetAudioButton(button) {
        button.innerHTML = '<i class="fas fa-microphone mr-2"></i>Audio';
        button.classList.remove('bg-red-50', 'border-red-300');
    }
    
    // ========================================
    // GESTION FICHIERS
    // ========================================
    
    handleFileUpload(input, pointId) {
        const files = Array.from(input.files);
        
        if (files.length === 0) return;
        
        // Vérifier la taille des fichiers
        for (let file of files) {
            if (file.size > this.maxFileSize) {
                this.showError(`Le fichier ${file.name} est trop volumineux (max 50MB)`);
                return;
            }
        }
        
        // Uploader chaque fichier
        files.forEach(file => {
            this.uploadMedia(file, pointId, this.getFileType(file), file.name);
        });
        
        // Reset input
        input.value = '';
    }
    
    getFileType(file) {
        const mimeType = file.type.toLowerCase();
        
        if (mimeType.startsWith('image/')) return 'PHOTO';
        if (mimeType.startsWith('video/')) return 'VIDEO';
        if (mimeType.startsWith('audio/')) return 'AUDIO';
        return 'DOCUMENT';
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
                        this.showSuccess('Fichier uploadé avec succès');
                        this.addMediaToContainer(response.media, pointId);
                    } else {
                        this.showError('Erreur: ' + response.error);
                    }
                } catch (e) {
                    this.showError('Erreur lors du traitement de la réponse');
                }
            } else {
                this.showError('Erreur lors de l\'upload');
            }
        };
        
        xhr.onerror = () => {
            this.hideUploadProgress(pointId);
            this.showError('Erreur de connexion');
        };
        
        const uploadUrl = document.getElementById('intervention-meta-data')?.dataset?.mediaUploadUrl;
        if (!uploadUrl) {
            this.showError('URL d\'upload non configurée');
            return;
        }
        
        xhr.open('POST', uploadUrl);
        xhr.send(formData);
    }
    
    // ========================================
    // GESTION AFFICHAGE MÉDIAS
    // ========================================
    
    addMediaToContainer(media, pointId) {
        const container = document.getElementById(`media-container-${pointId}`);
        if (!container) return;
        
        const mediaElement = document.createElement('div');
        mediaElement.className = 'relative group';
        mediaElement.dataset.mediaId = media.id;
        
        let content = '';
        
        if (media.type_fichier === 'PHOTO') {
            content = `
                <div class="w-20 h-20 rounded-lg overflow-hidden border border-gray-200 cursor-pointer"
                     onclick="viewMedia('${media.fichier_url}', 'image', '${media.nom_original}')">
                    <img src="${media.fichier_url}" alt="${media.nom_original}" 
                         class="w-full h-full object-cover">
                </div>
            `;
        } else if (media.type_fichier === 'VIDEO') {
            content = `
                <div class="w-20 h-20 rounded-lg bg-gray-100 border border-gray-200 flex items-center justify-center cursor-pointer"
                     onclick="viewMedia('${media.fichier_url}', 'video', '${media.nom_original}')">
                    <i class="fas fa-video text-2xl text-blue-500"></i>
                </div>
            `;
        } else if (media.type_fichier === 'AUDIO') {
            content = `
                <div class="w-20 h-20 rounded-lg bg-green-50 border border-green-200 flex flex-col items-center justify-center p-2">
                    <i class="fas fa-music text-lg text-green-600 mb-1"></i>
                    <span class="text-xs text-green-800 text-center">Audio</span>
                    <audio id="audio-${media.id}" class="hidden w-full mt-1" controls>
                        <source src="${media.fichier_url}" type="audio/mpeg">
                    </audio>
                    <button onclick="toggleAudioPlayer('audio-${media.id}')" class="text-xs text-green-600 mt-1">
                        ▶ Play
                    </button>
                </div>
            `;
        } else {
            const truncatedName = media.nom_original.length > 10 ? 
                media.nom_original.substring(0, 10) + '...' : media.nom_original;
            content = `
                <div class="w-20 h-20 rounded-lg bg-gray-50 border border-gray-200 flex flex-col items-center justify-center p-2 cursor-pointer"
                     onclick="window.open('${media.fichier_url}', '_blank')">
                    <i class="fas fa-file text-lg text-gray-600 mb-1"></i>
                    <span class="text-xs text-gray-800 text-center">${truncatedName}</span>
                </div>
            `;
        }
        
        // Bouton de suppression
        content += `
            <button onclick="deleteMedia(${media.id}, ${pointId})" 
                    class="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        mediaElement.innerHTML = content;
        container.appendChild(mediaElement);
    }
    
    deleteMedia(mediaId, pointId) {
        if (!confirm('Êtes-vous sûr de vouloir supprimer ce fichier ?')) {
            return;
        }
        
        fetch(`/media/${mediaId}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.csrfToken,
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const mediaElement = document.querySelector(`[data-media-id="${mediaId}"]`);
                if (mediaElement) {
                    mediaElement.remove();
                }
                this.showSuccess('Fichier supprimé');
            } else {
                this.showError('Erreur lors de la suppression');
            }
        })
        .catch(error => {
            this.showError('Erreur de connexion');
        });
    }
    
    // ========================================
    // VISUALISATION MÉDIAS
    // ========================================
    
    viewMedia(url, type, filename) {
        const modal = document.getElementById('media-view-modal');
        const title = document.getElementById('view-modal-title');
        const content = document.getElementById('view-modal-content');
        
        title.textContent = filename;
        
        let mediaContent = '';
        
        if (type === 'image') {
            mediaContent = `<img src="${url}" alt="${filename}" class="max-w-full max-h-96 mx-auto rounded-lg">`;
        } else if (type === 'video') {
            mediaContent = `
                <video controls class="max-w-full max-h-96 mx-auto rounded-lg">
                    <source src="${url}" type="video/mp4">
                    <source src="${url}" type="video/webm">
                    Votre navigateur ne supporte pas la lecture vidéo.
                </video>
            `;
        } else if (type === 'audio') {
            mediaContent = `
                <div class="p-8 text-center">
                    <i class="fas fa-music text-6xl text-gray-400 mb-4"></i>
                    <p class="text-gray-600 mb-4">${filename}</p>
                    <audio controls class="w-full max-w-md">
                        <source src="${url}" type="audio/mpeg">
                        <source src="${url}" type="audio/wav">
                        Votre navigateur ne supporte pas la lecture audio.
                    </audio>
                </div>
            `;
        } else {
            mediaContent = `
                <div class="p-8 text-center">
                    <i class="fas fa-file text-6xl text-gray-400 mb-4"></i>
                    <p class="text-gray-600 mb-4">${filename}</p>
                    <a href="${url}" target="_blank" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
                        Ouvrir le fichier
                    </a>
                </div>
            `;
        }
        
        content.innerHTML = mediaContent;
        modal.classList.remove('hidden');
    }
    
    // ========================================
    // GESTION MODALS
    // ========================================
    
    showMediaModal(title) {
        const modal = document.getElementById('media-modal');
        const modalTitle = document.getElementById('media-modal-title');
        
        modalTitle.textContent = title;
        modal.classList.remove('hidden');
    }
    
    closeMediaModal() {
        const modal = document.getElementById('media-modal');
        
        // Arrêter tous les streams en cours
        this.stopCurrentStream();
        
        // Arrêter les enregistrements
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
        }
        
        if (this.audioRecorder && this.audioRecorder.state === 'recording') {
            this.audioRecorder.stop();
        }
        
        // Nettoyer les timers
        this.stopRecordingTimer();
        
        modal.classList.add('hidden');
    }
    
    closeViewModal() {
        const modal = document.getElementById('media-view-modal');
        const content = document.getElementById('view-modal-content');
        
        // Arrêter tous les médias en cours
        const videos = content.querySelectorAll('video');
        const audios = content.querySelectorAll('audio');
        
        videos.forEach(video => {
            video.pause();
            video.currentTime = 0;
        });
        
        audios.forEach(audio => {
            audio.pause();
            audio.currentTime = 0;
        });
        
        modal.classList.add('hidden');
    }
    
    stopCurrentStream() {
        if (this.currentStream) {
            this.currentStream.getTracks().forEach(track => track.stop());
            this.currentStream = null;
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
    // MESSAGES
    // ========================================
    
    showSuccess(message) {
        this.showMessage(message, 'success');
    }
    
    showError(message) {
        this.showMessage(message, 'error');
    }
    
    showMessage(message, type) {
        // Utiliser la fonction globale showToast si disponible
        if (window.showToast) {
            window.showToast(message, type);
            return;
        }
        
        // Fallback
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
window.capturePhoto = function(pointId) {
    if (mediaManager) mediaManager.capturePhoto(pointId);
};

window.captureVideo = function(pointId) {
    if (mediaManager) mediaManager.captureVideo(pointId);
};

window.toggleAudioRecording = function(pointId) {
    if (mediaManager) mediaManager.toggleAudioRecording(pointId);
};

window.handleFileUpload = function(input, pointId) {
    if (mediaManager) mediaManager.handleFileUpload(input, pointId);
};

window.deleteMedia = function(mediaId, pointId) {
    if (mediaManager) mediaManager.deleteMedia(mediaId, pointId);
};

window.closeMediaModal = function() {
    if (mediaManager) mediaManager.closeMediaModal();
};

window.closeViewModal = function() {
    if (mediaManager) mediaManager.closeViewModal();
};

window.viewMedia = function(url, mimeType, nomOriginal) {
    if (mediaManager) mediaManager.viewMedia(url, mimeType, nomOriginal);
};

window.toggleAudioPlayer = function(audioId) {
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
};