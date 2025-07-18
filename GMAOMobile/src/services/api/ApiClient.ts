// src/services/api/ApiClient.ts
import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import { store } from '../../store/store';
import { forceLogout, refreshAuthToken } from '../../store/slices/authSlice';
import { setNetworkState } from '../../store/slices/networkSlice';

// Configuration API
const API_CONFIG = {
  BASE_URL: __DEV__ ? 'http://10.0.2.2:8000' : 'https://votre-domaine.com', // 10.0.2.2 pour émulateur Android
  MOBILE_API_PREFIX: '/api/mobile',
  TIMEOUT: 30000, // 30 secondes
  MAX_RETRIES: 3,
};

// Types pour les réponses API
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  status?: number;
}

export interface LoginResponse {
  token: string;
  refreshToken?: string;
  user: {
    id: number;
    username: string;
    first_name: string;
    last_name: string;
    email: string;
    role: string;
    full_name: string;
  };
  permissions: Record<string, boolean>;
}

export interface SyncResponse {
  success: boolean;
  timestamp: string;
  data: {
    ordres_travail: any[];
    interventions: any[];
    assets: any[];
  };
  counts: {
    ordres_travail: number;
    interventions: number;
    assets: number;
  };
}

class ApiClient {
  private static instance: ApiClient;
  private axiosInstance: AxiosInstance;
  private isRefreshing = false;
  private failedQueue: Array<{
    resolve: (value?: unknown) => void;
    reject: (reason?: any) => void;
  }> = [];

  private constructor() {
    this.axiosInstance = axios.create({
      baseURL: API_CONFIG.BASE_URL + API_CONFIG.MOBILE_API_PREFIX,
      timeout: API_CONFIG.TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    });

    this.setupInterceptors();
    this.setupNetworkMonitoring();
  }

  public static getInstance(): ApiClient {
    if (!ApiClient.instance) {
      ApiClient.instance = new ApiClient();
    }
    return ApiClient.instance;
  }

