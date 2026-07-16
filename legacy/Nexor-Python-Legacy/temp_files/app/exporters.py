"""
Módulo de exportação em PDF baseado no ProjetoJocasta
Suporta modo SUMMARY (resumido) e FULL (completo)
"""

from datetime import datetime
from pathlib import Path
from typing import List
from app.parsers import Block, Job

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm, mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# ============================================================
# PDF Export
# ============================================================

def export_blocks_to_pdf_summary(
    blocks: List[Block],
    roll_name: str,
    output_path: str,
) -> bool:
    """
    Exporta blocos em modo SUMMARY (resumido).
    
    Formato:
    - Cabeçalho com nome do rolo e data
    - Tabela: Tecido | Qtd Jobs | Total (m)
    - Linha separadora entre blocos
    - Total geral no final
    """
    if not HAS_REPORTLAB:
        return False
    
    try:
        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4
        
        # Cabeçalho
        c.setFont("Helvetica-Bold", 16)
        c.drawString(1*cm, height - 1*cm, f"Rolo: {roll_name}")
        
        c.setFont("Helvetica", 10)
        c.drawString(1*cm, height - 1.5*cm, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        # Tabela de blocos
        y = height - 2.5*cm
        c.setFont("Helvetica-Bold", 11)
        
        # Cabeçalho da tabela
        c.drawString(1*cm, y, "Tecido")
        c.drawString(8*cm, y, "Qtd Jobs")
        c.drawString(12*cm, y, "Total (m)")
        
        # Linha separadora
        y -= 0.4*cm
        c.line(1*cm, y, 15*cm, y)
        y -= 0.3*cm
        
        # Dados dos blocos
        c.setFont("Helvetica", 10)
        total_m = 0
        total_jobs = 0
        
        for block in blocks:
            c.drawString(1*cm, y, block.fabric[:40])
            c.drawString(8*cm, y, str(block.job_count))
            c.drawString(12*cm, y, f"{block.total_m:.2f}")
            
            total_m += block.total_m
            total_jobs += block.job_count
            y -= 0.5*cm
            
            # Quebra de página se necessário
            if y < 2*cm:
                c.showPage()
                y = height - 1*cm
        
        # Total geral
        y -= 0.3*cm
        c.line(1*cm, y, 15*cm, y)
        y -= 0.4*cm
        
        c.setFont("Helvetica-Bold", 11)
        c.drawString(1*cm, y, "TOTAL")
        c.drawString(8*cm, y, str(total_jobs))
        c.drawString(12*cm, y, f"{total_m:.2f}")
        
        c.save()
        return True
    
    except Exception as e:
        print(f"Erro ao exportar PDF: {e}")
        return False


def export_blocks_to_pdf_full(
    blocks: List[Block],
    roll_name: str,
    output_path: str,
) -> bool:
    """
    Exporta blocos em modo FULL (completo).
    
    Formato:
    1) Lista de Jobs: EndTime | Document | Tecido | Tamanho
       + linha separadora quando mudar tecido
    2) Separação
    3) Resumo (igual ao SUMMARY) + Total geral
    """
    if not HAS_REPORTLAB:
        return False
    
    try:
        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4
        
        # Cabeçalho
        c.setFont("Helvetica-Bold", 16)
        c.drawString(1*cm, height - 1*cm, f"Rolo: {roll_name} (COMPLETO)")
        
        c.setFont("Helvetica", 10)
        c.drawString(1*cm, height - 1.5*cm, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        # ---- PARTE 1: Lista de Jobs ----
        y = height - 2.5*cm
        c.setFont("Helvetica-Bold", 10)
        
        c.drawString(1*cm, y, "Data/Hora")
        c.drawString(3.5*cm, y, "Pedido")
        c.drawString(9*cm, y, "Tecido")
        c.drawString(13*cm, y, "Tamanho (m)")
        
        y -= 0.4*cm
        c.line(1*cm, y, 15*cm, y)
        y -= 0.3*cm
        
        c.setFont("Helvetica", 9)
        current_fabric = None
        
        for block in blocks:
            for job in block.jobs:
                # Linha separadora quando tecido muda
                if current_fabric != job.fabric:
                    if current_fabric is not None:
                        y -= 0.2*cm
                        c.line(1*cm, y, 15*cm, y)
                        y -= 0.3*cm
                    current_fabric = job.fabric
                
                # Dados do job
                time_str = job.end_time.strftime("%d/%m %H:%M")
                c.drawString(1*cm, y, time_str)
                c.drawString(3.5*cm, y, job.document[:30])
                c.drawString(9*cm, y, job.fabric[:20])
                c.drawString(13*cm, y, f"{job.real_m:.2f}")
                
                y -= 0.4*cm
                
                # Quebra de página se necessário
                if y < 2*cm:
                    c.showPage()
                    y = height - 1*cm
        
        # ---- PARTE 2: Resumo ----
        y -= 0.5*cm
        c.line(1*cm, y, 15*cm, y)
        y -= 0.5*cm
        
        c.setFont("Helvetica-Bold", 11)
        c.drawString(1*cm, y, "RESUMO POR TECIDO")
        y -= 0.5*cm
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(1*cm, y, "Tecido")
        c.drawString(8*cm, y, "Qtd Jobs")
        c.drawString(12*cm, y, "Total (m)")
        
        y -= 0.4*cm
        c.line(1*cm, y, 15*cm, y)
        y -= 0.3*cm
        
        c.setFont("Helvetica", 10)
        total_m = 0
        total_jobs = 0
        
        for block in blocks:
            c.drawString(1*cm, y, block.fabric[:40])
            c.drawString(8*cm, y, str(block.job_count))
            c.drawString(12*cm, y, f"{block.total_m:.2f}")
            
            total_m += block.total_m
            total_jobs += block.job_count
            y -= 0.5*cm
            
            if y < 2*cm:
                c.showPage()
                y = height - 1*cm
        
        # Total geral
        y -= 0.3*cm
        c.line(1*cm, y, 15*cm, y)
        y -= 0.4*cm
        
        c.setFont("Helvetica-Bold", 11)
        c.drawString(1*cm, y, "TOTAL")
        c.drawString(8*cm, y, str(total_jobs))
        c.drawString(12*cm, y, f"{total_m:.2f}")
        
        c.save()
        return True
    
    except Exception as e:
        print(f"Erro ao exportar PDF: {e}")
        return False


def export_blocks_to_pdf(
    blocks: List[Block],
    roll_name: str,
    output_path: str,
    mode: str = "summary",
) -> bool:
    """
    Exporta blocos em PDF.
    
    Args:
        blocks: Lista de blocos
        roll_name: Nome do rolo
        output_path: Caminho do arquivo PDF
        mode: "summary" ou "full"
    
    Returns:
        True se sucesso, False caso contrário
    """
    if mode == "full":
        return export_blocks_to_pdf_full(blocks, roll_name, output_path)
    else:
        return export_blocks_to_pdf_summary(blocks, roll_name, output_path)


# ============================================================
# JPG Export (Mirror)
# ============================================================

def export_blocks_to_jpg_mirror(
    blocks: List[Block],
    roll_name: str,
    output_path: str,
    width: int = 1200,
    height: int = 1600,
) -> bool:
    """
    Exporta blocos em JPG com efeito mirror (espelhado).
    
    Formato:
    - Cabeçalho com nome do rolo e data
    - Tabela: Tecido | Qtd Jobs | Total (m)
    - Efeito mirror: imagem é espelhada horizontalmente
    - Fundo com gradiente
    
    Args:
        blocks: Lista de blocos
        roll_name: Nome do rolo
        output_path: Caminho do arquivo JPG
        width: Largura da imagem em pixels
        height: Altura da imagem em pixels
    
    Returns:
        True se sucesso, False caso contrário
    """
    if not HAS_PIL:
        return False
    
    try:
        # Criar imagem com fundo escuro
        img = Image.new('RGB', (width, height), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)
        
        # Tentar carregar fonte, se não conseguir usar padrão
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
            header_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        except:
            title_font = ImageFont.load_default()
            header_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
        
        y_offset = 50
        
        # Cabeçalho
        draw.text((50, y_offset), f"Rolo: {roll_name}", fill=(255, 255, 255), font=title_font)
        y_offset += 60
        
        # Data
        date_str = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        draw.text((50, y_offset), f"Data: {date_str}", fill=(200, 200, 200), font=text_font)
        y_offset += 50
        
        # Linha separadora
        draw.line([(50, y_offset), (width - 50, y_offset)], fill=(100, 100, 100), width=2)
        y_offset += 30
        
        # Cabeçalho da tabela
        draw.text((50, y_offset), "Tecido", fill=(255, 200, 0), font=header_font)
        draw.text((500, y_offset), "Qtd Jobs", fill=(255, 200, 0), font=header_font)
        draw.text((850, y_offset), "Total (m)", fill=(255, 200, 0), font=header_font)
        y_offset += 40
        
        # Linha separadora
        draw.line([(50, y_offset), (width - 50, y_offset)], fill=(100, 100, 100), width=1)
        y_offset += 20
        
        # Dados dos blocos
        total_m = 0
        total_jobs = 0
        
        for idx, block in enumerate(blocks):
            # Alternar cores das linhas
            if (idx % 2) == 0:
                draw.rectangle([(50, y_offset), (width - 50, y_offset + 35)], fill=(50, 50, 50))
            
            fabric_text = block.fabric[:40]
            draw.text((50, y_offset), fabric_text, fill=(255, 255, 255), font=text_font)
            draw.text((500, y_offset), str(block.job_count), fill=(200, 200, 200), font=text_font)
            draw.text((850, y_offset), f"{block.total_m:.2f}", fill=(200, 200, 200), font=text_font)
            
            total_m += block.total_m
            total_jobs += block.job_count
            y_offset += 40
            
            if y_offset > height - 150:
                break
        
        # Linha separadora final
        y_offset += 10
        draw.line([(50, y_offset), (width - 50, y_offset)], fill=(100, 100, 100), width=2)
        y_offset += 20
        
        # Total geral
        draw.text((50, y_offset), "TOTAL", fill=(0, 255, 0), font=header_font)
        draw.text((500, y_offset), str(total_jobs), fill=(0, 255, 0), font=header_font)
        draw.text((850, y_offset), f"{total_m:.2f}", fill=(0, 255, 0), font=header_font)
        
        # Aplicar efeito mirror (espelhar horizontalmente)
        img_mirrored = img.transpose(Image.FLIP_LEFT_RIGHT)
        
        # Salvar como JPG
        img_mirrored.save(output_path, 'JPEG', quality=95)
        return True
    
    except Exception as e:
        print(f"Erro ao exportar JPG: {e}")
        return False


def export_blocks_to_jpg(
    blocks: List[Block],
    roll_name: str,
    output_path: str,
    mirror: bool = True,
) -> bool:
    """
    Exporta blocos em JPG.
    
    Args:
        blocks: Lista de blocos
        roll_name: Nome do rolo
        output_path: Caminho do arquivo JPG
        mirror: Se True, aplica efeito mirror (espelhado)
    
    Returns:
        True se sucesso, False caso contrário
    """
    if mirror:
        return export_blocks_to_jpg_mirror(blocks, roll_name, output_path)
    else:
        return export_blocks_to_jpg_mirror(blocks, roll_name, output_path, mirror=False)
