// src/database/operations.ts
import DatabaseManager from './DatabaseManager';
import { TABLES } from './schema';
import {
  WorkOrder,
  WorkOrderWithDetails,
  Intervention,
  Operation,
  Checkpoint,
  Asset,
  ExecutionReport,
  MediaFile,
  Response,
  SyncQueueItem,
  UserProfile,
  SyncResult
} from '../types/database';

const db = DatabaseManager.getInstance();

/**
 * Opérations pour les Ordres de Travail
 */
export class WorkOrderOperations {
  
  /**
   * Obtient tous les OT assignés à un utilisateur
   */
  static async getAssignedWorkOrders(userId: number): Promise<WorkOrderWithDetails[]> {
    const sql = `
      SELECT 
        wo.*,
        a.nom as asset_name,
        a.reference as asset_reference,
        i.nom as intervention_name,
        u.first_name || ' ' || u.last_name as assigned_user_name,
        t.nom as team_name,
        (SELECT COUNT(*) FROM ${TABLES.OPERATIONS} o 
         INNER JOIN ${TABLES.INTERVENTIONS} iv ON o.intervention_id = iv.id 
         WHERE iv.id = wo.intervention_id) as operations_count,
        (SELECT COUNT(*) FROM ${TABLES.EXECUTION_REPORTS} er 
         WHERE er.work_order_id = wo.id AND er.statut = 'TERMINE') as completed_operations,
        (SELECT COUNT(*) FROM ${TABLES.MEDIA_FILES} mf 
         WHERE mf.work_order_id = wo.id) as media_files_count
      FROM ${TABLES.WORK_ORDERS} wo
      LEFT JOIN ${TABLES.ASSETS} a ON wo.asset_id = a.id
      LEFT JOIN ${TABLES.INTERVENTIONS} i ON wo.intervention_id = i.id
      LEFT JOIN ${TABLES.USER_PROFILE} u ON wo.assigned_user_id = u.id
      LEFT JOIN ${TABLES.TEAMS} t ON wo.assigned_team_id = t.id
      WHERE wo.assigned_user_id = ? OR wo.assigned_team_id IN (
        SELECT team_id FROM ${TABLES.USER_PROFILE} WHERE id = ?
      )
      ORDER BY 
        CASE wo.priorite 
          WHEN 'URGENTE' THEN 1 
          WHEN 'HAUTE' THEN 2 
          WHEN 'NORMALE' THEN 3 
          WHEN 'BASSE' THEN 4 
        END,
        wo.date_planifiee ASC
    `;
    
    return db.select(sql, [userId, userId]);
  }

  /**
   * Obtient un OT avec tous ses détails
   */
  static async getWorkOrderDetails(workOrderId: number): Promise<any> {
    const workOrder = await db.selectById(TABLES.WORK_ORDERS, workOrderId);
    if (!workOrder) return null;

    // Récupérer l'intervention et ses opérations
    const intervention = workOrder.intervention_id 
      ? await db.selectById(TABLES.INTERVENTIONS, workOrder.intervention_id)
      : null;

    const operations = intervention 
      ? await db.selectAll(TABLES.OPERATIONS, 'intervention_id = ?', [intervention.id])
      : [];

    // Récupérer les points de contrôle pour chaque opération
    for (const operation of operations) {
      operation.checkpoints = await db.selectAll(TABLES.CHECKPOINTS, 'operation_id = ?', [operation.id]);
      
      // Récupérer les rapports d'exécution
      operation.execution_reports = await db.selectAll(TABLES.EXECUTION_REPORTS, 
        'work_order_id = ? AND operation_id = ?', 
        [workOrderId, operation.id]
      );
    }

    // Récupérer l'asset
    const asset = workOrder.asset_id 
      ? await db.selectById(TABLES.ASSETS, workOrder.asset_id)
      : null;

    // Récupérer les fichiers média
    const mediaFiles = await db.selectAll(TABLES.MEDIA_FILES, 'work_order_id = ?', [workOrderId]);

    return {
      ...workOrder,
      intervention,
      operations,
      asset,
      mediaFiles
    };
  }

