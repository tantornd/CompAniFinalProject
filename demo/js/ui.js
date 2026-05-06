function setMode(mode) {
  cfg.mode = mode;

  document.getElementById('btnBaseline').className =
    'toggle-btn' + (mode === 'baseline' ? ' active-red' : '');
  document.getElementById('btnXPBD').className =
    'toggle-btn' + (mode === 'xpbd' ? ' active' : '');

  document.getElementById('canvasLabel').textContent =
    mode === 'baseline' ? 'MASS-SPRING BASELINE' : 'XPBD PROPOSED';
  document.getElementById('statMode').textContent =
    mode === 'baseline' ? 'Baseline' : 'XPBD';
  document.getElementById('modeLabel').textContent =
    mode === 'baseline' ? 'MASS-SPRING EXPLICIT EULER' : 'XPBD CONSTRAINT SOLVER';
  document.getElementById('modeDot').className =
    'mode-dot' + (mode === 'baseline' ? ' red' : '');
}

// parameter slider

function updateParam(key, val) {
  cfg[key] = val;
  const labelMap = { dt: 'lblDt', k: 'lblK', wind: 'lblWind', gravity: 'lblGrav' };
  if (labelMap[key]) {
    document.getElementById(labelMap[key]).textContent =
      parseFloat(val).toFixed(key === 'dt' ? 3 : 1);
  }
}

// grid resize

function setGrid(n) {
  cfg.N = n;
  document.getElementById('lblGrid').textContent = n + '×' + n;
  buildSim();
  updateStats();
}

// actions

function resetSim() {
  buildSim();
}

function explode() {
  if (!sim) return;
  for (let p = 0; p < sim.count; p++) {
    if (sim.pinned[p]) continue;
    sim.vel[p * 2]     += (Math.random() - 0.5) * 800;
    sim.vel[p * 2 + 1] += (Math.random() - 0.5) * 800 - 300;
  }
}

// mouse

let dragging = -1;

function initInteraction() {
  canvas.addEventListener('mousedown', e => {
    if (!sim) return;
    const r  = canvas.getBoundingClientRect();
    const mx = (e.clientX - r.left) * (canvas.width  / r.width);
    const my = (e.clientY - r.top)  * (canvas.height / r.height);
    let best = -1, bestD = 30;
    for (let p = 0; p < sim.count; p++) {
      if (sim.pinned[p]) continue;
      const d = Math.hypot(sim.pos[p * 2] - mx, sim.pos[p * 2 + 1] - my);
      if (d < bestD) { bestD = d; best = p; }
    }
    dragging = best;
  });

  canvas.addEventListener('mousemove', e => {
    if (dragging < 0 || !sim) return;
    const r = canvas.getBoundingClientRect();
    sim.pos[dragging * 2]     = (e.clientX - r.left) * (canvas.width  / r.width);
    sim.pos[dragging * 2 + 1] = (e.clientY - r.top)  * (canvas.height / r.height);
    sim.vel[dragging * 2]     = 0;
    sim.vel[dragging * 2 + 1] = 0;
  });

  canvas.addEventListener('mouseup',    () => { dragging = -1; });
  canvas.addEventListener('mouseleave', () => { dragging = -1; });

  // touch passthrough to mouse handlers
  canvas.addEventListener('touchstart', e => {
    e.preventDefault();
    const t = e.touches[0];
    canvas.dispatchEvent(new MouseEvent('mousedown', { clientX: t.clientX, clientY: t.clientY }));
  }, { passive: false });

  canvas.addEventListener('touchmove', e => {
    e.preventDefault();
    const t = e.touches[0];
    canvas.dispatchEvent(new MouseEvent('mousemove', { clientX: t.clientX, clientY: t.clientY }));
  }, { passive: false });

  canvas.addEventListener('touchend', () => { dragging = -1; });
}
