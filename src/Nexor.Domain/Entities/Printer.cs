namespace Nexor.Domain.Entities;

public sealed class Printer
{
    public long Id { get; set; }
    public string Code { get; set; } = string.Empty;
    public string DisplayName { get; set; } = string.Empty;
    public string Manufacturer { get; set; } = string.Empty;
    public string Model { get; set; } = string.Empty;
    public string Notes { get; set; } = string.Empty;
    public bool IsActive { get; set; } = true;
    public DateTime CreatedAt { get; set; } = DateTime.Now;
    public string Description => string.Join(" · ", new[] { Manufacturer, Model }.Where(x => !string.IsNullOrWhiteSpace(x)));
}