  /**
   * Met à jour le statut d'un OT
   */
  static async updateStatus(workOrderId: number, status: string, userId?: number): Promise<void> {
    const updateData: any = {
      statut: status,
      updated_at: new Date().toISOString(),
      needs_sync: true
    };

    if (status === 'EN_COURS' && !await this.hasStarted(workOrderId)) {
      updateData.date_debut = new Date().toISOString();
    }

    if (status === 'TERMINE') {
      updateData.date_fin = new Date().toISOString();
      // Calculer la durée réelle
      const workOrder = await db.selectById(TABLES.WORK_ORDERS, workOrderId);
      if (workOrder?.date_debut) {
        const start = new Date(workOrder.date_debut);
        const end = new Date();
        updateData.duree_reelle = (end.getTime() - start.getTime()) / (1000 * 60 * 60); // en heures
      }
    }

    await db.update(TABLES.WORK_ORDERS, updateData, 'id = ?', [workOrderId]);
    
    // Ajouter à la queue de synchronisation
    await SyncOperations.addToQueue(TABLES.WORK_ORDERS, workOrderId, 'UPDATE');
  }

  /**
   * Vérifie si un OT a été commencé
   */
  static async hasStarted(workOrderId: number): Promise<boolean> {
    const workOrder = await db.selectById(TABLES.WORK_ORDERS, workOrderId);
    return workOrder?.date_debut !== null;
  }

  /**
   * Sauvegarde un OT (insert ou update)
   */
  static async saveWorkOrder(workOrder: Partial<WorkOrder>): Promise<number> {
    workOrder.updated_at = new Date().toISOString();
    workOrder.needs_sync = true;

    if (workOrder.id) {
      await db.update(TABLES.WORK_ORDERS, workOrder, 'id = ?', [workOrder.id]);
      await SyncOperations.addToQueue(TABLES.WORK_ORDERS, workOrder.id, 'UPDATE');
      return workOrder.id;
    } else {
      workOrder.created_at = new Date().toISOString();
      const id = await db.insert(TABLES.WORK_ORDERS, workOrder);
      await SyncOperations.addToQueue(TABLES.WORK_ORDERS, id, 'INSERT');
      return id;
    }
  }
}

/**
 * Opérations pour les Rapports d'Exécution
 */
export class ExecutionReportOperations {
  
  /**
   * Crée ou met à jour un rapport d'exécution
   */
  static async saveExecutionReport(report: Partial<ExecutionReport>): Promise<number> {
    report.updated_at = new Date().toISOString();
    report.needs_sync = true;

    if (report.id) {
      await db.update(TABLES.EXECUTION_REPORTS, report, 'id = ?', [report.id]);
      await SyncOperations.addToQueue(TABLES.EXECUTION_REPORTS, report.id, 'UPDATE');
      return report.id;
    } else {
      report.created_at = new Date().toISOString();
      const id = await db.insert(TABLES.EXECUTION_REPORTS, report);
      await SyncOperations.addToQueue(TABLES.EXECUTION_REPORTS, id, 'INSERT');
      return id;
    }
  }

  /**
   * Obtient le rapport d'exécution pour une opération d'un OT
   */
  static async getExecutionReport(workOrderId: number, operationId?: number): Promise<ExecutionReport | null> {
    let sql = `SELECT * FROM ${TABLES.EXECUTION_REPORTS} WHERE work_order_id = ?`;
    const params = [workOrderId];

    if (operationId) {
      sql += ' AND operation_id = ?';
      params.push(operationId);
    }

    return db.selectOne(sql, params);
  }

  /**
   * Démarre l'exécution d'une opération
   */
  static async startOperation(workOrderId: number, operationId: number, userId: number): Promise<number> {
    const report: Partial<ExecutionReport> = {
      work_order_id: workOrderId,
      operation_id: operationId,
      user_id: userId,
      statut: 'EN_COURS',
      date_debut: new Date().toISOString()
    };

    return this.saveExecutionReport(report);
  }

  /**
   * Termine l'exécution d'une opération
   */
  static async completeOperation(reportId: number, notes?: string): Promise<void> {
    const report = await db.selectById(TABLES.EXECUTION_REPORTS, reportId);
    if (!report) throw new Error('Rapport d\'exécution non trouvé');

    const updateData: Partial<ExecutionReport> = {
      statut: 'TERMINE',
      date_fin: new Date().toISOString(),
      notes: notes || report.notes
    };

    // Calculer la durée réelle
    if (report.date_debut) {
      const start = new Date(report.date_debut);
      const end = new Date();
      updateData.duree_reelle = (end.getTime() - start.getTime()) / (1000 * 60 * 60); // en heures
    }

    await this.saveExecutionReport({ id: reportId, ...updateData });
  }
}

