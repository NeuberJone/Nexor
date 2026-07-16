using System.Globalization;
using System.IO;
namespace Nexor.Desktop.Presentation.Trial;
public static class TrialGuard
{
 private const int TrialDays = 30;
 public static TrialStatus Check(string localDataDirectory, DateTime utcNow)
 {
  var directory = Path.Combine(localDataDirectory, "Trial");
  var marker = Path.Combine(directory, "first-run.txt");
  Directory.CreateDirectory(directory);
  DateTime firstRun;
  if (!File.Exists(marker)) { firstRun = utcNow.Date; File.WriteAllText(marker, firstRun.ToString("O", CultureInfo.InvariantCulture)); }
  else if (!DateTime.TryParse(File.ReadAllText(marker), CultureInfo.InvariantCulture, DateTimeStyles.RoundtripKind, out firstRun)) return new(false, 0);
  var elapsed = (utcNow.Date - firstRun.Date).Days;
  return new(elapsed >= 0 && elapsed < TrialDays, Math.Max(0, TrialDays - elapsed));
 }
}
public sealed record TrialStatus(bool IsValid, int DaysRemaining);
