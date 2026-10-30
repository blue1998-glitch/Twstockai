'use strict';
// Render the offline adapter's facts and exact pre-serialized downloads only.
const ATTEMPT_DATA = JSON.parse(document.getElementById('attemptData').textContent);
const el = id => document.getElementById(id);
let selected = null, current = null, index = null;
let windowState = {start: 0, end: 0, cursor: 0};
const geometry = {};
const relationLabels = {ABOVE: '高於', BELOW: '低於', AT_LEVEL: '等於'};
const conditionLabels = {MET: '價格子條件成立', NOT_MET: '價格子條件尚未成立', AT_BOUNDARY: '等於關卡，未算超越'};
const volumeLabels = {HIGHER: '高於', LOWER: '低於', EQUAL: '等於', UNKNOWN: '未知'};
const eventLabels = {
  INTRADAY_CROSSED_ABOVE: '盤中已觀察越過', INTRADAY_RETURNED_BELOW: '盤中已觀察跌回',
  INTRADAY_BELOW_LEVEL: '盤中已觀察低於', CLOSE_CROSSED_ABOVE: '完成日收盤越過',
  CLOSE_STILL_ABOVE: '完成日收盤仍高於', CLOSE_RETURNED_BELOW: '完成日收盤跌回',
  CLOSE_BELOW_LEVEL: '完成日收盤低於', CLOSE_AT_LEVEL: '完成日收盤等於關卡',
  VOLUME_LEAD_OBSERVED: '在已提供窗口觀察到量先價支持',
  VOLUME_EXCESS_ORDER_UNKNOWN: '量已超標，量價先後未知',
  VOLUME_EXCESS_PRICE_ALREADY_PASSED: '量超標前價格已越上緣，未記為新量先價'
};
const referenceName = id => id === 'NEAR_HIGH' ? '近期關卡' : id === 'LEFT_ZONE_UPPER' ? '左區上緣' : '左區最高量';