  /**
   * Configuration des intercepteurs
   */
  private setupInterceptors(): void {
    // Intercepteur de requête
    this.axiosInstance.interceptors.request.use(
      async (config) => {
        // Ajouter le token d'authentification
        const token = await AsyncStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Token ${token}`;
        }

        // Ajouter des headers spécifiques mobile
        config.headers['X-Mobile-App'] = 'GMAO-Mobile';
        config.headers['X-App-Version'] = '1.0.0';
        config.headers['X-Platform'] = 'react-native';

        console.log(`🔄 API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('❌ Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Intercepteur de réponse
    this.axiosInstance.interceptors.response.use(
      (response: AxiosResponse) => {
        console.log(`✅ API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      async (error: AxiosError) => {
        const originalRequest = error.config as any;

        console.error(`❌ API Error: ${error.response?.status} ${error.config?.url}`, error.response?.data);

        // Gestion de l'expiration du token (401)
        if (error.response?.status === 401 && !originalRequest._retry) {
          if (this.isRefreshing) {
            // Si un refresh est déjà en cours, attendre
            return new Promise((resolve, reject) => {
              this.failedQueue.push({ resolve, reject });
            }).then(() => {
              return this.axiosInstance(originalRequest);
            }).catch(err => {
              return Promise.reject(err);
            });
          }

          originalRequest._retry = true;
          this.isRefreshing = true;

          try {
            // Tenter de rafraîchir le token
            const refreshToken = await AsyncStorage.getItem('refresh_token');
            if (refreshToken) {
              const response = await store.dispatch(refreshAuthToken()).unwrap();
              await AsyncStorage.setItem('auth_token', response.token);
              
              // Traiter la queue des requêtes en attente
              this.processQueue(null);
              
              // Relancer la requête originale
              return this.axiosInstance(originalRequest);
            } else {
              throw new Error('No refresh token');
            }
          } catch (refreshError) {
            // Échec du refresh, déconnecter l'utilisateur
            this.processQueue(refreshError);
            store.dispatch(forceLogout());
            await AsyncStorage.multiRemove(['auth_token', 'refresh_token']);
            return Promise.reject(refreshError);
          } finally {
            this.isRefreshing = false;
          }
        }

        // Gestion des autres erreurs
        return Promise.reject(this.handleApiError(error));
      }
    );
  }

  /**
   * Traite la queue des requêtes en attente
   */
  private processQueue(error: any): void {
    this.failedQueue.forEach(({ resolve, reject }) => {
      if (error) {
        reject(error);
      } else {
        resolve();
      }
    });
    
    this.failedQueue = [];
  }

  /**
   * Surveillance de la connexion réseau
   */
  private setupNetworkMonitoring(): void {
    NetInfo.addEventListener(state => {
      store.dispatch(setNetworkState({
        isConnected: state.isConnected || false,
        type: state.type,
        isWifiConnection: state.type === 'wifi',
        isCellularConnection: state.type === 'cellular',
        isExpensive: state.isConnectionExpensive || false,
      }));
    });
  }

  /**
   * Gestion des erreurs API
   */
  private handleApiError(error: AxiosError): ApiResponse {
    const response = error.response;
    
    if (!response) {
      // Erreur réseau
      return {
        success: false,
        error: 'Erreur de connexion réseau',
        status: 0
      };
    }

    const errorMessage = this.extractErrorMessage(response.data);
    
    return {
      success: false,
      error: errorMessage,
      status: response.status,
      data: response.data
    };
  }

  /**
   * Extrait le message d'erreur de la réponse
   */
  private extractErrorMessage(data: any): string {
    if (typeof data === 'string') return data;
    if (data?.error) return data.error;
    if (data?.message) return data.message;
    if (data?.detail) return data.detail;
    
    // Erreurs de validation Django REST Framework
    if (data && typeof data === 'object') {
      const firstError = Object.values(data)[0];
      if (Array.isArray(firstError)) {
        return firstError[0] as string;
      }
      if (typeof firstError === 'string') {
        return firstError;
      }
    }

    return 'Erreur inconnue';
  }

  /**
   * Vérifie la connexion réseau
   */
  private async checkNetworkConnection(): Promise<boolean> {
    const netInfo = await NetInfo.fetch();
    return netInfo.isConnected || false;
  }

  /**
   * Effectue une requête avec retry automatique
   */
  private async makeRequestWithRetry<T>(
    requestFn: () => Promise<AxiosResponse<T>>,
    retries = API_CONFIG.MAX_RETRIES
  ): Promise<ApiResponse<T>> {
    try {
      const response = await requestFn();
      return {
        success: true,
        data: response.data,
        status: response.status
      };
    } catch (error) {
      if (retries > 0 && this.shouldRetry(error as AxiosError)) {
        console.log(`🔄 Retry attempt ${API_CONFIG.MAX_RETRIES - retries + 1}/${API_CONFIG.MAX_RETRIES}`);
        await this.delay(1000 * (API_CONFIG.MAX_RETRIES - retries + 1)); // Backoff exponentiel
        return this.makeRequestWithRetry(requestFn, retries - 1);
      }
      
      return this.handleApiError(error as AxiosError);
    }
  }

  /**
   * Détermine si une requête doit être re-tentée
   */
  private shouldRetry(error: AxiosError): boolean {
    // Retry sur les erreurs réseau ou les erreurs serveur 5xx
    return !error.response || 
           error.response.status >= 500 || 
           error.code === 'NETWORK_ERROR' ||
           error.code === 'TIMEOUT';
  }

  /**
   * Délai asynchrone
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // ============================================================================
  // MÉTHODES PUBLIQUES D'API
  // ============================================================================

  /**
   * Connexion utilisateur
   */
  async login(credentials: { username: string; password: string; device_id?: string }): Promise<ApiResponse<LoginResponse>> {
    const isOnline = await this.checkNetworkConnection();
    if (!isOnline) {
      return {
        success: false,
        error: 'Connexion réseau requise pour la connexion'
      };
    }

    return this.makeRequestWithRetry(() =>
      this.axiosInstance.post('/auth/login/', credentials)
    );
  }

  /**
   * Déconnexion utilisateur
   */
  async logout(token: string): Promise<ApiResponse> {
    return this.makeRequestWithRetry(() =>
      this.axiosInstance.post('/auth/logout/', {}, {
        headers: { Authorization: `Token ${token}` }
      })
    );
  }

  /**
   * Rafraîchissement du token
   */
  async refreshToken(refreshToken: string): Promise<ApiResponse<{ token: string; refreshToken: string }>> {
    return this.makeRequestWithRetry(() =>
      this.axiosInstance.post('/auth/refresh/', { refresh_token: refreshToken })
    );
  }

  /**
   * Récupération du profil utilisateur
   */
  async getUserProfile(): Promise<ApiResponse> {
    return this.makeRequestWithRetry(() =>
      this.axiosInstance.get('/auth/profile/')
    );
  }

  /**
   * Récupération des ordres de travail
   */
  async getWorkOrders(userId: number, filters?: any): Promise<ApiResponse> {
    const params = new URLSearchParams();
    if (filters) {
      Object.keys(filters).forEach(key => {
        if (filters[key] !== undefined && filters[key] !== null) {
          params.append(key, filters[key]);
        }
      });
    }

    return this.makeRequestWithRetry(() =>
      this.axiosInstance.get(`/ordres-travail/?${params.toString()}`)
    );
  }

  /**
   * Récupération des détails d'un ordre de travail
   */
  async getWorkOrderDetails(workOrderId: number): Promise<ApiResponse> {
    return this.makeRequestWithRetry(() =>
      this.axiosInstance.get(`/ordres-travail/${workOrderId}/`)
    );
  }

  /**
   * Mise à jour du statut d'un ordre de travail
   */
  async updateWorkOrderStatus(workOrderId: number, status: string, data?: any): Promise<ApiResponse> {
    return this.makeRequestWithRetry(() =>
      this.axiosInstance.patch(`/ordres-travail/${workOrderId}/`, {
        statut: status,
        ...data
      })
    );
  }

  /**
   * Upload d'un fichier média
   */
  async uploadMedia(file: any, metadata: any): Promise<ApiResponse> {
    const formData = new FormData();
    formData.append('fichier', file);
    
    Object.keys(metadata).forEach(key => {
      formData.append(key, metadata[key]);
    });

    return this.makeRequestWithRetry(() =>
      this.axiosInstance.post('/medias/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 60000, // 60 secondes pour les uploads
      })
    );
  }

  /**
   * Scan d'un QR code
   */
  async scanQRCode(code: string): Promise<ApiResponse> {
    return this.makeRequestWithRetry(() =>
      this.axiosInstance.post('/assets/scan_qr/', { code })
    );
  }

  /**
   * Synchronisation - Pull data
   */
  async pullSyncData(lastSync?: string): Promise<ApiResponse<SyncResponse>> {
    const params = lastSync ? `?last_sync=${encodeURIComponent(lastSync)}` : '';
    
    return this.makeRequestWithRetry(() =>
      this.axiosInstance.get(`/sync/pull_data/${params}`)
    );
  }

  /**
   * Synchronisation - Push data
   */
  async pushSyncData(data: any): Promise<ApiResponse> {
    return this.makeRequestWithRetry(() =>
      this.axiosInstance.post('/sync/push_data/', data)
    );
  }

  /**
   * Récupération des statistiques
   */
  async getDashboardStats(): Promise<ApiResponse> {
    return this.makeRequestWithRetry(() =>
      this.axiosInstance.get('/ordres-travail/dashboard_stats/')
    );
  }

  /**
   * Récupération des notifications
   */
  async getNotifications(limit = 20): Promise<ApiResponse> {
    return this.makeRequestWithRetry(() =>
      this.axiosInstance.get(`/ordres-travail/notifications/?limit=${limit}`)
    );
  }

  /**
   * Test de connectivité avec le serveur
   */
  async ping(): Promise<boolean> {
    try {
      const response = await this.axiosInstance.get('/sync/status/', { timeout: 5000 });
      return response.status === 200;
    } catch {
      return false;
    }
  }

  /**
   * Obtient l'instance Axios (pour usage avancé)
   */
  getAxiosInstance(): AxiosInstance {
    return this.axiosInstance;
  }
}

export default ApiClient.getInstance();