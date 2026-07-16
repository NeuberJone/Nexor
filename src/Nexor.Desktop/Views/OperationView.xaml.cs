using System.Windows;
using Nexor.Desktop.Presentation.ViewModels;
namespace Nexor.Desktop.Presentation.Views;
public partial class OperationView : System.Windows.Controls.UserControl
{
 public OperationView()=>InitializeComponent();
 private void OnDragOver(object sender,DragEventArgs e){e.Effects=e.Data.GetDataPresent(DataFormats.FileDrop)?DragDropEffects.Copy:DragDropEffects.None;e.Handled=true;}
 private void OnDrop(object sender,DragEventArgs e){if(DataContext is OperationViewModel vm && e.Data.GetData(DataFormats.FileDrop) is string[] paths)vm.Import(paths.Where(path=>path.EndsWith(".txt",StringComparison.OrdinalIgnoreCase)));}
}
