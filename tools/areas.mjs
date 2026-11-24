import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const nodeRoot = path.dirname(path.dirname(process.execPath));
const requireRuntime = createRequire(path.join(nodeRoot, 'package.json'));
const { Workbook, SpreadsheetFile } = await import(pathToFileURL(requireRuntime.resolve('@oai/artifact-tool')));
const load = async file => JSON.parse((await fs.readFile(path.join(root,file),'utf8')).replace(/^\uFEFF/,''));
const base = await load('01-source/base.json');
const design = await load('02-design/design.json');
const book = Workbook.create();
const summary = book.worksheets.add('Հաշվեկշիռ');
const rooms = book.worksheets.add('Սենքեր');
const verts = book.worksheets.add('Գագաթներ');
const ext = book.worksheets.add('Ընդլայնում');

const A = (s,row,col,val) => {
  const cell=s.getCell(row-1,col-1);
  if(typeof val==='string' && val.startsWith('=')) cell.formulas=[[val]];
  else cell.values=[[val]];
};
const row = (s,n,values) => values.forEach((v,i)=>v!==null&&A(s,n,i+1,v));
const ref = (s,r) => "'"+s.name+"'!"+r;
const quote = (s)=>"'"+s.name+"'!";
function merge(s,range,caption) {
  const cells=s.getRange(range);
  cells.merge();cells.getCell(0,0).values=[[caption]];
}
function heading(s,end,title,sub,widths,heads) {
  s.showGridLines=false;
  const block=s.getRange('A1:'+end+'175');
  block.format.font.name='Arial';block.format.font.size=10;
  block.format.font.color='#223936';
  block.format.rowHeight=19;
  for(let i=0;i<widths.length;i++)s.getCell(0,i).format.columnWidthPx=widths[i];
  merge(s,'A1:'+end+'1',title);merge(s,'A2:'+end+'2',sub);
  s.getRange('A1:'+end+'1').format.fill='#1F504D';
  s.getRange('A1:'+end+'1').format.font={name:'Arial',bold:true,size:18,color:'#FFFFFF'};
  s.getRange('A1:'+end+'1').format.rowHeight=35;
  s.getRange('A2:'+end+'2').format.fill='#E6F1ED';
  s.getRange('A2:'+end+'2').format.font.color='#305D55';
  s.getRange('A2:'+end+'2').format.rowHeight=30;
  row(s,4,heads);band(s,'A4:'+end+'4');
  s.freezePanes.freezeRows(4);
}
function band(s,address) {
  const a=s.getRange(address);a.format.fill='#D4E7DD';a.format.font.bold=true;
  a.format.rowHeight=24;
}
function section(s,n,end,title){
  merge(s,'A'+n+':'+end+n,title);band(s,'A'+n+':'+end+n)
}
function linkSum(sheet, addresses){return '='+addresses.map(a=>ref(sheet,a)).join('+')}
const oldIds=['living','kitchen','bath','bed_e','bed_w','vestibule','wc','balcony'];
const newIds=design.rooms.map(r=>r.id);
const mappings=new Map(design.rooms.map(r=>[r.id,r]));
heading(verts,'I','Բազմանկյունների գագաթներ','Կապույտ թվերը մուտքային կոորդինատներ են։ Յուրաքանչյուր խմբի վերջին տողից հաշվարկը վերադառնում է նույն խմբի առաջին գագաթին։',[125,260,72,110,110,110,110,135,132],['Փուլ','Ուրվագիծ','Գագաթ','X, մ','Y, մ','Հաջորդ X, մ','Հաջորդ Y, մ','Կրկնակի մակ., մ²','Կողի երկար., մ']);
heading(rooms,'F','Ուրվագծերի մակերեսներ','Մաքուր մակերեսը հաշվվում է վերջնամշակված ներքին եզրերով։ Սյունը և շեմերը մաքուր մակերեսից դուրս են։',[120,310,172,174,145,320],['Փուլ','Տարածք','PDF-ի մակագր., մ²','Բազմանկյուն, մ²','Շեղում, մ²','Նկարագրություն']);
heading(summary,'G','Բնակարանի մակերեսների հաշվեկշիռ','R3  •  23.11.2026  •  Նախնական թվայնացում և հաշվարկ  •  Մակերեսները՝ մ²',[270,312,143,150,142,120,335],['Ելակետային տարածք','Մուտք №3 նախագծում','PDF-ում նշված','Մինչև՝ ուրվագիծ','Հետո՝ ուրվագիծ','Փոփոխություն','Հաշվառման հիմք']);
heading(ext,'G','1.00 մ ընդլայնման հաշվարկ','Շերտի արտաքին սահմանը ճակատին զուգահեռ է։ Արտաքին երկու կողերի շեղումները պահպանվում են։',[300,150,150,130,130,130,310],['Մեծություն','Արժեք / X','Y','Ուղղություն X','Ուղղություն Y','Հատման t','Միավոր / հիմք']);
let vr=5,rr=5;
const record={},starts={};
function polygon(id,name,points,phase,stated,source){
  const first=vr;
  const range=[];
  for(let j=0;j<points.length;j++) {
    const k=first+j,next=first+(j+1)%points.length;
    range.push([phase,name,j+1,...points[j]]);
    A(verts,k,6,'=D'+next);A(verts,k,7,'=E'+next);
    A(verts,k,8,'=D'+k+'*G'+k+'-E'+k+'*F'+k);
    A(verts,k,9,'=SQRT((F'+k+'-D'+k+')^2+(G'+k+'-E'+k+')^2)');
  }
  verts.getRangeByIndexes(first-1,0,points.length,5).values=range;
  vr+=points.length;
  verts.getRange('D'+first+':E'+(vr-1)).format.font.color='#245F95';
  row(rooms,rr,[phase,name,stated,'=ABS(SUM('+quote(verts)+'H'+first+':H'+(vr-1)+'))/2',stated===null?null:'=D'+rr+'-C'+rr,source]);
  starts[id]=first;record[id]=rr;rr++;
}
for(const id of oldIds){const z=base.rooms[id];polygon(id,z.name+' • '+z.stated_area.toFixed(2)+' մ²',z.points,'Մինչև',z.stated_area,'PDF-ի գիծ և մակագրություն');}
for(const id of newIds){const z=mappings.get(id);polygon(id,z.name,z.points,'Հետո',null,'R3 նախագծային ուրվագիծ');}
polygon('outer','Ընդհանուր արտաքին սահման',base.features.outer_boundary,'Ընդհանուր',null,'Ներառում է պատերը, նախամուտքը, WC-ն և պատշգամբը');
const clipped = [];
const p=base.rooms.balcony.points[3], q=base.rooms.balcony.points[4];
const length=Math.hypot(q[0]-p[0],q[1]-p[1]),n=[-(q[1]-p[1])/length,(q[0]-p[0])/length];
const side = a=>(a[0]-p[0])*n[0]+(a[1]-p[1])*n[1];
const cp=base.features.column;
for(let j=0;j<cp.length;j++){
   const a=cp[(j+cp.length-1)%cp.length],b=cp[j],da=side(a),db=side(b);
   if((da>=0)!=(db>=0))clipped.push([0,1].map(i=>a[i]+(b[i]-a[i])*da/(da-db)));
   if(db>=0)clipped.push(b);
}
polygon('clip','Սյուն / շերտի հատում',clipped,'1 մ սցենար',null,'Թվայնացված սյան՝ գործող ճակատից դուրս մասը');
verts.getRange('D5:I'+(vr-1)).setNumberFormat('0.000000');
rooms.getRange('C5:E'+(rr-1)).setNumberFormat('0.00');
const groups=[
 ['№4 հյուրասենյակ, №5 բաղնիք և №1 միջանցք-խոհանոց','Պատշգամբահայաց ննջասենյակ + միասնական ստուդիա',['living','bath','kitchen'],['B1','ST']],
 ['№3 ննջասենյակ • 13.55','Առանց պատուհանի ներքին սենյակ',['bed_w'],['B2']],
 ['№2 ննջասենյակ • 15.54','Սեփական ներքին միջանցք + համատեղ սանհանգույց',['bed_e'],['H1','BA']],
 [null,null,[],[]],
 ['№1 ընդհանուր նախամուտք • 8.84','Ընդհանուր նախամուտք',['vestibule'],['SH']],
 ['№2 փոքր զուգարան • 0.80','Խորդանոց',['wc'],['SR']],
 ['Բ/Պ բաց պատշգամբ • 31.24','Ապակեպատ պատշգամբ',['balcony'],['BAL']]
];
groups.forEach(([name,target,old,current],i)=>{
  const k=5+i;
  if (!old.length) return;
  row(summary,k,[name,target,linkSum(rooms,old.map(id=>'C'+record[id])),linkSum(rooms,old.map(id=>'D'+record[id])),linkSum(rooms,current.map(id=>'D'+record[id])),'=E'+k+'-D'+k,i<4?'Հինգ բնակարանային սենքերի բաժին':'Առանձնացված հաշվառում']);
});
row(summary,13,['Բնակարանի ներքին օգտակար մակերես',null,'=SUM(C5:C8)','=SUM(D5:D8)','=SUM(E5:E8)','=E13-D13','Հինգ ելակետային տարածք, նույն հաշվարկային սահման']);
row(summary,14,['Նախամուտք, խորդանոց և պատշգամբ',null,'=SUM(C9:C11)','=SUM(D9:D11)','=SUM(E9:E11)','=E14-D14','Ընդհանուր և առանձին հաշվառվող ուրվագծեր']);
row(summary,15,['Պատեր, կառուցվածքներ և շեմեր',null,null,'=D16-D13-D14','=E16-E13-E14','=E15-D15','Ամբողջ արտաքին ուրվագծի մնացորդ']);
row(summary,16,['Ընդհանուր արտաքին ուրվագիծ',null,null,'='+ref(rooms,'D'+record.outer),'=D16','=E16-D16','Ամբողջ գծագրի սահման • սեփականության մակերեսը բաց է']);
row(summary,18,['Ներքին մակերեսի թվաբանական ստուգում',null,66.15,'=C13-C18',null,null,'Մակագրված հինգ սենքերի գումարից հանվում է 66.15 մ²']);
row(summary,19,['Թվայնացման շեղում, մ²',null,null,'=D13-C13',null,null,'Վեկտորային գծեր և երկու նիշով մակագրություններ']);
row(summary,20,['Արտաքին հաշվեկշռի չփակված մաս',null,null,'=D16-SUM(D13:D15)','=E16-SUM(E13:E15)',null,'Սպասվող արդյունքը՝ 0.00 մ²']);
band(summary,'A13:G13');band(summary,'A16:G16');
summary.getRange('C5:F20').setNumberFormat('0.00');
section(summary,22,'G','Պատշգամբի երկու սցենար');
row(summary,23,['Տարածքի բաժին','Առանց ընդլայնման','1.00 մ ընդլայնում','Տարբերություն']);
const xref=(r)=>'='+ref(ext,'B'+r);
row(summary,24,['Ներքին օգտակար մաս','=E13','=B24+'+ref(ext,'B25'),'=C24-B24']);
row(summary,25,['Մնացորդային պատշգամբ','=E11',xref(27),'=C25-B25']);
row(summary,26,['Նոր ճակատի շերտ և սյան համընկնում',0,'='+ref(ext,'B23')+'+'+ref(ext,'B24'),'=C26-B26']);
row(summary,27,['Ներքին մաս + պատշգամբ + նոր շերտ','=SUM(B24:B26)','=SUM(C24:C26)','=C27-B27',null,null,'Նույն գրաֆիկական սահման • տարբերությունը՝ 0.00 մ²']);
row(summary,28,['Արտաքին սահմանի հսկիչ տարբերություն',null,'=D27',null,null,null,'Միացված շերտը մեկ անգամ է հաշվված']);
band(summary,'A27:G27');summary.getRange('B24:D28').setNumberFormat('0.00');
summary.getRange('A5:A11').format.wrapText=true;summary.getRange('A5:G11').format.rowHeight=34;
summary.getRange('G5:G28').format.wrapText=true;
summary.getRange('A13:G20').format.rowHeight=33;
summary.getRange('A27:G28').format.rowHeight=34;
row(ext,5,['Արտաքին սահմանի տեղափոխում',1.00,null,null,null,null,'մ • նախագծային սցենար']);
row(ext,6,['Շրջանակի հաշվարկային խորություն',0.12,null,null,null,null,'մ • հաստատել հանգույցով']);
const bi=starts.balcony;
function putPoint(k,title,offset){row(ext,k,[title,'='+ref(verts,'D'+(bi+offset)),'='+ref(verts,'E'+(bi+offset)),null,null,null,'մ • նշումներով PDF-ի ուրվագիծ']);}
putPoint(8,'Հին ճակատի ձախ ծայր',3);putPoint(9,'Հին ճակատի աջ ծայր',4);putPoint(10,'Ձախ կողի հաջորդ գագաթ',2);putPoint(11,'Աջ կողի հաջորդ գագաթ',5);
row(ext,12,['Հին ճակատի երկարություն','=SQRT((B9-B8)^2+(C9-C8)^2)',null,'=-(C9-C8)/B12','=(B9-B8)/B12',null,'մ • միավոր նորմալի ուղղությամբ']);
for(const [k,title,start,next,d] of [[14,'Արտաքին շերտի ձախ ծայր',8,10,'B5'],[15,'Արտաքին շերտի աջ ծայր',9,11,'B5'],[17,'Ներքին մաքուր գծի ձախ ծայր',8,10,'(B5-B6)'],[18,'Ներքին մաքուր գծի աջ ծայր',9,11,'(B5-B6)']]){
  row(ext,k,[title,'=B'+start+'+F'+k+'*(B'+next+'-B'+start+')','=C'+start+'+F'+k+'*(C'+next+'-C'+start+')',null,null,'='+d+'/((B'+next+'-B'+start+')*D12+(C'+next+'-C'+start+')*E12)','մ • շեղ կողի հետ հատում']);
}
// Շերտերը համեմատվում են փակ ուրվագծերով, նաև երբ երկու կողերը տարբեր են։
function area4(stations){return '=ABS(('+stations.map((k,i)=>{const n=stations[(i+1)%stations.length];return 'B'+k+'*C'+n+'-C'+k+'*B'+n;}).join('+')+'))/2';}
row(ext,21,['Տեղափոխվող ամբողջ շերտ',area4([8,9,15,14]),null,null,null,null,'մ² • չորս գագաթ']);
row(ext,22,['Նոր շրջանակի ներսի մակերես',area4([8,9,18,17]),null,null,null,null,'մ² • առանց շրջանակի']);
row(ext,23,['Նոր շրջանակի մակերես','=B21-B22',null,null,null,null,'մ² • ճակատի 120 մմ պայմանական պրոֆիլ']);
row(ext,24,['Սյան համընկնող մաս','='+ref(rooms,'D'+record.clip),null,null,null,null,'մ² • սկզբնական սահմանագծի հատում']);
row(ext,25,['Մաքուր միացվող մաս','=B22-B24',null,null,null,null,'մ² • ավելանում է մեկ անգամ']);
row(ext,26,['Պատշգամբի սկզբնական ուրվագիծ','='+ref(rooms,'D'+record.balcony),null,null,null,null,'մ² • նույն թվայնացում']);
row(ext,27,['Մնացող պատշգամբ','=B26-B21',null,null,null,null,'մ² • ամբողջ շերտը հանված է']);
row(ext,28,['Չհաշվառված մնացորդ','=B26-SUM(B23:B25)-B27',null,null,null,null,'մ² • սպասվող արդյունք 0']);
ext.getRange('B5:F28').setNumberFormat('0.000000');ext.getRange('B5:B6').format.font.color='#245F95';
band(ext,'A25:G25');band(ext,'A28:G28');
book.recalculate();
const result = await SpreadsheetFile.exportXlsx(book);
const tmp = await fs.mkdtemp(path.join(os.tmpdir(),'apartment-areas-'));
const exportPath=path.join(tmp,'Areas.xlsx');
await result.save(exportPath);
await fs.copyFile(exportPath,path.join(root,'03-calculations','Areas.xlsx'));
const expected = [[13,4,66.17854],[13,5,68.38183],[16,4,128.8158],[18,4,0],[27,4,0]];
for(const [row,col,want] of expected){
  const got = summary.getCell(row-1,col-1).values[0][0];
  if(typeof got!=='number'||Math.abs(got-want)>.001)throw Error('Հաշվարկի շեղում '+row+','+col+' '+got+' / '+want);
}
console.log('XLSX',summary.getRange('C13:F13').values,ext.getRange('B25:B28').values);
if(process.env.AREA_PREVIEW){
 const view=await book.render({sheetName:summary.name,range:'A1:G28',scale:1.0,format:'png'});
 await fs.writeFile(process.env.AREA_PREVIEW,new Uint8Array(await view.arrayBuffer()));
}
