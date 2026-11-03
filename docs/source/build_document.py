from pathlib import Path
import re, json, math
from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'docs/assets'
OUT = ROOT / 'docs/EyeAssist_Bao_cao_chung_v0.1.docx'
FONT = 'C:/Windows/Fonts/arial.ttf'
BOLD = 'C:/Windows/Fonts/arialbd.ttf'

def diagram(name, size, boxes, arrows, labels):
    im = Image.new('RGB', size, 'white'); d = ImageDraw.Draw(im)
    def text_at(x,y,s,fs=27,bold=False,center=True):
        f=ImageFont.truetype(BOLD if bold else FONT,fs)
        d.multiline_text((x,y),s,font=f,fill='#152d40',anchor='mm' if center else None,align='center',spacing=10)
    for x1,y1,x2,y2,title,body in boxes:
        d.rounded_rectangle((x1,y1,x2,y2),radius=15,fill='#edf3f7',outline='#70899b',width=3)
        text_at((x1+x2)/2,y1+40,title,29,True)
        text_at((x1+x2)/2,(y1+y2)/2+25,body,26)
    for points in arrows:
        d.line(points, fill='#36566c',width=4)
        x,y=points[-1]; a,b=points[-2]; angle=math.atan2(y-b,x-a)
        p1=(x-17*math.cos(angle-.45),y-17*math.sin(angle-.45))
        p2=(x-17*math.cos(angle+.45),y-17*math.sin(angle+.45))
        d.polygon([(x,y),p1,p2],fill='#36566c')
    for x,y,s in labels:
        f=ImageFont.truetype(FONT,23)
        bb=d.textbbox((x,y),s,font=f,anchor='mm')
        d.rectangle((bb[0]-6,bb[1]-5,bb[2]+6,bb[3]+5),fill='white')
        text_at(x,y,s,23)
    im.save(ASSETS/name)

diagram('architecture.png',(1500,760),[
 (20,60,420,310,'Ứng dụng web','Bàn phím và giọng nói\nFocus và highlight\nText, earcon và audio'),
 (550,60,950,310,'FastAPI','REST và phiên truy cập\nKiểm tra và điều phối\nJob và lỗi chuẩn hóa'),
 (1080,60,1480,310,'Worker AI','Layout và OCR\nCaption và VQA\nSTT và TTS'),
 (550,460,950,695,'Kho dùng chung','SQLite và tệp riêng\nTài liệu, khối và job\nCrop và audio tạm'),
 (1080,460,1480,695,'Model hoặc dịch vụ AI','Thông qua adapter\nKhóa do backend giữ\nChỉ gửi dữ liệu cần thiết')
], [ [(420,140),(550,140)],[(550,240),(420,240)],[(950,140),(1080,140)],[(1080,240),(950,240)],[(750,310),(750,460)],[(1160,310),(1160,385),(850,385),(850,460)],[(1280,310),(1280,460)] ],[(485,108,'Request'),(485,276,'Response'),(1015,108,'Nhận job'),(1015,276,'Kết quả')])

diagram('flow.png',(1500,1030),[
 (25,30,455,215,'1 Nhập tài liệu','PDF hoặc ảnh webcam\nPOST documents → job'),
 (535,30,965,215,'2 Xử lý và chuẩn hóa','Layout → OCR → blocks\nLưu thứ tự đọc và bbox'),
 (1045,30,1475,215,'3 Duyệt nội dung','Polling job → content\nChọn khối bằng bàn phím'),
 (1045,400,1475,585,'4 Chọn cách yêu cầu','Gõ câu hỏi hoặc ghi âm\nAudio → STT → xác nhận'),
 (535,400,965,585,'5 Hỏi đáp hoặc mô tả','document_id và block_id\nCrop + ngữ cảnh → VQA'),
 (25,400,455,585,'6 Nhận kết quả văn bản','Câu trả lời + evidence\nCảnh báo nếu chưa rõ'),
 (25,770,455,955,'7 Tổng hợp giọng đọc','POST speech → job TTS\nGET media → audio'),
 (535,770,965,955,'8 Phản hồi người dùng','Text + audio + earcon\nGiữ focus và highlight'),
 (1045,770,1475,955,'Khi có lỗi','Thông báo dễ tiếp cận\nGiữ vị trí và cho thử lại')
], [[(455,120),(535,120)],[(965,120),(1045,120)],[(1260,215),(1260,400)],[(1045,490),(965,490)],[(535,490),(455,490)],[(240,585),(240,770)],[(455,860),(535,860)],[(1260,585),(1260,770)]],[(1260,305,'Đọc đoạn hoặc hỏi sâu'),(240,680,'Nếu bật đọc tự động'),(1260,680,'Lỗi ở các bước xử lý')])