/**
 * Opérations pour les Fichiers Média
 */
export class MediaFileOperations {
  
  /**
   * Sauvegarde un fichier média
   */
  static async saveMediaFile(mediaFile: Partial<MediaFile>): Promise<number> {
    mediaFile.updated_at = new Date().toISOString();
    mediaFile.needs_sync = true;
    mediaFile.date_capture = mediaFile.date_capture || new Date().toISOString();

    if (mediaFile.id) {
      await db.update(TABLES.MEDIA_FILES, mediaFile, 'id = ?', [mediaFile.id]);
      await SyncOperations.addToQueue(TABLES.MEDIA_FILES, mediaFile.id, 'UPDATE');
      return mediaFile.id;
    } else {
      mediaFile.created_at = new Date().toISOString();
      const id = await db.insert(TABLES.MEDIA_FILES, mediaFile);
      await SyncOperations.addToQueue(TABLES.MEDIA_FILES, id, 'INSERT');
      return id;
    }
  }

  /**
   * Obtient tous les fichiers média d'un OT
   */
  static async getMediaFiles(workOrderId: number): Promise<MediaFile[]> {
    return db.selectAll(TABLES.MEDIA_FILES, 'work_order_id = ?', [workOrderId]);
  }

  /**
   * Marque un fichier comme uploadé
   */
  static async markAsUploaded(mediaFileId: number, serverPath: string): Promise<void> {
    await db.update(TABLES.MEDIA_FILES, {
      is_uploaded: true,
      chemin_serveur: serverPath,
      updated_at: new Date().toISOString()
    }, 'id = ?', [mediaFileId]);
  }

  /**
   * Obtient les fichiers non uploadés
   */
  static async getPendingUploads(): Promise<MediaFile[]> {
    return db.selectAll(TABLES.MEDIA_FILES, 'is_uploaded = 0 AND needs_sync = 1');
  }
}

/**
 * Opérations pour les Réponses aux Points de Contrôle
 */
export class ResponseOperations {
  
  /**
   * Sauvegarde une réponse
   */
  static async saveResponse(response: Partial<Response>): Promise<number> {
    response.updated_at = new Date().toISOString();
    response.needs_sync = true;

    if (response.id) {
      await db.update(TABLES.RESPONSES, response, 'id = ?', [response.id]);
      await SyncOperations.addToQueue(TABLES.RESPONSES, response.id, 'UPDATE');
      return response.id;
    } else {
      response.created_at = new Date().toISOString();
      const id = await db.insert(TABLES.RESPONSES, response);
      await SyncOperations.addToQueue(TABLES.RESPONSES, id, 'INSERT');
      return id;
    }
  }

  /**
   * Obtient toutes les réponses d'un rapport d'exécution
   */
  static async getResponses(executionReportId: number): Promise<Response[]> {
    return db.selectAll(TABLES.RESPONSES, 'execution_report_id = ?', [executionReportId]);
  }

  /**
   * Obtient une réponse spécifique
   */
  static async getResponse(executionReportId: number, checkpointId: number): Promise<Response | null> {
    return db.selectOne(
      `SELECT * FROM ${TABLES.RESPONSES} WHERE execution_report_id = ? AND checkpoint_id = ?`,
      [executionReportId, checkpointId]
    );
  }
}

/**
 * Opérations pour les Assets
 */
export class AssetOperations {
  
  /**
   * Recherche un asset par QR code ou code-barres
   */
  static async findByCode(code: string): Promise<Asset | null> {
    return db.selectOne(
      `SELECT * FROM ${TABLES.ASSETS} WHERE qr_code = ? OR barcode = ?`,
      [code, code]
    );
  }

  /**
   * Recherche des assets par nom ou référence
   */
  static async searchAssets(query: string): Promise<Asset[]> {
    const searchTerm = `%${query}%`;
    return db.select(
      `SELECT * FROM ${TABLES.ASSETS} 
       WHERE nom LIKE ? OR reference LIKE ? 
       ORDER BY nom LIMIT 20`,
      [searchTerm, searchTerm]
    );
  }

  /**
   * Met à jour le statut d'un asset
   */
  static async updateStatus(assetId: number, status: string): Promise<void> {
    await db.update(TABLES.ASSETS, {
      statut: status,
      updated_at: new Date().toISOString()
    }, 'id = ?', [assetId]);
  }
}

