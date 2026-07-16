using System.Windows;
using System.IO;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using Nexor.Domain.Entities;
using Nexor.Domain.Services;
using PdfSharp.Drawing;
using PdfSharp.Pdf;

namespace Nexor.Reporting;

public sealed class RollReportService
{
    public static ExportResult Export(string directory,string rollName,string machine,IReadOnlyList<ProductionLog> items,bool full,double mirrorWidthCm=17)
    {
        Directory.CreateDirectory(directory); var tag=full?"FULL":"SUMMARY"; var basis=$"{DateTime.Now:yyyy-MM-dd}_{machine}_{Safe(rollName)}_{tag}";
        var pdf=Versioned(Path.Combine(directory,basis+".pdf")); var jpg=Versioned(Path.Combine(directory,basis+"_MIRROR.jpg"));
        WritePdf(pdf,rollName,machine,items,full); WriteMirrorJpg(jpg,rollName,machine,items,mirrorWidthCm); return new(pdf,jpg);
    }

    private static void WritePdf(string path,string roll,string machine,IReadOnlyList<ProductionLog> items,bool full)
    {
        using var document=new PdfDocument(); var page=document.AddPage(); page.Size=PdfSharp.PageSize.A4; var g=XGraphics.FromPdfPage(page); var normal=new XFont("Arial",9); var bold=new XFont("Arial",11,XFontStyleEx.Bold); double y=35;
        g.DrawString($"Ordem do Rolo - {roll}",new XFont("Arial",14,XFontStyleEx.Bold),XBrushes.Black,35,y); y+=18; g.DrawString($"Máquina: {machine}   Modo: {(full?"Completo":"Resumido")}   Gerado: {DateTime.Now:dd/MM/yyyy HH:mm:ss}",normal,XBrushes.Black,35,y); y+=22;
        var blocks=ProductionRules.GroupConsecutiveFabrics(ProductionRules.NewestFirst(items));
        if(full){g.DrawString("EndTime",bold,XBrushes.Black,35,y);g.DrawString("Arquivo / pedido",bold,XBrushes.Black,145,y);g.DrawString("Tecido",bold,XBrushes.Black,400,y);g.DrawString("Metros",bold,XBrushes.Black,510,y);y+=16;foreach(var item in ProductionRules.NewestFirst(items)){if(y>790){page=document.AddPage();g=XGraphics.FromPdfPage(page);y=35;}g.DrawString($"{item.EndTime:dd/MM/yyyy HH:mm:ss}",normal,XBrushes.Black,35,y);g.DrawString(Trim(item.Document,42),normal,XBrushes.Black,145,y);g.DrawString(Trim(item.Fabric,16),normal,XBrushes.Black,400,y);g.DrawString($"{RoundUp(item.RealLengthMeters):F2} m",normal,XBrushes.Black,510,y);y+=14;}y+=12;}
        g.DrawString("Resumo (blocos consecutivos)",bold,XBrushes.Black,35,y);y+=18;var index=1;foreach(var block in blocks){g.DrawString($"{index++}. {block.Fabric}",normal,XBrushes.Black,35,y);g.DrawString($"{block.Items.Count} itens",normal,XBrushes.Black,330,y);g.DrawString($"{RoundUp(block.TotalMeters):F2} m",bold,XBrushes.Black,480,y);y+=15;}y+=10;g.DrawString($"Total geral: {RoundUp(items.Sum(x=>x.RealLengthMeters)):F2} m",bold,XBrushes.Black,35,y);document.Save(path);
    }

    private static void WriteMirrorJpg(string path,string roll,string machine,IReadOnlyList<ProductionLog> items,double widthCm)
    {
        const int dpi=300; var width=(int)Math.Round(widthCm/2.54*dpi); var blocks=ProductionRules.GroupConsecutiveFabrics(ProductionRules.NewestFirst(items)); var height=Math.Max(500,180+blocks.Count*55); var visual=new DrawingVisual(); using(var dc=visual.RenderOpen()){dc.PushTransform(new ScaleTransform(-1,1,width/2d,0));dc.DrawRectangle(Brushes.White,null,new Rect(0,0,width,height));var title=new FormattedText($"ORDEM DO ROLO - {roll}",System.Globalization.CultureInfo.CurrentCulture,FlowDirection.LeftToRight,new Typeface("Arial"),28,Brushes.Black,1);dc.DrawText(title,new Point(30,25));var y=85d;foreach(var b in blocks){var text=new FormattedText($"{b.Fabric}   {b.Items.Count} itens   {RoundUp(b.TotalMeters):F2} m",System.Globalization.CultureInfo.CurrentCulture,FlowDirection.LeftToRight,new Typeface("Arial"),22,Brushes.Black,1);dc.DrawText(text,new Point(30,y));y+=50;}dc.Pop();}var bitmap=new RenderTargetBitmap(width,height,dpi,dpi,PixelFormats.Pbgra32);bitmap.Render(visual);var encoder=new JpegBitmapEncoder{QualityLevel=95};encoder.Frames.Add(BitmapFrame.Create(bitmap));using var stream=File.Create(path);encoder.Save(stream);
    }
    private static double RoundUp(double value)=>Math.Ceiling(value*100)/100; private static string Trim(string value,int max)=>value.Length<=max?value:value[..(max-1)]+"…";
    private static string Safe(string value)=>string.Concat(value.Select(ch=>Path.GetInvalidFileNameChars().Contains(ch)?'_':ch));
    private static string Versioned(string path){if(!File.Exists(path))return path;for(var i=2;;i++){var candidate=Path.Combine(Path.GetDirectoryName(path)!,Path.GetFileNameWithoutExtension(path)+$"_v{i}"+Path.GetExtension(path));if(!File.Exists(candidate))return candidate;}}
}
public sealed record ExportResult(string PdfPath,string MirrorJpgPath);
