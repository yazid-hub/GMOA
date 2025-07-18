// src/services/sync/SyncService.ts
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import { SyncOperations, WorkOrderOperations, MediaFileOperations } from '../../database/operations';
import DatabaseManager from '../../database/DatabaseManager';
import ApiClient from '../api/ApiClient';
import { TABLES } from '../../database/schema';
import { SyncResult, SyncQueueItem } from '../../types/database';

export interface SyncProgress {
  current: number;
  total: number;
  table?: string;
  operation?: string;
}

export type SyncProgressCallback = (progress: SyncProgress) => void;

class SyncService {
  private static instance: SyncService;
  private isSyncing = false;
  private currentSyncId: string | null = null;
  private db = DatabaseManager.getInstance();

  private constructor() {}

  public static getInstance(): SyncService {
    if (!SyncService.instance) {
      SyncService.instance = new SyncService();
    }
    return SyncService.instance;
  }

  /**
   * Vérifie si une synchronisation est possible
   */
  async canSync(): Promise<{ canSync: boolean; reason?: string }> {
    // Vérifier la connexion réseau
    const netInfo = await NetInfo.fetch();
    if (!netInfo.isConnected) {
      return { canSync: false, reason: 'Pas de connexion réseau' };
    }

    // Vérifier si une sync est déjà en cours
    if (this.isSyncing) {
      return { canSync: false, reason: 'Synchronisation déjà en cours' };
    }

    // Vérifier la connectivité avec le serveur
    const serverReachable = await ApiClient.ping();
    if (!serverReachable) {
      return { canSync: false, reason: 'Serveur inaccessible' };
    }

    return { canSync: true };
  }

  /**
   * Synchronisation complète (download + upload)
   */
  async performFullSync(progressCallback?: SyncProgressCallback): Promise<SyncResult> {
    const syncId = Date.now().toString();
    this.currentSyncId = syncId;
    this.isSyncing = true;

    const startTime = Date.now();
    let totalProcessed = 0;
    let totalSuccess = 0;
    let totalFailed = 0;
    const errors: string[] = [];

    try {
      console.log('🔄 Démarrage synchronisation complète');

      // Phase 1: Upload des données locales
      progressCallback?.({ current: 10, total: 100, operation: 'Upload données locales' });
      
      const uploadResult = await this.uploadPendingData((progress) => {
        progressCallback?.({ 
          current: 10 + (progress.current / progress.total) * 40, 
          total: 100,
          operation: 'Upload données',
          table: progress.table 
        });
      });

      totalProcessed += uploadResult.recordsProcessed;
      totalSuccess += uploadResult.recordsSuccess;
      totalFailed += uploadResult.recordsFailed;
      errors.push(...uploadResult.errors);

      // Phase 2: Download des données serveur
      progressCallback?.({ current: 50, total: 100, operation: 'Téléchargement données serveur' });
      
      const downloadResult = await this.downloadLatestData(1, (progress) => { // TODO: récupérer vrai user ID
        progressCallback?.({ 
          current: 50 + (progress.current / progress.total) * 40, 
          total: 100,
          operation: 'Téléchargement',
          table: progress.table 
        });
      });

      totalProcessed += downloadResult.recordsProcessed;
      totalSuccess += downloadResult.recordsSuccess;
      totalFailed += downloadResult.recordsFailed;
      errors.push(...downloadResult.errors);

      // Phase 3: Nettoyage
      progressCallback?.({ current: 90, total: 100, operation: 'Nettoyage' });
      await SyncOperations.cleanupSyncQueue(7); // Nettoyer les éléments de plus de 7 jours

      progressCallback?.({ current: 100, total: 100, operation: 'Terminé' });

      // Sauvegarder la date de dernière sync
      await AsyncStorage.setItem('last_sync_time', new Date().toISOString());

      const duration = (Date.now() - startTime) / 1000;
      console.log(`✅ Synchronisation terminée en ${duration}s`);

      return {
        success: totalFailed === 0,
        recordsProcessed: totalProcessed,
        recordsSuccess: totalSuccess,
        recordsFailed: totalFailed,
        errors,
        duration
      };

    } catch (error: any) {
      console.error('❌ Erreur synchronisation complète:', error);
      errors.push(error.message || 'Erreur inconnue');
      
      return {
        success: false,
        recordsProcessed: totalProcessed,
        recordsSuccess: totalSuccess,
        recordsFailed: totalProcessed - totalSuccess,
        errors,
        duration: (Date.now() - startTime) / 1000
      };
    } finally {
      this.isSyncing = false;
      this.currentSyncId = null;
    }
  }

