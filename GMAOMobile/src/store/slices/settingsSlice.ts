// src/store/slices/settingsSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

// Types pour les paramètres
interface SettingsState {
  // Synchronisation
  autoSync: boolean;
  syncInterval: number; // en minutes
  syncWifiOnly: boolean;
  uploadMediaWifiOnly: boolean;
  
  // Interface
  theme: 'light' | 'dark' | 'auto';
  language: 'fr' | 'en';
  fontSize: 'small' | 'medium' | 'large';
  
  // Notifications
  notificationsEnabled: boolean;
  soundEnabled: boolean;
  vibrationEnabled: boolean;
  showNewWorkOrderNotification: boolean;
  showSyncNotification: boolean;
  
  // Géolocalisation
  locationEnabled: boolean;
  locationPrecision: 'high' | 'medium' | 'low';
  trackLocation: boolean;
  
  // Caméra et média
  photoQuality: 'low' | 'medium' | 'high';
  videoQuality: 'low' | 'medium' | 'high';
  compressMedia: boolean;
  maxPhotoSize: number; // en MB
  
  // Sécurité
  biometricEnabled: boolean;
  autoLockTime: number; // en minutes (0 = disabled)
  requirePinForSensitiveActions: boolean;
  
  // Debug et développement
  debugMode: boolean;
  logLevel: 'error' | 'warn' | 'info' | 'debug';
  
  // Cache et stockage
  cacheSize: number; // en MB
  autoCleanCache: boolean;
  keepDataDuration: number; // en jours (0 = illimité)
  
  // Formulaires
  autoSaveInterval: number; // en secondes
  confirmBeforeDelete: boolean;
  showProgressIndicators: boolean;
}

// État initial
const initialState: SettingsState = {
  // Synchronisation
  autoSync: true,
  syncInterval: 15, // 15 minutes
  syncWifiOnly: false,
  uploadMediaWifiOnly: true,
  
  // Interface
  theme: 'auto',
  language: 'fr',
  fontSize: 'medium',
  
  // Notifications
  notificationsEnabled: true,
  soundEnabled: true,
  vibrationEnabled: true,
  showNewWorkOrderNotification: true,
  showSyncNotification: false,
  
  // Géolocalisation
  locationEnabled: true,
  locationPrecision: 'high',
  trackLocation: true,
  
  // Caméra et média
  photoQuality: 'medium',
  videoQuality: 'medium',
  compressMedia: true,
  maxPhotoSize: 5, // 5 MB
  
  // Sécurité
  biometricEnabled: false,
  autoLockTime: 0, // Désactivé par défaut
  requirePinForSensitiveActions: false,
  
  // Debug
  debugMode: false,
  logLevel: 'error',
  
  // Cache
  cacheSize: 100, // 100 MB
  autoCleanCache: true,
  keepDataDuration: 0, // Illimité par défaut
  
  // Formulaires
  autoSaveInterval: 30, // 30 secondes
  confirmBeforeDelete: true,
  showProgressIndicators: true,
};

