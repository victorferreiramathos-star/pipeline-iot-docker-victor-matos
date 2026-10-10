"""Gera e inspeciona o relatório a partir de evidências locais; não acessa o banco."""
from pathlib import Path
import hashlib
import json
import re
import shutil
from xml.sax.saxutils import escape
import pymupdf
from PIL import Image as PILImage, ImageDraw
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph,
    Spacer, PageBreak, NextPageTemplate, Table, TableStyle, Image, Preformatted)

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
SOURCE = Path(r'C:\Users\Jane\Downloads\TRABALHO - Disruptive Architectures_ IOT, Big Data e IA.docx - Copy.pdf')
PDF = DOCS / 'relatorio_final_victor_matos.pdf'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    assert SOURCE.exists(), 'Orientação original ausente.'
    with pymupdf.open(SOURCE) as original:
        instructions = '\n'.join(p.get_text() for p in original)
        assert len(original) == 7
        for requirement in ['Contextualização', 'views SQL', 'Print das visualizações', 'insights']:
            assert requirement in instructions
    preserved = DOCS / 'orientacao_academica_original.pdf'
    if preserved.exists():
        assert sha(preserved) == sha(SOURCE)
    else:
        shutil.copyfile(SOURCE, preserved)
    (DOCS / 'orientacao_academica_original.txt').write_text(instructions, encoding='utf-8')
    csv_before = sha(ROOT / 'data/IOT-temp.csv')
    assert csv_before == '2bf965701db96cd5788403d395a25d2dd7282bea24e317b7f7b157b7a02063d4'
    results = json.loads((DOCS / 'visual_csv_validation.json').read_text(encoding='utf-8'))
    assert len(results['csv_checks']) == 16 and results['treated_records'] == 97605
    assert all(c['utf8_bom'] and c['sql_reference_match'] and c['download_payload_match'] for c in results['csv_checks'])
    assert 'Ran 9 tests in 39.258s' in (DOCS / 'final_evidence_tests.txt').read_text(encoding='utf-8')
    fonts = Path(r'C:\Windows\Fonts')
    for name, file in [('Arial', 'arial.ttf'), ('ArialBold', 'arialbd.ttf'), ('Mono', 'consola.ttf')]:
        pdfmetrics.registerFont(TTFont(name, str(fonts / file)))
    pdfmetrics.registerFontFamily('Arial', normal='Arial', bold='ArialBold', italic='Arial', boldItalic='ArialBold')
    styles = {
        'body': ParagraphStyle('body', fontName='Arial', fontSize=10.25, leading=14, spaceAfter=8),
        'h1': ParagraphStyle('h1', fontName='ArialBold', fontSize=24, leading=29, textColor=colors.HexColor('#172B3A'), spaceAfter=20),
        'h2': ParagraphStyle('h2', fontName='ArialBold', fontSize=15, leading=20, textColor=colors.HexColor('#007F86'), spaceBefore=10, spaceAfter=12, keepWithNext=True),
        'h3': ParagraphStyle('h3', fontName='ArialBold', fontSize=12, leading=17, spaceBefore=10, spaceAfter=9, keepWithNext=True),
        'table': ParagraphStyle('table', fontName='Arial', fontSize=8.5, leading=11),
        'caption': ParagraphStyle('caption', fontName='ArialBold', fontSize=12, leading=17, spaceAfter=12),
        'code': ParagraphStyle('code', fontName='Mono', fontSize=8, leading=10, spaceAfter=12),
    }
    margin = 42
    portrait_w, portrait_h = A4
    landscape_w, landscape_h = landscape(A4)
    def footer(canvas, doc):
        w, h = canvas._pagesize
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor('#007F86'))
        canvas.line(margin, 33, w - margin, 33)
        canvas.setFont('Arial', 8)
        canvas.setFillColor(colors.HexColor('#526777'))
        canvas.drawString(margin, 21, 'Victor Matos | Pipeline de Dados com IoT e Docker | 10/10/2026')
        canvas.drawRightString(w - margin, 21, str(doc.page))
        canvas.restoreState()
    doc = BaseDocTemplate(str(PDF), pagesize=A4, title='Pipeline de Dados com IoT e Docker — Victor Matos',
        author='Victor Matos', subject='Relatório acadêmico: Disruptive Architectures: IoT, Big Data e IA',
        leftMargin=margin, rightMargin=margin, topMargin=margin, bottomMargin=margin)
    doc.addPageTemplates([
        PageTemplate(id='portrait', frames=[Frame(margin, margin, portrait_w-2*margin, portrait_h-2*margin, leftPadding=0, rightPadding=0)], pagesize=A4, onPage=footer),
        PageTemplate(id='visual', frames=[Frame(margin, margin, landscape_w-2*margin, landscape_h-2*margin, leftPadding=0, rightPadding=0)], pagesize=landscape(A4), onPage=footer),
    ])
    source = DOCS / 'relatorio_final_victor_matos.md'
    content = source.read_text(encoding='utf-8')
    sql = (ROOT / 'sql/views.sql').read_text(encoding='utf-8')
    if '{{VIEWS_SQL}}' in content:
        content = content.replace('{{VIEWS_SQL}}', '```sql\n' + sql + '\n```')
        source.write_text(content, encoding='utf-8')
    lines = content.splitlines()
    flow, figures = [], []
    def formatted(value):
        return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', escape(value))
    n = 0
    while n < len(lines):
        line = lines[n].strip()
        if not line:
            n += 1
            continue
        image_match = re.match(r'!\[(.*?)\]\((.*?)\)', line)
        if image_match:
            caption, relative = image_match.groups()
            path = DOCS / relative
            with PILImage.open(path) as im:
                assert im.format == 'PNG'
                im.verify()
            with PILImage.open(path) as im:
                im.load()
                iw, ih = im.size
            if not figures:
                flow += [NextPageTemplate('visual'), PageBreak()]
            else:
                flow.append(PageBreak())
            flow.append(Paragraph(escape(caption), styles['caption']))
            scale = min((landscape_w-2*margin)/iw, (landscape_h-2*margin-65)/ih)
            flow.append(Image(str(path), width=iw*scale, height=ih*scale))
            flow.append(Spacer(1, 8))
            flow.append(Paragraph('Fonte: captura real do dashboard, arquivo ' + escape(path.name) + '. Sem edição ou montagem.', styles['table']))
            figures.append({'file': relative, 'sha256': sha(path), 'dimensions': [iw, ih]})
            n += 1
            continue
        if line.startswith('```'):
            n += 1
            block = []
            while n < len(lines) and not lines[n].startswith('```'):
                value = lines[n]
                # Quebra de exibição, sem alterar o SQL de origem.
                while len(value) > 100:
                    point = value.rfind(' ', 0, 100)
                    if point <= 0:
                        point = 100
                    block.append(value[:point])
                    value = '    ' + value[point:].lstrip()
                block.append(value)
                n += 1
            flow.append(Preformatted('\n'.join(block), styles['code']))
            n += 1
            continue
        if line.startswith('|'):
            rows = []
            while n < len(lines) and lines[n].strip().startswith('|'):
                cells = [x.strip() for x in lines[n].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[:\- ]+', c) for c in cells):
                    rows.append([Paragraph(formatted(c), styles['table']) for c in cells])
                n += 1
            width = portrait_w - 2*margin
            count = len(rows[0])
            widths = [width/count]*count
            if count == 2:
                widths = [width*.35, width*.65]
            elif count == 5:
                widths = [width*.30] + [width*.175]*4
            table = Table(rows, colWidths=widths, repeatRows=1, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E9EFF3')),
                ('GRID', (0,0), (-1,-1), .4, colors.HexColor('#CBD5DC')),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 6), ('RIGHTPADDING', (0,0), (-1,-1), 6),
                ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ]))
            flow += [table, Spacer(1,12)]
            continue
        if line.startswith('#'):
            level = len(line)-len(line.lstrip('#'))
            heading = line[level:].strip()
            if level == 2 and re.match(r'([1-9]\d*\.|Referências|Apêndice|Anexo|Resumo)', heading):
                flow.append(PageBreak())
            flow.append(Paragraph(formatted(heading), styles['h1' if level == 1 else 'h2' if level == 2 else 'h3']))
            n += 1
            continue
        paragraph = [line]
        n += 1
        while n < len(lines) and lines[n].strip() and not lines[n].startswith(('#','|','```','![')):
            paragraph.append(lines[n].strip())
            n += 1
        flow.append(Paragraph(formatted(' '.join(paragraph)), styles['body']))
    doc.build(flow)
    assert csv_before == sha(ROOT / 'data/IOT-temp.csv')
    review(PDF, figures, sha(SOURCE), csv_before)