  /**
   * Upload des données en attente
   */
  async uploadPendingData(progressCallback?: SyncProgressCallback): Promise<SyncResult> {
    console.log('📤 Upload des données en attente');
    
    const startTime = Date.now();
    const errors: string[] = [];
    let processed = 0;
    let success = 0;

    try {
      // Récupérer les éléments en attente
      const pendingItems = await SyncOperations.getPendingSyncItems(100);
      const total = pendingItems.length;

      if (total === 0) {
        console.log('✅ Aucune donnée en attente d\'upload');
        return {
          success: true,
          recordsProcessed: 0,
          recordsSuccess: 0,
          recordsFailed: 0,
          errors: [],
          duration: 0
        };
      }

      console.log(`📤 ${total} éléments à synchroniser`);

      // Grouper par table pour optimiser
      const itemsByTable = this.groupItemsByTable(pendingItems);

      let currentIndex = 0;
      for (const [tableName, items] of Object.entries(itemsByTable)) {
        progressCallback?.({ 
          current: currentIndex, 
          total, 
          table: tableName,
          operation: 'Upload' 
        });

        const tableResult = await this.uploadTableData(tableName, items);
        processed += tableResult.processed;
        success += tableResult.success;
        errors.push(...tableResult.errors);

        currentIndex += items.length;
      }

      // Upload des fichiers média en attente
      const mediaResult = await this.uploadPendingMedia(progressCallback, processed, total);
      processed += mediaResult.processed;
      success += mediaResult.success;
      errors.push(...mediaResult.errors);

      return {
        success: errors.length === 0,
        recordsProcessed: processed,
        recordsSuccess: success,
        recordsFailed: processed - success,
        errors,
        duration: (Date.now() - startTime) / 1000
      };

    } catch (error: any) {
      console.error('❌ Erreur upload:', error);
      return {
        success: false,
        recordsProcessed: processed,
        recordsSuccess: success,
        recordsFailed: processed - success,
        errors: [error.message || 'Erreur upload'],
        duration: (Date.now() - startTime) / 1000
      };
    }
  }

  /**
   * Téléchargement des données du serveur
   */
  async downloadLatestData(userId: number, progressCallback?: SyncProgressCallback): Promise<SyncResult> {
    console.log('📥 Téléchargement des données serveur');
    
    const startTime = Date.now();
    const errors: string[] = [];
    let processed = 0;
    let success = 0;

    try {
      // Récupérer la date de dernière sync
      const lastSync = await AsyncStorage.getItem('last_sync_time');

      progressCallback?.({ current: 10, total: 100, operation: 'Récupération données serveur' });

      // Appel API pour récupérer les données
      const response = await ApiClient.pullSyncData(lastSync || undefined);

      if (!response.success) {
        throw new Error(response.error || 'Erreur lors de la récupération des données');
      }

      const data = response.data!;
      progressCallback?.({ current: 30, total: 100, operation: 'Traitement ordres de travail' });

      // Sauvegarder les ordres de travail
      if (data.data.ordres_travail) {
        const otResult = await this.saveWorkOrders(data.data.ordres_travail);
        processed += otResult.processed;
        success += otResult.success;
        errors.push(...otResult.errors);
      }

      progressCallback?.({ current: 60, total: 100, operation: 'Traitement interventions' });

      // Sauvegarder les interventions
      if (data.data.interventions) {
        const interventionResult = await this.saveInterventions(data.data.interventions);
        processed += interventionResult.processed;
        success += interventionResult.success;
        errors.push(...interventionResult.errors);
      }

      progressCallback?.({ current: 90, total: 100, operation: 'Traitement assets' });

      // Sauvegarder les assets
      if (data.data.assets) {
        const assetResult = await this.saveAssets(data.data.assets);
        processed += assetResult.processed;
        success += assetResult.success;
        errors.push(...assetResult.errors);
      }

      return {
        success: errors.length === 0,
        recordsProcessed: processed,
        recordsSuccess: success,
        recordsFailed: processed - success,
        errors,
        duration: (Date.now() - startTime) / 1000
      };

    } catch (error: any) {
      console.error('❌ Erreur download:', error);
      return {
        success: false,
        recordsProcessed: processed,
        recordsSuccess: success,
        recordsFailed: processed - success,
        errors: [error.message || 'Erreur download'],
        duration: (Date.now() - startTime) / 1000
      };
    }
  }

