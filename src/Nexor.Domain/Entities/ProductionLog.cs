namespace Nexor.Domain.Entities;

public sealed class ProductionLog
{
    public int Id { get; set; }
    public string SourcePath { get; set; } = string.Empty;
    public string SourceName { get; set; } = string.Empty;
    public string Machine { get; set; } = string.Empty;
    public string Document { get; set; } = string.Empty;
    public string Fabric { get; set; } = string.Empty;
    public DateTime? EndTime { get; set; }
    public double HeightMm { get; set; }
    public double VPositionMm { get; set; }
    public double RealLengthMeters => Services.ProductionRules.MetersFromHeight(HeightMm);
    public bool IsDuplicate { get; set; }
    public string Fingerprint { get; set; } = string.Empty;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}
