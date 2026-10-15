import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {execFileSync} from 'node:child_process';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
const root=path.resolve(import.meta.dirname,'..');
const data=JSON.parse(await fs.readFile(path.join(root,'resultados/presentacion_datos.json'),'utf8'));
const SKILL='/Users/juanhevialosa/.codex/plugins/cache/openai-primary-runtime/presentations/26.1007.11041/skills/presentations';
const PY='/Users/juanhevialosa/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';
const {finalizePresentation,applyPresentationChartFont}=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')).href);
const P=Presentation.create({slideSize:{width:1280,height:720}});
const C={navy:'#102C3D',teal:'#007F83',gray:'#526674',pale:'#EAF2F3',red:'#AC493F',white:'#FFFFFF'};
const f=(x,n=0)=>Number(x).toLocaleString('es-ES',{minimumFractionDigits:n,maximumFractionDigits:n});
const row=(sc,s='TOTAL')=>data.tabla5.find(r=>r.escenario===sc&&r.segmento===s);
const interval=(sc,s='TOTAL')=>data.intervalos.find(r=>r.escenario===sc&&r.segmento===s);
const mainNotes=[];
function txt(slide,str,x,y,w,h,size=26,bold=false,color=C.navy){
 const sh=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 sh.text=str;sh.text.style={typeface:'Arial',fontSize:size,bold,color};return sh;
}
function slide(title,notes,seconds,appendix=false){
 const s=P.slides.add();s.background.fill=C.white;
 txt(s,title,58,43,1164,105,42,true);
 txt(s,appendix?'Anexo de consulta':`Kaido Motors España · A013`,58,673,850,24,15,false,C.gray);
 txt(s,String(P.slides.items.length),1175,673,50,24,15,false,C.gray);
 s.speakerNotes.text=`${seconds?`Tiempo: ${seconds} segundos.\n`:''}${notes}\nFuente: https://github.com/UAX-VCMT-26-27/sim-kaido-motors, enunciado secciones 7 y 9, siete CSV. Resultados propios en resultados/.`;
 if(!appendix) mainNotes.push({title,seconds,notes});return s;
}
function table(slide,values,{x=58,y=166,w=1164,h=400,size=23,widths}={}){
 const t=slide.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,values,columnWidths:widths});
 t.borders.assign({fill:'#D7E3E7',width:0.5,style:'solid'});
 t.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({margins:{top:3,bottom:3,left:9,right:9},anchor:'middle'});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
  const cell=t.getCell(r,c);cell.fill=r===0?C.navy:r%2===0?C.pale:C.white;
  cell.text.style={typeface:'Arial',fontSize:size,color:r===0?C.white:C.navy,bold:r===0};
 }
 return t;
}
function chart(s,categories,series,y=180,h=390){
 const ch=s.charts.add('bar',{position:{left:60,top:y,width:1130,height:h},categories,series,hasLegend:true,
  legend:{position:'bottom',textStyle:{fontSize:22}},barOptions:{direction:'column',grouping:'clustered'},
  xAxis:{textStyle:{typeface:'Arial',fontSize:20}},yAxis:{min:0,numberFormatCode:'#,##0',textStyle:{typeface:'Arial',fontSize:18},majorGridlines:{style:'solid',fill:'#D7E3E7',width:1}},
  dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'#,##0',textStyle:{typeface:'Arial',fontSize:19}},chartFill:C.white});
 applyPresentationChartFont(ch,{fontFamily:'Arial'});return ch;
}

let s=slide('Kaido Motors España',
 'La propuesta inicial es pedir 23.162 coches en A013. La incertidumbre obliga a revisar cada mes. El punto económico crítico es que CO2 y aranceles pueden convertir el crecimiento en pérdidas. Presento primero la demanda, después el plan físico y finalmente sus costes. El resultado financiero es contribución de marca, no beneficio contable.',30);
txt(s,'Plan de producción A013',58,220,1100,100,61,true);
txt(s,f(data.total_plan)+' coches',58,355,1100,90,66,true,C.teal);
txt(s,'Demanda mensual, inventario y contribución de la marca',58,490,1120,70,29,false,C.gray);

s=slide('El crecimiento observado sobrestima la demanda de fondo',
 'Las matriculaciones pasan de 21.362 a 23.175: crecen 8,5%. Sin automatriculaciones, el crecimiento es 6,0%. Al neutralizar los sucesos y añadir 77 ventas censuradas estimadas, queda 2,7%. Esta tercera comparación es un contrafactual del modelo. Las ayudas y la caída posterior también se neutralizan, por lo que no todo el ajuste es adelanto de compras. El nuevo CSUV añade cinco meses de gama en A012.',60);
