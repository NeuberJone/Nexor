using Nexor.Domain.Entities;
using Nexor.Infrastructure.Parsing;
using Nexor.Infrastructure.Persistence;
using Nexor.Infrastructure.Repositories;
namespace Nexor.Infrastructure.Tests;
public sealed class InfrastructureTests
{
 [Fact] public void ParsesPxLogValues()
 {
  var path=Path.GetTempFileName(); try { File.WriteAllText(path,"[General]\nDocument=123 - Cotton\nEndTime=14/07/2026 10:30:00\nComputerName=PRINT-M2\n[1]\nHeightMM=2500,5\nVPositionMM=125\n"); var item=new ProductionLogParser().Parse(path)!; Assert.Equal("M2",item.Machine); Assert.Equal("COTTON",item.Fabric); Assert.Equal(2.5005,item.RealLengthMeters,4); Assert.Equal(125,item.VPositionMm); } finally { File.Delete(path); }
 }
 [Fact] public void CreatesDatabaseAndRecoversRoll()
 {
  var path=Path.Combine(Path.GetTempPath(),$"nexor-{Guid.NewGuid():N}.db"); try { var repo=new SqliteRollRepository(new SqliteContext(path)); var id=repo.Insert(new Roll{Name="R-001",Machine="M1",Fabric="A"}); Assert.Equal("R-001",repo.GetById(id)?.Name); } finally { if(File.Exists(path)) File.Delete(path); }
 }
 [Fact] public void SearchesRollByContainedDocumentAndLoadsDetails()
 {
  var path=Path.Combine(Path.GetTempPath(),$"nexor-{Guid.NewGuid():N}.db");
  try { var context=new SqliteContext(path); var logs=new SqliteProductionLogRepository(context); var logId=logs.Insert(new ProductionLog{SourcePath="a.txt",SourceName="a.txt",Machine="M1",Document="PEDIDO 7788 CAMISA",Fabric="DRYFIT",HeightMm=2500,Fingerprint=Guid.NewGuid().ToString("N")}); var repo=new SqliteRollRepository(context); var id=repo.Insert(new Roll{Name="M1_TEST",Machine="M1",Fabric="DRYFIT"}); repo.AddItem(new RollItem{RollId=id,ProductionLogId=logId,Document="PEDIDO 7788 CAMISA",Machine="M1",Fabric="DRYFIT",EffectiveMeters=2.5}); repo.AddEvent(new RollEvent{RollId=id,EventType="EXPORT_ROLL",Message="PDF completo"}); var found=repo.List("M1","7788",20); Assert.Single(found); var detail=repo.GetById(id)!; Assert.Single(detail.Items); Assert.Single(detail.Events); Assert.Equal(2.5,detail.TotalMeters); }
  finally { if(File.Exists(path)) File.Delete(path); }
 }
 [Fact] public void CreatesDefaultsAndPersistsPrinterRegistration()
 {
  var path=Path.Combine(Path.GetTempPath(),$"nexor-{Guid.NewGuid():N}.db");
  try
  {
   var repo=new SqlitePrinterRepository(new SqliteContext(path));
   Assert.Contains(repo.List(),x=>x.Code=="M1"); Assert.Contains(repo.List(),x=>x.Code=="M2");
   var id=repo.Save(new Printer{Code="SUB1",DisplayName="Sublimática principal",Manufacturer="Epson",Model="SureColor",Notes="Setor A"});
   var saved=Assert.Single(repo.List().Where(x=>x.Id==id)); Assert.Equal("Epson",saved.Manufacturer); Assert.Equal("SureColor",saved.Model);
   saved.IsActive=false; repo.Save(saved); Assert.DoesNotContain(repo.List(true),x=>x.Id==id);
  }
  finally { if(File.Exists(path)) File.Delete(path); }
 }
 [Fact] public void ListsRollWhoseFractionalItemsSumToRealNumber()
 {
  var path=Path.Combine(Path.GetTempPath(),$"nexor-{Guid.NewGuid():N}.db");
  try
  {
   var context=new SqliteContext(path); var logs=new SqliteProductionLogRepository(context); var rolls=new SqliteRollRepository(context);
   var rollId=rolls.Insert(new Roll{Name="M1_REAL_TOTAL",Machine="M1",Fabric="MIX"});
   foreach(var meters in new[]{8.567,2.985,9.985,0.361,0.855,10.005,8.501,1.277,2.277,0.848,0.085})
   {
    var logId=logs.Insert(new ProductionLog{SourcePath=$"{Guid.NewGuid():N}.txt",SourceName="x.txt",Machine="M1",Document="PEDIDO",Fabric="MIX",HeightMm=meters*1000,Fingerprint=Guid.NewGuid().ToString("N")});
    rolls.AddItem(new RollItem{RollId=rollId,ProductionLogId=logId,Document="PEDIDO",Machine="M1",Fabric="MIX",EffectiveMeters=meters});
   }
   var listed=Assert.Single(rolls.List("M1","REAL_TOTAL",10)); Assert.Equal(11,listed.ItemCount); Assert.Equal(45.746,listed.TotalMeters,3);
  }
  finally { if(File.Exists(path)) File.Delete(path); }
 }
}
