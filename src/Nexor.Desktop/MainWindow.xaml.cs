using Nexor.Desktop.Presentation.ViewModels;
namespace Nexor.Desktop.Presentation;
public partial class MainWindow : System.Windows.Window
{
    public MainWindow() { InitializeComponent(); DataContext = new MainViewModel(); }
}
