let isDark=true;
const days=['Seg','Ter','Qua','Qui','Sex','Sáb','Dom'];
const scores=[72,80,85,78,91,88,87];
const months=['Set','Out','Nov','Dez','Jan','Fev','Mar','Abr'];
const monthScores=[58,62,68,75,80,82,87,null];
const colors=['#B5FF2D','#00F5FF','#7C3AED','#FF6B6B','#FFD700','#B5FF2D','#00F5FF','#FF6B6B'];

function goPage(id){document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));document.getElementById(id).classList.add('active');}
function goAuth(tab){goPage('auth');swTab(tab);}
function login(){goPage('dashboard');buildCharts();toast('🎉 Bem-vindo ao GLevel!');}
function swTab(t){document.getElementById('f-li').style.display=t==='li'?'block':'none';document.getElementById('f-su').style.display=t==='su'?'block':'none';document.getElementById('t-li').classList.toggle('active',t==='li');document.getElementById('t-su').classList.toggle('active',t==='su');}
function toggleTheme(){isDark=!isDark;document.body.classList.toggle('light',!isDark);document.querySelectorAll('.theme-btn').forEach(b=>b.textContent=isDark?'🌙':'☀️');}
function sv(v){document.querySelectorAll('.view').forEach(d=>d.classList.remove('active'));document.querySelectorAll('.ni').forEach(n=>n.classList.remove('active'));document.getElementById('v-'+v).classList.add('active');}
function toast(msg){const t=document.createElement('div');t.className='toast';t.textContent=msg;document.getElementById('toasts').appendChild(t);setTimeout(()=>t.remove(),3000);}

function buildCharts(){
  // Week chart
  const wc=document.getElementById('weekChart');
  const wl=document.getElementById('weekLabels');
  if(!wc)return;
  wc.innerHTML='';wl.innerHTML='';
  const maxS=Math.max(...scores);
  days.forEach((d,i)=>{
    const col=document.createElement('div');col.className='cb';
    col.style.cssText=`height:${(scores[i]/maxS)*120}px;background:linear-gradient(180deg,${colors[i%colors.length]},${colors[(i+1)%colors.length]});`;
    col.title=`${d}: ${scores[i]}%`;
    wc.appendChild(col);
    const lbl=document.createElement('div');lbl.className='cx-item';lbl.textContent=d;wl.appendChild(lbl);
  });
  // History chart
  const hc=document.getElementById('histChart');
  const hl=document.getElementById('histLabels');
  if(!hc)return;
  hc.innerHTML='';hl.innerHTML='';
  const maxM=Math.max(...monthScores.filter(Boolean));
  months.forEach((m,i)=>{
    const col=document.createElement('div');col.className='hc-col';
    const bar=document.createElement('div');bar.className='hc-bar';
    const h=monthScores[i]?(monthScores[i]/maxM)*140:0;
    bar.style.cssText=`height:${h}px;background:${monthScores[i]?`linear-gradient(180deg,${colors[i%colors.length]},${colors[(i+2)%colors.length]})`:colors[i%colors.length]};opacity:${monthScores[i]?1:.3}`;
    const lbl=document.createElement('div');lbl.className='hc-label';lbl.textContent=m;
    col.appendChild(bar);col.appendChild(lbl);hc.appendChild(col);
  });
}