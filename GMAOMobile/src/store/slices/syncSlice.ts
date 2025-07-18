// src/store/slices/syncSlice.ts
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { SyncOperations } from '../../database/operations';
import { SyncService } from '../../services/sync/SyncService';
import NetInfo from '@react-native-community/netinfo';

// Types pour l'état de synchronisation
interface SyncState {
  isOnline: boolean;
  isSyncing: boolean;
  isAutoSyncEnabled: boolean;
  lastSyncTime: string | null;
  syncProgress: {
    current: number;
    total: number;
    currentTable: string | null;
  };
  pendingUploads: number;
  pendingSync: number;
  syncQueue: any[];
  error: string | null;
  syncHistory: SyncLogEntry[];
  connectionType: string | null;
  isWifiOnly: boolean;
}

interface SyncLogEntry {
  id: string;
  timestamp: string;
  type: 'UPLOAD' | 'DOWNLOAD' | 'FULL' | 'PARTIAL';
  status: 'SUCCESS' | 'FAILED' | 'PARTIAL';
  recordsProcessed: number;
  duration: number;
  error?: string;
}

// État initial
const initialState: SyncState = {
  isOnline: false,
  isSyncing: false,
  isAutoSyncEnabled: true,
  lastSyncTime: null,
  syncProgress: {
    current: 0,
    total: 0,
    currentTable: null,
  },
  pendingUploads: 0,
  pendingSync: 0,
  syncQueue: [],
  error: null,
  syncHistory: [],
  connectionType: null,
  isWifiOnly: false,
};

// Thunks asynchrones
export const checkNetworkStatus = createAsyncThunk(
  'sync/checkNetworkStatus',
  async () => {
    const netInfo = await NetInfo.fetch();
    return {
      isConnected: netInfo.isConnected || false,
      type: netInfo.type,
      isWifiConnection: netInfo.type === 'wifi',
    };
  }
);

export const performFullSync = createAsyncThunk(
  'sync/performFullSync',
  async (_, { dispatch, getState }) => {
    try {
      const state = getState() as any;
      
      // Vérifier la connexion
      if (!state.sync.isOnline) {
        throw new Error('Pas de connexion réseau');
      }
      
      // Vérifier si WiFi seulement est activé
      if (state.sync.isWifiOnly && state.sync.connectionType !== 'wifi') {
        throw new Error('Synchronisation limitée au WiFi');
      }

      // Démarrer la synchronisation
      dispatch(startSync({ type: 'FULL', total: 100 }));
      
      const syncResult = await SyncService.performFullSync((progress) => {
        dispatch(updateSyncProgress(progress));
      });

      // Mettre à jour les compteurs
      dispatch(updatePendingCounts());
      
      return {
        ...syncResult,
        timestamp: new Date().toISOString(),
      };
    } catch (error: any) {
      throw error;
    }
  }
);

export const uploadPendingData = createAsyncThunk(
  'sync/uploadPendingData',
  async (_, { dispatch, getState }) => {
    try {
      const state = getState() as any;
      
      if (!state.sync.isOnline) {
        throw new Error('Pas de connexion réseau');
      }

      dispatch(startSync({ type: 'UPLOAD', total: state.sync.pendingSync }));
      
      const uploadResult = await SyncService.uploadPendingData((progress) => {
        dispatch(updateSyncProgress(progress));
      });

      dispatch(updatePendingCounts());
      
      return {
        ...uploadResult,
        timestamp: new Date().toISOString(),
      };
    } catch (error: any) {
      throw error;
    }
  }
);

export const downloadLatestData = createAsyncThunk(
  'sync/downloadLatestData',
  async (userId: number, { dispatch }) => {
    try {
      dispatch(startSync({ type: 'DOWNLOAD', total: 50 }));
      
      const downloadResult = await SyncService.downloadLatestData(userId, (progress) => {
        dispatch(updateSyncProgress(progress));
      });

      dispatch(updatePendingCounts());
      
      return {
        ...downloadResult,
        timestamp: new Date().toISOString(),
      };
    } catch (error: any) {
      throw error;
    }
  }
);

