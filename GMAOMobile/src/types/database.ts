// src/types/database.ts

// Types de base
export interface BaseEntity {
  id: number;
  server_id?: number;
  created_at: string;
  updated_at: string;
  last_sync?: string;
}

export interface SyncableEntity extends BaseEntity {
  needs_sync: boolean;
}

// Profil utilisateur
export interface UserProfile extends BaseEntity {
  username: string;
  first_name?: string;
  last_name?: string;
  email?: string;
  role: 'ADMIN' | 'MANAGER' | 'TECHNICIEN' | 'OPERATEUR';
  team_id?: number;
  competences?: string; // JSON array
  is_active: boolean;
}

// Ordre de travail
export interface WorkOrder extends SyncableEntity {
  numero_ot: string;
  titre: string;
  description?: string;
  statut: 'NOUVEAU' | 'ASSIGNE' | 'EN_COURS' | 'SUSPENDU' | 'TERMINE' | 'ANNULE';
  priorite: 'BASSE' | 'NORMALE' | 'HAUTE' | 'URGENTE';
  type_ot?: string;
  asset_id?: number;
  assigned_user_id?: number;
  assigned_team_id?: number;
  date_creation: string;
  date_planifiee?: string;
  date_debut?: string;
  date_fin?: string;
  duree_estimee?: number;
  duree_reelle?: number;
  localisation?: string;
  latitude?: number;
  longitude?: number;
  intervention_id?: number;
  notes?: string;
}

// Intervention (template)
export interface Intervention extends BaseEntity {
  nom: string;
  description?: string;
  statut: 'ACTIVE' | 'INACTIVE' | 'ARCHIVEE';
  duree_estimee_heures?: number;
  techniciens_requis: number;
  competences_requises?: string; // JSON array
}

// Opération dans une intervention
export interface Operation extends BaseEntity {
  intervention_id: number;
  nom: string;
  description?: string;
  ordre: number;
  duree_estimee?: number;
  competence_requise?: string;
  outils_requis?: string; // JSON array
  pieces_requises?: string; // JSON array
  is_obligatoire: boolean;
}

// Point de contrôle
export interface Checkpoint extends BaseEntity {
  operation_id: number;
  nom: string;
  description?: string;
  type_reponse: 'TEXTE' | 'NUMERIQUE' | 'BOOLEEN' | 'CHOIX_MULTIPLE' | 'PHOTO' | 'SIGNATURE';
  valeur_attendue?: string;
  unite_mesure?: string;
  is_obligatoire: boolean;
  ordre: number;
}

// Asset/Équipement
export interface Asset extends BaseEntity {
  nom: string;
  reference?: string;
  qr_code?: string;
  barcode?: string;
  categorie_id?: number;
  marque?: string;
  modele?: string;
  statut: 'EN_SERVICE' | 'EN_PANNE' | 'EN_MAINTENANCE' | 'HORS_SERVICE';
  localisation?: string;
  latitude?: number;
  longitude?: number;
  date_installation?: string;
  date_mise_en_service?: string;
  fin_garantie?: string;
  criticite: number;
  specifications?: string; // JSON object
}

// Catégorie d'asset
export interface AssetCategory extends BaseEntity {
  nom: string;
  description?: string;
  couleur: string;
  icone: string;
}

// Rapport d'exécution
export interface ExecutionReport extends SyncableEntity {
  work_order_id: number;
  operation_id?: number;
  checkpoint_id?: number;
  user_id?: number;
  statut: 'EN_COURS' | 'TERMINE' | 'SUSPENDU' | 'ECHEC';
  date_debut?: string;
  date_fin?: string;
  duree_reelle?: number;
  notes?: string;
  difficultees_rencontrees?: string;
  pieces_utilisees?: string; // JSON array
  outils_utilises?: string; // JSON array
  signature_client?: string;
  satisfaction_client?: number; // 1-5
}

// Fichier média
export interface MediaFile extends SyncableEntity {
  work_order_id?: number;
  execution_report_id?: number;
  operation_id?: number;
  asset_id?: number;
  type_media: 'photo' | 'audio' | 'video' | 'signature' | 'document';
  nom_fichier: string;
  chemin_local: string;
  chemin_serveur?: string;
  taille_fichier?: number;
  mime_type?: string;
  description?: string;
  latitude?: number;
  longitude?: number;
  date_capture: string;
  is_uploaded: boolean;
  upload_attempts: number;
}

// Réponse à un point de contrôle
export interface Response extends SyncableEntity {
  execution_report_id: number;
  checkpoint_id: number;
  valeur?: string;
  valeur_numerique?: number;
  commentaire?: string;
  is_conforme?: boolean;
  media_file_id?: number;
}

// File de synchronisation
export interface SyncQueueItem extends BaseEntity {
  table_name: string;
  record_id: number;
  action: 'INSERT' | 'UPDATE' | 'DELETE';
  data?: string; // JSON data
  priority: number; // 1=high, 5=low
  attempts: number;
  max_attempts: number;
  error_message?: string;
  status: 'PENDING' | 'PROCESSING' | 'SUCCESS' | 'FAILED';
}

// Log de synchronisation
export interface SyncLog extends BaseEntity {
  sync_type: 'FULL' | 'PARTIAL' | 'UPLOAD' | 'DOWNLOAD';
  table_name?: string;
  records_processed: number;
  records_success: number;
  records_failed: number;
  start_time?: string;
  end_time?: string;
  duration_seconds?: number;
  status: 'RUNNING' | 'SUCCESS' | 'FAILED' | 'PARTIAL';
  error_message?: string;
}

// Pièce détachée
export interface SparePart extends BaseEntity {
  nom: string;
  reference?: string;
  description?: string;
  categorie?: string;
  prix_unitaire?: number;
  unite: string;
  stock_min: number;
  fournisseur?: string;
}

// Équipe
export interface Team extends BaseEntity {
  nom: string;
  description?: string;
  chef_equipe_id?: number;
  specialites?: string; // JSON array
  zone_intervention?: string;
}

// Compétence
export interface Competence extends BaseEntity {
  nom: string;
  description?: string;
  niveau_requis: 'DEBUTANT' | 'INTERMEDIAIRE' | 'AVANCE' | 'EXPERT';
  categorie?: string;
}

// Types pour les opérations de synchronisation
export interface SyncResult {
  success: boolean;
  recordsProcessed: number;
  recordsSuccess: number;
  recordsFailed: number;
  errors: string[];
  duration: number;
}

// Types pour les statistiques
export interface DatabaseStats {
  [tableName: string]: number;
}

// Types pour les requêtes complexes
export interface WorkOrderWithDetails extends WorkOrder {
  asset_name?: string;
  asset_reference?: string;
  intervention_name?: string;
  assigned_user_name?: string;
  team_name?: string;
  operations_count?: number;
  completed_operations?: number;
  media_files_count?: number;
}