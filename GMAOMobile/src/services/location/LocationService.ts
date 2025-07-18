// src/services/location/LocationService.ts
import Geolocation from '@react-native-community/geolocation';
import { Platform, PermissionsAndroid, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface LocationCoordinates {
  latitude: number;
  longitude: number;
  accuracy?: number;
  altitude?: number;
  heading?: number;
  speed?: number;
  timestamp: number;
}

export interface LocationOptions {
  enableHighAccuracy?: boolean;
  timeout?: number;
  maximumAge?: number;
  distanceFilter?: number;
}

export interface LocationError {
  code: number;
  message: string;
}

class LocationService {
  private static instance: LocationService;
  private watchId: number | null = null;
  private lastKnownLocation: LocationCoordinates | null = null;
  private isWatching = false;
  private locationHistory: LocationCoordinates[] = [];
  private maxHistorySize = 100;

  private constructor() {
    this.loadLastKnownLocation();
  }

  public static getInstance(): LocationService {
    if (!LocationService.instance) {
      LocationService.instance = new LocationService();
    }
    return LocationService.instance;
  }

  /**
   * Demande les permissions de géolocalisation
   */
  async requestLocationPermission(): Promise<boolean> {
    try {
      if (Platform.OS === 'android') {
        const granted = await PermissionsAndroid.request(
          PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
          {
            title: 'Permission de géolocalisation',
            message: 'Cette application a besoin d\'accéder à votre position pour fonctionner correctement.',
            buttonNeutral: 'Plus tard',
            buttonNegative: 'Refuser',
            buttonPositive: 'Autoriser',
          },
        );

        if (granted === PermissionsAndroid.RESULTS.GRANTED) {
          console.log('✅ Permission géolocalisation accordée');
          return true;
        } else {
          console.log('❌ Permission géolocalisation refusée');
          this.showPermissionDeniedAlert();
          return false;
        }
      } else {
        // iOS - La permission est demandée automatiquement lors du premier appel
        return true;
      }
    } catch (error) {
      console.error('Erreur demande permission géolocalisation:', error);
      return false;
    }
  }

  /**
   * Vérifie si les permissions sont accordées
   */
  async hasLocationPermission(): Promise<boolean> {
    if (Platform.OS === 'android') {
      try {
        const hasPermission = await PermissionsAndroid.check(
          PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION
        );
        return hasPermission;
      } catch (error) {
        console.error('Erreur vérification permission:', error);
        return false;
      }
    }
    return true; // iOS
  }

  /**
   * Obtient la position actuelle
   */
  async getCurrentPosition(options?: LocationOptions): Promise<LocationCoordinates> {
    return new Promise(async (resolve, reject) => {
      // Vérifier les permissions
      const hasPermission = await this.hasLocationPermission();
      if (!hasPermission) {
        const granted = await this.requestLocationPermission();
        if (!granted) {
          reject(new Error('Permission de géolocalisation refusée'));
          return;
        }
      }

      const defaultOptions: LocationOptions = {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 10000,
        ...options,
      };

      Geolocation.getCurrentPosition(
        (position) => {
          const coords: LocationCoordinates = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            altitude: position.coords.altitude || undefined,
            heading: position.coords.heading || undefined,
            speed: position.coords.speed || undefined,
            timestamp: position.timestamp,
          };

          this.lastKnownLocation = coords;
          this.saveLastKnownLocation(coords);
          this.addToHistory(coords);

          console.log('📍 Position obtenue:', coords);
          resolve(coords);
        },
        (error) => {
          console.error('❌ Erreur géolocalisation:', error);
          
          // Essayer de retourner la dernière position connue si disponible
          if (this.lastKnownLocation && options?.maximumAge) {
            const age = Date.now() - this.lastKnownLocation.timestamp;
            if (age <= options.maximumAge) {
              console.log('📍 Utilisation dernière position connue');
              resolve(this.lastKnownLocation);
              return;
            }
          }

          reject(this.formatLocationError(error));
        },
        defaultOptions
      );
    });
  }

  /**
   * Démarre le suivi de la position
   */
  async startWatchingPosition(
    callback: (location: LocationCoordinates) => void,
    errorCallback?: (error: LocationError) => void,
    options?: LocationOptions
  ): Promise<boolean> {
    if (this.isWatching) {
      console.log('⚠️ Suivi de position déjà actif');
      return true;
    }

    // Vérifier les permissions
    const hasPermission = await this.hasLocationPermission();
    if (!hasPermission) {
      const granted = await this.requestLocationPermission();
      if (!granted) {
        errorCallback?.({ code: 1, message: 'Permission refusée' });
        return false;
      }
    }

    const defaultOptions: LocationOptions = {
      enableHighAccuracy: true,
      timeout: 15000,
      maximumAge: 5000,
      distanceFilter: 10, // Mise à jour tous les 10 mètres
      ...options,
    };

    try {
      this.watchId = Geolocation.watchPosition(
        (position) => {
          const coords: LocationCoordinates = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            altitude: position.coords.altitude || undefined,
            heading: position.coords.heading || undefined,
            speed: position.coords.speed || undefined,
            timestamp: position.timestamp,
          };

          this.lastKnownLocation = coords;
          this.saveLastKnownLocation(coords);
          this.addToHistory(coords);

          callback(coords);
        },
        (error) => {
          console.error('❌ Erreur suivi position:', error);
          errorCallback?.(this.formatLocationError(error));
        },
        defaultOptions
      );

      this.isWatching = true;
      console.log('📍 Suivi de position démarré');
      return true;

    } catch (error) {
      console.error('❌ Erreur démarrage suivi position:', error);
      errorCallback?.({ code: 2, message: 'Erreur technique' });
      return false;
    }
  }

  /**
   * Arrête le suivi de la position
   */
  stopWatchingPosition(): void {
    if (this.watchId !== null) {
      Geolocation.clearWatch(this.watchId);
      this.watchId = null;
      this.isWatching = false;
      console.log('📍 Suivi de position arrêté');
    }
  }

  /**
   * Obtient la dernière position connue
   */
  getLastKnownLocation(): LocationCoordinates | null {
    return this.lastKnownLocation;
  }

  /**
   * Obtient l'historique des positions
   */
  getLocationHistory(): LocationCoordinates[] {
    return [...this.locationHistory];
  }

  /**
   * Calcule la distance entre deux points (en mètres)
   */
  calculateDistance(
    from: { latitude: number; longitude: number },
    to: { latitude: number; longitude: number }
  ): number {
    const R = 6371000; // Rayon de la Terre en mètres
    const lat1Rad = (from.latitude * Math.PI) / 180;
    const lat2Rad = (to.latitude * Math.PI) / 180;
    const deltaLatRad = ((to.latitude - from.latitude) * Math.PI) / 180;
    const deltaLonRad = ((to.longitude - from.longitude) * Math.PI) / 180;

    const a =
      Math.sin(deltaLatRad / 2) * Math.sin(deltaLatRad / 2) +
      Math.cos(lat1Rad) *
        Math.cos(lat2Rad) *
        Math.sin(deltaLonRad / 2) *
        Math.sin(deltaLonRad / 2);

    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    const distance = R * c;

    return Math.round(distance);
  }

  /**
   * Calcule le bearing entre deux points (en degrés)
   */
  calculateBearing(
    from: { latitude: number; longitude: number },
    to: { latitude: number; longitude: number }
  ): number {
    const lat1Rad = (from.latitude * Math.PI) / 180;
    const lat2Rad = (to.latitude * Math.PI) / 180;
    const deltaLonRad = ((to.longitude - from.longitude) * Math.PI) / 180;

    const x = Math.sin(deltaLonRad) * Math.cos(lat2Rad);
    const y =
      Math.cos(lat1Rad) * Math.sin(lat2Rad) -
      Math.sin(lat1Rad) * Math.cos(lat2Rad) * Math.cos(deltaLonRad);

    const bearingRad = Math.atan2(x, y);
    const bearingDeg = (bearingRad * 180) / Math.PI;

    return (bearingDeg + 360) % 360;
  }

  /**
   * Vérifie si une position est dans un rayon donné
   */
  isWithinRadius(
    center: { latitude: number; longitude: number },
    point: { latitude: number; longitude: number },
    radiusMeters: number
  ): boolean {
    const distance = this.calculateDistance(center, point);
    return distance <= radiusMeters;
  }

  /**
   * Formate les coordonnées pour l'affichage
   */
  formatCoordinates(coords: LocationCoordinates, precision = 6): string {
    return `${coords.latitude.toFixed(precision)}, ${coords.longitude.toFixed(precision)}`;
  }

  /**
   * Obtient l'adresse approximative (si service disponible)
   */
  async getAddressFromCoordinates(coords: LocationCoordinates): Promise<string | null> {
    try {
      // TODO: Intégrer un service de géocodage inverse
      // Pour l'instant, retourner les coordonnées formatées
      return this.formatCoordinates(coords, 4);
    } catch (error) {
      console.error('Erreur géocodage inverse:', error);
      return null;
    }
  }

  /**
   * Sauvegarde la dernière position connue
   */
  private async saveLastKnownLocation(coords: LocationCoordinates): Promise<void> {
    try {
      await AsyncStorage.setItem('last_known_location', JSON.stringify(coords));
    } catch (error) {
      console.error('Erreur sauvegarde position:', error);
    }
  }

  /**
   * Charge la dernière position connue
   */
  private async loadLastKnownLocation(): Promise<void> {
    try {
      const stored = await AsyncStorage.getItem('last_known_location');
      if (stored) {
        this.lastKnownLocation = JSON.parse(stored);
        console.log('📍 Dernière position chargée:', this.lastKnownLocation);
      }
    } catch (error) {
      console.error('Erreur chargement position:', error);
    }
  }

  /**
   * Ajoute une position à l'historique
   */
  private addToHistory(coords: LocationCoordinates): void {
    this.locationHistory.push(coords);
    
    // Limiter la taille de l'historique
    if (this.locationHistory.length > this.maxHistorySize) {
      this.locationHistory = this.locationHistory.slice(-this.maxHistorySize);
    }
  }

  /**
   * Formate les erreurs de géolocalisation
   */
  private formatLocationError(error: any): LocationError {
    let message = 'Erreur de géolocalisation';
    
    switch (error.code) {
      case 1:
        message = 'Permission de géolocalisation refusée';
        break;
      case 2:
        message = 'Position indisponible';
        break;
      case 3:
        message = 'Délai de géolocalisation dépassé';
        break;
    }

    return {
      code: error.code,
      message,
    };
  }

  /**
   * Affiche une alerte pour permission refusée
   */
  private showPermissionDeniedAlert(): void {
    Alert.alert(
      'Permission requise',
      'L\'application a besoin d\'accéder à votre position pour fonctionner correctement. Vous pouvez activer cette permission dans les paramètres de votre appareil.',
      [
        { text: 'Plus tard', style: 'cancel' },
        { text: 'Paramètres', onPress: () => {
          // TODO: Ouvrir les paramètres de l'app
        }},
      ]
    );
  }

  /**
   * Obtient le statut du service
   */
  getStatus(): {
    isWatching: boolean;
    hasLastKnownLocation: boolean;
    historySize: number;
  } {
    return {
      isWatching: this.isWatching,
      hasLastKnownLocation: this.lastKnownLocation !== null,
      historySize: this.locationHistory.length,
    };
  }

  /**
   * Nettoie les ressources
   */
  cleanup(): void {
    this.stopWatchingPosition();
    this.locationHistory = [];
  }
}

export default LocationService.getInstance();