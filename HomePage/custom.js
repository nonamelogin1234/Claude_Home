/* HOMEPAGE NATURE — custom.js */

var API = '/grok-news';
var NEWS_CACHE_KEY = 'hp_news';
var NEWS_TTL = 30 * 60 * 1000;

function makeEl(tag, attrs, children) {
  var node = document.createElement(tag);
  if (attrs) Object.keys(attrs).forEach(function(k) {
    var v = attrs[k];
    if (k === 'class') node.className = v;
    else if (k === 'html') node.innerHTML = v;
    else node.setAttribute(k, v);
  });
  if (children) children.forEach(function(c) {
    if (!c) return;
    if (typeof c === 'string') node.appendChild(document.createTextNode(c));
    else node.appendChild(c);
  });
  return node;
}

function initWaterfall() {
  var canvas = makeEl('canvas', { id: 'hp-waterfall' });
  document.body.appendChild(canvas);
  document.body.appendChild(makeEl('div', { id: 'hp-mist' }));

  var ctx = canvas.getContext('2d');
  var W = 340, H = window.innerHeight;
  canvas.width = W; canvas.height = H;

  var WC = [[125,211,252],[147,232,255],[186,230,253],[74,222,128],[255,255,255],[165,243,252]];
  function rc() { var c = WC[Math.floor(Math.random()*WC.length)]; return 'rgba('+c[0]+','+c[1]+','+c[2]+','; }

  var main = [], thin = [], spl = [];
  for (var i=0;i<10;i++) main.push({x:20+Math.random()*(W-40),y:Math.random()*H-H,speed:1.2+Math.random()*2,len:120+Math.random()*200,width:2.5+Math.random()*5,opacity:0.25+Math.random()*0.45,color:rc(),wobble:(Math.random()-.5)*.3});
  for (var j=0;j<28;j++) thin.push({x:5+Math.random()*(W-10),y:Math.random()*H-H,speed:0.6+Math.random()*1.5,len:60+Math.random()*140,width:0.5+Math.random()*1.5,opacity:0.12+Math.random()*0.35,color:rc(),wobble:(Math.random()-.5)*.5});
  for (var k=0;k<18;k++) spl.push({x:W*.4+Math.random()*W*.6,y:Math.random()*H-H*.3,speed:2.5+Math.random()*4,len:15+Math.random()*45,width:0.4+Math.random()*1,opacity:0.08+Math.random()*.22,color:'rgba(255,255,255,',wobble:(Math.random()-.5)*.8});

  var foam = [];
  for (var f=0;f<40;f++) foam.push({x:W*.3+Math.random()*W*.7,y:H*.6+Math.random()*H*.4,r:.5+Math.random()*2,opacity:.05+Math.random()*.18,speed:.2+Math.random()*.6,drift:(Math.random()-.5)*.4});

  function drawStreams(arr, wobble) {
    arr.forEach(function(s) {
      if (wobble) { s.x += s.wobble; if(s.x<2)s.x=2; if(s.x>W-2)s.x=W-2; }
      var g = ctx.createLinearGradient(s.x,s.y-s.len,s.x,s.y);
      g.addColorStop(0,s.color+'0)'); g.addColorStop(.15,s.color+(s.opacity*.3)+')');
      g.addColorStop(.5,s.color+s.opacity+')'); g.addColorStop(.85,s.color+(s.opacity*.6)+')');
      g.addColorStop(1,s.color+'0)');
      ctx.beginPath(); ctx.strokeStyle=g; ctx.lineWidth=s.width; ctx.lineCap='round';
      ctx.moveTo(s.x,s.y-s.len); ctx.lineTo(s.x,s.y); ctx.stroke();
      s.y+=s.speed; if(s.y-s.len>H){s.y=-s.len;s.x=5+Math.random()*(W-10);}
    });
  }

  function draw() {
    ctx.clearRect(0,0,W,H);
    var g=ctx.createRadialGradient(W,H*.5,0,W,H*.5,W*1.2);
    g.addColorStop(0,'rgba(125,211,252,0.04)'); g.addColorStop(.5,'rgba(74,222,128,0.02)'); g.addColorStop(1,'transparent');
    ctx.fillStyle=g; ctx.fillRect(0,0,W,H);
    drawStreams(thin,true); drawStreams(main,true); drawStreams(spl,false);
    foam.forEach(function(p){
      ctx.beginPath(); ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
      ctx.fillStyle='rgba(255,255,255,'+p.opacity+')'; ctx.fill();
      p.y+=p.speed; p.x+=p.drift;
      if(p.y>H+5){p.y=H*.55+Math.random()*30;p.x=W*.3+Math.random()*W*.7;}
    });
    requestAnimationFrame(draw);
  }
  window.addEventListener('resize',function(){H=window.innerHeight;canvas.height=H;});
  draw();
}