chart(s,['Matriculaciones','Sin automatriculación','Demanda ajustada'],[{name:'A011',values:[21362,19543,19703.6235],fill:'#93AAB4'},{name:'A012',values:[23175,20706,20243.4801],fill:C.teal}]);
txt(s,'Ajustado: +2,7%. Estimación sensible a la corrección de sucesos y faltas de stock.',58,610,1150,45,24,false,C.gray);

s=slide('El modelo separa mercado y cuota de Kaido',
 'Se ajusta mercado mensual para siete segmentos y tres canales. Usamos tendencia, estacionalidad, calendario y dos o tres variables económicas relevantes para cada canal, más sucesos. La demanda de Kaido es mercado por cuota neta. La cuota usa doce meses y una tendencia amortiguada. Los lanzamientos de abril son supuestos porque no hay fechas de producto. Los signos restringidos evitan interpretar correlaciones históricas absurdas como efectos económicos. Todas las variables futuras se publican en el ZIP.',65);
txt(s,'Demanda de Kaido = mercado del segmento × cuota neta',58,172,1150,65,33,true,C.teal);
table(s,[['Componente','Tratamiento'],['Mercado','Regresión mensual por segmento y canal'],['Economía','Paro y variables específicas de cada canal'],['Calendario','Mes, días laborables y Semana Santa del CSV'],['Cuota y producto','Cuota reciente, tendencia amortiguada y códigos nuevos']],{y:262,h:275,size:25,widths:[285,879]});
txt(s,'CSUV: cinco meses de historia. La mejora de producto es un supuesto de escenario.',58,586,1150,60,24,false,C.gray);

s=slide('La prueba A012 mejora la referencia, pero falla en MD',
 'El modelo se entrenó hasta A011. La prueba principal no conoce la macro ni los sucesos de A012. WAPE ponderado: 28,3% frente al 31,1% de repetir el año anterior. No mejora todos los segmentos. MD tiene un error del 95,2% y necesita revisión con pedidos reales. En CSUV el modelo preveía cero por falta de historial antes del lanzamiento. El 100% de error no debe ocultarse ni llamarse validación del nuevo producto. Hay una prueba condicional separada usando la macro observada.',65);
table(s,[['Segmento','WAPE modelo','WAPE año anterior'],...data.validacion.map(r=>[r.segmento,f(r.wape*100,1)+'%',f(r.wape_naive*100,1)+'%'])],{y:163,h:368,size:25,widths:[330,415,419]});
txt(s,'Total: 28,3% frente a 31,1%. CSUV sin historial previo. MD requiere especial cautela.',58,585,1164,60,24,false,C.red);

s=slide('Tres escenarios con un mismo plan inicial',
 'El central conserva la situación económica de final de A012. El optimista baja paro y crédito, incluye ayudas y producto más fuerte. El pesimista alarga la caída, añade CO2 y arancel, retrasa el lanzamiento CSUV y elimina su producción de mayo. El combustible no está en los datos: se representa mediante un multiplicador supuesto. No asignamos probabilidades a estas historias. Dentro de cada una se simulan mil años con errores correlacionados.',55);
table(s,[['Supuesto','Pesimista','Central','Optimista'],['Paro','+2 pp','Estable','-1 pp'],['Caída posadelanto','6 meses','3 meses','1 mes'],['CO2 / coste vehículo','CO2 + arancel 5%','Sin cargo','Coste -1%'],['Producto CSUV','Julio','Abril','Abril, mayor efecto'],['Suministro CSUV','Sin fabricar en mayo','Normal','Sin restricción']],{y:160,h:350,size:24,widths:[335,283,250,296]});
txt(s,'Supuestos externos: combustible -3% / 0% / +2% de demanda. Transfers hasta 10%.',58,568,1164,65,24,false,C.gray);

s=slide(f(data.total_plan)+' coches en el plan inicial de fabricación',
 'La tabla muestra pedidos a fábrica de cada mes, no llegadas ni matriculaciones. Enero llega en abril. El tránsito estimado de enero y febrero suma 4.313 coches. Marzo se fija a cierre de A012. Hay cero pedidos iniciales en compacto y SUV compacto para absorber existencias. Octubre a diciembre abastecen A014 con una continuación técnica de demanda. El plan inicial es la trayectoria sin ruido: la media de fabricación de las simulaciones cambia con las revisiones.',70);
const vals=[['Mes',...data.segmentos],...data.meses.map((m,i)=>[m,...data.segmentos.map(seg=>f(data.plan[seg][i]))])];
table(s,vals,{y:150,h:429,size:21,widths:[135,147,147,147,147,147,147,147]});
txt(s,'Enero llega en abril. Octubre-diciembre llegan en A014. Unidades por mes y segmento.',58,612,1164,40,23,false,C.gray);

