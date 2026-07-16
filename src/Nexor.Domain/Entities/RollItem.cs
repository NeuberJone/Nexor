namespace Nexor.Domain.Entities;

public sealed class RollItem
{
    public int Id { get; set; }
    public int RollId { get; set; }
    public int ProductionLogId { get; set; }
    public string Document { get; set; } = string.Empty;
    public string Machine { get; set; } = string.Empty;
    public string Fabric { get; set; } = string.Empty;
    public double EffectiveMeters { get; set; }
    public double VPositionOffsetMm { get; set; }
    public int SortOrder { get; set; }
    public DateTime? EndTime { get; set; }
}
