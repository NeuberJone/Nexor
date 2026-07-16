using Nexor.Domain.Entities;

namespace Nexor.Domain.Services;

public interface IProductionLogParser
{
    ProductionLog? Parse(string path);
    string ComputeFingerprint(string path);
}
