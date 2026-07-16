using System.Collections.ObjectModel;
using System.Windows.Input;
using Nexor.Application.Abstractions;
using Nexor.Domain.Entities;

namespace Nexor.Desktop.Presentation.ViewModels;

public sealed class PrintersViewModel : ObservableViewModel
{
    private readonly IPrinterRepository _repository;
    private Printer? _selected;
    private string _code = "";
    private string _displayName = "";
    private string _manufacturer = "";
    private string _model = "";
    private string _notes = "";
    private bool _isActive = true;
    private string _status = "Cadastre as impressoras usadas na produção.";

    public ObservableCollection<Printer> Printers { get; } = [];
    public Printer? Selected { get => _selected; set { Set(ref _selected, value); LoadSelected(); } }
    public string Code { get => _code; set => Set(ref _code, value); }
    public string DisplayName { get => _displayName; set => Set(ref _displayName, value); }
    public string Manufacturer { get => _manufacturer; set => Set(ref _manufacturer, value); }
    public string Model { get => _model; set => Set(ref _model, value); }
    public string Notes { get => _notes; set => Set(ref _notes, value); }
    public bool IsActive { get => _isActive; set => Set(ref _isActive, value); }
    public string Status { get => _status; private set => Set(ref _status, value); }
    public ICommand NewCommand { get; }
    public ICommand SaveCommand { get; }
    public ICommand DeleteCommand { get; }
    public event Action? PrintersChanged;

    public PrintersViewModel(IPrinterRepository repository)
    {
        _repository = repository;
        NewCommand = new RelayCommand(_ => New());
        SaveCommand = new RelayCommand(_ => Save());
        DeleteCommand = new RelayCommand(_ => Delete());
        Reload();
    }

    public void Reload()
    {
        Printers.Clear();
        foreach (var printer in _repository.List()) Printers.Add(printer);
    }

    private void New()
    {
        Selected = null; Code = ""; DisplayName = ""; Manufacturer = ""; Model = ""; Notes = ""; IsActive = true;
        Status = "Preencha os dados da nova impressora.";
    }

    private void LoadSelected()
    {
        if (Selected is null) return;
        Code = Selected.Code; DisplayName = Selected.DisplayName; Manufacturer = Selected.Manufacturer;
        Model = Selected.Model; Notes = Selected.Notes; IsActive = Selected.IsActive;
    }

    private void Save()
    {
        var code = Code.Trim().ToUpperInvariant();
        var name = DisplayName.Trim();
        if (string.IsNullOrWhiteSpace(code) || string.IsNullOrWhiteSpace(name)) { Status = "Identificação e nome de exibição são obrigatórios."; return; }
        try
        {
            var printer = new Printer { Id = Selected?.Id ?? 0, Code = code, DisplayName = name, Manufacturer = Manufacturer.Trim(), Model = Model.Trim(), Notes = Notes.Trim(), IsActive = IsActive, CreatedAt = Selected?.CreatedAt ?? DateTime.Now };
            var id = _repository.Save(printer); Reload(); Selected = Printers.First(x => x.Id == id);
            Status = $"Impressora {name} salva."; PrintersChanged?.Invoke();
        }
        catch (Exception ex) { Status = $"Não foi possível salvar: {ex.Message}"; }
    }

    private void Delete()
    {
        if (Selected is null) { Status = "Selecione uma impressora para excluir."; return; }
        try { _repository.Delete(Selected.Id); New(); Reload(); Status = "Impressora excluída."; PrintersChanged?.Invoke(); }
        catch (Exception ex) { Status = $"Não foi possível excluir: {ex.Message}"; }
    }
}