  /**
   * Upload des fichiers média en attente
   */
  private async uploadPendingMedia(
    progressCallback?: SyncProgressCallback, 
    currentIndex = 0, 
    total = 100
  ): Promise<{ processed: number; success: number; errors: string[] }> {
    const pendingMedia = await MediaFileOperations.getPendingUploads();
    let processed = 0;
    let success = 0;
    const errors: string[] = [];

    for (const media of pendingMedia) {
      try {
        progressCallback?.({ 
          current: currentIndex + processed, 
          total, 
          operation: `Upload ${media.type_media}` 
        });

        // TODO: Implémenter l'upload réel du fichier
        // const uploadResponse = await ApiClient.uploadMedia(file, metadata);
        
        // Marquer comme uploadé temporairement
        await MediaFileOperations.markAsUploaded(media.id, 'temp_path');
        
        success++;
      } catch (error: any) {
        errors.push(`Erreur upload média ${media.id}: ${error.message}`);
      }
      processed++;
    }

    return { processed, success, errors };
  }

  /**
   * Grouper les éléments par table
   */
  private groupItemsByTable(items: SyncQueueItem[]): Record<string, SyncQueueItem[]> {
    return items.reduce((groups, item) => {
      if (!groups[item.table_name]) {
        groups[item.table_name] = [];
      }
      groups[item.table_name].push(item);
      return groups;
    }, {} as Record<string, SyncQueueItem[]>);
  }

  /**
   * Upload des données d'une table
   */
  private async uploadTableData(
    tableName: string, 
    items: SyncQueueItem[]
  ): Promise<{ processed: number; success: number; errors: string[] }> {
    let processed = 0;
    let success = 0;
    const errors: string[] = [];

    for (const item of items) {
      try {
        await SyncOperations.markSyncSuccess(item.id);
        success++;
      } catch (error: any) {
        await SyncOperations.markSyncFailed(item.id, error.message);
        errors.push(`Erreur sync ${tableName} ${item.record_id}: ${error.message}`);
      }
      processed++;
    }

    return { processed, success, errors };
  }

  /**
   * Sauvegarde des ordres de travail
   */
  private async saveWorkOrders(workOrders: any[]): Promise<{ processed: number; success: number; errors: string[] }> {
    let processed = 0;
    let success = 0;
    const errors: string[] = [];

    for (const wo of workOrders) {
      try {
        await WorkOrderOperations.saveWorkOrder(wo);
        success++;
      } catch (error: any) {
        errors.push(`Erreur sauvegarde OT ${wo.id}: ${error.message}`);
      }
      processed++;
    }

    return { processed, success, errors };
  }

  /**
   * Sauvegarde des interventions
   */
  private async saveInterventions(interventions: any[]): Promise<{ processed: number; success: number; errors: string[] }> {
    let processed = 0;
    let success = 0;
    const errors: string[] = [];

    for (const intervention of interventions) {
      try {
        await this.db.upsert(TABLES.INTERVENTIONS, intervention, ['server_id']);
        success++;
      } catch (error: any) {
        errors.push(`Erreur sauvegarde intervention ${intervention.id}: ${error.message}`);
      }
      processed++;
    }

    return { processed, success, errors };
  }

