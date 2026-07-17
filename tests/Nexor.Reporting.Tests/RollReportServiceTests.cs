using Nexor.Domain.Entities;
using Nexor.Reporting;
using Xunit;
namespace Nexor.Reporting.Tests;
public sealed class RollReportServiceTests
{
 [Fact] public void CreatesPdfAndMirroredJpgWithoutOverwriting()
 {
  var directory=Path.Combine(Path.GetTempPath(),$"nexor-report-{Guid.NewGuid():N}"); Directory.CreateDirectory(directory);
  try { var items=new[]{new ProductionLog{Document="100 - DRYFIT - CAMISA",Fabric="DRYFIT",HeightMm=1234,EndTime=new DateTime(2026,7,14,10,0,0)},new ProductionLog{Document="101 - DRYFIT - SHORT",Fabric="DRYFIT",HeightMm=2000,EndTime=new DateTime(2026,7,14,9,0,0)}}; var first=RollReportService.Export(directory,"M1_TESTE","M1",items,true); var second=RollReportService.Export(directory,"M1_TESTE","M1",items,true); Assert.True(File.Exists(first.PdfPath));Assert.True(File.Exists(first.MirrorJpgPath));Assert.NotEqual(first.PdfPath,second.PdfPath);Assert.Equal("%PDF",System.Text.Encoding.ASCII.GetString(File.ReadAllBytes(first.PdfPath),0,4));var jpg=File.ReadAllBytes(first.MirrorJpgPath);Assert.Equal(0xFF,jpg[0]);Assert.Equal(0xD8,jpg[1]);using var stream=File.OpenRead(first.MirrorJpgPath);var frame=System.Windows.Media.Imaging.BitmapFrame.Create(stream,System.Windows.Media.Imaging.BitmapCreateOptions.PreservePixelFormat,System.Windows.Media.Imaging.BitmapCacheOption.OnLoad);Assert.InRange(frame.PixelWidth,2000,2016);Assert.InRange(frame.PixelHeight,2825,2855);var converted=new System.Windows.Media.Imaging.FormatConvertedBitmap(frame,System.Windows.Media.PixelFormats.Bgr24,null,0);var stride=converted.PixelWidth*3;var pixels=new byte[stride*converted.PixelHeight];converted.CopyPixels(pixels,stride,0);Assert.True(pixels.Count(value=>value<180)>10000,"O JPG deve conter texto e linhas, não apenas pixels brancos."); }
  finally { Directory.Delete(directory,true); }
 }
}