function price(value) {
  if (value === null || value === undefined) return '未知';
  const parts = String(value).match(/^(\d+)(?:\.(\d+))?$/);
  if (!parts) return String(value);
  const fraction = (parts[2] || '') + '000';
  let cents = BigInt(parts[1] + fraction.slice(0, 2));
  if (fraction[2] >= '5') cents++;
  const text = cents.toString().padStart(3, '0');
  return text.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, ',') + '.' + text.slice(-2);
}
const shares = value => value === null ? '未知' : String(value).replace(/\B(?=(\d{3})+(?!\d))/g, ',') + ' 股';
const coordinate = value => value === null || !Number.isFinite(Number(value)) ? null : Number(value);
function node(tag, text) { const n = document.createElement(tag); n.textContent = text; return n; }
function evidence(id, rows, empty) {
  const list = el(id); list.replaceChildren();
  if (!rows.length) list.append(node('li', empty));
  for (const row of rows) {
    const li = node('li', typeof row === 'string' ? row : row.text);
    if (typeof row !== 'string') {
      const details = node('details', '');
      details.append(node('summary', '依據連結'), node('pre', row.references.join('\n')));
      li.append(details);
    }
    list.append(li);
  }
}
function clearResult() {
  current = null; index = null; el('result').hidden = true; el('download').disabled = true;
}
function clearSource() {
  clearResult(); selected = null;
  el('observation').replaceChildren(new Option('請明選時點', ''));
  el('observation').disabled = true; el('loadAttempt').disabled = true;
}
function chooseSource() {
  clearSource();
  if (!el('enableAttempt').checked) return;
  selected = ATTEMPT_DATA.cases.find(c => c.info.id === el('sourceCase').value) || null;
  if (!selected) { el('referenceStatus').textContent = '來源未選，近期關卡與左區來源未知。'; return; }
  const first = selected.views[0], chart = first.chart;
  el('referenceStatus').textContent = '來源檔已明選近期高點 ' + price(chart.near_high.price) + '（' + chart.near_high.bar_date +
    '）；左區 ' + price(chart.left_zone.low) + ' ～ ' + price(chart.left_zone.high) + '，來源日 ' +
    chart.left_zone.bar_dates.join('、') + '。這是來源檔設定，非本頁自動選區；請再明選時點。';
  selected.views.forEach((v, i) => el('observation').append(new Option(v.frame.observed_at + (v.frame.is_close ? '｜完成日' : '｜盤中'), String(i))));
  el('observation').disabled = false;
}
function load(i) {
  if (!el('enableAttempt').checked || !selected || !Number.isInteger(i) || i < 0 || i >= selected.views.length) return;
  current = selected.views[i]; index = i;
  windowState = {start: 0, end: current.chart.daily.length - 1, cursor: current.chart.daily.length - 1};
  el('observation').value = String(i); el('replay').value = String(i); el('replay').max = String(selected.views.length - 1);
  el('previous').disabled = i === 0; el('next').disabled = i === selected.views.length - 1;
  el('result').hidden = false; el('download').disabled = false;
  el('message').textContent = '已讀取該前綴的核心輸出；不使用後來觀察或在瀏覽器重新分析。';
  summary(); draw();
}
function summary() {
  const f = current.frame, c = current.chart, p = current.presentation;
  el('scope').textContent = selected.info.label + ' · ' + selected.info.price_mode + ' · 假想工程來源';
  el('phase').textContent = f.observed_at + (f.is_close ? '｜完成日收盤' : '｜盤中截面，收盤未知');
  el('coverage').textContent = '僅有 ' + c.daily[0].date + ' ～ ' + f.bar_date + ' 明列片段；當時 ' + c.daily.length +
    ' 根 K，非完整交易日曆。近期關卡及左區來源均為來源檔明選；共同基底尚未經市場認證。';
  const levels = el('attemptLevels'); levels.replaceChildren();
  for (const level of f.attempt_levels) {
    const card = node('article', ''); card.dataset.reference = level.reference_id;
    card.append(node('h3', referenceName(level.reference_id) + ' ' + price(level.price)),
      node('p', conditionLabels[level.price_attempt_condition]),
      node('p', '當時價格 ' + price(f.current_price) + '，' + relationLabels[level.relation] + '參照。'),
      node('p', '最新已完成日收盤：' + relationLabels[level.latest_completed_close_relation] + '此關卡。'));
    card.append(node('p', level.reference_id === 'NEAR_HIGH' ? '這個嘗試不要求先越過左區上緣，也不要求先有量先價。' :
      '這是另一個嘗試；量能支持不能替代價格實際超越。'));
    levels.append(card);
  }
  el('volumeNumbers').textContent = (f.is_close ? '本日完成量 ' : '截至觀察時點累計量 ') + shares(f.volume_shares) +
    '；指定左區最高全日量 ' + shares(f.left_zone_max_volume_shares) + '；核心比較：' + volumeLabels[f.volume_relation] + '。';
  el('volumeText').textContent = p.volume_text;
  el('leadHistory').textContent = p.volume_lead_first_observed_at.length ? '歷史支持首次看到於：' + p.volume_lead_first_observed_at.join('、') +
    '。歷史存在不代表支持永久有效。' : '截至這個時點，沒有已保存的量先價證據。';
  evidence('supporting', p.supporting, '目前沒有可列的支持子條件。');
  evidence('opposing', p.opposing, '此前綴尚無已保存的跌回事件，不代表沒有其他風險。');
  evidence('missing', p.missing, '無');
  el('replayStatus').textContent = '觀察 ' + (index + 1) + '／' + selected.views.length + ' · ' + f.observed_at +
    '；普通價格兩位小數，條件及下載保留原精度。';
  const events = el('events'); events.replaceChildren();
  for (const event of current.events) {
    const row = node('article', ''); row.className = 'event'; row.dataset.kind = event.kind;
    row.append(node('p', referenceName(event.reference_id) + ' · ' + (eventLabels[event.kind] || event.kind)),
      node('p', '首次觀察 ' + event.first_observed_at + '；確認 ' + (event.confirmed_at || '未知／尚未完成') + '；發生時刻未知。'));
    const details = node('details', ''); details.append(node('summary', '原事件及精度'), node('pre', JSON.stringify(event, null, 2)));
    row.append(details); events.append(row);
  }
  if (!current.events.length) events.append(node('p', '本前綴沒有新增事件，不補造觸發。'));
  el('qualification').textContent = '核心 ' + ATTEMPT_DATA.core_version + '；畫面接入 ' + ATTEMPT_DATA.adapter_version +
    '。分類 NOT_VALIDATED，完整交易資格 NOT_EVALUATED，強勢延續 NOT_CLASSIFIED，勝率未知。';
  el('references').textContent = current.reference_details; el('context').textContent = current.context_details;
  el('lineage').textContent = current.lineage;
  // Preserve original arbitrary-size integers without parsing/re-serializing.
  el('exactSource').textContent = current.selection_text;
}