  /**
   * Sauvegarde des assets
   */
  private async saveAssets(assets: any[]): Promise<{ processed: number; success: number; errors: string[] }> {
    let processed = 0;
    let success = 0;
    const errors: string[] = [];

    for (const asset of assets) {
      try {
        await this.db.upsert(TABLES.ASSETS, asset, ['server_id']);
        success++;
      } catch (error: any) {
        errors.push(`Erreur sauvegarde asset ${asset.id}: ${error.message}`);
      }
      processed++;
    }

    return { processed, success, errors };
  }

  /**
   * Retry des éléments de synchronisation échoués
   */
  async retryFailedItems(): Promise<SyncResult> {
    console.log('🔄 Retry des éléments échoués');
    
    const startTime = Date.now();
    const errors: string[] = [];
    let processed = 0;
    let success = 0;

    try {
      // Récupérer les éléments échoués
      const failedItems = await this.db.select(
        `SELECT * FROM ${TABLES.SYNC_QUEUE} WHERE status = 'FAILED' ORDER BY priority ASC, created_at ASC LIMIT 50`
      );

      for (const item of failedItems) {
        try {
          // Réinitialiser le statut pour permettre un nouveau traitement
          await this.db.update(TABLES.SYNC_QUEUE, {
            status: 'PENDING',
            attempts: 0,
            error_message: null,
            updated_at: new Date().toISOString()
          }, 'id = ?', [item.id]);

          success++;
        } catch (error: any) {
          errors.push(`Erreur retry item ${item.id}: ${error.message}`);
        }
        processed++;
      }

      return {
        success: errors.length === 0,
        recordsProcessed: processed,
        recordsSuccess: success,
        recordsFailed: processed - success,
        errors,
        duration: (Date.now() - startTime) / 1000
      };

    } catch (error: any) {
      console.error('❌ Erreur retry:', error);
      return {
        success: false,
        recordsProcessed: processed,
        recordsSuccess: success,
        recordsFailed: processed - success,
        errors: [error.message || 'Erreur retry'],
        duration: (Date.now() - startTime) / 1000
      };
    }
  }

  /**
   * Synchronisation automatique en arrière-plan
   */
  async performBackgroundSync(): Promise<boolean> {
    try {
      // Vérifier si la sync auto est possible
      const { canSync, reason } = await this.canSync();
      if (!canSync) {
        console.log(`⏸️ Sync auto annulée: ${reason}`);
        return false;
      }

      // Vérifier les paramètres utilisateur
      const settings = await this.getUserSyncSettings();
      if (!settings.autoSync) {
        console.log('⏸️ Sync auto désactivée par l\'utilisateur');
        return false;
      }

      // Vérifier si assez de temps s'est écoulé
      const lastSyncTime = await AsyncStorage.getItem('last_sync_time');
      if (lastSyncTime) {
        const lastSync = new Date(lastSyncTime);
        const now = new Date();
        const diffMinutes = (now.getTime() - lastSync.getTime()) / (1000 * 60);
        
        if (diffMinutes < settings.syncInterval) {
          console.log(`⏸️ Sync auto trop récente (${diffMinutes}min < ${settings.syncInterval}min)`);
          return false;
        }
      }

      console.log('🔄 Démarrage sync automatique');
      
      // Effectuer une sync rapide (upload seulement)
      const result = await this.uploadPendingData();
      
      if (result.success) {
        await AsyncStorage.setItem('last_auto_sync_time', new Date().toISOString());
        console.log('✅ Sync automatique terminée avec succès');
        return true;
      } else {
        console.log('⚠️ Sync automatique partiellement échouée');
        return false;
      }

    } catch (error: any) {
      console.error('❌ Erreur sync automatique:', error);
      return false;
    }
  }

