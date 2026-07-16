using Nexor.Domain.Entities;

namespace Nexor.Application.Abstractions;

public interface IProductionLogRepository
{
    bool ExistsByFingerprint(string fingerprint);
    int Insert(ProductionLog item);
    ProductionLog? GetById(int id);
}