function initFireflies() {
  for (var i=0;i<12;i++) (function(){
    var el=makeEl('div',{class:'hp-firefly'});
    el.style.left=(5+Math.random()*60)+'vw';
    el.style.top=(10+Math.random()*80)+'vh';
    el.style.setProperty('--fx',(Math.random()-.5)*120+'px');
    el.style.setProperty('--fy',(-30-Math.random()*80)+'px');
    el.style.animationDuration=(4+Math.random()*8)+'s';
    el.style.animationDelay=(Math.random()*6)+'s';
    var sz=(2+Math.random()*2)+'px'; el.style.width=sz; el.style.height=sz; el.style.opacity=0;
    document.body.appendChild(el);
  })();
}

function initCursorGlow() {
  var g=makeEl('div',{id:'hp-glow'}); document.body.appendChild(g);
  document.addEventListener('mousemove',function(e){g.style.left=e.clientX+'px';g.style.top=e.clientY+'px';});
}

function initParallax() {
  document.addEventListener('mousemove',function(e){
    document.documentElement.style.setProperty('--px',((e.clientX/window.innerWidth)-.5)*10+'%');
    document.documentElement.style.setProperty('--py',((e.clientY/window.innerHeight)-.5)*7+'%');
  });
}

function greeting() {
  var h=new Date().getHours();
  if(h<6) return '\u0414\u043e\u0431\u0440\u043e\u0439 \u043d\u043e\u0447\u0438';
  if(h<12) return '\u0414\u043e\u0431\u0440\u043e\u0435 \u0443\u0442\u0440\u043e';
  if(h<18) return '\u0414\u043e\u0431\u0440\u044b\u0439 \u0434\u0435\u043d\u044c';
  return '\u0414\u043e\u0431\u0440\u044b\u0439 \u0432\u0435\u0447\u0435\u0440';
}

function buildHeader(container) {
  var header=makeEl('div',{id:'hp-header'});
  var left=makeEl('div');
  left.appendChild(makeEl('div',{id:'hp-greeting'},[greeting()]));
  var td=makeEl('div',{id:'hp-time'});
  left.appendChild(td);
  function tick(){td.textContent=new Date().toLocaleString('ru-RU',{weekday:'long',day:'numeric',month:'long',hour:'2-digit',minute:'2-digit'});}
  tick(); setInterval(tick,30000);
  var right=makeEl('div',{id:'hp-header-right'});
  var b1=makeEl('button',{class:'hp-btn',html:'\u21bb \u041e\u0431\u043d\u043e\u0432\u0438\u0442\u044c'});
  b1.onclick=function(){loadWeather();loadHealth();};
  var b2=makeEl('button',{class:'hp-btn accent',html:'\ud83c\udf3f \u0421\u0432\u043e\u0434\u043a\u0430'});
  b2.onclick=function(){loadNews(true);};
  right.appendChild(b1); right.appendChild(b2);
  header.appendChild(left); header.appendChild(right);
  container.insertBefore(header,container.firstChild);
}

