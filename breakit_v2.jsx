import { useState, useCallback, useRef } from "react";

// ═══════════════════════════════════════════════════════════════
// BREAKIT v2.0 — p53 Full-Length Destruction Puzzle
// Based on Gate & Channel v17 (13 channels, 30+ gates)
// Zero fitted parameters. All physics from textbooks.
// ═══════════════════════════════════════════════════════════════

const AA = {
  G:{n:"Glycine",v:60,h:-0.4,q:0,hbd:0,hba:0,ar:false,br:false,pr:false,po:true,su:false,hp:.00},
  A:{n:"Alanine",v:88,h:1.8,q:0,hbd:0,hba:0,ar:false,br:false,pr:false,po:false,su:false,hp:.29},
  V:{n:"Valine",v:140,h:4.2,q:0,hbd:0,hba:0,ar:false,br:true,pr:false,po:false,su:false,hp:.14},
  L:{n:"Leucine",v:167,h:3.8,q:0,hbd:0,hba:0,ar:false,br:false,pr:false,po:false,su:false,hp:.79},
  I:{n:"Isoleucine",v:167,h:4.5,q:0,hbd:0,hba:0,ar:false,br:true,pr:false,po:false,su:false,hp:.30},
  P:{n:"Proline",v:112,h:-1.6,q:0,hbd:0,hba:0,ar:false,br:false,pr:true,po:false,su:false,hp:.00},
  F:{n:"Phenylalanine",v:190,h:2.8,q:0,hbd:0,hba:0,ar:true,br:false,pr:false,po:false,su:false,hp:.47},
  W:{n:"Tryptophan",v:228,h:-0.9,q:0,hbd:1,hba:0,ar:true,br:false,pr:false,po:false,su:false,hp:.37},
  M:{n:"Methionine",v:163,h:1.9,q:0,hbd:0,hba:0,ar:false,br:false,pr:false,po:false,su:true,hp:.68},
  S:{n:"Serine",v:89,h:-0.8,q:0,hbd:1,hba:1,ar:false,br:false,pr:false,po:true,su:false,hp:.29},
  T:{n:"Threonine",v:116,h:-0.7,q:0,hbd:1,hba:1,ar:false,br:true,pr:false,po:true,su:false,hp:.25},
  C:{n:"Cysteine",v:109,h:2.5,q:0,hbd:0,hba:0,ar:false,br:false,pr:false,po:false,su:true,hp:.17},
  Y:{n:"Tyrosine",v:194,h:-1.3,q:0,hbd:1,hba:1,ar:true,br:false,pr:false,po:true,su:false,hp:.28},
  H:{n:"Histidine",v:153,h:-3.2,q:.1,hbd:1,hba:1,ar:true,br:false,pr:false,po:true,su:false,hp:.40},
  D:{n:"Aspartate",v:111,h:-3.5,q:-1,hbd:0,hba:2,ar:false,br:false,pr:false,po:true,su:false,hp:.23},
  E:{n:"Glutamate",v:138,h:-3.5,q:-1,hbd:0,hba:2,ar:false,br:false,pr:false,po:true,su:false,hp:.37},
  N:{n:"Asparagine",v:114,h:-3.5,q:0,hbd:1,hba:1,ar:false,br:false,pr:false,po:true,su:false,hp:.33},
  Q:{n:"Glutamine",v:143,h:-3.5,q:0,hbd:1,hba:1,ar:false,br:false,pr:false,po:true,su:false,hp:.33},
  K:{n:"Lysine",v:168,h:-3.9,q:1,hbd:1,hba:0,ar:false,br:false,pr:false,po:true,su:false,hp:.40},
  R:{n:"Arginine",v:173,h:-4.5,q:1,hbd:3,hba:0,ar:false,br:false,pr:false,po:true,su:false,hp:.21},
};

