// src/database/schema.ts
import * as SQLite from 'expo-sqlite';

export const DATABASE_NAME = 'gmao_mobile.db';
export const DATABASE_VERSION = '1.0';
export const DATABASE_DISPLAYNAME = 'GMAO Mobile Database';
export const DATABASE_SIZE = 200000;

// Tables principales pour la synchronisation
export const TABLES = {
  // Authentification et utilisateur
  USER_PROFILE: 'user_profiles',
  
  // Interventions et ordres de travail
  WORK_ORDERS: 'work_orders',
  INTERVENTIONS: 'interventions',
  OPERATIONS: 'operations',
  CHECKPOINTS: 'checkpoints',
  
  // Assets et équipements
  ASSETS: 'assets',
  ASSET_CATEGORIES: 'asset_categories',
  
  // Rapports et captures
  EXECUTION_REPORTS: 'execution_reports',
  MEDIA_FILES: 'media_files',
  RESPONSES: 'responses',
  
  // Synchronisation
  SYNC_QUEUE: 'sync_queue',
  SYNC_LOG: 'sync_log',
  
  // Données de référence
  SPARE_PARTS: 'spare_parts',
  TEAMS: 'teams',
  COMPETENCES: 'competences'
};

// Scripts de création des tables
export const CREATE_TABLES = {
  // Profil utilisateur local
  USER_PROFILE: `
    CREATE TABLE IF NOT EXISTS ${TABLES.USER_PROFILE} (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      server_id INTEGER,
      username TEXT NOT NULL,
      first_name TEXT,
      last_name TEXT,
      email TEXT,
      role TEXT DEFAULT 'TECHNICIEN',
      team_id INTEGER,
      competences TEXT, -- JSON array
      last_sync DATETIME,
      is_active BOOLEAN DEFAULT 1,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `,

  // Ordres de travail
  WORK_ORDERS: `
    CREATE TABLE IF NOT EXISTS ${TABLES.WORK_ORDERS} (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      server_id INTEGER,
      numero_ot TEXT NOT NULL,
      titre TEXT NOT NULL,
      description TEXT,
      statut TEXT DEFAULT 'NOUVEAU',
      priorite TEXT DEFAULT 'NORMALE',
      type_ot TEXT,
      asset_id INTEGER,
      assigned_user_id INTEGER,
      assigned_team_id INTEGER,
      date_creation DATETIME,
      date_planifiee DATETIME,
      date_debut DATETIME,
      date_fin DATETIME,
      duree_estimee REAL,
      duree_reelle REAL,
      localisation TEXT,
      latitude REAL,
      longitude REAL,
      intervention_id INTEGER,
      notes TEXT,
      needs_sync BOOLEAN DEFAULT 1,
      last_sync DATETIME,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `,

  // Interventions (templates)
  INTERVENTIONS: `
    CREATE TABLE IF NOT EXISTS ${TABLES.INTERVENTIONS} (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      server_id INTEGER,
      nom TEXT NOT NULL,
      description TEXT,
      statut TEXT DEFAULT 'ACTIVE',
      duree_estimee_heures REAL,
      techniciens_requis INTEGER DEFAULT 1,
      competences_requises TEXT, -- JSON array
      last_sync DATETIME,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `,

  // Opérations dans une intervention
  OPERATIONS: `
    CREATE TABLE IF NOT EXISTS ${TABLES.OPERATIONS} (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      server_id INTEGER,
      intervention_id INTEGER,
      nom TEXT NOT NULL,
      description TEXT,
      ordre INTEGER DEFAULT 1,
      duree_estimee REAL,
      competence_requise TEXT,
      outils_requis TEXT, -- JSON array
      pieces_requises TEXT, -- JSON array
      is_obligatoire BOOLEAN DEFAULT 1,
      last_sync DATETIME,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (intervention_id) REFERENCES ${TABLES.INTERVENTIONS}(id)
    );
  `,

  // Points de contrôle dans une opération
  CHECKPOINTS: `
    CREATE TABLE IF NOT EXISTS ${TABLES.CHECKPOINTS} (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      server_id INTEGER,
      operation_id INTEGER,
      nom TEXT NOT NULL,
      description TEXT,
      type_reponse TEXT DEFAULT 'TEXTE',
      valeur_attendue TEXT,
      unite_mesure TEXT,
      is_obligatoire BOOLEAN DEFAULT 1,
      ordre INTEGER DEFAULT 1,
      last_sync DATETIME,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (operation_id) REFERENCES ${TABLES.OPERATIONS}(id)
    );
  `,

  // Équipements/Assets
  ASSETS: `
    CREATE TABLE IF NOT EXISTS ${TABLES.ASSETS} (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      server_id INTEGER,
      nom TEXT NOT NULL,
      reference TEXT,
      qr_code TEXT,
      barcode TEXT,
      categorie_id INTEGER,
      marque TEXT,
      modele TEXT,
      statut TEXT DEFAULT 'EN_SERVICE',
      localisation TEXT,
      latitude REAL,
      longitude REAL,
      date_installation DATETIME,
      date_mise_en_service DATETIME,
      fin_garantie DATETIME,
      criticite INTEGER DEFAULT 1,
      specifications TEXT, -- JSON object
      last_sync DATETIME,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `,

  // Catégories d'assets
  ASSET_CATEGORIES: `
    CREATE TABLE IF NOT EXISTS ${TABLES.ASSET_CATEGORIES} (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      server_id INTEGER,
      nom TEXT NOT NULL,
      description TEXT,
      couleur TEXT DEFAULT '#6B7280',
      icone TEXT DEFAULT 'cog',
      last_sync DATETIME,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `,

  // Rapports d'exécution
  EXECUTION_REPORTS: `
    CREATE TABLE IF NOT EXISTS ${TABLES.EXECUTION_REPORTS} (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      server_id INTEGER,
      work_order_id INTEGER NOT NULL,
      operation_id INTEGER,
      checkpoint_id INTEGER,
      user_id INTEGER,
      statut TEXT DEFAULT 'EN_COURS',
      date_debut DATETIME,
      date_fin DATETIME,
      duree_reelle REAL,
      notes TEXT,
      difficultees_rencontrees TEXT,
      pieces_utilisees TEXT, -- JSON array
      outils_utilises TEXT, -- JSON array
      signature_client TEXT, -- Base64 ou chemin fichier
      satisfaction_client INTEGER, -- 1-5
      needs_sync BOOLEAN DEFAULT 1,
      last_sync DATETIME,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (work_order_id) REFERENCES ${TABLES.WORK_ORDERS}(id)
    );
  `,

  // Fichiers média (photos, audio, etc.)
  MEDIA_FILES: `
    CREATE TABLE IF NOT EXISTS ${TABLES.MEDIA_FILES} (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      server_id INTEGER,
      work_order_id INTEGER,
      execution_report_id INTEGER,
      operation_id INTEGER,
      asset_id INTEGER,
      type_media TEXT NOT NULL, -- photo, audio, video, signature, document
      nom_fichier TEXT NOT NULL,
      chemin_local TEXT NOT NULL,
      chemin_serveur TEXT,
      taille_fichier INTEGER,
      mime_type TEXT,
      description TEXT,
      latitude REAL,
      longitude REAL,
      date_capture DATETIME DEFAULT CURRENT_TIMESTAMP,
      is_uploaded BOOLEAN DEFAULT 0,
      needs_sync BOOLEAN DEFAULT 1,
      upload_attempts INTEGER DEFAULT 0,
      last_sync DATETIME,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `,

  // Réponses aux points de contrôle
  RESPONSES: `
    CREATE TABLE IF NOT EXISTS ${TABLES.RESPONSES} (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      server_id INTEGER,
      execution_report_id INTEGER NOT NULL,
      checkpoint_id INTEGER NOT NULL,
      valeur TEXT,
      valeur_numerique REAL,
      commentaire TEXT,
      is_conforme BOOLEAN,
      media_file_id INTEGER,
      needs_sync BOOLEAN DEFAULT 1,
      last_sync DATETIME,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (execution_report_id) REFERENCES ${TABLES.EXECUTION_REPORTS}(id),
      FOREIGN KEY (checkpoint_id) REFERENCES ${TABLES.CHECKPOINTS}(id)
    );
  `,

  // File d'attente de synchronisation
  SYNC_QUEUE: `
    CREATE TABLE IF NOT EXISTS ${TABLES.SYNC_QUEUE} (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      table_name TEXT NOT NULL,
      record_id INTEGER NOT NULL,
      action TEXT NOT NULL, -- INSERT, UPDATE, DELETE
      data TEXT, -- JSON data
      priority INTEGER DEFAULT 1, -- 1=high, 5=low
      attempts INTEGER DEFAULT 0,
      max_attempts INTEGER DEFAULT 3,
      error_message TEXT,
      status TEXT DEFAULT 'PENDING', -- PENDING, PROCESSING, SUCCESS, FAILED
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `,

  // Log de synchronisation
  SYNC_LOG: `
    CREATE TABLE IF NOT EXISTS ${TABLES.SYNC_LOG} (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      sync_type TEXT NOT NULL, -- FULL, PARTIAL, UPLOAD, DOWNLOAD
      table_name TEXT,
      records_processed INTEGER DEFAULT 0,
      records_success INTEGER DEFAULT 0,
      records_failed INTEGER DEFAULT 0,
      start_time DATETIME,
      end_time DATETIME,
      duration_seconds REAL,
      status TEXT DEFAULT 'RUNNING', -- RUNNING, SUCCESS, FAILED, PARTIAL
      error_message TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `,

  // Pièces détachées
  SPARE_PARTS: `
    CREATE TABLE IF NOT EXISTS ${TABLES.SPARE_PARTS} (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      server_id INTEGER,
      nom TEXT NOT NULL,
      reference TEXT,
      description TEXT,
      categorie TEXT,
      prix_unitaire REAL,
      unite TEXT DEFAULT 'unité',
      stock_min INTEGER DEFAULT 0,
      fournisseur TEXT,
      last_sync DATETIME,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `,

  // Équipes
  TEAMS: `
    CREATE TABLE IF NOT EXISTS ${TABLES.TEAMS} (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      server_id INTEGER,
      nom TEXT NOT NULL,
      description TEXT,
      chef_equipe_id INTEGER,
      specialites TEXT, -- JSON array
      zone_intervention TEXT,
      last_sync DATETIME,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `,

  // Compétences
  COMPETENCES: `
    CREATE TABLE IF NOT EXISTS ${TABLES.COMPETENCES} (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      server_id INTEGER,
      nom TEXT NOT NULL,
      description TEXT,
      niveau_requis TEXT DEFAULT 'DEBUTANT',
      categorie TEXT,
      last_sync DATETIME,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
  `
};

