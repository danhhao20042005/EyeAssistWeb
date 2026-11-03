from pathlib import Path
import pypdfium2 as pdfium
from PIL import Image, ImageOps, ImageDraw
root=Path(__file__).resolve().parents[2]
out=root/'.tmp/doc-qa'
pdf=pdfium.PdfDocument(out/'review.pdf')
for i,page in enumerate(pdf):
    image=page.render(scale=1.8).to_pil()
    image.save(out/f'page-{i+1}.png')
    text=page.get_textpage().get_text_range()
    (out/f'page-{i+1}.txt').write_text(text,encoding='utf-8')
    print(i+1, len(text),text[:85].replace('\r\n',' | '))
for offset in range(0,len(pdf),6):
    canvas=Image.new('RGB',(1080,1560),'#a0a0a0')
    d=ImageDraw.Draw(canvas)
    for j in range(offset,min(offset+6,len(pdf))):
        im=Image.open(out/f'page-{j+1}.png'); im.thumbnail((525,735))
        x=((j-offset)%2)*540+(540-im.width)//2;y=((j-offset)//2)*520
        im.thumbnail((355,492)); x=((j-offset)%2)*540+(540-im.width)//2
        canvas.paste(im,(x,y+23));d.text((x,y+4),f'Page {j+1}',fill='black')
    canvas.save(out/f'contact-{offset//6+1}.png')