const RES = [
  {pos:175,aa:'R',bur:.98,ss:'C',dZn:6.39,dDNA:15,zone:'core',stg:1,desc:'Zn環境制御(Layer3)',nAr:0,nSu:0,nCh:2,znL:false,idr:false,lore:'R175Hは世界最多のp53変異。6.39ÅからZn配位をcascade破壊する「遠距離砲撃」。'},
  {pos:176,aa:'C',bur:.93,ss:'C',dZn:2.27,dDNA:12,zone:'core',stg:1,desc:'Zn直接配位(Layer1)',nAr:0,nSu:3,nCh:1,znL:true,idr:false,lore:'Cys176→Zn=2.27Å。直接配位リガンド。ここが壊れたらZnが外れる。'},
  {pos:220,aa:'Y',bur:.86,ss:'E',dZn:18,dDNA:20,zone:'core',stg:1,desc:'β-sandwich疎水コア',nAr:2,nSu:0,nCh:0,znL:false,idr:false,lore:'Y220Cは薬物標的。PhiKan083がY220Cの空洞に入って安定化する。'},
  {pos:246,aa:'M',bur:1.0,ss:'C',dZn:8.5,dDNA:10,zone:'core',stg:1,desc:'S...S硫黄シールド',nAr:0,nSu:4,nCh:0,znL:false,idr:false,lore:'C176,C238,C242,M243の硫黄4つ。カルコゲン結合ネットワーク=Znの「免震構造」。'},
  {pos:257,aa:'L',bur:.98,ss:'E',dZn:16,dDNA:14,zone:'core',stg:1,desc:'深部β-strand',nAr:1,nSu:0,nCh:0,znL:false,idr:false,lore:'bur=0.98。β-strandのインターロック。L→Vでも噛み合わせが外れる。'},
  {pos:245,aa:'G',bur:.76,ss:'C',dZn:12,dDNA:8,zone:'loop',stg:2,desc:'L3ループアンカー',nAr:0,nSu:0,nCh:1,znL:false,idr:false,lore:'G245→非GlyでL3ループ硬直化。R248がDNAに届かなくなる。'},
  {pos:249,aa:'R',bur:.76,ss:'E',dZn:14,dDNA:6,zone:'loop',stg:2,desc:'L3ループアンカー',nAr:0,nSu:0,nCh:1,znL:false,idr:false,lore:'R249S=Ch3(cavity)+Ch5(loop)の2ch同時破壊。世界高頻度の理由。'},
  {pos:278,aa:'P',bur:1.0,ss:'H',dZn:20,dDNA:18,zone:'helix',stg:2,desc:'Helix cap Pro',nAr:0,nSu:0,nCh:0,znL:false,idr:false,lore:'Helix cap位置でkinkを作るPro。消えるとhelixがまっすぐに→接続崩壊。'},
  {pos:266,aa:'G',bur:.99,ss:'E',dZn:15,dDNA:16,zone:'core',stg:2,desc:'深部β内Gly',nAr:0,nSu:0,nCh:0,znL:false,idr:false,lore:'bur=0.99のβ内。G→Vで+80ų押し込み=steric clash。'},
  {pos:281,aa:'D',bur:.61,ss:'H',dZn:22,dDNA:15,zone:'surface',stg:3,desc:'静電キーストーン',nAr:0,nSu:0,nCh:4,znL:false,idr:false,lore:'R280,R282,R283,E285に囲まれた精密ノード。D→Eの1.5Åですら致命的。'},
  {pos:273,aa:'R',bur:.96,ss:'E',dZn:18,dDNA:2.53,zone:'core',stg:3,desc:'DNA backbone接触',nAr:0,nSu:0,nCh:1,znL:false,idr:false,lore:'NH2→DNA OP2に2.53Å。bur=0.96なのにDNAに手を伸ばす。'},
  {pos:280,aa:'R',bur:.86,ss:'H',dZn:20,dDNA:2.82,zone:'surface',stg:3,desc:'DNA H-bond',nAr:0,nSu:0,nCh:2,znL:false,idr:false,lore:'R280K: 電荷同じだがH-bond供与体5→3。「同じ+1」は「同じ」じゃない。'},
  {pos:180,aa:'E',bur:.61,ss:'C',dZn:7.1,dDNA:14,zone:'surface',stg:3,desc:'R175塩橋',nAr:0,nSu:0,nCh:2,znL:false,idr:false,lore:'E180K(charge flip)でR175塩橋消滅→Zn cascade起点。予測的中第1号。'},
  {pos:248,aa:'R',bur:.43,ss:'C',dZn:16,dDNA:3.38,zone:'loop',stg:3,desc:'DNA minor groove',nAr:0,nSu:0,nCh:0,znL:false,idr:false,lore:'DNA minor grooveに3.38Å。表面だがDNA認識の要。'},
  {pos:179,aa:'H',bur:.93,ss:'C',dZn:4.12,dDNA:14,zone:'core',stg:4,desc:'Phantom coordinator',nAr:0,nSu:1,nCh:1,znL:true,idr:false,lore:'4.12Å。直接配位してないが静電的にZn位置を制御。B-factor z=-1.08(RIGID)。幽霊配位。'},
  {pos:238,aa:'C',bur:.86,ss:'C',dZn:2.22,dDNA:14,zone:'core',stg:4,desc:'Zn配位',nAr:0,nSu:2,nCh:0,znL:true,idr:false,lore:'C238-SG→Zn=2.22Å。四面体の一角。'},
  {pos:242,aa:'C',bur:.86,ss:'C',dZn:2.30,dDNA:12,zone:'core',stg:4,desc:'Zn配位',nAr:0,nSu:2,nCh:0,znL:true,idr:false,lore:'C242-SG→Zn=2.30Å。理想値にピッタリ。'},
  {pos:19,aa:'F',bur:.1,ss:'C',dZn:99,dDNA:99,zone:'idr',stg:5,desc:'MDM2結合(coupled folding)',nAr:0,nSu:0,nCh:0,znL:false,idr:true,slim:'MDM2',lore:'MDM2結合ヘリックスの疎水アンカー。coupled foldingで結合時にα-helix形成。'},
  {pos:23,aa:'W',bur:.1,ss:'C',dZn:99,dDNA:99,zone:'idr',stg:5,desc:'MDM2結合(Trpポケット)',nAr:0,nSu:0,nCh:0,znL:false,idr:true,slim:'MDM2',lore:'W23のインドール環がMDM2 Trpポケットに嵌合。最重要アンカー。'},
  {pos:47,aa:'P',bur:.1,ss:'C',dZn:99,dDNA:99,zone:'idr',stg:5,desc:'[S/T]-P kinase motif',nAr:0,nSu:0,nCh:0,znL:false,idr:true,slim:'kinase',ptm:{s:46,k:'CDK5/DYRK2/HIPK2'},lore:'S46-P47=[S/T]-P。P47S=分子機能破壊だがClinVar=Benign。Gate & Channelが「正しくて」ClinVarが「粗い」例。'},
  {pos:34,aa:'P',bur:.1,ss:'C',dZn:99,dDNA:99,zone:'idr',stg:5,desc:'[S/T]-P kinase motif',nAr:0,nSu:0,nCh:0,znL:false,idr:true,slim:'kinase',ptm:{s:33,k:'CDK5/CDK7'},lore:'S33-P34=[S/T]-P。CDK5/CDK7基質認識にPro環構造が必須。'},
  {pos:75,aa:'P',bur:.1,ss:'C',dZn:99,dDNA:99,zone:'idr',stg:5,desc:'PRD PPIIヘリックス',nAr:0,nSu:0,nCh:0,znL:false,idr:true,slim:'PRD',lore:'PRD=Pro-Rich Domain。PPIIヘリックスでSH3ドメインと結合。'},
  {pos:113,aa:'F',bur:.43,ss:'E',dZn:25,dDNA:22,zone:'surface',stg:6,desc:'??? 未知パートナー',nAr:1,nSu:0,nCh:0,znL:false,idr:false,lore:'4変異全部pathogenic。bur=0.43。何と結合してるか不明。暗黒物質。存在の証明○、正体の同定×。'},
  {pos:202,aa:'R',bur:.15,ss:'C',dZn:30,dDNA:25,zone:'surface',stg:6,desc:'表面塩橋',nAr:0,nSu:0,nCh:1,znL:false,idr:false,sbP:true,lore:'R202-E204(6.6Å)の塩橋。表面の静電ジッパー。'},
  {pos:21,aa:'D',bur:.1,ss:'C',dZn:99,dDNA:99,zone:'idr',stg:6,desc:'??? 未知メカニズム',nAr:0,nSu:0,nCh:0,znL:false,idr:true,lore:'D21E(+1.5Å)=pathogenic。MDM2面から6.59Å。未知パートナーとの相互作用？'},
];

