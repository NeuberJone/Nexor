using System.Data;
using Microsoft.Data.Sqlite;

namespace Nexor.Infrastructure.Persistence;

public sealed class SqliteContext
{
    private readonly string _connectionString;

    public SqliteContext(string databasePath)
    {
        _connectionString = new SqliteConnectionStringBuilder
        {
            DataSource = databasePath,
            Mode = SqliteOpenMode.ReadWriteCreate,
            Pooling = false,
            ForeignKeys = true
        }.ToString();

        EnsureDatabase();
    }

    public IDbConnection CreateConnection() => new SqliteConnection(_connectionString);

    private void EnsureDatabase()
    {
        using var connection = CreateConnection();
        connection.Open();
        using var command = connection.CreateCommand();
        command.CommandText = @"
            CREATE TABLE IF NOT EXISTS SchemaMigrations (
                Version INTEGER PRIMARY KEY,
                AppliedAt TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS ProductionLogs (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                SourcePath TEXT NOT NULL,
                SourceName TEXT NOT NULL,
                Machine TEXT NOT NULL,
                Document TEXT NOT NULL,
                Fabric TEXT NOT NULL,
                EndTime TEXT,
                HeightMm REAL NOT NULL DEFAULT 0,
                VPositionMm REAL NOT NULL DEFAULT 0,
                IsDuplicate INTEGER NOT NULL DEFAULT 0,
                Fingerprint TEXT NOT NULL UNIQUE,
                CreatedAt TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS Rolls (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                Name TEXT NOT NULL UNIQUE,
                Machine TEXT NOT NULL,
                Fabric TEXT NOT NULL,
                Status TEXT NOT NULL,
                Note TEXT,
                CreatedAt TEXT NOT NULL,
                ClosedAt TEXT,
                ExportedAt TEXT
            );

            CREATE TABLE IF NOT EXISTS RollItems (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                RollId INTEGER NOT NULL,
                ProductionLogId INTEGER NOT NULL,
                Document TEXT NOT NULL,
                Machine TEXT NOT NULL,
                Fabric TEXT NOT NULL,
                EffectiveMeters REAL NOT NULL DEFAULT 0,
                VPositionOffsetMm REAL NOT NULL DEFAULT 0,
                SortOrder INTEGER NOT NULL DEFAULT 0,
                EndTime TEXT,
                FOREIGN KEY (RollId) REFERENCES Rolls(Id),
                FOREIGN KEY (ProductionLogId) REFERENCES ProductionLogs(Id)
            );

            CREATE TABLE IF NOT EXISTS RollEvents (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                RollId INTEGER NOT NULL,
                EventType TEXT NOT NULL,
                Message TEXT NOT NULL,
                CreatedAt TEXT NOT NULL,
                FOREIGN KEY (RollId) REFERENCES Rolls(Id)
            );

            CREATE TABLE IF NOT EXISTS Settings (
                Key TEXT PRIMARY KEY,
                Value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS Printers (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                Code TEXT NOT NULL UNIQUE COLLATE NOCASE,
                DisplayName TEXT NOT NULL,
                Manufacturer TEXT NOT NULL DEFAULT '',
                Model TEXT NOT NULL DEFAULT '',
                Notes TEXT NOT NULL DEFAULT '',
                IsActive INTEGER NOT NULL DEFAULT 1,
                CreatedAt TEXT NOT NULL
            );
            INSERT OR IGNORE INTO Printers (Code, DisplayName, Manufacturer, Model, Notes, IsActive, CreatedAt)
                VALUES ('M1', 'M1', '', '', 'Impressora inicial', 1, CURRENT_TIMESTAMP);
            INSERT OR IGNORE INTO Printers (Code, DisplayName, Manufacturer, Model, Notes, IsActive, CreatedAt)
                VALUES ('M2', 'M2', '', '', 'Impressora inicial', 1, CURRENT_TIMESTAMP);
            INSERT OR IGNORE INTO SchemaMigrations (Version, AppliedAt) VALUES (1, CURRENT_TIMESTAMP);
        ";
        command.ExecuteNonQuery();
    }
}
