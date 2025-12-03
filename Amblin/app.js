// Basic front-end only mock logic
const weeks = n => Array.from({length:n}, (_,i)=>i);

function genWeeklyLabels(n){
  const today = new Date();
  const labels = [];
  for(let i=n-1;i>=0;i--){
    const d = new Date(today);
    d.setDate(today.getDate() - i*7);
    labels.push(`${d.getMonth()+1}/${d.getDate()}`);
  }
  return labels;
}

function clamp(v, a, b){return Math.max(a, Math.min(b, v));}

const presets = {
  conservative: { lift:0.00, sens:0.35, acq:0.6 },
  balanced:     { lift:0.15, sens:0.50, acq:1.0 },
  ambitious:    { lift:0.35, sens:0.65, acq:1.5 },
};

// Platform multipliers reflecting Amblin-like film/entertainment footprint
const formatMult = {
  IG: { short:1.1, image:1.12, carousel:1.25, long:1.05 },
  TT: { short:1.3, image:0.7,  carousel:0.85, long:0.9  },
  YT: { short:0.9, image:0.7,  carousel:0.85, long:1.3  },
  FB: { short:1.0, image:1.0,  carousel:1.05, long:1.1  },
};

const colors = {
  ig: '#4F46E5', tt:'#06B6D4', yt:'#10B981', fb:'#F59E0B',
  aware:'#4F46E5', reach:'#06B6D4', dwell:'#94A3B8', ugc:'#EF4444'
};

// Synthetic baselines for historical series
function genBaseline(n, mean, noise){
  const out = [];
  let val = mean;
  for(let i=0;i<n;i++){
    val = val*(0.98+Math.random()*0.04) + (Math.random()-0.5)*noise;
    out.push(Math.max(0, val));
  }
  return out;
}

function weightedSum(obj, weights){
  return Object.keys(obj).reduce((acc,k)=>acc+obj[k]*(weights[k]||0),0)
}

