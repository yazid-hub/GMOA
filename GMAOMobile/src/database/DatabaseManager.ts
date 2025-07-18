// src/database/DatabaseManager.ts
import * as SQLite from 'expo-sqlite';
import { 
  DATABASE_NAME, 
  DATABASE_VERSION, 
  DATABASE_DISPLAYNAME, 
  DATABASE_SIZE,
  CREATE_TABLES,
  CREATE_INDEXES,
  TABLES 
} from './schema';

class DatabaseManager {
  private static instance: DatabaseManager;
  private database: SQLite.SQLiteDatabase | null = null;

  private constructor() {}

  public static getInstance(): DatabaseManager {
    if (!DatabaseManager.instance) {
      DatabaseManager.instance = new DatabaseManager();
    }
    return DatabaseManager.instance;
  }

  /**
   * Initialise la base de données
   */
  public async initializeDatabase(): Promise<void> {
    try {
      console.log('🔄 Initialisation de la base de données...');
      
      // Nouvelle API Expo SQLite
      this.database = await SQLite.openDatabaseAsync(DATABASE_NAME);

      await this.createTables();
      await this.createIndexes();
      
      console.log('✅ Base de données initialisée avec succès');
    } catch (error) {
      console.error('❌ Erreur lors de l\'initialisation de la DB:', error);
      throw error;
    }
  }

  /**
   * Crée toutes les tables
   */
  private async createTables(): Promise<void> {
    if (!this.database) throw new Error('Database non initialisée');

    try {
      for (const [tableName, createSQL] of Object.entries(CREATE_TABLES)) {
        await this.database.execAsync(createSQL);
        console.log(`✅ Table ${tableName} créée`);
      }
    } catch (error) {
      console.error('❌ Erreur création tables:', error);
      throw error;
    }
  }

  /**
   * Crée les index
   */
  private async createIndexes(): Promise<void> {
    if (!this.database) throw new Error('Database non initialisée');

    try {
      for (const indexSQL of CREATE_INDEXES) {
        await this.database.execAsync(indexSQL);
      }
      console.log('✅ Index créés');
    } catch (error) {
      console.error('❌ Erreur création index:', error);
      throw error;
    }
  }

  /**
   * Exécute une requête SQL
   */
  public async executeSql(sql: string, params: any[] = []): Promise<any> {
    if (!this.database) {
      await this.initializeDatabase();
    }

    try {
      const result = await this.database!.runAsync(sql, params);
      return result;
    } catch (error) {
      console.error('❌ Erreur SQL:', error, 'Query:', sql, 'Params:', params);
      throw error;
    }
  }

  /**
   * Insert un enregistrement
   */
  public async insert(table: string, data: Record<string, any>): Promise<number> {
    const columns = Object.keys(data);
    const placeholders = columns.map(() => '?').join(', ');
    const values = Object.values(data);

    const sql = `INSERT INTO ${table} (${columns.join(', ')}) VALUES (${placeholders})`;
    
    try {
      const result = await this.database!.runAsync(sql, values);
      return result.lastInsertRowId;
    } catch (error) {
      console.error('❌ Erreur INSERT:', error);
      throw error;
    }
  }

  /**
   * Met à jour un enregistrement
   */
  public async update(table: string, data: Record<string, any>, where: string, whereParams: any[] = []): Promise<number> {
    const columns = Object.keys(data);
    const setClause = columns.map(col => `${col} = ?`).join(', ');
    const values = [...Object.values(data), ...whereParams];

    const sql = `UPDATE ${table} SET ${setClause} WHERE ${where}`;
    
    try {
      const result = await this.database!.runAsync(sql, values);
      return result.changes;
    } catch (error) {
      console.error('❌ Erreur UPDATE:', error);
      throw error;
    }
  }

  /**
   * Supprime un enregistrement
   */
  public async delete(table: string, where: string, whereParams: any[] = []): Promise<number> {
    const sql = `DELETE FROM ${table} WHERE ${where}`;
    
    try {
      const result = await this.database!.runAsync(sql, whereParams);
      return result.changes;
    } catch (error) {
      console.error('❌ Erreur DELETE:', error);
      throw error;
    }
  }

