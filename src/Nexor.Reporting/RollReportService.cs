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
        WritePdf(pdf,rollName,machine,items,full); WriteMirrorJpg(jpg,rollName,machine,items,full,mirrorWidthCm); return new(pdf,jpg);
    }

    private static void WritePdf(string path,string roll,string machine,IReadOnlyList<ProductionLog> items,bool full)
    {
        using var document=new PdfDocument(); var page=document.AddPage(); page.Size=PdfSharp.PageSize.A4; var g=XGraphics.FromPdfPage(page); var normal=new XFont("Arial",9); var bold=new XFont("Arial",11,XFontStyleEx.Bold); double y=35;
        g.DrawString($"Ordem do Rolo - {roll}",new XFont("Arial",14,XFontStyleEx.Bold),XBrushes.Black,35,y); y+=18; g.DrawString($"Máquina: {machine}   Modo: {(full?"Completo":"Resumido")}   Gerado: {DateTime.Now:dd/MM/yyyy HH:mm:ss}",normal,XBrushes.Black,35,y); y+=22;
        var blocks=ProductionRules.GroupConsecutiveFabrics(ProductionRules.NewestFirst(items));
        if(full){g.DrawString("EndTime",bold,XBrushes.Black,35,y);g.DrawString("Arquivo / pedido",bold,XBrushes.Black,145,y);g.DrawString("Tecido",bold,XBrushes.Black,400,y);g.DrawString("Metros",bold,XBrushes.Black,510,y);y+=16;foreach(var item in ProductionRules.NewestFirst(items)){if(y>790){page=document.AddPage();g=XGraphics.FromPdfPage(page);y=35;}g.DrawString($"{item.EndTime:dd/MM/yyyy HH:mm:ss}",normal,XBrushes.Black,35,y);g.DrawString(Trim(item.Document,42),normal,XBrushes.Black,145,y);g.DrawString(Trim(item.Fabric,16),normal,XBrushes.Black,400,y);g.DrawString($"{RoundUp(item.RealLengthMeters):F2} m",normal,XBrushes.Black,510,y);y+=14;}y+=12;}
        g.DrawString("Resumo (blocos consecutivos)",bold,XBrushes.Black,35,y);y+=18;var index=1;foreach(var block in blocks){g.DrawString($"{index++}. {block.Fabric}",normal,XBrushes.Black,35,y);g.DrawString($"{block.Items.Count} itens",normal,XBrushes.Black,330,y);g.DrawString($"{RoundUp(block.TotalMeters):F2} m",bold,XBrushes.Black,480,y);y+=15;}y+=10;g.DrawString($"Total geral: {RoundUp(items.Sum(x=>x.RealLengthMeters)):F2} m",bold,XBrushes.Black,35,y);document.Save(path);
    }

    private static void WriteMirrorJpg(string path,string roll,string machine,IReadOnlyList<ProductionLog> items,bool full,double widthCm)
    {
        const int dpi=300; const double pageWidth=793.7; const double pageHeight=1122.5;
        var pixelWidth=(int)Math.Round(widthCm/2.54*dpi); var pixelHeight=(int)Math.Round(pixelWidth*pageHeight/pageWidth);
        var logicalWidth=pixelWidth*96d/dpi; var scale=logicalWidth/pageWidth; var visual=new DrawingVisual();
        var ordered=ProductionRules.NewestFirst(items); var blocks=ProductionRules.GroupConsecutiveFabrics(ordered);
        using(var dc=visual.RenderOpen())
        {
            dc.PushTransform(new MatrixTransform(new Matrix(-scale,0,0,scale,logicalWidth,0)));
            dc.DrawRectangle(Brushes.White,null,new Rect(0,0,pageWidth,pageHeight)); var black=new SolidColorBrush(Colors.Black); var line=new Pen(black,1);
            Draw(dc,$"Ordem do Rolo - {roll}",53,45,19,FontWeights.Bold,black);
            Draw(dc,$"Máquina: {machine}    Modo: {(full?"Completo":"Resumido")}    Gerado: {DateTime.Now:dd/MM/yyyy HH:mm:ss}",53,72,13,FontWeights.Normal,black);
            dc.DrawLine(line,new Point(53,88),new Point(740,88)); var y=108d;
            if(full)
            {
                Draw(dc,"EndTime",53,y,13,FontWeights.Bold,black); Draw(dc,"Arquivo / pedido",195,y,13,FontWeights.Bold,black); Draw(dc,"Tecido",535,y,13,FontWeights.Bold,black); Draw(dc,"Metros",690,y,13,FontWeights.Bold,black); y+=23;
                foreach(var item in ordered)
                {
                    if(y>760)break; Draw(dc,$"{item.EndTime:dd/MM/yyyy HH:mm:ss}",53,y,11,FontWeights.Normal,black); Draw(dc,Trim(item.Document,45),195,y,11,FontWeights.Normal,black); Draw(dc,Trim(item.Fabric,18),535,y,11,FontWeights.Normal,black); Draw(dc,$"{RoundUp(item.RealLengthMeters):F2} m",690,y,11,FontWeights.Normal,black); y+=19;
                }
                y+=18;
            }
            Draw(dc,"Resumo (ordem do rolo)",53,y,16,FontWeights.Bold,black); y+=24; dc.DrawLine(line,new Point(53,y),new Point(740,y)); y+=22;
            Draw(dc,"#",53,y,13,FontWeights.Bold,black); Draw(dc,"Tecido",85,y,13,FontWeights.Bold,black); Draw(dc,"Total (m)",380,y,13,FontWeights.Bold,black); Draw(dc,"Qtd Pedidos",500,y,13,FontWeights.Bold,black); Draw(dc,"Último fim",610,y,13,FontWeights.Bold,black); y+=22;
            var index=1; foreach(var block in blocks)
            {
                if(y>1030)break; Draw(dc,(index++).ToString(System.Globalization.CultureInfo.InvariantCulture),53,y,12,FontWeights.Normal,black); Draw(dc,Trim(block.Fabric,32),85,y,12,FontWeights.Normal,black); Draw(dc,$"{RoundUp(block.TotalMeters):F2} m",380,y,12,FontWeights.Normal,black); Draw(dc,block.Items.Count.ToString(System.Globalization.CultureInfo.InvariantCulture),525,y,12,FontWeights.Normal,black); Draw(dc,$"{block.Items.Max(x=>x.EndTime):dd/MM/yyyy HH:mm:ss}",610,y,12,FontWeights.Normal,black); y+=20;
            }
            y+=8; dc.DrawLine(line,new Point(53,y),new Point(740,y)); y+=24; Draw(dc,"Total geral do rolo:",53,y,15,FontWeights.Bold,black); Draw(dc,$"{RoundUp(items.Sum(x=>x.RealLengthMeters)):F2} m",650,y,15,FontWeights.Bold,black);
            dc.Pop();
        }
        var bitmap=new RenderTargetBitmap(pixelWidth,pixelHeight,dpi,dpi,PixelFormats.Pbgra32);bitmap.Render(visual);var encoder=new JpegBitmapEncoder{QualityLevel=95};encoder.Frames.Add(BitmapFrame.Create(bitmap));using var stream=File.Create(path);encoder.Save(stream);
    }
    private static void Draw(DrawingContext dc,string text,double x,double y,double size,FontWeight weight,Brush brush)=>dc.DrawText(new FormattedText(text,System.Globalization.CultureInfo.GetCultureInfo("pt-BR"),FlowDirection.LeftToRight,new Typeface(new FontFamily("Arial"),FontStyles.Normal,weight,FontStretches.Normal),size,brush,1),new Point(x,y));
    private static double RoundUp(double value)=>Math.Ceiling(value*100)/100; private static string Trim(string value,int max)=>value.Length<=max?value:value[..(max-1)]+"…";
    private static string Safe(string value)=>string.Concat(value.Select(ch=>Path.GetInvalidFileNameChars().Contains(ch)?'_':ch));
    private static string Versioned(string path){if(!File.Exists(path))return path;for(var i=2;;i++){var candidate=Path.Combine(Path.GetDirectoryName(path)!,Path.GetFileNameWithoutExtension(path)+$"_v{i}"+Path.GetExtension(path));if(!File.Exists(candidate))return candidate;}}
}
public sealed record ExportResult(string PdfPath,string MirrorJpgPath);