s=slide('Los colchones reflejan el coste de quedarse corto',
 'Con tres meses de espera no basta mirar el stock físico de hoy. Se suma el tránsito y se resta la demanda hasta el último mes fijo. El pedido cubre el mes modificable y el colchón. Ajustamos el colchón por correlación temporal del error. B no tiene colchón porque 125 euros de contribución joven no cubren tres meses de stock. Un exceso de 150 SUV medios durante un mes cuesta 9.000 euros, frente a 233.460 de transfer o 857.100 de oportunidad perdida usando el CVP histórico.',65);
table(s,[['Segmento','Stock seguridad (u.)','z'],...data.stock_seguridad.map(r=>[r.segmento,f(r.stock_seguridad),f(r.z,2)])],{x:58,y:163,w:630,h:380,size:25,widths:[210,290,130]});
txt(s,'150 SUV medios',755,179,455,50,31,true,C.teal);
txt(s,'9.000 €\nexceso durante un mes',755,258,455,96,29,true);
txt(s,'233.460 €\ntransfer de las 150 unidades',755,386,455,96,29,true);
txt(s,'El transfer está limitado. La producción solo cambia la llegada de t + 3.',58,600,1164,50,24,false,C.gray);

s=slide('El escenario pesimista deja una contribución negativa',
 'La Tabla 5 usa el mismo arranque y una regla común de revisión según demanda. El CVP neto central es 79,88 millones, el optimista 102,81 y el pesimista menos 5,88. El pesimista añade 57,83 millones de CO2 y 13,32 de arancel. No hay transfers rentables en ese escenario. El optimista tiene más ventas perdidas por el desfase de tres meses. Las pérdidas de venta son coste de oportunidad separado, no otro descuento al CVP. El stock medio considera entradas al inicio y venta a mitad de mes.',70);
const metrics=[['Ventas','ventas',0,1],['Fabricación revisada','fabricados',0,1],['Stock medio (u.)','stock_medio',0,1],['Stock >90 días al cierre (u.)','viejos90',0,1],['Stock marca (M€)','stock_eur',2,1e6],['Ventas perdidas (u.)','perdidas_u',0,1],['Transfers (u.)','transfers_u',0,1],['VM (M€)','vm_eur',2,1e6],['CVP neto (M€)','cvp_eur',2,1e6]];
table(s,[['Resultado','Pesimista','Central','Optimista'],...metrics.map(([label,key,n,div])=>[label,...['pesimista','central','optimista'].map(sc=>f(row(sc)[key]/div,n))])],{y:154,h:415,size:24,widths:[459,235,235,235]});
txt(s,'Medias de 1.000 simulaciones. CVP después de VM, stock, transfer, CO2 y arancel.',58,613,1164,42,23,false,C.gray);

s=slide('MSUV y CSUV concentran la contribución',
 'SUV medio y SUV compacto son la prioridad comercial. El compacto tiene exceso inicial y margen menor. El pequeño se limita a demanda confirmada y sin stock especulativo. Con el cargo de CO2 y arancel, B, C, SSUV y S pasan a pérdida. Recomiendo suspender nuevos pedidos deficitarios cuando se confirme ese cambio de costes, siempre respetando el tránsito. Esta medida de crisis es adicional y su mejora no está incluida en los resultados de la Tabla 5. El objetivo es evitar empujar volumen que destruya margen.',60);
table(s,[['Segmento','CVP central (M€)','CVP pesimista (M€)'],...data.segmentos.map(seg=>[seg,f(row('central',seg).cvp_eur/1e6,2),f(row('pesimista',seg).cvp_eur/1e6,2)])],{y:163,h:364,size:26,widths:[310,427,427]});
txt(s,'Con CO2 y arancel: veto propuesto a nuevos pedidos deficitarios B, C, SSUV y S.',58,582,1164,70,26,true,C.red);

const ci=interval('central');
s=slide('La aprobación requiere revisión mensual',
 'Solicito aprobar el plan inicial sujeto a revisión cada mes. Confirmar primero el tránsito real y las fechas de producto, porque son supuestos determinantes. Registrar también demanda no servida para que las roturas no hagan caer la previsión artificialmente. Recalcular cuando el error supere 15% durante dos meses o cuando más del 20% del stock tenga más de 90 días. Vigilar CO2 y arancel para activar el veto comercial. El intervalo central refleja ruido del modelo y no incluye toda la incertidumbre de parámetros. El ZIP contiene datos, código, resultados, pruebas y guía de reproducción.',60);
