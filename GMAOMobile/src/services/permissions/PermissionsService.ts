// src/services/permissions/PermissionsService.ts
import { Platform, PermissionsAndroid, Alert, Linking } from 'react-native';
import { check, request, PERMISSIONS, RESULTS, openSettings } from 'react-native-permissions';

export type PermissionType = 
  | 'camera'
  | 'microphone'
  | 'location'
  | 'storage'
  | 'notification';

export type PermissionStatus = 
  | 'granted'
  | 'denied'
  | 'blocked'
  | 'unavailable'
  | 'limited';

export interface PermissionResult {
  status: PermissionStatus;
  canAskAgain: boolean;
  message?: string;
}

class PermissionsService {
  private static instance: PermissionsService;

  private constructor() {}

  public static getInstance(): PermissionsService {
    if (!PermissionsService.instance) {
      PermissionsService.instance = new PermissionsService();
    }
    return PermissionsService.instance;
  }

  /**
   * Vérifie le statut d'une permission
   */
  async checkPermission(permission: PermissionType): Promise<PermissionStatus> {
    try {
      const nativePermission = this.getNativePermission(permission);
      if (!nativePermission) {
        return 'unavailable';
      }

      if (Platform.OS === 'android' && permission === 'storage') {
        // Gestion spéciale pour le stockage Android
        const hasPermission = await PermissionsAndroid.check(
          PermissionsAndroid.PERMISSIONS.WRITE_EXTERNAL_STORAGE
        );
        return hasPermission ? 'granted' : 'denied';
      }

      const result = await check(nativePermission);
      return this.mapPermissionResult(result);
    } catch (error) {
      console.error(`Erreur vérification permission ${permission}:`, error);
      return 'unavailable';
    }
  }

  /**
   * Demande une permission
   */
  async requestPermission(permission: PermissionType): Promise<PermissionResult> {
    try {
      const currentStatus = await this.checkPermission(permission);
      
      if (currentStatus === 'granted') {
        return {
          status: 'granted',
          canAskAgain: false,
          message: 'Permission déjà accordée'
        };
      }

      if (currentStatus === 'blocked') {
        return {
          status: 'blocked',
          canAskAgain: false,
          message: 'Permission bloquée. Aller dans les paramètres pour l\'activer.'
        };
      }

      const nativePermission = this.getNativePermission(permission);
      if (!nativePermission) {
        return {
          status: 'unavailable',
          canAskAgain: false,
          message: 'Permission non disponible sur cet appareil'
        };
      }

      // Demande spéciale pour Android storage
      if (Platform.OS === 'android' && permission === 'storage') {
        const granted = await PermissionsAndroid.request(
          PermissionsAndroid.PERMISSIONS.WRITE_EXTERNAL_STORAGE,
          {
            title: 'Permission de stockage',
            message: 'Cette application a besoin d\'accéder au stockage pour sauvegarder les fichiers.',
            buttonNeutral: 'Plus tard',
            buttonNegative: 'Refuser',
            buttonPositive: 'Autoriser',
          }
        );

        const status = granted === PermissionsAndroid.RESULTS.GRANTED ? 'granted' : 'denied';
        return {
          status,
          canAskAgain: granted !== PermissionsAndroid.RESULTS.NEVER_ASK_AGAIN,
          message: this.getPermissionMessage(permission, status)
        };
      }

      const result = await request(nativePermission);
      const status = this.mapPermissionResult(result);
      
      return {
        status,
        canAskAgain: status !== 'blocked',
        message: this.getPermissionMessage(permission, status)
      };

    } catch (error) {
      console.error(`Erreur demande permission ${permission}:`, error);
      return {
        status: 'unavailable',
        canAskAgain: false,
        message: 'Erreur lors de la demande de permission'
      };
    }
  }

  /**
   * Demande plusieurs permissions
   */
  async requestMultiplePermissions(permissions: PermissionType[]): Promise<Record<PermissionType, PermissionResult>> {
    const results: Record<string, PermissionResult> = {};
    
    for (const permission of permissions) {
      results[permission] = await this.requestPermission(permission);
    }

    return results as Record<PermissionType, PermissionResult>;
  }

  /**
   * Vérifie si toutes les permissions sont accordées
   */
  async checkAllPermissions(permissions: PermissionType[]): Promise<boolean> {
    for (const permission of permissions) {
      const status = await this.checkPermission(permission);
      if (status !== 'granted') {
        return false;
      }
    }
    return true;
  }

