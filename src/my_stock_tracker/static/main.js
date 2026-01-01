// Client logic: fetch chart and analysis, render with Lightweight Charts
(function(){
  const ALLOWED_RANGES = ['1m','5m','15m','1h','4h','1d'];
  let currentSymbol = null;

  const themeToggle = document.getElementById('themeToggle');
  const pageBody = document.getElementById('page-body');
  if (themeToggle) {
    themeToggle.addEventListener('change', ()=>{
      if(themeToggle.checked) pageBody.classList.add('dark'); else pageBody.classList.remove('dark');
    });
  }

  const form = document.getElementById('searchForm');
  if (form) {
    form.addEventListener('submit', async (e)=>{
      e.preventDefault();
      const sym = document.getElementById('symbolInput').value.trim();
      if(!sym) return;
      currentSymbol = sym;
      const range = document.getElementById('rangeSelect').value;
      if(!ALLOWED_RANGES.includes(range)){
        alert('טווח לא נתמך');
        return;
      }
      await loadChart(sym, range);
      await loadAnalysis(sym, range);
    });
  }

  async function loadChart(sym, range){
    const res = await fetch(`/api/stock/${sym}/chart?range=${range}`);
    if(!res.ok){ alert('שגיאה בטעינת נתונים'); return; }
    const js = await res.json();
    const data = js.data.map(d=>({time: d.time, open: d.open, high: d.high, low: d.low, close: d.close}));
    const script = document.createElement('script');
    script.src = 'https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js';
    script.onload = ()=>{
      const chart = LightweightCharts.createChart(document.getElementById('chart'), {layout: {textColor: '#000', background: {color: 'transparent'}}});
      const candleSeries = chart.addCandlestickSeries();
      candleSeries.setData(data);
    };
    document.head.appendChild(script);
  }

  async function loadAnalysis(sym, range){
    const res = await fetch(`/api/stock/${sym}/analysis?range=${range}`);
    if(!res.ok){ document.getElementById('indicatorsContent').innerText = 'שגיאה בטעינת ניתוח'; return; }
    const a = await res.json();
    const html = [];
    html.push(`<strong>ציון כללי:</strong> ${a.score} — <em>${a.recommendation}</em>`);
    html.push('<ul>');
    for(const n of a.notes) html.push(`<li>${n}</li>`);
    html.push('</ul>');
    html.push('<h6>פרטים</h6>');
    html.push('<table class="table table-sm">');
    html.push(`<tr><th>SMA10</th><td>${a.sma10 ?? '-'}</td></tr>`);
    html.push(`<tr><th>SMA50</th><td>${a.sma50 ?? '-'}</td></tr>`);
    html.push(`<tr><th>EMA20</th><td>${a.ema20 ?? '-'}</td></tr>`);
    html.push(`<tr><th>RSI</th><td>${a.rsi ?? '-'}</td></tr>`);
    html.push('</table>');
    document.getElementById('indicatorsContent').innerHTML = html.join('');
    document.getElementById('scoreBox').innerText = 'ציון מניה: ' + a.score;
  }
})();