function makeCharts(){
  const timeRange = parseInt(document.getElementById('timeRange').value,10);
  const labels = genWeeklyLabels(timeRange);

  // Baselines
  const baseEngIG = genBaseline(timeRange, 3.6, 0.3);
  const baseEngTT = genBaseline(timeRange, 5.0, 0.4);
  const baseEngYT = genBaseline(timeRange, 3.4, 0.25);
  const baseEngFB = genBaseline(timeRange, 2.0, 0.25);

  const ctxEng = document.getElementById('engChart');
  const ctxAR = document.getElementById('awareReachChart');
  const ctxDwell = document.getElementById('dwellChart');
  const ctxUGC = document.getElementById('ugcChart');

  const datasetsEng = [];
  if(document.getElementById('chk-ig').checked) datasetsEng.push({label:'Instagram',data:baseEngIG,borderColor:colors.ig,backgroundColor:colors.ig,fill:false,tension:.35});
  if(document.getElementById('chk-tt').checked) datasetsEng.push({label:'TikTok',data:baseEngTT,borderColor:colors.tt,backgroundColor:colors.tt,fill:false,tension:.35});
  if(document.getElementById('chk-yt').checked) datasetsEng.push({label:'YouTube',data:baseEngYT,borderColor:colors.yt,backgroundColor:colors.yt,fill:false,tension:.35});
  if(document.getElementById('chk-fb').checked) datasetsEng.push({label:'Facebook',data:baseEngFB,borderColor:colors.fb,backgroundColor:colors.fb,fill:false,tension:.35});

  const engChart = new Chart(ctxEng, {
    type:'line',
    data:{ labels, datasets: datasetsEng },
    options:{
      responsive:true,
      plugins:{ legend:{position:'top', labels:{usePointStyle:true, boxWidth:8}} },
      scales:{ y:{ title:{display:true,text:'%'} } }
    }
  });

  const aware = genBaseline(timeRange, 60, 4);
  const reach = genBaseline(timeRange, 1200, 100); // in thousands
  const awareReachChart = new Chart(ctxAR, {
    type:'line',
    data:{ labels, datasets:[
      {label:'Awareness', data:aware, borderColor:colors.aware, backgroundColor:colors.aware, tension:.35, fill:false},
      {label:'Reach (k)', data:reach, borderColor:colors.reach, backgroundColor:colors.reach, tension:.35, fill:false}
    ]},
    options:{ plugins:{ legend:{position:'top'} }, scales:{ y:{ beginAtZero:true } } }
  });

  const dwell = [
    {label:'Instagram', val: 36},
    {label:'TikTok', val: 28},
    {label:'YouTube', val: 86},
    {label:'Facebook', val: 22},
  ];
  const dwellChart = new Chart(ctxDwell, {
    type:'bar',
    data:{ labels: dwell.map(d=>d.label), datasets:[{label:'Seconds', data:dwell.map(d=>d.val), backgroundColor:[colors.ig,colors.tt,colors.yt,colors.fb]}] },
    options:{ indexAxis:'y', plugins:{legend:{display:false}} }
  });

  const ugc = genBaseline(timeRange, 2.1, 0.3); // thousands / wk
  const ugcChart = new Chart(ctxUGC, {
    type:'bar',
    data:{ labels, datasets:[{label:'UGC (k/wk)', data:ugc, backgroundColor:colors.ugc}] },
    options:{ plugins:{legend:{position:'top'}}, scales:{y:{beginAtZero:true}} }
  });

  // Scenario controls: front-end only mock math
  const posts = document.getElementById('posts');
  const postsVal = document.getElementById('postsVal');
  const ig = document.getElementById('igPct');
  const tt = document.getElementById('ttPct');
  const yt = document.getElementById('ytPct');
  const fb = document.getElementById('fbPct');
  const updatePercents = ()=>{
    const total = parseInt(ig.value)+parseInt(tt.value)+parseInt(yt.value)+parseInt(fb.value);
    if(total===100) return;
    // normalize to 100
    const scale = 100/Math.max(1,total);
    ig.value = Math.round(parseInt(ig.value)*scale);
    tt.value = Math.round(parseInt(tt.value)*scale);
    yt.value = Math.round(parseInt(yt.value)*scale);
    fb.value = Math.round(parseInt(fb.value)*scale);
  };
  const reflectLabels = ()=>{
    document.getElementById('igVal').innerText = ig.value+'%';
    document.getElementById('ttVal').innerText = tt.value+'%';
    document.getElementById('ytVal').innerText = yt.value+'%';
    document.getElementById('fbVal').innerText = fb.value+'%';
    postsVal.innerText = posts.value;
  };
  const presetSel = document.getElementById('preset');

  function applyScenario(){
    reflectLabels();
    const p = presets[presetSel.value];
    const freq = parseInt(posts.value,10);
    const alloc = {IG:ig.value/100, TT:tt.value/100, YT:yt.value/100, FB:fb.value/100};
    const freqEff = x=> x/(x+10); // soft saturation
    const qual = 0.5 + 0.5*(0.6 + p.lift); // rough EI proxy
    const perPostBase = {IG:640, TT:450, YT:500, FB:300};
    const perPost = k => perPostBase[k]*p.acq*qual*(0.5+0.5*freqEff(freq*alloc[k]));
    const weeklyAdd = weightedSum({IG:1,TT:1,YT:1,FB:1}, {IG:freq*alloc.IG*perPost('IG'), TT:freq*alloc.TT*perPost('TT'), YT:freq*alloc.YT*perPost('YT'), FB:freq*alloc.FB*perPost('FB')});
    // update KPIs (mock): engagement slightly reacts, reach + awareness move with weeklyAdd
    const engNow = 3.2 + (p.sens*0.6)*freqEff(freq)*0.6; // %
    document.getElementById('kpi-eng').innerText = engNow.toFixed(1)+'%';
    document.getElementById('kpi-aware').innerText = Math.round(64 + weeklyAdd/15000);
    document.getElementById('kpi-reach').innerText = (1.2 + weeklyAdd/1000000).toFixed(1)+'M';
    document.getElementById('kpi-dwell').innerText = Math.round(38 + p.sens*4) + 's';
    document.getElementById('kpi-ugc').innerText = (2.1 + weeklyAdd/20000).toFixed(1)+'K';
  }

  // interactions
  [posts, ig, tt, yt, fb].forEach(el=>{
    el.addEventListener('input', ()=>{ updatePercents(); reflectLabels(); applyScenario(); });
  });
  presetSel.addEventListener('change', applyScenario);
  document.getElementById('timeRange').addEventListener('change', ()=> location.reload());

  updatePercents();
  reflectLabels();
  applyScenario();
}

window.addEventListener('DOMContentLoaded', makeCharts);