export const updatePendingCounts = createAsyncThunk(
  'sync/updatePendingCounts',
  async () => {
    try {
      // Compter les éléments en attente de synchronisation
      const pendingSyncItems = await SyncOperations.getPendingSyncItems();
      const pendingUploads = await SyncOperations.getPendingUploads();
      
      return {
        pendingSync: pendingSyncItems.length,
        pendingUploads: pendingUploads.length,
      };
    } catch (error: any) {
      console.error('Erreur mise à jour compteurs:', error);
      return { pendingSync: 0, pendingUploads: 0 };
    }
  }
);

export const retryFailedSync = createAsyncThunk(
  'sync/retryFailedSync',
  async (_, { dispatch }) => {
    try {
      const result = await SyncService.retryFailedItems();
      dispatch(updatePendingCounts());
      return result;
    } catch (error: any) {
      throw error;
    }
  }
);

// Slice
const syncSlice = createSlice({
  name: 'sync',
  initialState,
  reducers: {
    setOnlineStatus: (state, action: PayloadAction<boolean>) => {
      state.isOnline = action.payload;
    },
    
    setConnectionType: (state, action: PayloadAction<string | null>) => {
      state.connectionType = action.payload;
    },
    
    setAutoSync: (state, action: PayloadAction<boolean>) => {
      state.isAutoSyncEnabled = action.payload;
    },
    
    setWifiOnly: (state, action: PayloadAction<boolean>) => {
      state.isWifiOnly = action.payload;
    },
    
    startSync: (state, action: PayloadAction<{ type: string; total: number }>) => {
      state.isSyncing = true;
      state.error = null;
      state.syncProgress = {
        current: 0,
        total: action.payload.total,
        currentTable: null,
      };
    },
    
    updateSyncProgress: (state, action: PayloadAction<{ current: number; table?: string }>) => {
      state.syncProgress.current = action.payload.current;
      if (action.payload.table) {
        state.syncProgress.currentTable = action.payload.table;
      }
    },
    
    stopSync: (state) => {
      state.isSyncing = false;
      state.syncProgress = {
        current: 0,
        total: 0,
        currentTable: null,
      };
    },
    
    addSyncLogEntry: (state, action: PayloadAction<SyncLogEntry>) => {
      state.syncHistory.unshift(action.payload);
      // Garder seulement les 50 dernières entrées
      if (state.syncHistory.length > 50) {
        state.syncHistory = state.syncHistory.slice(0, 50);
      }
    },
    
    clearSyncError: (state) => {
      state.error = null;
    },
    
    setSyncQueue: (state, action: PayloadAction<any[]>) => {
      state.syncQueue = action.payload;
    },
    
    updateLastSyncTime: (state, action: PayloadAction<string>) => {
      state.lastSyncTime = action.payload;
    },
  },
  
  extraReducers: (builder) => {
    // Vérification statut réseau
    builder
      .addCase(checkNetworkStatus.fulfilled, (state, action) => {
        state.isOnline = action.payload.isConnected;
        state.connectionType = action.payload.type;
      });

    // Synchronisation complète
    builder
      .addCase(performFullSync.pending, (state) => {
        state.isSyncing = true;
        state.error = null;
      })
      .addCase(performFullSync.fulfilled, (state, action) => {
        state.isSyncing = false;
        state.lastSyncTime = action.payload.timestamp;
        state.syncProgress = { current: 0, total: 0, currentTable: null };
        
        // Ajouter au log
        const logEntry: SyncLogEntry = {
          id: Date.now().toString(),
          timestamp: action.payload.timestamp,
          type: 'FULL',
          status: action.payload.success ? 'SUCCESS' : 'PARTIAL',
          recordsProcessed: action.payload.recordsProcessed,
          duration: action.payload.duration,
        };
        state.syncHistory.unshift(logEntry);
      })
      .addCase(performFullSync.rejected, (state, action) => {
        state.isSyncing = false;
        state.error = action.error.message || 'Erreur synchronisation';
        state.syncProgress = { current: 0, total: 0, currentTable: null };
        
        // Ajouter au log d'erreur
        const logEntry: SyncLogEntry = {
          id: Date.now().toString(),
          timestamp: new Date().toISOString(),
          type: 'FULL',
          status: 'FAILED',
          recordsProcessed: 0,
          duration: 0,
          error: action.error.message,
        };
        state.syncHistory.unshift(logEntry);
      });

    // Upload des données en attente
    builder
      .addCase(uploadPendingData.fulfilled, (state, action) => {
        state.isSyncing = false;
        state.lastSyncTime = action.payload.timestamp;
        state.syncProgress = { current: 0, total: 0, currentTable: null };
        
        const logEntry: SyncLogEntry = {
          id: Date.now().toString(),
          timestamp: action.payload.timestamp,
          type: 'UPLOAD',
          status: action.payload.success ? 'SUCCESS' : 'PARTIAL',
          recordsProcessed: action.payload.recordsProcessed,
          duration: action.payload.duration,
        };
        state.syncHistory.unshift(logEntry);
      })
      .addCase(uploadPendingData.rejected, (state, action) => {
        state.isSyncing = false;
        state.error = action.error.message || 'Erreur upload';
        state.syncProgress = { current: 0, total: 0, currentTable: null };
      });

    // Téléchargement des dernières données
    builder
      .addCase(downloadLatestData.fulfilled, (state, action) => {
        state.isSyncing = false;
        state.lastSyncTime = action.payload.timestamp;
        state.syncProgress = { current: 0, total: 0, currentTable: null };
        
        const logEntry: SyncLogEntry = {
          id: Date.now().toString(),
          timestamp: action.payload.timestamp,
          type: 'DOWNLOAD',
          status: action.payload.success ? 'SUCCESS' : 'PARTIAL',
          recordsProcessed: action.payload.recordsProcessed,
          duration: action.payload.duration,
        };
        state.syncHistory.unshift(logEntry);
      })
      .addCase(downloadLatestData.rejected, (state, action) => {
        state.isSyncing = false;
        state.error = action.error.message || 'Erreur téléchargement';
        state.syncProgress = { current: 0, total: 0, currentTable: null };
      });

    // Mise à jour des compteurs
    builder
      .addCase(updatePendingCounts.fulfilled, (state, action) => {
        state.pendingSync = action.payload.pendingSync;
        state.pendingUploads = action.payload.pendingUploads;
      });

    // Retry des éléments échoués
    builder
      .addCase(retryFailedSync.fulfilled, (state, action) => {
        const logEntry: SyncLogEntry = {
          id: Date.now().toString(),
          timestamp: new Date().toISOString(),
          type: 'PARTIAL',
          status: action.payload.success ? 'SUCCESS' : 'FAILED',
          recordsProcessed: action.payload.recordsProcessed,
          duration: action.payload.duration,
        };
        state.syncHistory.unshift(logEntry);
      });
  },
});

