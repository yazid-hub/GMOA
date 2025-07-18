// src/store/slices/networkSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

// Types pour l'état réseau
interface NetworkState {
  isConnected: boolean;
  connectionType: string | null;
  isWifiConnection: boolean;
  isCellularConnection: boolean;
  isExpensive: boolean;
  strength: number | null; // Signal strength (0-100)
  lastConnectedTime: string | null;
  lastDisconnectedTime: string | null;
  reconnectAttempts: number;
  isReconnecting: boolean;
}

// État initial
const initialState: NetworkState = {
  isConnected: false,
  connectionType: null,
  isWifiConnection: false,
  isCellularConnection: false,
  isExpensive: false,
  strength: null,
  lastConnectedTime: null,
  lastDisconnectedTime: null,
  reconnectAttempts: 0,
  isReconnecting: false,
};

// Slice
const networkSlice = createSlice({
  name: 'network',
  initialState,
  reducers: {
    setNetworkState: (state, action: PayloadAction<{
      isConnected: boolean;
      type: string | null;
      isWifiConnection?: boolean;
      isCellularConnection?: boolean;
      isExpensive?: boolean;
      strength?: number | null;
    }>) => {
      const { isConnected, type, isWifiConnection, isCellularConnection, isExpensive, strength } = action.payload;
      
      // Détecter les changements de connexion
      const wasConnected = state.isConnected;
      const now = new Date().toISOString();
      
      state.isConnected = isConnected;
      state.connectionType = type;
      state.isWifiConnection = isWifiConnection || false;
      state.isCellularConnection = isCellularConnection || false;
      state.isExpensive = isExpensive || false;
      state.strength = strength || null;
      
      // Mettre à jour les timestamps
      if (isConnected && !wasConnected) {
        state.lastConnectedTime = now;
        state.reconnectAttempts = 0;
        state.isReconnecting = false;
      } else if (!isConnected && wasConnected) {
        state.lastDisconnectedTime = now;
      }
    },
    
    incrementReconnectAttempts: (state) => {
      state.reconnectAttempts += 1;
    },
    
    setReconnecting: (state, action: PayloadAction<boolean>) => {
      state.isReconnecting = action.payload;
    },
    
    resetReconnectAttempts: (state) => {
      state.reconnectAttempts = 0;
      state.isReconnecting = false;
    },
    
    updateSignalStrength: (state, action: PayloadAction<number>) => {
      state.strength = action.payload;
    },
  },
});

// Actions
export const {
  setNetworkState,
  incrementReconnectAttempts,
  setReconnecting,
  resetReconnectAttempts,
  updateSignalStrength,
} = networkSlice.actions;

// Sélecteurs
export const selectNetworkState = (state: any) => state.network;
export const selectIsConnected = (state: any) => state.network.isConnected;
export const selectConnectionType = (state: any) => state.network.connectionType;
export const selectIsWifiConnection = (state: any) => state.network.isWifiConnection;
export const selectIsCellularConnection = (state: any) => state.network.isCellularConnection;
export const selectIsExpensiveConnection = (state: any) => state.network.isExpensive;
export const selectSignalStrength = (state: any) => state.network.strength;
export const selectReconnectAttempts = (state: any) => state.network.reconnectAttempts;
export const selectIsReconnecting = (state: any) => state.network.isReconnecting;

// Sélecteur pour déterminer si on peut utiliser le réseau pour la sync
export const selectCanUseNetwork = (state: any) => {
  const network = state.network;
  const settings = state.settings;
  
  if (!network.isConnected) return false;
  
  // Si "WiFi seulement" est activé
  if (settings?.syncWifiOnly && !network.isWifiConnection) {
    return false;
  }
  
  return true;
};

export default networkSlice.reducer;