/**
 * Opérations de Synchronisation
 */
export class SyncOperations {
  
  /**
   * Ajoute un élément à la queue de synchronisation
   */
  static async addToQueue(tableName: string, recordId: number, action: 'INSERT' | 'UPDATE' | 'DELETE', data?: any): Promise<void> {
    const queueItem: Partial<SyncQueueItem> = {
      table_name: tableName,
      record_id: recordId,
      action,
      data: data ? JSON.stringify(data) : undefined,
      priority: this.getPriority(tableName),
      attempts: 0,
      max_attempts: 3,
      status: 'PENDING'
    };

    await db.insert(TABLES.SYNC_QUEUE, queueItem);
  }

  /**
   * Obtient la priorité d'une table pour la synchronisation
   */
  private static getPriority(tableName: string): number {
    const priorities: Record<string, number> = {
      [TABLES.WORK_ORDERS]: 1,        // Haute priorité
      [TABLES.EXECUTION_REPORTS]: 1,
      [TABLES.MEDIA_FILES]: 2,
      [TABLES.RESPONSES]: 2,
      [TABLES.ASSETS]: 3,             // Priorité normale
      [TABLES.USER_PROFILE]: 4,
      [TABLES.INTERVENTIONS]: 5       // Basse priorité
    };

    return priorities[tableName] || 3;
  }

  /**
   * Obtient les éléments en attente de synchronisation
   */
  static async getPendingSyncItems(limit: number = 50): Promise<SyncQueueItem[]> {
    return db.select(
      `SELECT * FROM ${TABLES.SYNC_QUEUE} 
       WHERE status = 'PENDING' 
       ORDER BY priority ASC, created_at ASC 
       LIMIT ?`,
      [limit]
    );
  }

  /**
   * Marque un élément comme synchronisé avec succès
   */
  static async markSyncSuccess(queueItemId: number): Promise<void> {
    await db.update(TABLES.SYNC_QUEUE, {
      status: 'SUCCESS',
      updated_at: new Date().toISOString()
    }, 'id = ?', [queueItemId]);
  }

  /**
   * Marque un élément comme échoué
   */
  static async markSyncFailed(queueItemId: number, errorMessage: string): Promise<void> {
    const item = await db.selectById(TABLES.SYNC_QUEUE, queueItemId);
    const newAttempts = (item?.attempts || 0) + 1;
    
    await db.update(TABLES.SYNC_QUEUE, {
      status: newAttempts >= (item?.max_attempts || 3) ? 'FAILED' : 'PENDING',
      attempts: newAttempts,
      error_message: errorMessage,
      updated_at: new Date().toISOString()
    }, 'id = ?', [queueItemId]);
  }

  /**
   * Nettoie les éléments synchronisés avec succès (plus anciens que X jours)
   */
  static async cleanupSyncQueue(daysOld: number = 7): Promise<void> {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - daysOld);
    
    await db.delete(TABLES.SYNC_QUEUE, 
      'status = ? AND updated_at < ?', 
      ['SUCCESS', cutoffDate.toISOString()]
    );
  }
}

/**
 * Opérations générales
 */
export class GeneralOperations {
  
  /**
   * Obtient les statistiques de l'application
   */
  static async getAppStatistics(): Promise<any> {
    const stats = await db.getStatistics();
    
    // Statistiques spécifiques
    const pendingSync = await db.selectOne(
      `SELECT COUNT(*) as count FROM ${TABLES.SYNC_QUEUE} WHERE status = 'PENDING'`
    );
    
    const pendingUploads = await db.selectOne(
      `SELECT COUNT(*) as count FROM ${TABLES.MEDIA_FILES} WHERE is_uploaded = 0`
    );
    
    const activeWorkOrders = await db.selectOne(
      `SELECT COUNT(*) as count FROM ${TABLES.WORK_ORDERS} WHERE statut IN ('NOUVEAU', 'ASSIGNE', 'EN_COURS')`
    );

    return {
      ...stats,
      pending_sync: pendingSync?.count || 0,
      pending_uploads: pendingUploads?.count || 0,
      active_work_orders: activeWorkOrders?.count || 0
    };
  }

  /**
   * Réinitialise toutes les données (garde la structure)
   */
  static async resetAllData(): Promise<void> {
    await db.clearAllData();
  }
}