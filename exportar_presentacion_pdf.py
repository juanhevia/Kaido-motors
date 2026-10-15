"""Empaqueta las diapositivas renderizadas a 2x como un PDF de presentación."""
from pathlib import Path
from reportlab.pdfgen import canvas
ROOT=Path(__file__).resolve().parent
out=ROOT/'entrega/presentacion.pdf'
c=canvas.Canvas(str(out),pagesize=(960,540))
c.setTitle('Kaido Motors España - Presentación A013')
c.setAuthor('Estudio individual del caso Kaido Motors')
for i in range(1,13):
    image=ROOT/f'.build/slides/slide-{i}.png'
    assert image.is_file(),image
    c.drawImage(str(image),0,0,width=960,height=540)
    c.showPage()
c.save()
print(out)
