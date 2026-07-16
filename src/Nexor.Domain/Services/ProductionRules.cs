using Nexor.Domain.Entities;

namespace Nexor.Domain.Services;

public static class ProductionRules
{
    public static double MetersFromHeight(double heightMm) => Math.Max(0, heightMm) / 1000d;

    public static IReadOnlyList<ProductionLog> NewestFirst(IEnumerable<ProductionLog> items) =>
        items.OrderByDescending(x => x.EndTime ?? DateTime.MinValue).ToList();

    public static IReadOnlyList<FabricBlock> GroupConsecutiveFabrics(IEnumerable<ProductionLog> items)
    {
        var blocks = new List<FabricBlock>();
        foreach (var item in items)
        {
            var fabric = string.IsNullOrWhiteSpace(item.Fabric) ? "Não identificado" : item.Fabric.Trim();
            if (blocks.Count == 0 || !string.Equals(blocks[^1].Fabric, fabric, StringComparison.OrdinalIgnoreCase))
                blocks.Add(new FabricBlock(fabric, new List<ProductionLog>()));
            blocks[^1].Items.Add(item);
        }
        return blocks;
    }
}

public sealed record FabricBlock(string Fabric, List<ProductionLog> Items)
{
    public double TotalMeters => Items.Sum(x => x.RealLengthMeters);
}