  /**
   * Obtient les paramètres de sync de l'utilisateur
   */
  private async getUserSyncSettings(): Promise<{
    autoSync: boolean;
    syncInterval: number;
    wifiOnly: boolean;
  }> {
    try {
      const settings = await AsyncStorage.getItem('user_settings');
      if (settings) {
        const parsed = JSON.parse(settings);
        return {
          autoSync: parsed.autoSync ?? true,
          syncInterval: parsed.syncInterval ?? 15, // 15 minutes par défaut
          wifiOnly: parsed.syncWifiOnly ?? false,
        };
      }
    } catch (error) {
      console.error('Erreur lecture paramètres sync:', error);
    }

    // Valeurs par défaut
    return {
      autoSync: true,
      syncInterval: 15,
      wifiOnly: false,
    };
  }

  /**
   * Force l'arrêt de la synchronisation en cours
   */
  async cancelSync(): Promise<void> {
    if (this.isSyncing && this.currentSyncId) {
      console.log(`🛑 Annulation de la sync ${this.currentSyncId}`);
      this.isSyncing = false;
      this.currentSyncId = null;
    }
  }

  /**
   * Obtient le statut de la synchronisation
   */
  getSyncStatus(): {
    isSyncing: boolean;
    currentSyncId: string | null;
  } {
    return {
      isSyncing: this.isSyncing,
      currentSyncId: this.currentSyncId,
    };
  }

  /**
   * Obtient les statistiques de synchronisation
   */
  async getSyncStats(): Promise<{
    pendingItems: number;
    failedItems: number;
    lastSyncTime: string | null;
    lastAutoSyncTime: string | null;
    totalSynced: number;
  }> {
    try {
      // Compter les éléments en attente
      const pendingCount = await this.db.selectOne(
        `SELECT COUNT(*) as count FROM ${TABLES.SYNC_QUEUE} WHERE status = 'PENDING'`
      );

      // Compter les éléments échoués
      const failedCount = await this.db.selectOne(
        `SELECT COUNT(*) as count FROM ${TABLES.SYNC_QUEUE} WHERE status = 'FAILED'`
      );

      // Compter le total synchronisé
      const totalSynced = await this.db.selectOne(
        `SELECT COUNT(*) as count FROM ${TABLES.SYNC_QUEUE} WHERE status = 'SUCCESS'`
      );

      // Récupérer les timestamps
      const lastSyncTime = await AsyncStorage.getItem('last_sync_time');
      const lastAutoSyncTime = await AsyncStorage.getItem('last_auto_sync_time');

      return {
        pendingItems: pendingCount?.count || 0,
        failedItems: failedCount?.count || 0,
        lastSyncTime,
        lastAutoSyncTime,
        totalSynced: totalSynced?.count || 0,
      };

    } catch (error) {
      console.error('Erreur récupération stats sync:', error);
      return {
        pendingItems: 0,
        failedItems: 0,
        lastSyncTime: null,
        lastAutoSyncTime: null,
        totalSynced: 0,
      };
    }
  }

  /**
   * Purge les anciennes données de synchronisation
   */
  async cleanupOldSyncData(olderThanDays = 30): Promise<number> {
    try {
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - olderThanDays);

      const result = await this.db.delete(
        TABLES.SYNC_QUEUE,
        'status = ? AND updated_at < ?',
        ['SUCCESS', cutoffDate.toISOString()]
      );

      console.log(`🧹 ${result} anciens éléments de sync supprimés`);
      return result;

    } catch (error) {
      console.error('Erreur nettoyage sync:', error);
      return 0;
    }
  }

  /**
   * Test de la connectivité avec le serveur
   */
  async testConnectivity(): Promise<{
    isConnected: boolean;
    responseTime?: number;
    error?: string;
  }> {
    const startTime = Date.now();
    
    try {
      const isReachable = await ApiClient.ping();
      const responseTime = Date.now() - startTime;

      return {
        isConnected: isReachable,
        responseTime: isReachable ? responseTime : undefined,
      };

    } catch (error: any) {
      return {
        isConnected: false,
        error: error.message || 'Erreur de connectivité',
      };
    }
  }
}

export default SyncService.getInstance();