  /**
   * Sélectionne des enregistrements
   */
  public async select(sql: string, params: any[] = []): Promise<any[]> {
    try {
      const result = await this.database!.getAllAsync(sql, params);
      return result;
    } catch (error) {
      console.error('❌ Erreur SELECT:', error);
      throw error;
    }
  }

  /**
   * Sélectionne un seul enregistrement
   */
  public async selectOne(sql: string, params: any[] = []): Promise<any | null> {
    try {
      const result = await this.database!.getFirstAsync(sql, params);
      return result || null;
    } catch (error) {
      console.error('❌ Erreur SELECT ONE:', error);
      throw error;
    }
  }

  /**
   * Sélectionne tous les enregistrements d'une table
   */
  public async selectAll(table: string, where?: string, whereParams: any[] = []): Promise<any[]> {
    let sql = `SELECT * FROM ${table}`;
    if (where) {
      sql += ` WHERE ${where}`;
    }
    
    return this.select(sql, whereParams);
  }

  /**
   * Sélectionne un enregistrement par ID
   */
  public async selectById(table: string, id: number): Promise<any | null> {
    const sql = `SELECT * FROM ${table} WHERE id = ?`;
    return this.selectOne(sql, [id]);
  }

  /**
   * Insert ou update (upsert)
   */
  public async upsert(table: string, data: Record<string, any>, uniqueColumns: string[]): Promise<number> {
    try {
      // Essaie de trouver l'enregistrement existant
      const whereClause = uniqueColumns.map(col => `${col} = ?`).join(' AND ');
      const whereValues = uniqueColumns.map(col => data[col]);
      
      const existing = await this.selectOne(`SELECT id FROM ${table} WHERE ${whereClause}`, whereValues);
      
      if (existing) {
        // Update
        await this.update(table, data, 'id = ?', [existing.id]);
        return existing.id;
      } else {
        // Insert
        return await this.insert(table, data);
      }
    } catch (error) {
      console.error('❌ Erreur UPSERT:', error);
      throw error;
    }
  }

  /**
   * Commence une transaction
   */
  public async transaction(operations: () => Promise<void>): Promise<void> {
    if (!this.database) {
      await this.initializeDatabase();
    }

    try {
      await this.database!.withTransactionAsync(operations);
    } catch (error) {
      console.error('❌ Erreur TRANSACTION:', error);
      throw error;
    }
  }

  /**
   * Vide toutes les tables (reset complet)
   */
  public async clearAllData(): Promise<void> {
    try {
      console.log('🔄 Suppression de toutes les données...');
      
      const tables = Object.values(TABLES);
      for (const table of tables) {
        await this.database!.runAsync(`DELETE FROM ${table}`);
        console.log(`✅ Table ${table} vidée`);
      }
      
      console.log('✅ Toutes les données supprimées');
    } catch (error) {
      console.error('❌ Erreur clearAllData:', error);
      throw error;
    }
  }

  /**
   * Obtient des statistiques sur la base
   */
  public async getStatistics(): Promise<Record<string, number>> {
    try {
      const stats: Record<string, number> = {};
      
      const tables = Object.values(TABLES);
      for (const table of tables) {
        const result = await this.selectOne(`SELECT COUNT(*) as count FROM ${table}`);
        stats[table] = result?.count || 0;
      }
      
      return stats;
    } catch (error) {
      console.error('❌ Erreur getStatistics:', error);
      throw error;
    }
  }

  /**
   * Ferme la base de données
   */
  public async closeDatabase(): Promise<void> {
    if (this.database) {
      try {
        await this.database.closeAsync();
        this.database = null;
        console.log('✅ Base de données fermée');
      } catch (error) {
        console.error('❌ Erreur fermeture DB:', error);
      }
    }
  }

  /**
   * Obtient la base de données (pour usage avancé)
   */
  public getDatabase(): SQLite.SQLiteDatabase | null {
    return this.database;
  }
}

export default DatabaseManager;