namespace Nexor.Domain.Entities;

public sealed class RollEvent
{
    public int Id { get; set; }
    public int RollId { get; set; }
    public string EventType { get; set; } = string.Empty;
    public string Message { get; set; } = string.Empty;
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}