// Actions
export const {
  setOnlineStatus,
  setConnectionType,
  setAutoSync,
  setWifiOnly,
  startSync,
  updateSyncProgress,
  stopSync,
  addSyncLogEntry,
  clearSyncError,
  setSyncQueue,
  updateLastSyncTime,
} = syncSlice.actions;

// Sélecteurs
export const selectSyncState = (state: any) => state.sync;
export const selectIsOnline = (state: any) => state.sync.isOnline;
export const selectIsSyncing = (state: any) => state.sync.isSyncing;
export const selectSyncProgress = (state: any) => state.sync.syncProgress;
export const selectPendingCounts = (state: any) => ({
  sync: state.sync.pendingSync,
  uploads: state.sync.pendingUploads,
});
export const selectLastSyncTime = (state: any) => state.sync.lastSyncTime;
export const selectSyncError = (state: any) => state.sync.error;
export const selectSyncHistory = (state: any) => state.sync.syncHistory;
export const selectIsAutoSyncEnabled = (state: any) => state.sync.isAutoSyncEnabled;
export const selectConnectionType = (state: any) => state.sync.connectionType;
export const selectIsWifiOnly = (state: any) => state.sync.isWifiOnly;

// Sélecteur pour vérifier si la synchronisation est possible
export const selectCanSync = (state: any) => {
  const sync = state.sync;
  return sync.isOnline && !sync.isSyncing && (!sync.isWifiOnly || sync.connectionType === 'wifi');
};

export default syncSlice.reducer;