doc=Document(); sec=doc.sections[0]
sec.page_width=Cm(21); sec.page_height=Cm(29.7)
sec.top_margin=Cm(1.8); sec.bottom_margin=Cm(1.8); sec.left_margin=Cm(2); sec.right_margin=Cm(2)
sec.footer_distance=Cm(.8)
styles=doc.styles
for s in ['Normal','Title','Subtitle','Heading 1','Heading 2','Heading 3','Caption','TOC Heading']:
    if s not in styles: continue
    styles[s].font.name='Arial'; styles[s].font.color.rgb=RGBColor(0,0,0)
styles['Normal'].font.size=Pt(10.5)
styles['Normal'].paragraph_format.line_spacing=1.12
styles['Normal'].paragraph_format.space_after=Pt(7)
for sn,sz in [('Heading 1',16),('Heading 2',12),('Heading 3',11)]:
    styles[sn].font.size=Pt(sz); styles[sn].font.bold=True
    styles[sn].paragraph_format.space_before=Pt(12); styles[sn].paragraph_format.space_after=Pt(7)
    styles[sn].paragraph_format.keep_with_next=True
styles['Title'].font.size=Pt(30); styles['Title'].font.bold=True
styles['Caption'].font.size=Pt(9); styles['Caption'].font.italic=True
styles['Caption'].paragraph_format.space_after=Pt(9)
for sn in ['TOC 1','TOC 2']:
    if sn not in styles: styles.add_style(sn,1)
    styles[sn].font.name='Arial'; styles[sn].font.size=Pt(10)
    styles[sn].paragraph_format.space_after=Pt(3)
styles['TOC 2'].paragraph_format.left_indent=Cm(.5)

# Real multilevel Word numbering linked to heading styles.
numbering=doc.part.numbering_part.element
absn=OxmlElement('w:abstractNum'); absn.set(qn('w:abstractNumId'),'42')
multi=OxmlElement('w:multiLevelType'); multi.set(qn('w:val'),'multilevel'); absn.append(multi)
for level in range(2):
    lv=OxmlElement('w:lvl'); lv.set(qn('w:ilvl'),str(level))
    for tag,val in [('start','1'),('numFmt','decimal'),('pStyle',f'Heading{level+1}'),('lvlText','%1' if level==0 else '%1.%2'),('suff','space')]:
        el=OxmlElement('w:'+tag); el.set(qn('w:val'),val); lv.append(el)
    absn.append(lv)
numbering.append(absn)
num=OxmlElement('w:num'); num.set(qn('w:numId'),'42')
el=OxmlElement('w:abstractNumId'); el.set(qn('w:val'),'42'); num.append(el); numbering.append(num)

heading_index=0
def bookmark(p):
    global heading_index
    heading_index+=1
    start=OxmlElement('w:bookmarkStart'); start.set(qn('w:id'),str(heading_index));start.set(qn('w:name'),f'section_{heading_index}')
    end=OxmlElement('w:bookmarkEnd');end.set(qn('w:id'),str(heading_index))
    p._p.insert(1,start);p._p.append(end)

def heading(s,lev):
    p=doc.add_paragraph(s,f'Heading {lev}')
    bookmark(p)
    np=OxmlElement('w:numPr')
    for tag,val in [('ilvl',str(lev-1)),('numId','42')]:
        el=OxmlElement('w:'+tag); el.set(qn('w:val'),val); np.append(el)
    p._p.get_or_add_pPr().append(np)

def table(rows):
    t=doc.add_table(rows=1,cols=len(rows[0])); t.alignment=WD_TABLE_ALIGNMENT.CENTER; t.autofit=False
    n=len(rows[0])
    first=rows[0][0]
    ratios=([.12,.40,.48] if first=='Mã' else [.40,.30,.30]) if n==3 else [.29,.71]
    if first=='Mã sinh viên':ratios=[.18,.30,.52]
    if first=='HTTP':ratios=[.10,.48,.42]
    if first=='Phương thức và đường dẫn':ratios=[.53,.20,.27]
    for c,w in zip(t.columns,ratios):c.width=Cm(17*w)
    for rid,row in enumerate(rows):
        cells=t.rows[0].cells if rid==0 else t.add_row().cells
        for ci,(c,txt) in enumerate(zip(cells,row)):
            c.width=Cm(17*ratios[ci]); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            tcPr=c._tc.get_or_add_tcPr()
            sh=OxmlElement('w:shd'); sh.set(qn('w:fill'),'DFE8EF' if rid==0 else ('F6F8FA' if rid%2==0 else 'FFFFFF')); tcPr.append(sh)
            margins=OxmlElement('w:tcMar')
            for side,v in [('top','75'),('bottom','75'),('left','90'),('right','90')]:
                e=OxmlElement('w:'+side);e.set(qn('w:w'),v);e.set(qn('w:type'),'dxa');margins.append(e)
            tcPr.append(margins)
            p=c.paragraphs[0]; p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1.06
            r=p.add_run(txt);r.font.size=Pt(9);r.bold=(rid==0)
        trpr=t.rows[rid]._tr.get_or_add_trPr()
        trpr.append(OxmlElement('w:cantSplit'))
        if rid==0:trpr.append(OxmlElement('w:tblHeader'))
    bd=OxmlElement('w:tblBorders')
    for side in ['top','left','bottom','right','insideH','insideV']:
        e=OxmlElement('w:'+side);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');bd.append(e)
    t._tbl.tblPr.append(bd)
    doc.add_paragraph().paragraph_format.space_after=Pt(1)

