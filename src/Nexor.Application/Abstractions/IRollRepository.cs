using Nexor.Domain.Entities;

namespace Nexor.Application.Abstractions;

public interface IRollRepository
{
    int Insert(Roll roll);
    Roll? GetById(int id);
    IReadOnlyList<Roll> List(string? machine, string? search, int limit);
    void AddItem(RollItem item);
    void AddEvent(RollEvent item);
    void UpdateStatus(int id, string status);
}
