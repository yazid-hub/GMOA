// src/store/slices/authSlice.ts
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { UserProfile } from '../../types/database';
import { ApiClient } from '../../services/api/ApiClient';
import DatabaseManager from '../../database/DatabaseManager';
import { TABLES } from '../../database/schema';

// Types pour l'état d'authentification
interface AuthState {
  isAuthenticated: boolean;
  user: UserProfile | null;
  token: string | null;
  refreshToken: string | null;
  loading: boolean;
  error: string | null;
  lastLoginTime: string | null;
  biometricEnabled: boolean;
}

// État initial
const initialState: AuthState = {
  isAuthenticated: false,
  user: null,
  token: null,
  refreshToken: null,
  loading: false,
  error: null,
  lastLoginTime: null,
  biometricEnabled: false,
};

// Thunks asynchrones
export const loginUser = createAsyncThunk(
  'auth/loginUser',
  async (credentials: { username: string; password: string }, { rejectWithValue }) => {
    try {
      // Appel API de connexion
      const response = await ApiClient.login(credentials);
      
      if (response.success) {
        // Sauvegarder le profil utilisateur en local
        const db = DatabaseManager.getInstance();
        await db.upsert(TABLES.USER_PROFILE, {
          server_id: response.user.id,
          username: response.user.username,
          first_name: response.user.first_name,
          last_name: response.user.last_name,
          email: response.user.email,
          role: response.user.role || 'TECHNICIEN',
          team_id: response.user.team_id,
          competences: JSON.stringify(response.user.competences || []),
          is_active: true,
          last_sync: new Date().toISOString(),
        }, ['server_id']);

        return {
          user: response.user,
          token: response.token,
          refreshToken: response.refreshToken,
        };
      } else {
        return rejectWithValue(response.error || 'Erreur de connexion');
      }
    } catch (error: any) {
      return rejectWithValue(error.message || 'Erreur réseau');
    }
  }
);

export const refreshAuthToken = createAsyncThunk(
  'auth/refreshToken',
  async (_, { getState, rejectWithValue }) => {
    try {
      const state = getState() as any;
      const refreshToken = state.auth.refreshToken;
      
      if (!refreshToken) {
        return rejectWithValue('Token de rafraîchissement manquant');
      }

      const response = await ApiClient.refreshToken(refreshToken);
      
      if (response.success) {
        return {
          token: response.token,
          refreshToken: response.refreshToken,
        };
      } else {
        return rejectWithValue(response.error || 'Erreur de rafraîchissement');
      }
    } catch (error: any) {
      return rejectWithValue(error.message || 'Erreur réseau');
    }
  }
);

export const logoutUser = createAsyncThunk(
  'auth/logoutUser',
  async (_, { getState }) => {
    try {
      const state = getState() as any;
      const token = state.auth.token;
      
      // Tenter de déconnecter côté serveur
      if (token) {
        await ApiClient.logout(token);
      }
    } catch (error) {
      // Ignorer les erreurs de déconnexion côté serveur
      console.warn('Erreur lors de la déconnexion serveur:', error);
    }
    
    return true;
  }
);

export const loadUserFromStorage = createAsyncThunk(
  'auth/loadUserFromStorage',
  async () => {
    try {
      const db = DatabaseManager.getInstance();
      const user = await db.selectOne(`SELECT * FROM ${TABLES.USER_PROFILE} WHERE is_active = 1`);
      
      return user;
    } catch (error) {
      console.error('Erreur chargement utilisateur:', error);
      return null;
    }
  }
);

// Slice
const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    
    setUser: (state, action: PayloadAction<UserProfile>) => {
      state.user = action.payload;
    },
    
    setBiometric: (state, action: PayloadAction<boolean>) => {
      state.biometricEnabled = action.payload;
    },
    
    updateUserProfile: (state, action: PayloadAction<Partial<UserProfile>>) => {
      if (state.user) {
        state.user = { ...state.user, ...action.payload };
      }
    },
    
    // Pour la déconnexion forcée (token expiré)
    forceLogout: (state) => {
      state.isAuthenticated = false;
      state.user = null;
      state.token = null;
      state.refreshToken = null;
      state.error = 'Session expirée. Veuillez vous reconnecter.';
    },
  },
  
  extraReducers: (builder) => {
    // Connexion
    builder
      .addCase(loginUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.loading = false;
        state.isAuthenticated = true;
        state.user = action.payload.user;
        state.token = action.payload.token;
        state.refreshToken = action.payload.refreshToken;
        state.lastLoginTime = new Date().toISOString();
        state.error = null;
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.loading = false;
        state.isAuthenticated = false;
        state.error = action.payload as string;
      });

    // Rafraîchissement token
    builder
      .addCase(refreshAuthToken.fulfilled, (state, action) => {
        state.token = action.payload.token;
        state.refreshToken = action.payload.refreshToken;
        state.error = null;
      })
      .addCase(refreshAuthToken.rejected, (state, action) => {
        state.isAuthenticated = false;
        state.user = null;
        state.token = null;
        state.refreshToken = null;
        state.error = action.payload as string;
      });

    // Déconnexion
    builder
      .addCase(logoutUser.fulfilled, (state) => {
        state.isAuthenticated = false;
        state.user = null;
        state.token = null;
        state.refreshToken = null;
        state.error = null;
        state.lastLoginTime = null;
      });

    // Chargement utilisateur depuis le stockage
    builder
      .addCase(loadUserFromStorage.fulfilled, (state, action) => {
        if (action.payload) {
          state.user = action.payload;
          // Ne pas marquer comme authentifié sans token valide
        }
      });
  },
});

// Actions
export const { 
  clearError, 
  setUser, 
  setBiometric, 
  updateUserProfile, 
  forceLogout 
} = authSlice.actions;

// Sélecteurs
export const selectAuth = (state: any) => state.auth;
export const selectUser = (state: any) => state.auth.user;
export const selectIsAuthenticated = (state: any) => state.auth.isAuthenticated;
export const selectAuthToken = (state: any) => state.auth.token;
export const selectAuthLoading = (state: any) => state.auth.loading;
export const selectAuthError = (state: any) => state.auth.error;

export default authSlice.reducer;