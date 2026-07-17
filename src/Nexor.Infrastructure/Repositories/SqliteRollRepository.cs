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
        var roll = connection.QuerySingleOrDefault<Roll>("SELECT * FROM Rolls WHERE Id=@Id", new { Id = id });
        if (roll is null) return null;
        roll.Items = connection.Query<RollItem>("SELECT * FROM RollItems WHERE RollId=@Id ORDER BY EndTime DESC", new { Id = id }).AsList();
        roll.Events = connection.Query<RollEvent>("SELECT * FROM RollEvents WHERE RollId=@Id ORDER BY Id DESC", new { Id = id }).AsList();
        roll.TotalMeters = roll.Items.Sum(item => item.EffectiveMeters);
        roll.ItemCount = roll.Items.Count;
        return roll;
    }

    public IReadOnlyList<Roll> List(string? machine = null, string? search = null, int limit = 50)
    {
        using var connection = _context.CreateConnection();
        connection.Open();
        var rolls = connection.Query<Roll>(@"
            SELECT r.* FROM Rolls r
            WHERE (@Machine IS NULL OR r.Machine = @Machine)
              AND (@Search IS NULL OR r.Name LIKE '%' || @Search || '%' OR r.Fabric LIKE '%' || @Search || '%' OR EXISTS (SELECT 1 FROM RollItems s WHERE s.RollId=r.Id AND s.Document LIKE '%' || @Search || '%'))
            ORDER BY r.Id DESC
            LIMIT @Limit
        ", new { Machine = machine, Search = search, Limit = limit }).AsList();
        if (rolls.Count == 0) return rolls;
        var metrics = connection.Query<RollMetric>("SELECT RollId, EffectiveMeters FROM RollItems WHERE RollId IN @Ids", new { Ids = rolls.Select(roll => roll.Id).ToArray() }).AsList();
        var byRoll = metrics.GroupBy(metric => metric.RollId).ToDictionary(group => group.Key, group => (Total: group.Sum(metric => metric.EffectiveMeters), Count: group.Count()));
        foreach (var roll in rolls)
        {
            if (!byRoll.TryGetValue(roll.Id, out var metric)) continue;
            roll.TotalMeters = metric.Total;
            roll.ItemCount = metric.Count;
        }
        return rolls;
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

    private sealed class RollMetric
    {
        public int RollId { get; set; }
        public double EffectiveMeters { get; set; }
    }
}
