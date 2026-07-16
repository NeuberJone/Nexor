using Nexor.Application.Abstractions;
using Nexor.Application.Services;
using Nexor.Domain.Entities;
namespace Nexor.Application.Tests;
public sealed class WorkflowTests
{
 [Fact] public void DuplicateFingerprintIsNotInserted() { var logs=new Logs{Exists=true}; var service=new ProductionWorkflowService(logs,new Rolls()); service.AddLogToRoll(1,new ProductionLog{Fingerprint="same"}); Assert.Equal(0,logs.Inserts); }
 private sealed class Logs:IProductionLogRepository { public bool Exists; public int Inserts; public bool ExistsByFingerprint(string x)=>Exists; public ProductionLog? GetById(int id)=>null; public int Insert(ProductionLog x){Inserts++;return 1;} }
 private sealed class Rolls:IRollRepository { public void AddEvent(RollEvent x){} public void AddItem(RollItem x){} public Roll? GetById(int id)=>null; public int Insert(Roll x)=>1; public IReadOnlyList<Roll> List(string? m,string? s,int l)=>[]; public void UpdateStatus(int id,string s){} }
}
