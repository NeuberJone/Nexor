using Dapper;
using Nexor.Application.Abstractions;
using Nexor.Domain.Entities;
using Nexor.Infrastructure.Persistence;

namespace Nexor.Infrastructure.Repositories;

public sealed class SqlitePrinterRepository(SqliteContext context) : IPrinterRepository
{
    public IReadOnlyList<Printer> List(bool activeOnly = false)
    {
        using var connection = context.CreateConnection();
        return connection.Query<Printer>("SELECT * FROM Printers WHERE (@ActiveOnly = 0 OR IsActive = 1) ORDER BY DisplayName", new { ActiveOnly = activeOnly }).AsList();
    }

    public long Save(Printer printer)
    {
        using var connection = context.CreateConnection();
        if (printer.Id == 0)
        {
            return connection.ExecuteScalar<long>(@"INSERT INTO Printers (Code, DisplayName, Manufacturer, Model, Notes, IsActive, CreatedAt)
                VALUES (@Code, @DisplayName, @Manufacturer, @Model, @Notes, @IsActive, @CreatedAt); SELECT last_insert_rowid();", printer);
        }
        connection.Execute(@"UPDATE Printers SET Code=@Code, DisplayName=@DisplayName, Manufacturer=@Manufacturer,
            Model=@Model, Notes=@Notes, IsActive=@IsActive WHERE Id=@Id", printer);
        return printer.Id;
    }

    public void Delete(long id)
    {
        using var connection = context.CreateConnection();
        connection.Execute("DELETE FROM Printers WHERE Id=@Id", new { Id = id });
    }
}
