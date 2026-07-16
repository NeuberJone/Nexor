using System.Collections.ObjectModel;
using System.Windows.Input;
using Nexor.Application.Services;
using Nexor.Application.Abstractions;
using Nexor.Domain.Entities;
namespace Nexor.Desktop.Presentation.ViewModels;
public sealed class RollsViewModel : ObservableViewModel
{
 private readonly ProductionWorkflowService _workflow; private readonly IPrinterRepository _printers; private string _machine=""; private string _search=""; private Roll? _selected;
 public ObservableCollection<Roll> Rolls { get; }=[]; public ObservableCollection<Printer> Machines { get; }=[];
 public string Machine{get=>_machine;set=>Set(ref _machine,value);} public string Search{get=>_search;set=>Set(ref _search,value);}
 public Roll? SelectedRoll{get=>_selected;set{if(value is null){Set(ref _selected,value);return;}Set(ref _selected,_workflow.GetRoll(value.Id));}}
 public ICommand SearchCommand{get;} public RollsViewModel(ProductionWorkflowService workflow,IPrinterRepository printers){_workflow=workflow;_printers=printers;SearchCommand=new RelayCommand(_=>Reload());ReloadPrinters();Reload();}
 public void ReloadPrinters(){var selected=Machine;Machines.Clear();Machines.Add(new Printer{Code="",DisplayName="Todas"});foreach(var printer in _printers.List())Machines.Add(printer);Machine=Machines.Any(x=>x.Code==selected)?selected:"";}
 public void Reload(){Rolls.Clear();foreach(var roll in _workflow.ListRolls(string.IsNullOrWhiteSpace(Machine)?null:Machine,string.IsNullOrWhiteSpace(Search)?null:Search,300))Rolls.Add(roll);}
}
