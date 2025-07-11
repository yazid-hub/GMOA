class OfflineManager {
    constructor() {
        this.syncQueue = [];
        this.isOnline = navigator.onLine;
        this.setupEventListeners();
    }
    
    // Méthodes : queueForSync, syncWhenOnline, handleOfflineMode
}