  /**
   * Affiche une alerte pour expliquer pourquoi la permission est nécessaire
   */
  showPermissionRationale(permission: PermissionType, onGranted?: () => void, onDenied?: () => void): void {
    const info = this.getPermissionInfo(permission);
    
    Alert.alert(
      info.title,
      info.rationale,
      [
        {
          text: 'Refuser',
          style: 'cancel',
          onPress: onDenied,
        },
        {
          text: 'Autoriser',
          onPress: async () => {
            const result = await this.requestPermission(permission);
            if (result.status === 'granted') {
              onGranted?.();
            } else {
              onDenied?.();
            }
          },
        },
      ]
    );
  }

  /**
   * Affiche une alerte pour rediriger vers les paramètres
   */
  showSettingsAlert(permission: PermissionType): void {
    const info = this.getPermissionInfo(permission);
    
    Alert.alert(
      'Permission requise',
      `${info.title} est nécessaire pour utiliser cette fonctionnalité. Veuillez l'activer dans les paramètres de l'application.`,
      [
        { text: 'Annuler', style: 'cancel' },
        {
          text: 'Paramètres',
          onPress: () => {
            openSettings().catch(() => {
              // Fallback vers les paramètres système
              Linking.openSettings();
            });
          },
        },
      ]
    );
  }

  /**
   * Vérifie et demande une permission avec gestion complète
   */
  async checkAndRequestPermission(
    permission: PermissionType,
    showRationale = true
  ): Promise<boolean> {
    try {
      // Vérifier le statut actuel
      const currentStatus = await this.checkPermission(permission);
      
      if (currentStatus === 'granted') {
        return true;
      }

      if (currentStatus === 'blocked') {
        this.showSettingsAlert(permission);
        return false;
      }

      // Demander la permission
      if (showRationale) {
        return new Promise((resolve) => {
          this.showPermissionRationale(
            permission,
            () => resolve(true),
            () => resolve(false)
          );
        });
      } else {
        const result = await this.requestPermission(permission);
        return result.status === 'granted';
      }

    } catch (error) {
      console.error(`Erreur checkAndRequestPermission ${permission}:`, error);
      return false;
    }
  }

  /**
   * Obtient la permission native correspondante
   */
  private getNativePermission(permission: PermissionType): string | null {
    const permissionMap = {
      camera: Platform.OS === 'ios' ? PERMISSIONS.IOS.CAMERA : PERMISSIONS.ANDROID.CAMERA,
      microphone: Platform.OS === 'ios' ? PERMISSIONS.IOS.MICROPHONE : PERMISSIONS.ANDROID.RECORD_AUDIO,
      location: Platform.OS === 'ios' ? PERMISSIONS.IOS.LOCATION_WHEN_IN_USE : PERMISSIONS.ANDROID.ACCESS_FINE_LOCATION,
      storage: Platform.OS === 'ios' ? PERMISSIONS.IOS.PHOTO_LIBRARY : PERMISSIONS.ANDROID.WRITE_EXTERNAL_STORAGE,
      notification: Platform.OS === 'ios' ? PERMISSIONS.IOS.NOTIFICATION : null, // Android gère différemment
    };

    return permissionMap[permission] || null;
  }

  /**
   * Mappe le résultat de permission
   */
  private mapPermissionResult(result: string): PermissionStatus {
    switch (result) {
      case RESULTS.GRANTED:
        return 'granted';
      case RESULTS.DENIED:
        return 'denied';
      case RESULTS.BLOCKED:
        return 'blocked';
      case RESULTS.LIMITED:
        return 'limited';
      case RESULTS.UNAVAILABLE:
      default:
        return 'unavailable';
    }
  }

  /**
   * Obtient le message correspondant au statut
   */
  private getPermissionMessage(permission: PermissionType, status: PermissionStatus): string {
    const messages = {
      granted: 'Permission accordée',
      denied: 'Permission refusée',
      blocked: 'Permission bloquée - aller dans les paramètres',
      limited: 'Permission limitée',
      unavailable: 'Permission non disponible',
    };

    return messages[status] || 'Statut inconnu';
  }

