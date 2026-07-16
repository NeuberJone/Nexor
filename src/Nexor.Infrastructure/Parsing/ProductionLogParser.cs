using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using Nexor.Domain.Entities;
using Nexor.Domain.Services;

namespace Nexor.Infrastructure.Parsing;

public sealed class ProductionLogParser : IProductionLogParser
{
    private static readonly string[] DateFormats = ["dd/MM/yyyy HH:mm:ss", "dd/MM/yyyy HH:mm", "yyyy-MM-dd HH:mm:ss"];

    public ProductionLog? Parse(string path)
    {
        if (!File.Exists(path)) return null;
        var sections = ParseSections(File.ReadAllLines(path));
        var general = Section(sections, "General");
        var item = Section(sections, "1");
        var costs = Section(sections, "Costs");
        var document = Value(general, "Document") ?? Value(item, "Name");
        if (string.IsNullOrWhiteSpace(document)) return null;

        var height = Number(Value(item, "HeightMM"));
        if (height <= 0) height = Number(Value(costs, "PrintHeightMM"));
        if (height <= 0) return null;

        var computer = Value(general, "ComputerName") ?? string.Empty;
        var driver = Value(general, "Driver") ?? string.Empty;
        return new ProductionLog
        {
            SourcePath = Path.GetFullPath(path), SourceName = Path.GetFileName(path),
            Machine = ResolveMachine(computer, driver), Document = document.Trim(),
            Fabric = ExtractFabric(document), EndTime = Date(Value(general, "EndTime")),
            HeightMm = height, VPositionMm = Math.Max(0, Number(Value(item, "VPosMM") ?? Value(item, "VPositionMM"))),
            Fingerprint = ComputeFingerprint(path)
        };
    }

    public string ComputeFingerprint(string path)
    {
        using var stream = File.OpenRead(path);
        return Convert.ToHexString(SHA256.HashData(stream));
    }

    private static Dictionary<string, Dictionary<string, string>> ParseSections(IEnumerable<string> lines)
    {
        var result = new Dictionary<string, Dictionary<string, string>>(StringComparer.OrdinalIgnoreCase);
        Dictionary<string, string>? current = null;
        foreach (var raw in lines)
        {
            var line = raw.Trim();
            if (line.StartsWith('[') && line.EndsWith(']')) { current = new(StringComparer.OrdinalIgnoreCase); result[line[1..^1]] = current; continue; }
            var separator = line.IndexOf('=');
            if (current is not null && separator > 0) current[line[..separator].Trim()] = line[(separator + 1)..].Trim();
        }
        return result;
    }

    private static Dictionary<string, string> Section(Dictionary<string, Dictionary<string, string>> all, string name) => all.GetValueOrDefault(name) ?? new();
    private static string? Value(Dictionary<string, string> section, string key) => section.GetValueOrDefault(key);
    private static double Number(string? value) => double.TryParse(value?.Replace(',', '.'), NumberStyles.Float, CultureInfo.InvariantCulture, out var number) ? number : 0;
    private static DateTime? Date(string? value) => DateTime.TryParseExact(value, DateFormats, CultureInfo.InvariantCulture, DateTimeStyles.None, out var date) ? date : null;
    private static string ExtractFabric(string document) { var parts = document.Split(" - ", StringSplitOptions.TrimEntries); return parts.Length > 1 ? parts[1].ToUpperInvariant() : "Não identificado"; }
    private static string ResolveMachine(string computer, string driver) { var source = $"{computer} {driver}"; return source.Contains("M2", StringComparison.OrdinalIgnoreCase) ? "M2" : source.Contains("M1", StringComparison.OrdinalIgnoreCase) ? "M1" : "Não identificada"; }
}
