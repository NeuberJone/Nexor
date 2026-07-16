using Dapper;
using Nexor.Domain.Entities;
using Nexor.Application.Abstractions;
using Nexor.Infrastructure.Persistence;

namespace Nexor.Infrastructure.Repositories;

public sealed class SqliteRollRepository : IRollRepository
{
    private readonly SqliteContext _context;

    public SqliteRollRepository(SqliteContext context)
    {
        _context = context;
    }

    public int Insert(Roll roll)
    {
        using var connection = _context.CreateConnection();
        connection.Open();
        return connection.ExecuteScalar<int>(@"
            INSERT INTO Rolls (Name, Machine, Fabric, Status, Note, CreatedAt, ClosedAt, ExportedAt)
            VALUES (@Name, @Machine, @Fabric, @Status, @Note, @CreatedAt, @ClosedAt, @ExportedAt);
            SELECT last_insert_rowid();
        ", roll);
    }

    public Roll? GetById(int id)
    {
        using var connection = _context.CreateConnection();
        connection.Open();
        var roll = connection.QuerySingleOrDefault<Roll>(@"SELECT r.*, COALESCE(SUM(i.EffectiveMeters),0) TotalMeters, COUNT(i.Id) ItemCount FROM Rolls r LEFT JOIN RollItems i ON i.RollId=r.Id WHERE r.Id=@Id GROUP BY r.Id", new { Id = id });
        if (roll is null) return null;
        roll.Items = connection.Query<RollItem>("SELECT * FROM RollItems WHERE RollId=@Id ORDER BY EndTime DESC", new { Id = id }).AsList();
        roll.Events = connection.Query<RollEvent>("SELECT * FROM RollEvents WHERE RollId=@Id ORDER BY Id DESC", new { Id = id }).AsList();
        return roll;
    }

    public IReadOnlyList<Roll> List(string? machine = null, string? search = null, int limit = 50)
    {
        using var connection = _context.CreateConnection();
        connection.Open();
        return connection.Query<Roll>(@"
            SELECT r.*, COALESCE(SUM(i.EffectiveMeters),0) TotalMeters, COUNT(i.Id) ItemCount FROM Rolls r
            LEFT JOIN RollItems i ON i.RollId = r.Id
            WHERE (@Machine IS NULL OR r.Machine = @Machine)
              AND (@Search IS NULL OR r.Name LIKE '%' || @Search || '%' OR r.Fabric LIKE '%' || @Search || '%' OR EXISTS (SELECT 1 FROM RollItems s WHERE s.RollId=r.Id AND s.Document LIKE '%' || @Search || '%'))
            GROUP BY r.Id ORDER BY r.Id DESC
            LIMIT @Limit
        ", new { Machine = machine, Search = search, Limit = limit }).AsList();
    }

    public void AddItem(RollItem item)
    {
        using var connection = _context.CreateConnection();
        connection.Open();
        connection.Execute(@"
            INSERT INTO RollItems (RollId, ProductionLogId, Document, Machine, Fabric, EffectiveMeters, VPositionOffsetMm, SortOrder, EndTime)
            VALUES (@RollId, @ProductionLogId, @Document, @Machine, @Fabric, @EffectiveMeters, @VPositionOffsetMm, @SortOrder, @EndTime)
        ", item);
    }

    public void AddEvent(RollEvent item)
    {
        using var connection = _context.CreateConnection();
        connection.Open();
        connection.Execute(@"
            INSERT INTO RollEvents (RollId, EventType, Message, CreatedAt)
            VALUES (@RollId, @EventType, @Message, @CreatedAt)
        ", item);
    }

    public void UpdateStatus(int id, string status)
    {
        using var connection = _context.CreateConnection();
        connection.Open();
        connection.Execute(@"
            UPDATE Rolls SET Status = @Status WHERE Id = @RollId
        ", new { Status = status, RollId = id });
    }
}
