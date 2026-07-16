using Nexor.Domain.Entities;
using Nexor.Domain.Services;
namespace Nexor.Domain.Tests;
public sealed class ProductionRulesTests
{
 [Fact] public void HeightIsRealLengthAndOffsetIsNotAdded() { var item = new ProductionLog { HeightMm = 2450, VPositionMm = 300 }; Assert.Equal(2.45, item.RealLengthMeters, 3); }
 [Fact] public void SortsNewestPrintFirst() { var old = new ProductionLog { EndTime = new(2026,1,1) }; var recent = new ProductionLog { EndTime = new(2026,2,1) }; Assert.Same(recent, ProductionRules.NewestFirst([old,recent])[0]); }
 [Fact] public void GroupsOnlyConsecutiveFabrics() { ProductionLog P(string f,double h)=>new(){Fabric=f,HeightMm=h}; var blocks=ProductionRules.GroupConsecutiveFabrics([P("A",1000),P("A",2000),P("B",500),P("A",1000)]); Assert.Equal(3,blocks.Count); Assert.Equal(3,blocks[0].TotalMeters); }
}