lines=(ROOT/'docs/source/bao-cao-chung.md').read_text(encoding='utf-8').splitlines()
i=0; cover=True; cover_p=0; json_count=0
while i<len(lines):
    line=lines[i];i+=1
    if not line.strip():continue
    if line=='@COVER':continue
    if line=='@TOC':
        cover=False;doc.add_page_break();p=doc.add_paragraph('Mục lục','Title');p.runs[0].font.size=Pt(20)
        idx=0
        for item in lines:
            if not (item.startswith('#') or item.startswith('@UNNUMBERED ')):continue
            idx+=1
            lev=2 if item.startswith('##') else 1
            label=item.lstrip('#').strip() if item.startswith('#') else item.split(' ',1)[1]
            p=doc.add_paragraph(style=f'TOC {lev}')
            p.paragraph_format.keep_with_next=False
            h=OxmlElement('w:hyperlink');h.set(qn('w:anchor'),f'section_{idx}');h.set(qn('w:history'),'1')
            rr=OxmlElement('w:r');pr=OxmlElement('w:rPr');color=OxmlElement('w:color');color.set(qn('w:val'),'000000');pr.append(color)
            if lev==1:pr.append(OxmlElement('w:b'))
            rr.append(pr);tt=OxmlElement('w:t');tt.text=label;rr.append(tt);h.append(rr);p._p.append(h)
        continue
    if line=='@PAGE':doc.add_page_break();continue
    if line.startswith('@IMAGE '):
        name=line.split(' ',1)[1];p=doc.add_paragraph();p.paragraph_format.keep_with_next=True
        p.add_run().add_picture(str(ASSETS/name),width=Cm(17))
        for e in p._p.iter(qn('wp:docPr')):e.set('descr','Sơ đồ kiến trúc EyeAssist' if name.startswith('arch') else 'Luồng dữ liệu end-to-end EyeAssist; các bước được mô tả ngay dưới hình')
        continue
    if line.startswith('@UNNUMBERED '):
        p=doc.add_paragraph(line.split(' ',1)[1],'Heading 1')
        bookmark(p)
        continue
    if line.startswith('#'):
        lev=len(line)-len(line.lstrip('#'));s=re.sub(r'^\d+(\.\d+)*\s+','',line.lstrip('#').strip());heading(s,lev);continue
    if line.startswith('|'):
        block=[line]
        while i<len(lines) and lines[i].startswith('|'):block.append(lines[i]);i+=1
        rows=[[x.strip() for x in l.strip('|').split('|')] for l in block if not re.match(r'^\|\s*---',l)]
        table(rows);continue
    if line.startswith('```'):
        block=[]
        while i<len(lines) and not lines[i].startswith('```'):block.append(lines[i]);i+=1
        i+=1
        if line=='```json':json.loads('\n'.join(block));json_count+=1
        for j,l in enumerate(block):
            p=doc.add_paragraph();p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1.0
            p.paragraph_format.keep_with_next=(j<len(block)-1)
            r=p.add_run(l);r.font.name='Consolas';r.font.size=Pt(8.6)
        doc.add_paragraph().paragraph_format.space_after=Pt(1)
        continue
    if line.startswith('Hình '):doc.add_paragraph(line,'Caption');continue
    if cover:
        p=doc.add_paragraph(line,'Title' if cover_p==0 else 'Normal')
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        if cover_p==0:p.paragraph_format.space_before=Pt(35);p.paragraph_format.space_after=Pt(15)
        if cover_p==1:p.runs[0].font.size=Pt(16);p.runs[0].bold=True;p.paragraph_format.space_after=Pt(20)
        if cover_p==2:p.paragraph_format.space_after=Pt(24);p.runs[0].font.size=Pt(12)
        cover_p+=1
    else:doc.add_paragraph(line)

foot=sec.footer.paragraphs[0];foot.alignment=WD_ALIGN_PARAGRAPH.RIGHT
r=foot.add_run('EyeAssist  |  ');r.font.size=Pt(8)
f=OxmlElement('w:fldSimple');f.set(qn('w:instr'),'PAGE');foot._p.append(f)
doc.core_properties.title='EyeAssist Khung báo cáo bài tập lớn và thiết kế tích hợp hệ thống'
doc.core_properties.author='Nhóm 11'
doc.core_properties.subject='Kiến trúc hệ thống và API contracts phiên bản 0.1'
doc.save(OUT)
print(f'Saved {OUT}; JSON examples validated: {json_count}; headings: {sum(p.style.name.startswith("Heading") for p in doc.paragraphs)}')