function setup(id, extent, startLabel, endLabel) {
  const canvas = el(id), box = canvas.getBoundingClientRect(), dpr = devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.round(box.width * dpr)); canvas.height = Math.max(1, Math.round(box.height * dpr));
  const ctx = canvas.getContext('2d'); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, box.width, box.height);
  const g = {ctx, canvas, width: box.width, height: box.height, left: 66, right: box.width - 12, top: 16, bottom: box.height - 30};
  const span = extent[1] - extent[0] || 1;
  g.y = value => g.bottom - (value - extent[0]) / span * (g.bottom - g.top);
  g.step = (g.right - g.left) / (windowState.end - windowState.start + 1);
  g.x = i => g.left + (i - windowState.start + .5) * g.step;
  ctx.font = '11px system-ui'; ctx.textBaseline = 'middle'; ctx.textAlign = 'right';
  for (let i = 0; i < 4; i++) {
    const value = extent[0] + span * i / 3, y = g.y(value);
    ctx.strokeStyle = '#dce7eb'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(g.left, y); ctx.lineTo(g.right, y); ctx.stroke();
    ctx.fillStyle = '#56717c';
    ctx.fillText(id === 'volume' ? Math.round(value).toLocaleString('en-US') : price(value.toFixed(2)), g.left - 6, y, 60);
  }
  ctx.textAlign = 'left'; ctx.fillText(startLabel, g.left, g.height - 10);
  ctx.textAlign = 'right'; ctx.fillText(endLabel, g.right, g.height - 10);
  ctx.save(); ctx.beginPath(); ctx.rect(g.left, g.top, g.right - g.left, g.bottom - g.top); ctx.clip();
  geometry[id] = g; return g;
}
function referenceLines(g) {
  const refs = current.chart;
  g.ctx.fillStyle = '#be93221a';
  g.ctx.fillRect(g.left, g.y(Number(refs.left_zone.high)), g.right - g.left, g.y(Number(refs.left_zone.low)) - g.y(Number(refs.left_zone.high)));
  for (const [value, color] of [[refs.near_high.price, '#b07514'], [refs.left_zone.high, '#7964a1']]) {
    g.ctx.strokeStyle = color; g.ctx.lineWidth = 1; g.ctx.setLineDash([5, 4]);
    g.ctx.beginPath(); g.ctx.moveTo(g.left, g.y(Number(value))); g.ctx.lineTo(g.right, g.y(Number(value))); g.ctx.stroke();
  }
  g.ctx.setLineDash([]);
}
function crosshair(g) {
  g.ctx.strokeStyle = '#537987'; g.ctx.setLineDash([3, 3]);
  g.ctx.beginPath(); g.ctx.moveTo(g.x(windowState.cursor), g.top); g.ctx.lineTo(g.x(windowState.cursor), g.bottom); g.ctx.stroke();
  g.ctx.setLineDash([]); g.ctx.restore();
}
function draw() {
  if (!current) return;
  const chart = current.chart, rows = chart.daily, start = windowState.start, end = windowState.end;
  const values = rows.slice(start, end + 1).flatMap(r => [coordinate(r.low), coordinate(r.high)]).filter(v => v !== null);
  values.push(Number(chart.near_high.price), Number(chart.left_zone.low), Number(chart.left_zone.high));
  let low = Math.min(...values), high = Math.max(...values), pad = Math.max((high - low) * .08, .01);
  const daily = setup('daily', [low - pad, high + pad], rows[start].date, rows[end].date); referenceLines(daily);
  for (let i = start; i <= end; i++) {
    const r = rows[i], x = daily.x(i), width = Math.max(1, Math.min(18, daily.step * .6));
    if (chart.left_zone.bar_dates.includes(r.date)) {
      daily.ctx.fillStyle = '#4b9ac116'; daily.ctx.fillRect(x - daily.step / 2, daily.top, daily.step, daily.bottom - daily.top);
    }
    if ([r.open, r.high, r.low, r.close].some(v => coordinate(v) === null)) continue;
    const color = Number(r.close) >= Number(r.open) ? '#c84646' : '#18835c';
    daily.ctx.strokeStyle = color; daily.ctx.fillStyle = color;
    daily.ctx.beginPath(); daily.ctx.moveTo(x, daily.y(Number(r.high))); daily.ctx.lineTo(x, daily.y(Number(r.low))); daily.ctx.stroke();
    const y = Math.min(daily.y(Number(r.open)), daily.y(Number(r.close))), height = Math.max(1, Math.abs(daily.y(Number(r.open)) - daily.y(Number(r.close))));
    if (r.is_close) daily.ctx.fillRect(x - width / 2, y, width, height);
    else { daily.ctx.setLineDash([3, 2]); daily.ctx.strokeRect(x - width / 2, y, width, height); daily.ctx.setLineDash([]); }
    if (r.date === chart.near_high.bar_date) {
      daily.ctx.fillStyle = '#b07514'; daily.ctx.beginPath(); daily.ctx.arc(x, daily.y(Number(chart.near_high.price)), 4, 0, Math.PI * 2); daily.ctx.fill();
    }
  }
  crosshair(daily);
  const volumeValues = rows.slice(start, end + 1).map(r => coordinate(r.volume_shares)).filter(v => v !== null);
  const volume = setup('volume', [0, Math.max(1, ...volumeValues, coordinate(chart.volume_benchmark) || 0) * 1.08], rows[start].date, rows[end].date);
  if (chart.volume_benchmark !== null) {
    volume.ctx.strokeStyle = '#7964a1'; volume.ctx.setLineDash([5, 3]);
    volume.ctx.beginPath(); volume.ctx.moveTo(volume.left, volume.y(Number(chart.volume_benchmark))); volume.ctx.lineTo(volume.right, volume.y(Number(chart.volume_benchmark))); volume.ctx.stroke(); volume.ctx.setLineDash([]);
  }
  for (let i = start; i <= end; i++) {
    const r = rows[i], value = coordinate(r.volume_shares); if (value === null) continue;
    const x = volume.x(i), width = Math.max(1, Math.min(22, volume.step * .65));
    volume.ctx.fillStyle = r.is_close ? '#477f92' : '#b07514';
    volume.ctx.fillRect(x - width / 2, volume.y(value), width, Math.max(1, volume.bottom - volume.y(value)));
  }
  crosshair(volume);
  const points = chart.intraday.points;
  el('intradayStatus').textContent = chart.intraday.status === 'INTRADAY_DATA_MISSING' ?
    '盤中資料缺少：只呈現已提供完成日K／量，不由日OHLC編造盤中次序。' :
    '僅連接已提供觀察點，不是逐筆成交或兩點間實際路徑；沒有較晚的點。';
  const pointValues = points.map(p => Number(p.price)).concat([Number(chart.near_high.price), Number(chart.left_zone.low), Number(chart.left_zone.high)]);
  const intraday = setup('intraday', [Math.min(...pointValues) - pad, Math.max(...pointValues) + pad],
    points.length ? points[0].observed_at.slice(11, 16) : '', points.length > 1 ? points.at(-1).observed_at.slice(11, 16) : '');
  if (points.length) {
    referenceLines(intraday);
    const firstTime = Date.parse(points[0].observed_at), span = Date.parse(points.at(-1).observed_at) - firstTime;
    intraday.px = i => span ? intraday.left + 8 + (Date.parse(points[i].observed_at) - firstTime) / span * (intraday.right - intraday.left - 16) : (intraday.left + intraday.right) / 2;
    intraday.ctx.strokeStyle = '#17677b'; intraday.ctx.lineWidth = 2; intraday.ctx.beginPath();
    points.forEach((p, i) => { if (i) intraday.ctx.lineTo(intraday.px(i), intraday.y(Number(p.price))); else intraday.ctx.moveTo(intraday.px(i), intraday.y(Number(p.price))); });
    intraday.ctx.stroke();
    points.forEach((p, i) => { intraday.ctx.fillStyle = p.is_close ? '#17677b' : '#b07514'; intraday.ctx.beginPath(); intraday.ctx.arc(intraday.px(i), intraday.y(Number(p.price)), 4, 0, Math.PI * 2); intraday.ctx.fill(); });
    el('intradayCursor').textContent = '最後已提供點 ' + points.at(-1).observed_at + ' · 價格 ' + price(points.at(-1).price);
  } else {
    intraday.ctx.fillStyle = '#526e78'; intraday.ctx.font = '14px system-ui'; intraday.ctx.textAlign = 'center';
    intraday.ctx.fillText('盤中資料缺少', (intraday.left + intraday.right) / 2, (intraday.top + intraday.bottom) / 2);
    el('intradayCursor').textContent = '沒有可定位的盤中觀察點。';
  }
  intraday.ctx.restore();
  const r = rows[windowState.cursor];
  el('cursorValues').textContent = '日K／量共同游標 ' + r.date + (r.is_close ? '｜完成日' : '｜當時未完成K') +
    '\nO ' + price(r.open) + ' / H ' + price(r.high) + ' / L ' + price(r.low) + ' / ' + (r.is_close ? 'C ' : '現價 ') + price(r.close) +
    '；量 ' + shares(r.volume_shares) + '\n首次提供時間 ' + r.known_at;
  el('range').textContent = '目前視窗 ' + rows[start].date + ' ～ ' + rows[end].date + '，' + (end - start + 1) +
    ' 根；本時點全部已提供 ' + rows.length + ' 根，左側未列日期仍未知。縮放不改分析或下載。';
}
function setRange(start, count) {
  if (!current) return;
  const total = current.chart.daily.length;
  count = Math.max(1, Math.min(total, Math.round(count)));
  start = Math.max(0, Math.min(total - count, Math.round(start)));
  windowState.start = start; windowState.end = start + count - 1;
  windowState.cursor = Math.max(start, Math.min(windowState.end, windowState.cursor)); draw();
}
function zoom(factor) {
  const count = windowState.end - windowState.start + 1, newCount = Math.max(1, Math.round(count * factor));
  setRange((windowState.start + windowState.end + 1 - newCount) / 2, newCount);
}
el('enableAttempt').addEventListener('change', () => {
  clearSource(); el('sourceCase').value = ''; el('sourceCase').disabled = !el('enableAttempt').checked;
  el('referenceStatus').textContent = el('enableAttempt').checked ? '請明選來源；不自選關卡或最新時點。' : '已停用；不保留先前來源或判斷。';
});
el('sourceCase').addEventListener('change', chooseSource);
el('observation').addEventListener('change', () => { clearResult(); el('loadAttempt').disabled = !selected || el('observation').value === ''; });
el('loadAttempt').addEventListener('click', () => { if (el('observation').value !== '') load(Number(el('observation').value)); });
el('previous').addEventListener('click', () => load(index - 1)); el('next').addEventListener('click', () => load(index + 1));
el('replay').addEventListener('input', () => load(Number(el('replay').value)));
el('zoomIn').addEventListener('click', () => zoom(.6)); el('zoomOut').addEventListener('click', () => zoom(1.8));
el('left').addEventListener('click', () => setRange(windowState.start - 1, windowState.end - windowState.start + 1));
el('right').addEventListener('click', () => setRange(windowState.start + 1, windowState.end - windowState.start + 1));
el('reset').addEventListener('click', () => setRange(0, current.chart.daily.length));
for (const id of ['daily', 'volume']) {
  const locate = event => {
    if (!current) return;
    const r = el(id).getBoundingClientRect(), g = geometry[id];
    windowState.cursor = Math.max(windowState.start, Math.min(windowState.end, Math.floor(windowState.start + (event.clientX - r.left - g.left) / g.step))); draw();
  };
  el(id).addEventListener('pointerdown', locate);
  el(id).addEventListener('pointermove', event => { if (event.pointerType === 'mouse') locate(event); });
}
el('intraday').addEventListener('pointerdown', event => {
  if (!current || !current.chart.intraday.points.length) return;
  const g = geometry.intraday, x = event.clientX - el('intraday').getBoundingClientRect().left;
  const points = current.chart.intraday.points;
  let nearest = 0;
  for (let i = 1; i < points.length; i++) if (Math.abs(g.px(i) - x) < Math.abs(g.px(nearest) - x)) nearest = i;
  el('intradayCursor').textContent = '已提供觀察點 ' + points[nearest].observed_at + ' · 價格 ' + price(points[nearest].price) +
    (points[nearest].is_close ? '｜完成日' : '｜盤中');
});
function focusMode() {
  document.body.classList.toggle('focus'); el('exitFocus').hidden = !document.body.classList.contains('focus');
  el('fullscreenStatus').textContent = document.body.classList.contains('focus') ? '頁內專注模式，未進入瀏覽器原生全螢幕。' : '已退出專注模式。'; draw();
}
el('full').addEventListener('click', async () => {
  if (document.fullscreenElement) { await document.exitFullscreen(); return; }
  if (document.body.classList.contains('focus')) { focusMode(); return; }
  try { if (!el('charts').requestFullscreen) throw Error('unsupported'); await el('charts').requestFullscreen(); }
  catch { focusMode(); }
});
el('exitFocus').addEventListener('click', async () => { if (document.fullscreenElement) await document.exitFullscreen(); else if (document.body.classList.contains('focus')) focusMode(); });
document.addEventListener('fullscreenchange', () => {
  el('exitFocus').hidden = !document.fullscreenElement;
  el('fullscreenStatus').textContent = document.fullscreenElement ? '瀏覽器原生全螢幕。' : '已退出全螢幕。'; draw();
});
document.addEventListener('keydown', event => { if (event.key === 'Escape' && document.body.classList.contains('focus')) focusMode(); });
el('download').addEventListener('click', () => {
  if (!current) return;
  const url = URL.createObjectURL(new Blob([current.selection_text], {type: 'application/json'}));
  const a = document.createElement('a'); a.href = url;
  a.download = 'SYNTHETIC_' + selected.info.id + '_' + String(index + 1) + '_attempt_candidate.json';
  document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
});
window.addEventListener('resize', () => { if (current) draw(); });
for (const c of ATTEMPT_DATA.cases) el('sourceCase').append(new Option(c.info.label, c.info.id));