txt(s,f(ci.ventas_p5)+' a '+f(ci.ventas_p95)+' ventas',58,177,1150,70,47,true,C.teal);
txt(s,'Intervalo P5-P95 del escenario central',58,250,1150,45,28,false,C.gray);
txt(s,'Cada mes: pedidos reales, demanda no servida, VM y edad del stock',58,348,1150,70,30,true);
txt(s,'Recalcular si el error supera 15% dos meses o el stock >90 días supera 20%',58,438,1150,85,29);
txt(s,'Confirmar tránsito y CO2 antes de comprometer los nuevos pedidos',58,549,1150,70,30,true,C.red);

s=slide('Demanda anual por segmento y escenario',
 'Medias de demanda potencial, antes de pérdidas por falta de producto. Cada celda recoge media y percentiles 5-95. Los intervalos no son probabilidades de escenario y no incluyen incertidumbre de parámetros.',0,true);
table(s,[['Segmento','Pesimista','Central','Optimista'],...data.segmentos.map(seg=>[seg,...['pesimista','central','optimista'].map(sc=>{const r=row(sc,seg),v=interval(sc,seg);return `${f(r.demanda)} (${f(v.demanda_p5)}-${f(v.demanda_p95)})`;})])],{y:158,h:444,size:21,widths:[180,328,328,328]});
txt(s,'Unidades. Media e intervalo P5-P95 entre paréntesis. Demanda potencial, no ventas.',58,620,1164,35,21,false,C.gray);

s=slide('Sensibilidad de los supuestos operativos',
 'Las pruebas usan la misma semilla y el escenario central. El tránsito no se observa, por eso se varía 25%. También se elimina transfer y se cambia el colchón 25%. Son pruebas de robustez, no una búsqueda exhaustiva de un óptimo.',0,true);
const labels={'transito_-25':'Tránsito -25%','transito_+25':'Tránsito +25%','sin_transfers':'Sin transfers','ss_-25':'Stock de seguridad -25%','ss_+25':'Stock de seguridad +25%'};
table(s,[['Prueba central','CVP neto (M€)','Ventas perdidas (u.)'],['Base',f(row('central').cvp_eur/1e6,2),f(row('central').perdidas_u)],...data.sensibilidades.map(r=>[labels[r.prueba],f(r.cvp_eur/1e6,2),f(r.perdidas_u)])],{y:164,h:365,size:25,widths:[500,330,334]});
txt(s,'No se presupone capacidad máxima de fábrica. Falta confirmación del tránsito real.',58,586,1164,70,24,false,C.gray);

await fs.mkdir(path.join(root,'.build/slides'),{recursive:true});
const candidate=path.join(root,'.build/candidate.pptx');
await(await PresentationFile.exportPptx(P)).save(candidate);
await fs.mkdir(path.join(root,'.build/final'),{recursive:true});
const revision=Date.now();
const final=path.join(root,`.build/final/presentacion_validada_${revision}.pptx`);
await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:final,pythonExecutable:PY,
 integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...[3,4,5,6,7,8,9,11,12].flatMap(n=>['--require-native-table-slide',String(n)])],
 explicitTotalSlideCount:12,requiredNativeTableOwnerSlides:[3,4,5,6,7,8,9,11,12],requiredNativeChartOwnerSlides:[2],
 fontPolicy:{basis:'design',families:['Arial']},materializeLiteralChartWorkbooks:true,verifyArtifactToolImport:true,
 receiptPath:path.join(root,`.build/validation_${revision}.json`)});
for(let i=0;i<P.slides.items.length;i++){
 const blob=await P.export({slide:P.slides.items[i],format:'png',scale:2});
 await fs.writeFile(path.join(root,`.build/slides/slide-${i+1}.png`),new Uint8Array(await blob.arrayBuffer()));
}
try {
 const pdf=await P.export({format:'pdf'});
 await fs.writeFile(path.join(root,'entrega/03_presentacion.pdf'),new Uint8Array(await pdf.arrayBuffer()));
} catch(error) {
 if(!String(error).includes('#standard-fonts/Helvetica')) throw error;
 // El runtime de PDF carece de esa fuente empaquetada. Ensamblar las
 // diapositivas ya renderizadas a 2x conserva exactamente el diseño validado.
 execFileSync(PY,[path.join(root,'exportar_presentacion_pdf.py')]);
}
const noteText='# Guion de exposición: diez minutos\n\n10 diapositivas principales y 2 anexos de consulta. Duración total: '+mainNotes.reduce((a,b)=>a+b.seconds,0)+' segundos.\n\n'+mainNotes.map((n,i)=>`## ${i+1}. ${n.title} (${n.seconds} s)\n\n${n.notes}`).join('\n\n');
await fs.writeFile(path.join(root,'GUION_PRESENTACION.md'),noteText);
console.log('PDF y 12 diapositivas exportados.');