  /**
   * Obtient les informations d'une permission
   */
  private getPermissionInfo(permission: PermissionType): {
    title: string;
    rationale: string;
    importance: 'essential' | 'important' | 'optional';
  } {
    const infos = {
      camera: {
        title: 'Accès à la caméra',
        rationale: 'Cette application a besoin d\'accéder à votre caméra pour prendre des photos lors des interventions et documenter les travaux effectués.',
        importance: 'essential' as const,
      },
      microphone: {
        title: 'Accès au microphone',
        rationale: 'Cette application a besoin d\'accéder à votre microphone pour enregistrer des notes audio lors des interventions.',
        importance: 'important' as const,
      },
      location: {
        title: 'Accès à la localisation',
        rationale: 'Cette application a besoin d\'accéder à votre position pour vous géolocaliser sur les sites d\'intervention et horodater vos déplacements.',
        importance: 'essential' as const,
      },
      storage: {
        title: 'Accès au stockage',
        rationale: 'Cette application a besoin d\'accéder au stockage pour sauvegarder les photos, documents et données d\'intervention.',
        importance: 'essential' as const,
      },
      notification: {
        title: 'Notifications',
        rationale: 'Cette application souhaite vous envoyer des notifications pour vous informer des nouveaux ordres de travail et des mises à jour importantes.',
        importance: 'important' as const,
      },
    };

    return infos[permission];
  }

  /**
   * Obtient toutes les permissions nécessaires pour l'application
   */
  getRequiredPermissions(): {
    essential: PermissionType[];
    important: PermissionType[];
    optional: PermissionType[];
  } {
    return {
      essential: ['camera', 'location', 'storage'],
      important: ['microphone', 'notification'],
      optional: [],
    };
  }

  /**
   * Vérifie toutes les permissions essentielles
   */
  async checkEssentialPermissions(): Promise<{
    allGranted: boolean;
    missing: PermissionType[];
    results: Record<PermissionType, PermissionStatus>;
  }> {
    const essential = this.getRequiredPermissions().essential;
    const results: Record<string, PermissionStatus> = {};
    const missing: PermissionType[] = [];

    for (const permission of essential) {
      const status = await this.checkPermission(permission);
      results[permission] = status;
      
      if (status !== 'granted') {
        missing.push(permission);
      }
    }

    return {
      allGranted: missing.length === 0,
      missing,
      results: results as Record<PermissionType, PermissionStatus>,
    };
  }

  /**
   * Demande toutes les permissions essentielles
   */
  async requestEssentialPermissions(): Promise<boolean> {
    const essential = this.getRequiredPermissions().essential;
    let allGranted = true;

    for (const permission of essential) {
      const granted = await this.checkAndRequestPermission(permission, true);
      if (!granted) {
        allGranted = false;
        console.log(`❌ Permission essentielle ${permission} refusée`);
      }
    }

    return allGranted;
  }

  /**
   * Affiche un écran d'onboarding pour les permissions
   */
  async showPermissionsOnboarding(): Promise<boolean> {
    return new Promise((resolve) => {
      Alert.alert(
        'Permissions nécessaires',
        'Pour fonctionner correctement, cette application a besoin de plusieurs permissions. Nous allons vous les demander une par une.',
        [
          {
            text: 'Plus tard',
            style: 'cancel',
            onPress: () => resolve(false),
          },
          {
            text: 'Continuer',
            onPress: async () => {
              const result = await this.requestEssentialPermissions();
              resolve(result);
            },
          },
        ]
      );
    });
  }

  /**
   * Obtient un résumé des permissions
   */
  async getPermissionsSummary(): Promise<{
    total: number;
    granted: number;
    denied: number;
    blocked: number;
    details: Record<PermissionType, PermissionStatus>;
  }> {
    const allPermissions: PermissionType[] = ['camera', 'microphone', 'location', 'storage', 'notification'];
    const details: Record<string, PermissionStatus> = {};
    
    let granted = 0;
    let denied = 0;
    let blocked = 0;

    for (const permission of allPermissions) {
      const status = await this.checkPermission(permission);
      details[permission] = status;
      
      switch (status) {
        case 'granted':
          granted++;
          break;
        case 'denied':
          denied++;
          break;
        case 'blocked':
          blocked++;
          break;
      }
    }

    return {
      total: allPermissions.length,
      granted,
      denied,
      blocked,
      details: details as Record<PermissionType, PermissionStatus>,
    };
  }

  /**
   * Réinitialise l'état des permissions (pour les tests)
   */
  async resetPermissions(): Promise<void> {
    // Cette méthode est principalement pour les tests
    // En production, les permissions ne peuvent pas être réinitialisées programmatiquement
    console.log('⚠️ resetPermissions: Méthode disponible seulement pour les tests');
  }

  /**
   * Vérifie si l'appareil supporte une permission
   */
  isPermissionSupported(permission: PermissionType): boolean {
    const nativePermission = this.getNativePermission(permission);
    return nativePermission !== null;
  }

  /**
   * Obtient la version de l'OS pour les permissions conditionnelles
   */
  getOSInfo(): { platform: string; version: string } {
    return {
      platform: Platform.OS,
      version: Platform.Version.toString(),
    };
  }
}

export default PermissionsService.getInstance();