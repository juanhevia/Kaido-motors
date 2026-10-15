"""Genera el resumen ejecutivo de dos páginas y datos de la presentación."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from modelo import ROOT, SEG

OUT=ROOT/'entrega'; OUT.mkdir(exist_ok=True)
R=ROOT/'resultados'
FONT=Path('/System/Library/Fonts/Supplemental')
if (FONT/'Arial.ttf').exists():
    pdfmetrics.registerFont(TTFont('Body',str(FONT/'Arial.ttf')))
    pdfmetrics.registerFont(TTFont('Bold',str(FONT/'Arial Bold.ttf')))
else:
    from reportlab.pdfbase.pdfmetrics import registerFont,Font
    registerFont(Font('Body','Helvetica','WinAnsiEncoding'));registerFont(Font('Bold','Helvetica-Bold','WinAnsiEncoding'))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold')
NAVY=HexColor('#102C3D'); TEAL=HexColor('#007F83'); GRAY=HexColor('#526674'); PALE=HexColor('#EAF2F3'); RED=HexColor('#AC493F')
W,H=landscape(A4)
fmt=lambda x,n=0:f'{x:,.{n}f}'.replace(',','X').replace('.',',').replace('X','.')
table=pd.read_csv(R/'tabla5.csv'); total=table[table.segmento=='TOTAL'].set_index('escenario')
iv=pd.read_csv(R/'intervalos.csv'); plan=pd.read_csv(R/'plan_fabricacion_A013.csv').set_index('mes_fabricacion')
growth=pd.read_csv(R/'crecimiento_limpio.csv').set_index('anio')
val=pd.read_csv(R/'validacion_A012.csv'); ev=val[val.modo=='ex_ante']
wape=(ev.wape*ev.real).sum()/ev.real.sum(); naive=(ev.wape_naive*ev.real).sum()/ev.real.sum()
g=growth.loc['A012','demanda_ajustada']/growth.loc['A011','demanda_ajustada']-1
months=['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
c=canvas.Canvas(str(OUT/'resumen_ejecutivo.pdf'),pagesize=(W,H));c.setTitle('Kaido Motors España - Plan A013');c.setAuthor('Estudio individual del caso Kaido Motors')

def text(x,y,txt,size=10,bold=False,color=NAVY):
    c.setFillColor(color);c.setFont('Bold' if bold else 'Body',size);c.drawString(x,H-y,txt)

def para(x,y,width,txt,size=9.3,color=NAVY,leading=None):
    p=Paragraph(txt,ParagraphStyle('p',fontName='Body',fontSize=size,leading=leading or size*1.28,textColor=color))
    _,h=p.wrap(width,H);p.drawOn(c,x,H-y-h);return h

def grid(data,x,y,widths,fontsize=8.5,rowheights=None,groups=None):
    tab=Table(data,colWidths=widths,rowHeights=rowheights)
    style=[('FONTNAME',(0,0),(-1,-1),'Body'),('FONTSIZE',(0,0),(-1,-1),fontsize),('TEXTCOLOR',(0,0),(-1,-1),NAVY),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ALIGN',(1,1),(-1,-1),'RIGHT'),('BACKGROUND',(0,0),(-1,0),NAVY),('TEXTCOLOR',(0,0),(-1,0),white),('FONTNAME',(0,0),(-1,0),'Bold'),('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5)]
    for r in range(1,len(data)):
        if (r%2==0 if groups is None else ((r-1)//3)%2==0):style.append(('BACKGROUND',(0,r),(-1,r),PALE))
    tab.setStyle(TableStyle(style));_,h=tab.wrap(W,H);tab.drawOn(c,x,H-y-h);return h

def footer(p):
    text(30,575,'Fuente: enunciado Kaido Motors, secciones 7 y 9, y siete CSV del repositorio docente. Cálculos propios.',7.5,color=GRAY)
    text(774,575,f'{p} / 2',8,color=GRAY)

text(30,34,'KAIDO MOTORS ESPAÑA',11,True,TEAL)
text(30,64,f'Propuesta A013: {fmt(plan.to_numpy().sum())} coches a fábrica',25,True)
para(30,79,780,f'Priorizar SUV medio y compacto: aportan 53,83 M€ de contribución central y conservan margen positivo en el escenario adverso. Objetivo central: {fmt(total.loc["central","ventas"])} ventas; revisar pedidos cada mes.',11)
base=total.loc['central','cvp_eur']
delta=lambda sc: fmt((total.loc[sc,'cvp_eur']-base)/1e6,2)+' M€ / '+fmt((total.loc[sc,'cvp_eur']/base-1)*100,1)+'%'
for x,number,label in [(30,fmt(base/1e6,2)+' M€','CVP neto central'),(292,fmt(total.loc['optimista','cvp_eur']/1e6,2)+' M€','Optimista: +'+delta('optimista')),(554,fmt(total.loc['pesimista','cvp_eur']/1e6,2)+' M€','Pesimista: '+delta('pesimista'))]:
    text(x,134,number,23,True,TEAL if x<550 else RED);text(x,151,label,9,color=GRAY)
text(30,178,'Plan inicial mensual de fabricación / pedido a fábrica (unidades)',11,True)
data=[['Segmento']+months+['A013']]
for s in SEG:data.append([s]+[fmt(x) for x in plan[s]]+[fmt(plan[s].sum())])
data.append(['TOTAL']+[fmt(x) for x in plan.sum(axis=1)]+[fmt(plan.to_numpy().sum())])
grid(data,30,188,[64]+[51]*12+[105],8.7,[18]*9)
para(30,354,780,'B: pequeño · C: compacto · MD: berlina media · SSUV: SUV pequeño · CSUV: SUV compacto · MSUV: SUV medio · S: descapotable.',8,color=GRAY)
para(30,371,780,'<b>Criterio y calendario:</b> cubrir demanda y seguridad, descontando existencias y llegadas comprometidas. C inicia con 1.107 coches y CSUV con 1.011: no pedir en enero-febrero. Enero-febrero ya están en tránsito (4.313 estimados); marzo se decide al cierre de A012. El pedido de enero llega en abril; octubre-diciembre abastecen A014. Este plan central sin ruido difiere de la media revisada de la Tabla 5.',8.7)
text(30,430,'Demanda y fiabilidad',10.5,True)
para(30,440,245,f'Modelo mensual por segmento y canal con estacionalidad, economía y sucesos. A012 creció 8,5% en matriculaciones, 6,0% sin automatriculaciones y {fmt(g*100,1)}% tras ajustar sucesos y faltas estimadas. WAPE de validación A012: {fmt(wape*100,1)}% frente a {fmt(naive*100,1)}% de repetir A011. MD falla con 95,2%; CSUV carece de historia previa a A012. Limitar B: deja 125 € antes de stock frente a 180 € por tres meses de espera.',8.5)
text(292,430,'Supuestos de los escenarios',10.5,True)
para(292,440,245,'Central: economía estable y caída posadelanto de 3 meses. Optimista: paro -1 pp, crédito -0,5 pp, ayuda desde abril y caída de 1 mes. Pesimista: paro +2 pp, caída de 6 meses, CO2 completo y arancel adicional del 5% del coste; CSUV retrasa su lanzamiento 3 meses y pierde producción en mayo. En el adverso, suspender nuevos pedidos deficitarios B, C, SSUV y S: medida adicional no incluida en la Tabla 5.',8.5)
ci=iv[(iv.segmento=='TOTAL')&(iv.escenario=='central')].iloc[0]
text(554,430,'Costes, riesgo y seguimiento',10.5,True)
para(554,440,257,f'Central: VM 49,24 M€, stock 2,43 M€ y transfers 0,19 M€; costes por segmento en la página siguiente. 1.000 simulaciones por escenario; ventas centrales P5-P95: {fmt(ci.ventas_p5)}-{fmt(ci.ventas_p95)}. Revisar cada mes pedidos, faltas, VM y edad. Recalcular si el error supera el 15% dos meses o el stock >90 días supera el 20%. Tránsito inicial estimado y demanda de segmentos nuevos son los principales límites del plan.',8.5)
footer(1);c.showPage()
text(30,33,'Resultados del mismo plan inicial, con revisión a tres meses',20,True)
para(30,44,780,'Tabla 5. Medias de 1.000 años simulados por escenario. P = pesimista, C = central, O = optimista. k€ = miles de euros. M€ = millones. Las cantidades fraccionarias se redondean solo para mostrar.',8.7)
header=['Segmento','Esc.','Ventas\nu.','Fábrica\nu.','Stock medio\nu. / meses','>90 días\nfin año','Stock\nk€','Perdidas\nu. / k€','Transfers\nu. / k€','VM\nM€','CVP neto\nM€']
rows=[header]
for s in SEG+['TOTAL']:
    for sc,ab in [('pesimista','P'),('central','C'),('optimista','O')]:
        r=table[(table.segmento==s)&(table.escenario==sc)].iloc[0]
        rows.append([s,ab,fmt(r.ventas),fmt(r.fabricados),fmt(r.stock_medio)+' / '+fmt(r.cobertura,2),fmt(r.viejos90),fmt(r.stock_eur/1000),fmt(r.perdidas_u)+' / '+fmt(r.perdidas_eur/1000),fmt(r.transfers_u)+' / '+fmt(r.transfers_eur/1000),fmt(r.vm_eur/1e6,2),fmt(r.cvp_eur/1e6,2)])
grid(rows,30,77,[55,32,51,56,87,48,55,91,91,65,81],8.2,[29]+[14.3]*24,groups=True)
para(30,455,780,'<b>Lectura económica:</b> CVP neto = beneficio bruto de coches vendidos - VM por edad - stock de la marca - sobrecoste transfer - CO2 - arancel. Las ventas perdidas son coste de oportunidad y no se restan otra vez. No es beneficio contable: excluye costes fijos e impuestos. Los 300 € de transporte repercutido no dejan margen.',8.4)
para(30,490,780,f'<b>Costes adicionales:</b> fabricar y traer los coches vendidos representa {fmt(total.loc["central","coste_vehiculos_vendidos_eur"]/1e6,2)} M€ en central (ya descontado en beneficio bruto). Pesimista: CO2 {fmt(total.loc["pesimista","co2_eur"]/1e6,2)} M€ y arancel {fmt(total.loc["pesimista","arancel_eur"]/1e6,2)} M€. Optimista: ahorro de compra del 1% ({fmt(-total.loc["optimista","arancel_eur"]/1e6,2)} M€), supuesto de euro fuerte. Intereses de la red central: {fmt(total.loc["central","interes_red_eur"]/1e6,2)} M€, separados del margen de la marca.',8.4)
para(30,526,780,f'<b>Operación:</b> FIFO, meses de 30 días, venta a mitad de mes y coste de stock limitado a 180 días. Transfers inmediatos hasta el 10% de demanda mensual, solo si su margen es positivo. Stock final central: {fmt(total.loc["central","stock_final"])} coches. En tránsito para A014: {fmt(total.loc["central","pipeline_final"])}. Cobertura = media de los cocientes por réplica. Detalle, intervalos por segmento y sensibilidades en el ZIP.',8.4)
footer(2);c.save()

# Una fuente de datos para las diapositivas y su guion.
payload={'segmentos':SEG,'meses':months,'plan':plan.to_dict(orient='list'),'total_plan':int(plan.to_numpy().sum()),'tabla5':table.to_dict(orient='records'),'intervalos':iv.to_dict(orient='records'),'wape':wape,'naive':naive,'crecimiento_ajustado':g,'validacion':ev.to_dict(orient='records'),'stock_seguridad':pd.read_csv(R/'stock_seguridad.csv').to_dict(orient='records'),'sensibilidades':pd.read_csv(R/'sensibilidades.csv').to_dict(orient='records')}
(R/'presentacion_datos.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2))
print(OUT/'resumen_ejecutivo.pdf')
