using Nexor.Domain.Entities;

namespace Nexor.Domain.Services;

public interface IRollService
{
    Roll CreateRoll(string name, string machine, string fabric, string? note = null);
    Roll? GetRoll(int id);
    IEnumerable<Roll> ListRolls(string? machine = null, string? search = null, int limit = 50);
    void AddLogToRoll(int rollId, ProductionLog log);
    void CloseRoll(int rollId);
    void AddEvent(int rollId, string eventType, string message);
}
