using Nexor.Domain.Entities;
using Nexor.Domain.Services;
using Nexor.Application.Abstractions;

namespace Nexor.Application.Services;

public sealed class ProductionWorkflowService : IRollService
{
    private readonly IProductionLogRepository _productionLogRepository;
    private readonly IRollRepository _rollRepository;

    public ProductionWorkflowService(IProductionLogRepository productionLogRepository, IRollRepository rollRepository)
    {
        _productionLogRepository = productionLogRepository;
        _rollRepository = rollRepository;
    }

    public Roll CreateRoll(string name, string machine, string fabric, string? note = null)
    {
        var roll = new Roll
        {
            Name = name,
            Machine = machine,
            Fabric = fabric,
            Note = note,
            Status = "Open"
        };

        var id = _rollRepository.Insert(roll);
        roll.Id = id;
        return roll;
    }

    public Roll? GetRoll(int id) => _rollRepository.GetById(id);

    public IEnumerable<Roll> ListRolls(string? machine = null, string? search = null, int limit = 50) => _rollRepository.List(machine, search, Math.Clamp(limit, 1, 500));

    public void AddLogToRoll(int rollId, ProductionLog log)
    {
        if (_productionLogRepository.ExistsByFingerprint(log.Fingerprint))
        {
            log.IsDuplicate = true;
            return;
        }

        var logId = _productionLogRepository.Insert(log);
        log.Id = logId;

        _rollRepository.AddItem(new RollItem
        {
            RollId = rollId,
            ProductionLogId = log.Id,
            Document = log.Document,
            Machine = log.Machine,
            Fabric = log.Fabric,
            EffectiveMeters = log.RealLengthMeters,
            VPositionOffsetMm = log.VPositionMm,
            EndTime = log.EndTime,
            SortOrder = 0
        });
    }

    public void CloseRoll(int rollId)
    {
        _rollRepository.UpdateStatus(rollId, "Closed");
        AddEvent(rollId, "ROLL_CLOSED", "Rolo fechado no Nexor.");
    }

    public void AddEvent(int rollId, string eventType, string message)
    {
        _rollRepository.AddEvent(new RollEvent
        {
            RollId = rollId,
            EventType = eventType,
            Message = message
        });
    }
}
