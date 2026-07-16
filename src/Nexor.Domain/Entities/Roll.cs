namespace Nexor.Domain.Entities;

public sealed class Roll
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Machine { get; set; } = string.Empty;
    public string Fabric { get; set; } = string.Empty;
    public string Status { get; set; } = "Open";
    public string? Note { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime? ClosedAt { get; set; }
    public DateTime? ExportedAt { get; set; }
    public List<RollItem> Items { get; set; } = new();
    public List<RollEvent> Events { get; set; } = new();
    public double TotalMeters { get; set; }
    public int ItemCount { get; set; }
}
