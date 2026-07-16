using System.Collections.ObjectModel;
using System.IO;
using System.Globalization;
using System.Windows.Input;
using Microsoft.Win32;
using Nexor.Application.Services;
using Nexor.Application.Abstractions;
using Nexor.Domain.Entities;
using Nexor.Domain.Services;
using Nexor.Infrastructure.Parsing;
using Nexor.Reporting;

namespace Nexor.Desktop.Presentation.ViewModels;

public sealed class OperationViewModel : ObservableViewModel
{
    private readonly ProductionLogParser _parser;
    private readonly ProductionWorkflowService _workflow;
    private readonly IPrinterRepository _printers;
    private string _machine = "M1";
    private string _rollName = CreateRollName("M1");
    private string _status = "Selecione arquivos ou uma pasta de logs.";
    private int? _savedRollId;
    public ObservableCollection<ProductionLog> Items { get; } = [];
    public ObservableCollection<FabricBlockRow> Blocks { get; } = [];
    public ObservableCollection<Printer> Machines { get; } = [];
    public string Machine { get => _machine; set { Set(ref _machine, value); _savedRollId=null; RollName = CreateRollName(value); } }
    public string RollName { get => _rollName; set => Set(ref _rollName, value); }
    public string Status { get => _status; private set => Set(ref _status, value); }
    public double TotalMeters => Items.Sum(x => x.RealLengthMeters);
    public ICommand ImportFilesCommand { get; }
    public ICommand ImportFolderCommand { get; }
    public ICommand ClearCommand { get; }
    public ICommand SaveRollCommand { get; }
    public ICommand ExportFullCommand { get; }
    public ICommand ExportSummaryCommand { get; }

    public OperationViewModel(ProductionLogParser parser, ProductionWorkflowService workflow, IPrinterRepository printers)
    {
        _parser = parser; _workflow = workflow; _printers = printers;
        ImportFilesCommand = new RelayCommand(_ => ImportFiles());
        ImportFolderCommand = new RelayCommand(_ => ImportFolder());
        ClearCommand = new RelayCommand(_ => Clear());
        SaveRollCommand = new RelayCommand(_ => SaveRoll());
        ExportFullCommand = new RelayCommand(_ => Export(true));
        ExportSummaryCommand = new RelayCommand(_ => Export(false));
        ReloadPrinters();
    }

    public void ReloadPrinters()
    {
        var selected = Machine;
        Machines.Clear(); foreach (var printer in _printers.List(true)) Machines.Add(printer);
        Machine = Machines.Any(x => x.Code.Equals(selected, StringComparison.OrdinalIgnoreCase)) ? selected : Machines.FirstOrDefault()?.Code ?? "";
    }

    private void ImportFiles()
    {
        var dialog = new OpenFileDialog { Filter = "Logs TXT (*.txt)|*.txt", Multiselect = true, Title = "Selecionar logs de produção" };
        if (dialog.ShowDialog() == true) Import(dialog.FileNames);
    }

    private void ImportFolder()
    {
        var dialog = new OpenFolderDialog { Title = "Selecionar pasta com logs" };
        if (dialog.ShowDialog() == true) Import(Directory.EnumerateFiles(dialog.FolderName, "*.txt", SearchOption.TopDirectoryOnly));
    }

    public void Import(IEnumerable<string> paths)
    {
        var known = Items.Select(x => x.Fingerprint).ToHashSet(StringComparer.OrdinalIgnoreCase);
        var added = 0; var invalid = 0;
        foreach (var path in paths)
        {
            var item = _parser.Parse(path);
            if (item is null || item.HeightMm <= 0) { invalid++; continue; }
            item.Machine = Machine;
            if (!known.Add(item.Fingerprint)) continue;
            Items.Add(item); added++;
        }
        RebuildBlocks();
        if(added>0)_savedRollId=null;
        Status = $"{Items.Count} itens no lote · +{added} novos · {invalid} inválidos.";
    }

    private void RebuildBlocks()
    {
        var sorted = ProductionRules.NewestFirst(Items);
        Items.Clear(); foreach (var item in sorted) Items.Add(item);
        Blocks.Clear(); foreach (var block in ProductionRules.GroupConsecutiveFabrics(Items)) Blocks.Add(new(block.Fabric, block.Items.Count, block.TotalMeters, block.Items.Max(x => x.EndTime)));
        Changed(nameof(TotalMeters));
    }

    private void SaveRoll()
    {
        if (Items.Count == 0) { Status = "Importe ao menos um log válido."; return; }
        if(_savedRollId is not null){Status=$"Rolo já salvo com ID {_savedRollId}.";return;}
        var name = string.IsNullOrWhiteSpace(RollName) ? CreateRollName(Machine) : RollName.Trim();
        var roll = _workflow.CreateRoll(name, Machine, Blocks.Count == 1 ? Blocks[0].Fabric : "Múltiplos");
        foreach (var item in Items) _workflow.AddLogToRoll(roll.Id, item);
        _workflow.AddEvent(roll.Id, "IMPORT_ROLL", $"{Items.Count} itens importados.");
        _workflow.CloseRoll(roll.Id);
        _savedRollId=roll.Id;
        Status = $"Rolo {name} salvo com ID {roll.Id}.";
    }
    private void Export(bool full)
    {
        if (Items.Count == 0) { Status = "Importe ao menos um log válido."; return; }
        try { if(_savedRollId is null)SaveRoll(); if(_savedRollId is null)return; var directory = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "Nexor", "Exportacoes", DateTime.Now.ToString("yyyy",CultureInfo.InvariantCulture), DateTime.Now.ToString("MM",CultureInfo.InvariantCulture)); var result = RollReportService.Export(directory, RollName, Machine, Items.ToList(), full); _workflow.AddEvent(_savedRollId.Value,"EXPORT_ROLL",$"PDF: {result.PdfPath} | JPG: {result.MirrorJpgPath}"); Status = $"Exportado: {result.PdfPath} | {result.MirrorJpgPath}"; }
        catch (Exception ex) { Status = $"Falha ao exportar: {ex.Message}"; }
    }

    private void Clear() { Items.Clear(); Blocks.Clear(); _savedRollId=null; RollName = CreateRollName(Machine); Status = "Lote limpo."; Changed(nameof(TotalMeters)); }
    private static string CreateRollName(string machine) => $"{machine}_{DateTime.Now:dd-MM-yyyy_HHmmss}";
}

public sealed record FabricBlockRow(string Fabric, int ItemCount, double TotalMeters, DateTime? NewestEnd);
