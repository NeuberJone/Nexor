using System.IO;
using System.Windows;

namespace Nexor.Desktop.Presentation.Themes;

public static class ThemeManager
{
    public const string DefaultTheme = "Nexor Dark";
    public static IReadOnlyList<string> AvailableThemes { get; } = [DefaultTheme, "Nexor Light", "SISBolt"];

    public static void Apply(string themeName)
    {
        var source = themeName switch
        {
            "Nexor Light" => "Themes/LightTheme.xaml",
            "SISBolt" => "Themes/SisBoltTheme.xaml",
            _ => "Themes/DarkTheme.xaml"
        };
        var dictionaries = System.Windows.Application.Current.Resources.MergedDictionaries;
        var palette = dictionaries.FirstOrDefault(x => x.Source?.OriginalString.Contains("Theme.xaml", StringComparison.OrdinalIgnoreCase) == true);
        var replacement = new ResourceDictionary { Source = new Uri(source, UriKind.Relative) };
        if (palette is null) dictionaries.Insert(0, replacement); else dictionaries[dictionaries.IndexOf(palette)] = replacement;
        Save(themeName);
    }

    public static string Load()
    {
        var path = SettingsPath();
        if (!File.Exists(path)) return DefaultTheme;
        var value = File.ReadAllText(path).Trim();
        return AvailableThemes.Contains(value) ? value : DefaultTheme;
    }

    private static void Save(string themeName)
    {
        var path = SettingsPath();
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        File.WriteAllText(path, themeName);
    }

    private static string SettingsPath() => Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Nexor", "theme.txt");
}