def review(path, figures, original_hash, csv_hash):
    destination = DOCS / 'pdf_review'
    destination.mkdir(exist_ok=True)
    records, thumbnails = [], []
    with pymupdf.open(path) as pdf:
        complete = re.sub(r'\s+', ' ', '\n'.join(page.get_text() for page in pdf))
        for value in ['Victor Matos', '97.605', '16 verificações automatizadas', 'NÃO foram conferidos manualmente', 'vw_daily_temperature_summary', 'vw_hourly_sampling_coverage', 'vw_hourly_indoor_outdoor_gap']:
            assert value in complete, value
        image_pages = []
        for number, page in enumerate(pdf, 1):
            assert page.get_text().strip(), 'Página vazia.'
            outside = []
            for block in page.get_text('dict')['blocks']:
                if block['type'] == 0:
                    for line in block['lines']:
                        for span in line['spans']:
                            rect = pymupdf.Rect(span['bbox'])
                            if not page.rect.contains(rect):
                                outside.append(span['text'])
            assert not outside, outside
            images = page.get_images(full=True)
            if images:
                assert len(images) == 1
                figure = figures[len(image_pages)]
                embedded = pymupdf.Pixmap(pdf, images[0][0])
                if embedded.n != 3:
                    embedded = pymupdf.Pixmap(pymupdf.csRGB, embedded)
                with PILImage.open(DOCS / figure['file']) as original:
                    pixels = original.convert('RGB').tobytes()
                assert embedded.samples == pixels, 'Pixels incorporados diferentes do PNG.'
                image_pages.append({'page': number, **figure, 'embedded_pixels_match': True})
            pix = page.get_pixmap(matrix=pymupdf.Matrix(1.5,1.5), alpha=False)
            target = destination / f'page_{number:02d}.png'
            pix.save(target)
            with PILImage.open(target) as rendered:
                thumb = rendered.copy()
                thumb.thumbnail((590,760))
            thumbnails.append((number,thumb))
            records.append({'page':number,'width':page.rect.width,'height':page.rect.height,'text_characters':len(page.get_text()),'images':len(images),'no_text_outside_page':True})
        assert len(image_pages) == 13
        for offset in range(0,len(thumbnails),4):
            sheet = PILImage.new('RGB',(1220,1620),'#dfe5e9')
            draw = ImageDraw.Draw(sheet)
            for index,(number,thumb) in enumerate(thumbnails[offset:offset+4]):
                x = 15+(index%2)*610
                y = 15+(index//2)*810
                draw.text((x,y),f'Pagina {number}',fill='black')
                sheet.paste(thumb,(x,y+25))
            sheet.save(destination / f'contact_{offset//4+1:02d}.png')
    result={'prepared_on':'2026-10-10','pdf':path.name,'sha256':sha(path),'pages':records,
            'figures':image_pages,'orientation_original_sha256':original_hash,'csv_sha256_unchanged':csv_hash,
            'services_started':False,'database_accessed':False,'visual_review':'pending inspection of rendered pages'}
    (DOCS/'pdf_review_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'pdf':str(path),'pages':len(records),'images':len(image_pages),'all_image_pixels_match':True,'csv_unchanged':True}))


if __name__ == '__main__':
    build()
