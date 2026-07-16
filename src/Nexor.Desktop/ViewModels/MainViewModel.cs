using System.ComponentModel;
using System.IO;
using System.Runtime.CompilerServices;
using System.Windows.Input;
using Nexor.Desktop.Presentation.Themes;
using Nexor.Application.Services;
using Nexor.Infrastructure.Persistence;
using Nexor.Infrastructure.Repositories;
using Nexor.Infrastructure.Parsing;

namespace Nexor.Desktop.Presentation.ViewModels;

public sealed class MainViewModel : INotifyPropertyChanged
{
    private string _currentPage = "Home";
    private object? _currentPageContent;
    private readonly OperationViewModel _operation;
    private readonly RollsViewModel _rolls;
    private readonly PrintersViewModel _printers;
    private string _selectedTheme;
    private readonly IReadOnlyList<string> _themes = ThemeManager.AvailableThemes;
    public string WindowTitle { get; } = $"{BuildInfo.ProductName} {BuildInfo.Version}";
    public string EditionLabel { get; } = BuildInfo.EditionLabel;
    public IReadOnlyList<string> Themes => _themes;
    public string SelectedTheme { get => _selectedTheme; set { if (_selectedTheme == value) return; _selectedTheme = value; ThemeManager.Apply(value); Changed(); } }
    public string CurrentPage { get => _currentPage; private set { _currentPage = value; Changed(); Changed(nameof(PageDescription)); } }
    public object? CurrentPageContent { get => _currentPageContent; private set => SetContent(value); }
    public string PageDescription => CurrentPage switch { "Operação" => "Importe logs e prepare o próximo rolo.", "Rolos" => "Consulte os rolos armazenados localmente.", "Configurações" => "Preferências essenciais deste computador.", "Sobre" => $"{BuildInfo.ProductName} {BuildInfo.Version} · .NET 8 · Windows x64", _ => "Visão rápida da produção local." };
    public ICommand NavigateCommand { get; }
    public MainViewModel()
    {
        var data = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Nexor", "nexor.db");
        var context = new SqliteContext(data); var workflow = new ProductionWorkflowService(new SqliteProductionLogRepository(context), new SqliteRollRepository(context));
        var printerRepository = new SqlitePrinterRepository(context);
        _printers = new PrintersViewModel(printerRepository); _operation = new OperationViewModel(new ProductionLogParser(), workflow, printerRepository); _rolls = new RollsViewModel(workflow, printerRepository);
        _printers.PrintersChanged += () => { _operation.ReloadPrinters(); _rolls.ReloadPrinters(); };
        NavigateCommand = new RelayCommand(p => Navigate(p?.ToString() ?? "Home"));
        _selectedTheme = ThemeManager.Load(); ThemeManager.Apply(_selectedTheme);
    }
    private void Navigate(string page){CurrentPage=page;CurrentPageContent=page switch{"Operação"=>_operation,"Rolos"=>_rolls,"Configurações"=>_printers,_=>null};if(page=="Rolos")_rolls.Reload();if(page=="Configurações")_printers.Reload();}
    private void SetContent(object? value){if(ReferenceEquals(_currentPageContent,value))return;_currentPageContent=value;Changed(nameof(CurrentPageContent));}
    public event PropertyChangedEventHandler? PropertyChanged;
    private void Changed([CallerMemberName] string? name = null) => PropertyChanged?.Invoke(this, new(name));
}