const STG=[
  {id:1,n:"満員電車",s:"Core Interior",e:"🚃",d:"コア深部でcavityかclashか！パッキング破壊の二刀流！",c:"#ff3344"},
  {id:2,n:"魔のループ",s:"Loops & Pro",e:"🔓",d:"Ramachandranの拘束を解き放て！ProとGlyが鍵！",c:"#ff9900"},
  {id:3,n:"表面の要塞",s:"Surface & DNA",e:"⚡",d:"DNA接触と静電ネットワークの急所を狙え！",c:"#3399ff"},
  {id:4,n:"Zn Cascade",s:"Layered Cascade",e:"💀",d:"4層構造を理解し、Layer 3からcascadeを起動！",c:"#ff44aa"},
  {id:5,n:"IDR侵攻",s:"Disordered Region",e:"🌊",d:"構造なき戦場。SLiM・キナーゼモチーフ・PPIIを破壊！",c:"#44ddaa"},
  {id:6,n:"暗黒物質",s:"Dark Matter",e:"👻",d:"未知のメカニズムを暴け！",c:"#aa44ff"},
];

function evalG(r,mt){
  const w=AA[r.aa],m=AA[mt];if(!w||!m)return{ch:[],sc:0,fx:[]};
  const ch=[],fx=[];let sc=0;
  const vL=Math.max(0,w.v-m.v),vG=Math.max(0,m.v-w.v);
  const dQ=Math.abs(m.q-w.q),dH=Math.abs(m.h-w.h),dHB=(w.hbd+w.hba)-(m.hbd+m.hba);
  const cF=w.q*m.q<0&&Math.abs(w.q)>.3&&Math.abs(m.q)>.3;
  const tc=t=>t==='S'?'#ff2266':'#ffaa00';

  // Ch1 DNA
  if(r.dDNA<3.5){if('RK'.includes(r.aa)&&!'RK'.includes(mt)){ch.push({c:'Ch1',n:'DNA Contact',r:`DNA面で正電荷喪失(d=${r.dDNA}Å)`,t:'A'});fx.push('💥 DNA CONTACT SEVERED!');sc+=400;}
  else if(dHB>=1){ch.push({c:'Ch1',n:'DNA Contact',r:`H-bond capacity低下(ΔHB=${dHB})`,t:'A'});fx.push('💥 DNA H-BOND BROKEN!');sc+=350;}
  else if(dQ>.5){ch.push({c:'Ch1',n:'DNA Contact',r:'DNA面で電荷変化',t:'A'});fx.push('⚡ DNA CHARGE DISRUPTED!');sc+=300;}}
  else if(r.dDNA<6&&'RK'.includes(r.aa)&&!'RKH'.includes(mt)&&dQ>.3){ch.push({c:'Ch1',n:'DNA Contact',r:'近接ゾーンで電荷喪失',t:'A'});fx.push('💥 DNA RECOGNITION LOST!');sc+=300;}

  // Ch2 Zn
  if(r.znL){ch.push({c:'Ch2',n:'Zn Coord',r:r.dZn<3?'Zn直接配位破壊(Layer1)':`Phantom coordination破壊(${r.dZn}Å)`,t:'S'});fx.push(r.dZn<3?'💀 Zn LIGAND DESTROYED!':'👻 PHANTOM ANCHOR SEVERED!');sc+=500;}
  else if(r.dZn<8&&dQ>.5){ch.push({c:'Ch2',n:'Zn Coord',r:`Zn環境電荷擾乱(d=${r.dZn}Å)`,t:'A'});fx.push(cF?'⚡ Zn CASCADE — CHARGE FLIP!':'⚡ Zn DISRUPTED!');sc+=cF?450:350;}

  // Ch3 Core — Tier S
  if(mt==='G'&&r.aa!=='G'&&r.bur>.5){ch.push({c:'Ch3',n:'Core',r:'→Gly: Cβ消失→Ramachandran解放(1963)',t:'S'});fx.push('🔓 RAMACHANDRAN RELEASED!');sc+=500;}
  if(r.ss==='E'&&w.br&&!m.br&&r.bur>.5){ch.push({c:'Ch3',n:'Core',r:'β-branch消失→sheet interlock崩壊',t:'S'});fx.push('🧩 β-INTERLOCK DESTROYED!');sc+=500;}
  if(w.su&&!m.su&&r.nAr>=1&&r.bur>.5){ch.push({c:'Ch3',n:'Core',r:`S...π切断(芳香族×${r.nAr})`,t:'S'});fx.push('✂️ S...π CUT!');sc+=450;}
  if(r.aa==='M'&&!m.su&&r.nSu>=3){ch.push({c:'Ch3',n:'Core',r:`S...S chalcogen崩壊(硫黄×${r.nSu})`,t:'S'});fx.push('💥 SULFUR SHIELD COLLAPSED!');sc+=500;}
  if(w.h<-1&&m.h>1&&r.bur>.7){ch.push({c:'Ch3',n:'Core',r:'極性→疎水: H-bond partner喪失',t:'S'});fx.push('🔥 H-BOND SEVERED!');sc+=450;}
  if(Math.abs(w.q)>.5&&r.nCh>=4){ch.push({c:'Ch3',n:'Core',r:`静電keystone破壊(荷電隣接×${r.nCh})`,t:'S'});fx.push('⚡ KEYSTONE DESTROYED!');sc+=500;}
  // Tier A
  if(vL>40&&r.bur>.7){ch.push({c:'Ch3',n:'Core',r:`Cavity(−${vL}ų)`,t:'A'});fx.push(`🕳️ CAVITY! −${vL}ų`);sc+=300;}
  else if(vL>20&&w.ar&&!m.ar&&r.bur>.5){ch.push({c:'Ch3',n:'Core',r:'Cavity+芳香環消失',t:'A'});fx.push('🕳️ CAVITY+ARO GONE!');sc+=350;}
  if(vG>40&&r.bur>.7){ch.push({c:'Ch3',n:'Core',r:`Steric clash(+${vG}ų) LJ反発壁`,t:'A'});fx.push(`💥 STERIC CLASH! +${vG}ų`);sc+=300;}
  else if(vG>20&&r.bur>.85&&r.ss==='E'){ch.push({c:'Ch3',n:'Core',r:`β-sheet clash(+${vG}ų)`,t:'A'});fx.push(`💥 β-CLASH! +${vG}ų`);sc+=280;}
  if(m.q!==0&&w.q===0&&r.bur>.7){ch.push({c:'Ch3',n:'Core',r:'コアへの電荷導入',t:'A'});fx.push('⚡ CHARGE IN CORE!');sc+=350;}
  if(cF&&r.bur>.5&&!r.idr){ch.push({c:'Ch3',n:'Core',r:'電荷符号反転',t:'A'});fx.push('⚡ CHARGE FLIP!');sc+=400;}
  if(r.bur<.5&&r.bur>.3&&w.ar&&!m.ar&&!r.idr){ch.push({c:'Ch3',n:'Core',r:'表面芳香族anchor消失',t:'A'});fx.push('👻 DARK ANCHOR PULLED!');sc+=350;}

  // Ch4 SS
  if(r.ss==='H'&&r.aa==='P'&&mt!=='P'){ch.push({c:'Ch4',n:'SS',r:'Helix Pro kink消失',t:'S'});fx.push('🔓 KINK RELEASED!');sc+=450;}
  if(mt==='P'&&r.aa!=='P'&&'HE'.includes(r.ss)){ch.push({c:'Ch4',n:'SS',r:'Pro導入→SS破壊',t:'A'});fx.push('💥 SS BROKEN!');sc+=300;}

  // Ch5 Pro/Gly/Loop
  if(r.aa==='P'&&mt!=='P'&&!r.idr&&!ch.some(c=>c.r.includes('kink'))){ch.push({c:'Ch5',n:'Pro/Gly',r:'Pro→X: φ拘束解除(Tier S)',t:'S'});fx.push('🔓 PROLINE RELEASED!');sc+=500;}
  if(r.aa==='G'&&mt!=='G'&&r.zone==='loop'){ch.push({c:'Ch5',n:'Pro/Gly',r:'ループ内Gly→X: 硬直化',t:'A'});fx.push('💥 LOOP RIGID!');sc+=350;}

  // IDR gates
  if(r.aa==='P'&&mt!=='P'&&r.idr){
    if(r.slim==='kinase'&&r.ptm){ch.push({c:'Ch7d',n:'Kinase',r:`[S/T]-P破壊: S${r.ptm.s}リン酸化不能(${r.ptm.k})`,t:'S'});fx.push(`🔑 [S/T]-P DESTROYED! ${r.ptm.k}`);sc+=500;
      if('ST'.includes(mt)){fx.push('💡 mt∈{S,T}→部分保存の可能性');sc-=100;}}
    else if(r.slim==='PRD'){ch.push({c:'Ch5',n:'IDR Pro',r:'PRD Pro→X: PPII崩壊',t:'A'});fx.push('🔓 PPII COLLAPSED!');sc+=350;}
    else{ch.push({c:'Ch5',n:'IDR Pro',r:'IDR Pro→X',t:'A'});fx.push('🔓 IDR PRO RELEASED!');sc+=250;}}
  if(r.idr&&r.slim==='MDM2'){ch.push({c:'Ch10',n:'SLiM',r:'MDM2結合面変異→coupled folding不能',t:'A'});fx.push('💀 MDM2 BINDING DESTROYED!');sc+=400;}
  if(r.idr&&r.aa==='G'&&mt!=='G'){ch.push({c:'GateB',n:'IDR Gly',r:'IDR Gly→X: backbone自由度消失。「無構造」が機能。',t:'A'});fx.push('🔒 IDR FLEXIBILITY LOST!');sc+=300;}

  // Ch9 salt bridge
  if(r.sbP&&dQ>.5&&r.bur<.5){ch.push({c:'Ch9',n:'Salt Bridge',r:'塩橋ジッパー崩壊',t:'S'});fx.push('⚡ SALT BRIDGE SNAPPED!');sc+=400;}

  // Multi-ch bonus
  if(ch.length>=2){sc=Math.floor(sc*1.5);fx.push(`🔥🔥 MULTI-CH ×${ch.length}!`);}
  if(ch.length>=3){fx.push('☠️ CATASTROPHIC!');sc+=300;}
  const nS=ch.filter(c=>c.t==='S').length;if(nS)sc+=nS*200;
  if(!ch.length){fx.push(r.idr?'🛡️ IDR absorbed. まだ見つかってないGateかも…':r.bur<.3?'😴 表面が吸収。':'🤔 Gate held。');sc=0;}
  return{ch,sc,fx,cF};
}