// Slice
const settingsSlice = createSlice({
  name: 'settings',
  initialState,
  reducers: {
    updateSetting: <K extends keyof SettingsState>(
      state: SettingsState,
      action: PayloadAction<{ key: K; value: SettingsState[K] }>
    ) => {
      const { key, value } = action.payload;
      state[key] = value;
    },
    
    updateMultipleSettings: (state, action: PayloadAction<Partial<SettingsState>>) => {
      Object.assign(state, action.payload);
    },
    
    resetSettings: () => initialState,
    
    resetSyncSettings: (state) => {
      state.autoSync = initialState.autoSync;
      state.syncInterval = initialState.syncInterval;
      state.syncWifiOnly = initialState.syncWifiOnly;
      state.uploadMediaWifiOnly = initialState.uploadMediaWifiOnly;
    },
    
    resetNotificationSettings: (state) => {
      state.notificationsEnabled = initialState.notificationsEnabled;
      state.soundEnabled = initialState.soundEnabled;
      state.vibrationEnabled = initialState.vibrationEnabled;
      state.showNewWorkOrderNotification = initialState.showNewWorkOrderNotification;
      state.showSyncNotification = initialState.showSyncNotification;
    },
    
    resetMediaSettings: (state) => {
      state.photoQuality = initialState.photoQuality;
      state.videoQuality = initialState.videoQuality;
      state.compressMedia = initialState.compressMedia;
      state.maxPhotoSize = initialState.maxPhotoSize;
    },
    
    toggleSetting: <K extends keyof SettingsState>(
      state: SettingsState,
      action: PayloadAction<K>
    ) => {
      const key = action.payload;
      if (typeof state[key] === 'boolean') {
        (state[key] as boolean) = !(state[key] as boolean);
      }
    },
    
    // Actions spécifiques pour des cas d'usage fréquents
    toggleAutoSync: (state) => {
      state.autoSync = !state.autoSync;
    },
    
    toggleWifiOnly: (state) => {
      state.syncWifiOnly = !state.syncWifiOnly;
    },
    
    toggleBiometric: (state) => {
      state.biometricEnabled = !state.biometricEnabled;
    },
    
    toggleDebugMode: (state) => {
      state.debugMode = !state.debugMode;
      // Ajuster le niveau de log automatiquement
      state.logLevel = state.debugMode ? 'debug' : 'error';
    },
    
    setTheme: (state, action: PayloadAction<'light' | 'dark' | 'auto'>) => {
      state.theme = action.payload;
    },
    
    setLanguage: (state, action: PayloadAction<'fr' | 'en'>) => {
      state.language = action.payload;
    },
    
    setSyncInterval: (state, action: PayloadAction<number>) => {
      // Valider l'intervalle (minimum 5 minutes)
      state.syncInterval = Math.max(5, action.payload);
    },
    
    setAutoLockTime: (state, action: PayloadAction<number>) => {
      // Valider le temps (0 pour désactivé, sinon minimum 1 minute)
      state.autoLockTime = action.payload === 0 ? 0 : Math.max(1, action.payload);
    },
    
    setCacheSize: (state, action: PayloadAction<number>) => {
      // Valider la taille du cache (minimum 10 MB, maximum 1000 MB)
      state.cacheSize = Math.min(1000, Math.max(10, action.payload));
    },
  },
});

// Actions
export const {
  updateSetting,
  updateMultipleSettings,
  resetSettings,
  resetSyncSettings,
  resetNotificationSettings,
  resetMediaSettings,
  toggleSetting,
  toggleAutoSync,
  toggleWifiOnly,
  toggleBiometric,
  toggleDebugMode,
  setTheme,
  setLanguage,
  setSyncInterval,
  setAutoLockTime,
  setCacheSize,
} = settingsSlice.actions;

// Sélecteurs
export const selectSettings = (state: any) => state.settings;
export const selectSyncSettings = (state: any) => ({
  autoSync: state.settings.autoSync,
  syncInterval: state.settings.syncInterval,
  syncWifiOnly: state.settings.syncWifiOnly,
  uploadMediaWifiOnly: state.settings.uploadMediaWifiOnly,
});
export const selectUISettings = (state: any) => ({
  theme: state.settings.theme,
  language: state.settings.language,
  fontSize: state.settings.fontSize,
});
export const selectNotificationSettings = (state: any) => ({
  notificationsEnabled: state.settings.notificationsEnabled,
  soundEnabled: state.settings.soundEnabled,
  vibrationEnabled: state.settings.vibrationEnabled,
  showNewWorkOrderNotification: state.settings.showNewWorkOrderNotification,
  showSyncNotification: state.settings.showSyncNotification,
});
export const selectLocationSettings = (state: any) => ({
  locationEnabled: state.settings.locationEnabled,
  locationPrecision: state.settings.locationPrecision,
  trackLocation: state.settings.trackLocation,
});
export const selectMediaSettings = (state: any) => ({
  photoQuality: state.settings.photoQuality,
  videoQuality: state.settings.videoQuality,
  compressMedia: state.settings.compressMedia,
  maxPhotoSize: state.settings.maxPhotoSize,
});
export const selectSecuritySettings = (state: any) => ({
  biometricEnabled: state.settings.biometricEnabled,
  autoLockTime: state.settings.autoLockTime,
  requirePinForSensitiveActions: state.settings.requirePinForSensitiveActions,
});
export const selectDebugSettings = (state: any) => ({
  debugMode: state.settings.debugMode,
  logLevel: state.settings.logLevel,
});

export default settingsSlice.reducer;