function buildWeather() {
  var c=makeEl('div',{id:'hp-weather',class:'hp-glass'});
  c.innerHTML='<div class="hp-card-label">\ud83c\udf27 \u041f\u043e\u0433\u043e\u0434\u0430 \u00b7 \u0421\u0430\u043d\u043a\u0442-\u041f\u0435\u0442\u0435\u0440\u0431\u0443\u0440\u0433</div><div id="hp-weather-main"><div id="hp-weather-temp">\u2014</div><div id="hp-weather-unit">\u00b0C</div></div><div id="hp-weather-cond">\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430\u2026</div><div id="hp-weather-stats"><span class="hp-wstat">\u041e\u0449. <b id="hw-feels">\u2014</b>\u00b0</span><span class="hp-wstat">\u0412\u043b. <b id="hw-hum">\u2014</b>%</span><span class="hp-wstat">\u0412\u0435\u0442. <b id="hw-wind">\u2014</b>\u043a\u043c/\u0447</span></div><div id="hp-weather-forecast"></div>';
  return c;
}

function wmoIcon(c){if(c===0)return'\u2600\ufe0f';if(c<=2)return'\u26c5';if(c<=3)return'\u2601\ufe0f';if(c<=48)return'\ud83c\udf2b\ufe0f';if(c<=55)return'\ud83c\udf26\ufe0f';if(c<=65)return'\ud83c\udf27\ufe0f';if(c<=77)return'\u2744\ufe0f';if(c<=82)return'\ud83c\udf29\ufe0f';if(c<=86)return'\ud83c\udf28\ufe0f';return'\u26c8\ufe0f';}

function renderWeather(d){
  var t=document.getElementById('hp-weather-temp'),c=document.getElementById('hp-weather-cond'),f=document.getElementById('hw-feels'),h=document.getElementById('hw-hum'),w=document.getElementById('hw-wind'),fc=document.getElementById('hp-weather-forecast');
  if(t)t.textContent=d.temp;if(c)c.textContent=d.condition;if(f)f.textContent=d.feels_like;if(h)h.textContent=d.humidity;if(w)w.textContent=d.wind;
  if(fc&&d.forecast){fc.innerHTML='';d.forecast.forEach(function(day){var el=makeEl('div',{class:'hp-fday'});el.innerHTML='<div class="hp-fday-name">'+day.day+'</div><div class="hp-fday-icon">'+wmoIcon(day.weathercode||0)+'</div><div class="hp-fday-temps">'+day.max+'\u00b0 <span class="lo">'+day.min+'\u00b0</span></div>';fc.appendChild(el);});}
}
function loadWeather(){fetch(API+'/weather').then(function(r){return r.json();}).then(function(d){if(!d.error)renderWeather(d);}).catch(function(){});}

function buildHealth(){
  var c=makeEl('div',{id:'hp-health',class:'hp-glass'});
  c.innerHTML='<div class="hp-card-label">\ud83c\udf31 \u0417\u0434\u043e\u0440\u043e\u0432\u044c\u0435</div><div id="hp-wt-row"><div id="hp-wt-cur">\u2014</div><div id="hp-wt-arrow">\u2192</div><div id="hp-wt-goal">85 \u043a\u0433</div></div><div id="hp-wt-diff"></div><div id="hp-bar"><div id="hp-bar-fill"></div></div><div id="hp-smoke"><div id="hp-smoke-n">\u2014</div><div id="hp-smoke-lbl">\u0434\u043d\u0435\u0439<br>\u0431\u0435\u0437 \u0441\u0438\u0433\u0430\u0440\u0435\u0442</div></div>';
  return c;
}
function renderHealth(d){
  var wc=document.getElementById('hp-wt-cur'),wd=document.getElementById('hp-wt-diff'),bf=document.getElementById('hp-bar-fill'),sn=document.getElementById('hp-smoke-n');
  if(wc&&d.weight!=null)wc.textContent=d.weight;
  if(wd&&d.diff!==undefined){wd.textContent=(d.diff>0?'\u2193 ':'\u2713 ')+Math.abs(d.diff)+' \u043a\u0433 \u0434\u043e \u0446\u0435\u043b\u0438';wd.style.color=d.diff>0?'var(--c-muted)':'var(--c-green)';}
  if(bf&&d.progress_pct!==undefined)setTimeout(function(){bf.style.width=d.progress_pct+'%';},350);
  if(sn)sn.textContent=d.smoke_days||0;
}
function loadHealth(){fetch(API+'/health-stats').then(function(r){return r.json();}).then(function(d){renderHealth(d);}).catch(function(){});}

