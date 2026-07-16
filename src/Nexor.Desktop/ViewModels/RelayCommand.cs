using System.Windows.Input;
namespace Nexor.Desktop.Presentation.ViewModels;
public sealed class RelayCommand(Action<object?> action) : ICommand
{
 public event EventHandler? CanExecuteChanged { add { } remove { } }
 public bool CanExecute(object? parameter) => true;
 public void Execute(object? parameter) => action(parameter);
}
