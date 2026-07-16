using System.IO;
using System.Windows;
using Nexor.Infrastructure.Persistence;
using Nexor.Desktop.Presentation.Trial;

namespace Nexor.Desktop.Presentation;

public partial class App : System.Windows.Application
{
    protected override void OnStartup(StartupEventArgs e)
    {
        var dataDirectory = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Nexor");
        Directory.CreateDirectory(dataDirectory);
#if TRIAL_EDITION
        var trial = TrialGuard.Check(dataDirectory, DateTime.UtcNow);
        if (!trial.IsValid)
        {
            MessageBox.Show("O período de avaliação do Nexor terminou.", "Nexor Trial", MessageBoxButton.OK, MessageBoxImage.Information);
            Shutdown();
            return;
        }
#endif
        _ = new SqliteContext(Path.Combine(dataDirectory, "nexor.db"));
        base.OnStartup(e);
    }
}