function buildNews(){
  var c=makeEl('div',{id:'hp-news',class:'hp-glass'});
  c.innerHTML='<div id="hp-news-top"><div class="hp-card-label">\ud83c\udf0d \u041d\u043e\u0432\u043e\u0441\u0442\u0438 \u00b7 Grok</div><button class="hp-btn" id="hp-news-btn">\u21bb \u041e\u0431\u043d\u043e\u0432\u0438\u0442\u044c</button></div><div id="hp-news-meta"></div><div id="hp-news-body">\u041d\u0430\u0436\u043c\u0438\u0442\u0435 \u00ab\u0421\u0432\u043e\u0434\u043a\u0430\u00bb \u0434\u043b\u044f \u0437\u0430\u0433\u0440\u0443\u0437\u043a\u0438\u2026</div>';
  setTimeout(function(){var b=document.getElementById('hp-news-btn');if(b)b.onclick=function(){loadNews(true);};},100);
  return c;
}
function loadNews(force){
  var body=document.getElementById('hp-news-body'),meta=document.getElementById('hp-news-meta'),btn=document.getElementById('hp-news-btn');
  if(!body)return;
  if(!force){try{var cached=JSON.parse(localStorage.getItem(NEWS_CACHE_KEY)||'null');if(cached&&Date.now()-cached.ts<NEWS_TTL){body.textContent=cached.text;body.className='loaded';if(meta)meta.textContent='\u041a\u044d\u0448 \u043e\u0442 '+new Date(cached.ts).toLocaleTimeString('ru-RU',{hour:'2-digit',minute:'2-digit'});return;}}catch(e){}return;}
  body.className='';body.textContent='\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430\u2026';if(btn)btn.disabled=true;
  fetch(API+'/summary',{method:'POST'}).then(function(r){return r.json();}).then(function(d){
    if(d.error)throw new Error(d.error);
    body.textContent=d.summary;body.className='loaded';
    var ts=Date.now();if(meta)meta.textContent='\u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u043e \u0432 '+new Date(ts).toLocaleTimeString('ru-RU',{hour:'2-digit',minute:'2-digit'});
    localStorage.setItem(NEWS_CACHE_KEY,JSON.stringify({text:d.summary,ts:ts}));
  }).catch(function(e){body.textContent='\u041e\u0448\u0438\u0431\u043a\u0430: '+e.message;body.className='error';}).then(function(){if(btn)btn.disabled=false;});
}

function buildWidgets(container){
  var se=document.getElementById('services');
  var row=makeEl('div',{id:'hp-widgets'});
  row.appendChild(buildWeather()); row.appendChild(buildHealth());
  var news=buildNews();
  if(se&&se.parentNode){var p=se.parentNode;p.insertBefore(news,se);p.insertBefore(row,news);}
  else{container.appendChild(row);container.appendChild(news);}
}

function init(){
  if(document.getElementById('hp-header'))return;
  ['information-widgets','information-widgets-right','widgets-wrap'].forEach(function(id){var n=document.getElementById(id);if(n)n.style.display='none';});
  var se=document.getElementById('services');
  var container=se?se.parentNode:document.querySelector('main')||document.body;
  buildHeader(container); buildWidgets(container);
  initWaterfall(); initFireflies(); initCursorGlow(); initParallax();
  loadWeather(); loadHealth(); loadNews(false);
}

window.addEventListener('load',function(){setTimeout(init,300);});
