using System.Data;
using Dapper;
using Nexor.Domain.Entities;
using Nexor.Application.Abstractions;
using Nexor.Infrastructure.Persistence;

namespace Nexor.Infrastructure.Repositories;

public sealed class SqliteProductionLogRepository : IProductionLogRepository
{
    private readonly SqliteContext _context;

    public SqliteProductionLogRepository(SqliteContext context)
    {
        _context = context;
    }

    public int Insert(ProductionLog item)
    {
        using var connection = _context.CreateConnection();
        connection.Open();
        return connection.ExecuteScalar<int>(@"
            INSERT INTO ProductionLogs (SourcePath, SourceName, Machine, Document, Fabric, EndTime, HeightMm, VPositionMm, IsDuplicate, Fingerprint, CreatedAt)
            VALUES (@SourcePath, @SourceName, @Machine, @Document, @Fabric, @EndTime, @HeightMm, @VPositionMm, @IsDuplicate, @Fingerprint, @CreatedAt);
            SELECT last_insert_rowid();
        ", item);
    }

    public bool ExistsByFingerprint(string fingerprint)
    {
        using var connection = _context.CreateConnection();
        connection.Open();
        return connection.ExecuteScalar<int>(@"
            SELECT COUNT(1) FROM ProductionLogs WHERE Fingerprint = @Fingerprint
        ", new { Fingerprint = fingerprint }) > 0;
    }

    public ProductionLog? GetById(int id)
    {
        using var connection = _context.CreateConnection();
        connection.Open();
        return connection.QuerySingleOrDefault<ProductionLog>(@"
            SELECT * FROM ProductionLogs WHERE Id = @Id
        ", new { Id = id });
    }
}