// Index pour optimiser les performances
export const CREATE_INDEXES = [
  `CREATE INDEX IF NOT EXISTS idx_work_orders_status ON ${TABLES.WORK_ORDERS}(statut);`,
  `CREATE INDEX IF NOT EXISTS idx_work_orders_assigned ON ${TABLES.WORK_ORDERS}(assigned_user_id);`,
  `CREATE INDEX IF NOT EXISTS idx_work_orders_sync ON ${TABLES.WORK_ORDERS}(needs_sync);`,
  `CREATE INDEX IF NOT EXISTS idx_media_sync ON ${TABLES.MEDIA_FILES}(needs_sync);`,
  `CREATE INDEX IF NOT EXISTS idx_media_uploaded ON ${TABLES.MEDIA_FILES}(is_uploaded);`,
  `CREATE INDEX IF NOT EXISTS idx_sync_queue_status ON ${TABLES.SYNC_QUEUE}(status);`,
  `CREATE INDEX IF NOT EXISTS idx_sync_queue_priority ON ${TABLES.SYNC_QUEUE}(priority);`,
  `CREATE INDEX IF NOT EXISTS idx_assets_qr ON ${TABLES.ASSETS}(qr_code);`,
  `CREATE INDEX IF NOT EXISTS idx_assets_barcode ON ${TABLES.ASSETS}(barcode);`,
  `CREATE INDEX IF NOT EXISTS idx_execution_reports_wo ON ${TABLES.EXECUTION_REPORTS}(work_order_id);`,
  `CREATE INDEX IF NOT EXISTS idx_responses_report ON ${TABLES.RESPONSES}(execution_report_id);`
];