using Nexor.Domain.Entities;

namespace Nexor.Application.Abstractions;

public interface IPrinterRepository
{
    IReadOnlyList<Printer> List(bool activeOnly = false);
    long Save(Printer printer);
    void Delete(long id);
}