const ACH={phantom:{n:"Phantom Coordinator",e:"👻"},rama:{n:"Ramachandran's Revenge",e:"🔓"},flipper:{n:"Charge Flipper",e:"⚡"},dark:{n:"Dark Matter Hunter",e:"🌑"},multi:{n:"Multi-Ch Breaker",e:"🔥"},sulfur:{n:"Sulfur Breaker",e:"☢️"},keystone:{n:"Keystone Destroyer",e:"⚡"},kinase:{n:"Kinase Breaker",e:"🔑"},idr:{n:"IDR Invader",e:"🌊"},lj:{n:"LJ Dual Wielder",e:"💥"},p47s:{n:"Molecular Truth",e:"🔬"},cascade:{n:"Cascade Master",e:"💀"}};

export default function App(){
  const[stg,setStg]=useState(1),[sR,setSR]=useState(null),[sM,setSM]=useState(null),[rs,setRs]=useState(null);
  const[tot,setTot]=useState(0),[bk,setBk]=useState(0),[sk,setSk]=useState(0),[ac,setAc]=useState(new Set());
  const[hi,setHi]=useState([]),[sh,setSh]=useState(false),[pp,setPp]=useState(null),[lo,setLo]=useState(false);
  const sr=RES.filter(r=>r.stg===stg),si=STG.find(s=>s.id===stg);

  const go=()=>{if(!sR||!sM||sM===sR.aa)return;const r=evalG(sR,sM);setRs(r);
    const ok=r.ch.length>0;if(ok){setTot(s=>s+r.sc);setBk(b=>b+1);setSk(s=>s+1);setSh(true);setTimeout(()=>setSh(false),600);}else setSk(0);
    const na=new Set(ac);
    if(sR.pos===179&&ok)na.add('phantom');if(sR.pos===113&&ok)na.add('dark');if(r.cF)na.add('flipper');
    if(r.ch.length>=3)na.add('multi');if(sR.pos===246&&r.ch.some(c=>c.r.includes('chalcogen')))na.add('sulfur');
    if(sR.pos===281&&r.ch.some(c=>c.r.includes('keystone')))na.add('keystone');
    if(r.ch.some(c=>c.r.includes('[S/T]-P')))na.add('kinase');if(sR.idr&&ok)na.add('idr');
    if(sR.pos===47&&sM==='S')na.add('p47s');
    if(r.ch.some(c=>c.r.includes('Ramachandran')||c.r.includes('φ拘束')))na.add('rama');
    const cv=hi.some(h=>h.fx?.some(f=>f.includes('CAVITY')))||r.fx.some(f=>f.includes('CAVITY'));
    const cl=hi.some(h=>h.fx?.some(f=>f.includes('CLASH')))||r.fx.some(f=>f.includes('CLASH'));
    if(cv&&cl)na.add('lj');
    if(sR.dZn<8&&ok)na.add('cascade');
    const nw=[...na].filter(a=>!ac.has(a));if(nw.length){setPp(ACH[nw[0]]);setTimeout(()=>setPp(null),3000);}
    setAc(na);setHi(h=>[...h,{pos:sR.pos,wt:sR.aa,mt:sM,...r}]);setSM(null);};

  return(<div style={{fontFamily:"'JetBrains Mono','Fira Code',monospace",background:'#08080f',color:'#d8d8e0',minHeight:'100vh'}}>
    <div style={{position:'fixed',inset:0,background:'repeating-linear-gradient(0deg,transparent,transparent 3px,rgba(0,255,80,.006) 3px,rgba(0,255,80,.006) 4px)',pointerEvents:'none',zIndex:100}}/>
    <div style={{background:'linear-gradient(135deg,#0c0c1a,#18082a)',borderBottom:`2px solid ${si?.c||'#333'}`,padding:'10px 16px',display:'flex',alignItems:'center',justifyContent:'space-between',flexWrap:'wrap',gap:'8px'}}>
      <div><h1 style={{margin:0,fontSize:'22px',background:'linear-gradient(90deg,#ff2266,#ff8844,#ffcc00)',WebkitBackgroundClip:'text',WebkitTextFillColor:'transparent',letterSpacing:'3px',fontWeight:900}}>🧬 BREAKIT</h1>
        <div style={{fontSize:'9px',color:'#333',letterSpacing:'1px'}}>v17 ENGINE · 13ch · ZERO PARAMS</div></div>
      <div style={{display:'flex',gap:'14px',fontSize:'11px'}}>
        <div><span style={{color:'#ff2266'}}>SC</span> <b style={{fontSize:'16px'}}>{tot}</b></div>
        <div><span style={{color:'#ffaa00'}}>BK</span> <b style={{fontSize:'16px'}}>{bk}</b></div>
        <div><span style={{color:'#44ff88'}}>ST</span> <b style={{fontSize:'16px'}}>{sk}</b></div>
        <div><span style={{color:'#aa44ff'}}>🏆</span> <b style={{fontSize:'16px'}}>{ac.size}/{Object.keys(ACH).length}</b></div></div></div>
    <div style={{display:'flex',gap:'2px',padding:'6px 10px',background:'#0a0a14',overflowX:'auto'}}>
      {STG.map(s=><button key={s.id} onClick={()=>{setStg(s.id);setSR(null);setRs(null);setSM(null);}}
        style={{flex:'1 0 auto',minWidth:'70px',padding:'6px 4px',border:stg===s.id?`2px solid ${s.c}`:'1px solid #1a1a24',borderRadius:'5px',
          background:stg===s.id?`${s.c}10`:'transparent',color:stg===s.id?s.c:'#333',cursor:'pointer',fontSize:'10px',fontFamily:'inherit'}}>
        <div style={{fontSize:'14px'}}>{s.e}</div><div style={{fontWeight:700,fontSize:'9px'}}>{s.n}</div></button>)}</div>
    <div style={{padding:'4px 16px',fontSize:'10px',color:si?.c,background:'#0a0a10',borderBottom:'1px solid #12121a'}}>{si?.e} {si?.d}</div>
    <div style={{display:'flex',flexWrap:'wrap'}}>
      <div style={{flex:'1 1 300px',padding:'10px 14px',borderRight:'1px solid #12121a',minWidth:'280px',maxHeight:'calc(100vh - 160px)',overflowY:'auto'}}>
        <div style={{fontSize:'10px',color:'#444',marginBottom:'6px',letterSpacing:'1px'}}>TARGETS</div>
        {sr.map(r=><button key={r.pos} onClick={()=>{setSR(r);setRs(null);setSM(null);setLo(false);}}
          style={{display:'flex',alignItems:'center',gap:'8px',padding:'7px 8px',marginBottom:'3px',
            border:sR?.pos===r.pos?`2px solid ${si?.c}`:'1px solid #16161e',borderRadius:'5px',
            background:sR?.pos===r.pos?'#12121e':'#0a0a12',color:'#ccc',cursor:'pointer',fontFamily:'inherit',fontSize:'11px',width:'100%',textAlign:'left'}}>
          <div style={{width:'32px',height:'32px',borderRadius:'50%',flexShrink:0,
            background:`radial-gradient(circle,${r.bur>.7?'#ff4444':r.bur>.4?'#ffaa00':r.idr?'#44ddaa':'#4488ff'} 0%,#08080f 100%)`,
            display:'flex',alignItems:'center',justifyContent:'center',fontWeight:900,fontSize:'13px',
            border:`2px solid ${r.znL?'#ff44aa44':'#222'}`}}>{r.aa}</div>
          <div style={{flex:1,minWidth:0}}>
            <div style={{fontWeight:700}}>{r.aa}{r.pos} <span style={{fontSize:'9px',color:'#444',fontWeight:400}}>{AA[r.aa]?.n}</span>
              {r.idr&&<span style={{marginLeft:'3px',padding:'0 3px',borderRadius:'2px',fontSize:'8px',background:'#44ddaa18',color:'#44ddaa'}}>IDR</span>}
              {r.znL&&<span style={{marginLeft:'3px',padding:'0 3px',borderRadius:'2px',fontSize:'8px',background:'#ff44aa18',color:'#ff44aa'}}>Zn</span>}</div>
            <div style={{fontSize:'9px',color:'#555',whiteSpace:'nowrap',overflow:'hidden',textOverflow:'ellipsis'}}>{r.desc}</div></div></button>)}</div>
      <div style={{flex:'1 1 360px',padding:'10px 14px',minWidth:'320px',maxHeight:'calc(100vh - 160px)',overflowY:'auto'}}>
        {sR?<>
          <button onClick={()=>setLo(!lo)} style={{width:'100%',padding:'5px 8px',marginBottom:'6px',border:'1px solid #1a1a24',borderRadius:'3px',background:'#0c0c16',color:'#666',cursor:'pointer',fontFamily:'inherit',fontSize:'9px',textAlign:'left'}}>
            {lo?'▼':'▶'} Intel {lo&&<div style={{color:'#999',marginTop:'3px',lineHeight:1.5,fontSize:'10px'}}>{sR.lore}</div>}</button>
          <div style={{fontSize:'11px',color:'#777',marginBottom:'4px'}}>MUTATE <span style={{color:si?.c,fontWeight:700}}>{sR.aa}{sR.pos}</span> →</div>
          <div style={{display:'grid',gridTemplateColumns:'repeat(5,1fr)',gap:'2px',marginBottom:'10px'}}>
            {Object.keys(AA).sort().filter(a=>a!==sR.aa).map(a=>{const p=AA[a],dv=p.v-AA[sR.aa].v;return(
              <button key={a} onClick={()=>setSM(a)} style={{padding:'6px 1px',border:sM===a?'2px solid #ff2266':'1px solid #1a1a24',borderRadius:'3px',
                background:sM===a?'#1a0814':'#0a0a12',color:p.q>.5?'#6699ff':p.q<-.5?'#ff6666':p.ar?'#ffcc44':p.po?'#44bb88':'#777',
                cursor:'pointer',fontFamily:'inherit',fontSize:'12px',fontWeight:700}}><div>{a}</div>
                <div style={{fontSize:'7px',color:'#333',fontWeight:400}}>{Math.abs(dv)>15?(dv>0?'+':'')+dv:''}</div></button>);})}
          </div>
          {sM&&<button onClick={go} style={{width:'100%',padding:'10px',border:'none',borderRadius:'5px',
            background:`linear-gradient(135deg,${si?.c||'#ff2266'},${si?.c||'#cc1144'}88)`,color:'white',fontSize:'13px',fontWeight:900,
            cursor:'pointer',fontFamily:'inherit',letterSpacing:'2px',boxShadow:`0 3px 12px ${si?.c||'#f24'}44`}}>💥 {sR.aa}{sR.pos}{sM}</button>}
          {rs&&<div style={{marginTop:'10px',padding:'10px',borderRadius:'6px',border:rs.ch.length>0?`2px solid ${si?.c}`:'1px solid #1a1a24',
            background:rs.ch.length>0?'#10081a':'#0a0a12',animation:sh?'shk .5s':undefined}}>
            {rs.fx.map((e,i)=><div key={i} style={{fontSize:i<1?'15px':'11px',fontWeight:i<2?900:400,
              color:rs.ch.length>0?(e.includes('💡')?'#44ddaa':'#ff4466'):'#444',marginBottom:'3px',
              animation:rs.ch.length>0?`fsl .4s ${i*.08}s both`:undefined}}>{e}</div>)}
            {rs.sc>0&&<div style={{fontSize:'20px',fontWeight:900,color:'#ffaa00',margin:'4px 0',textShadow:'0 0 12px rgba(255,170,0,.4)'}}>+{rs.sc}</div>}
            {rs.ch.map((c,i)=><div key={i} style={{margin:'4px 0',padding:'6px',borderRadius:'3px',background:'#08080f',border:`1px solid ${c.t==='S'?'#ff226618':'#ffaa0018'}`}}>
              <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
                <span style={{fontWeight:700,color:c.t==='S'?'#ff2266':'#ffaa00',fontSize:'11px'}}>{c.c}: {c.n}</span>
                <span style={{padding:'1px 5px',borderRadius:'2px',fontSize:'9px',fontWeight:900,
                  background:c.t==='S'?'#ff226620':'#ffaa0020',color:c.t==='S'?'#ff2266':'#ffaa00'}}>Tier {c.t}</span></div>
              <div style={{fontSize:'10px',color:'#888',marginTop:'2px',lineHeight:1.3}}>{c.r}</div></div>)}
            {!rs.ch.length&&<div style={{fontSize:'10px',color:'#333',marginTop:'4px'}}>💡 burial, 電荷, SS, 何が変わり何が残るか考えよう</div>}</div>}
        </>:<div style={{display:'flex',alignItems:'center',justifyContent:'center',height:'200px',color:'#1a1a24',fontSize:'12px',border:'1px dashed #1a1a24',borderRadius:'6px'}}>← target選択</div>}
        {ac.size>0&&<div style={{marginTop:'14px',borderTop:'1px solid #16161e',paddingTop:'8px'}}>
          <div style={{fontSize:'9px',color:'#444',letterSpacing:'1px',marginBottom:'4px'}}>🏆 ({ac.size}/{Object.keys(ACH).length})</div>
          <div style={{display:'flex',flexWrap:'wrap',gap:'3px'}}>{[...ac].map(a=><div key={a} style={{padding:'2px 6px',borderRadius:'8px',fontSize:'9px',background:'#12122a',border:'1px solid #2a2a44',color:'#bbb'}}>{ACH[a]?.e} {ACH[a]?.n}</div>)}</div></div>}</div></div>
    {pp&&<div style={{position:'fixed',top:'18%',left:'50%',transform:'translateX(-50%)',padding:'16px 32px',borderRadius:'8px',
      background:'linear-gradient(135deg,#18082e,#2a1040)',border:'2px solid #aa44ff',boxShadow:'0 0 40px rgba(170,68,255,.4)',
      zIndex:200,textAlign:'center',animation:'pop .3s ease-out'}}>
      <div style={{fontSize:'32px'}}>{pp.e}</div><div style={{fontSize:'12px',fontWeight:900,color:'#aa44ff',marginTop:'4px'}}>UNLOCKED</div>
      <div style={{fontSize:'13px',fontWeight:700,marginTop:'2px'}}>{pp.n}</div></div>}
    <div style={{padding:'6px 16px',borderTop:'1px solid #0e0e14',fontSize:'8px',color:'#1a1a24',textAlign:'center',background:'#06060a'}}>
      BREAKIT v2 — v17 Engine — 13ch/30+gates/7 Tier S — Zero Params — Ramachandran(1963)·Flory(1969)·Barlow&Thornton(1983)·Burley&Petsko(1985)</div>
    <style>{`@keyframes shk{0%,100%{transform:translateX(0)}15%{transform:translateX(-8px) rotate(-1deg)}30%{transform:translateX(8px) rotate(1deg)}45%{transform:translateX(-5px)}60%{transform:translateX(5px)}75%{transform:translateX(-2px)}}
    @keyframes fsl{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
    @keyframes pop{from{opacity:0;transform:translateX(-50%) scale(.7)}to{opacity:1;transform:translateX(-50%) scale(1)}}
    button:hover{filter:brightness(1.15)}*::-webkit-scrollbar{width:3px}*::-webkit-scrollbar-thumb{background:#1a1a2a;border-radius:2px}`}</style>
  </div>);
}
