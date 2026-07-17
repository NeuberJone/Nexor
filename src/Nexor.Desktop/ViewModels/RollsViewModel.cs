using System.Collections.ObjectModel;
using System.Windows.Input;
using Nexor.Application.Services;
using Nexor.Application.Abstractions;
using Nexor.Domain.Entities;
namespace Nexor.Desktop.Presentation.ViewModels;
public sealed class RollsViewModel : ObservableViewModel
{
 private readonly ProductionWorkflowService _workflow; private readonly IPrinterRepository _printers; private string _machine=""; private string _search=""; private string _status=""; private Roll? _selected;
 public ObservableCollection<Roll> Rolls { get; }=[]; public ObservableCollection<Printer> Machines { get; }=[];
 public string Machine{get=>_machine;set=>Set(ref _machine,value);} public string Search{get=>_search;set=>Set(ref _search,value);}
 public string Status{get=>_status;private set=>Set(ref _status,value);}
 public Roll? SelectedRoll{get=>_selected;set{if(value is null){Set(ref _selected,value);return;}try{Set(ref _selected,_workflow.GetRoll(value.Id));Status="";}catch(Exception ex){Status=$"Não foi possível carregar o rolo: {ex.Message}";}}}
 public ICommand SearchCommand{get;} public RollsViewModel(ProductionWorkflowService workflow,IPrinterRepository printers){_workflow=workflow;_printers=printers;SearchCommand=new RelayCommand(_=>Reload());ReloadPrinters();Reload();}
 public void ReloadPrinters(){var selected=Machine;Machines.Clear();Machines.Add(new Printer{Code="",DisplayName="Todas"});foreach(var printer in _printers.List())Machines.Add(printer);Machine=Machines.Any(x=>x.Code==selected)?selected:"";}
 public void Reload(){try{var found=_workflow.ListRolls(string.IsNullOrWhiteSpace(Machine)?null:Machine,string.IsNullOrWhiteSpace(Search)?null:Search,300);Rolls.Clear();foreach(var roll in found)Rolls.Add(roll);Status="";}catch(Exception ex){Status=$"Não foi possível consultar os rolos: {ex.Message}";}}
}
