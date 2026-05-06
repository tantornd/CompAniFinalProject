const canvas       = document.getElementById('simCanvas');
const ctx          = canvas.getContext('2d');
const energyCanvas = document.getElementById('energyCanvas');
const ectx         = energyCanvas.getContext('2d');

let cfg = {
  mode:      'baseline',  
  N:         16, // grid dimension
  dt:        0.016,
  k:         400,
  wind:      0.3,
  gravity:   9.8,
  xpbdIter:  8,
};

// runtime state

let sim       = null;
let raf       = null;
let lastTime  = 0;
let fps       = 0;
let simMs     = 0;
let frame     = 0;
let energyLog = { baseline: [], xpbd: [] };

// setup
function buildSim() {
  const W       = canvas.width;
  const H       = canvas.height;
  const clothW  = W * 0.65;
  const clothH  = H * 0.72;
  const originX = (W - clothW) / 2;
  const originY = H * 0.05;

  sim        = new Cloth(cfg.N, clothW, clothH, originX, originY);
  energyLog  = { baseline: [], xpbd: [] };
  frame      = 0;
  updateStats();
}

function updateStats() {
  if (!sim) return;
  document.getElementById('statVerts').textContent = sim.count;
  document.getElementById('statConst').textContent = sim.constraintCount;
}

// main
function loop(ts) {
  raf = requestAnimationFrame(loop);

  // fps smoothing
  const dt2 = ts - lastTime;
  fps       = 0.9 * fps + 0.1 * (1000 / dt2);
  lastTime  = ts;
  frame++;

  // resize
  const rect = canvas.parentElement.getBoundingClientRect();
  if (canvas.width  !== Math.floor(rect.width) ||
      canvas.height !== Math.floor(rect.height)) {
    canvas.width        = Math.floor(rect.width);
    canvas.height       = Math.floor(rect.height);
    energyCanvas.width  = energyCanvas.offsetWidth || 200;
    energyCanvas.height = 100;
    buildSim();
  }

  const t0 = performance.now();
  if (cfg.mode === 'baseline') {
    stepBaseline(sim, cfg.dt, cfg.k, cfg.gravity, cfg.wind);
  } else {
    stepXPBD(sim, cfg.dt, cfg.k, cfg.gravity, cfg.wind, cfg.xpbdIter);
  }
  simMs = 0.8 * simMs + 0.2 * (performance.now() - t0);

  // record energy
  const e = measureEnergy(sim, cfg.k);
  if (isFinite(e) && e < 1e8) energyLog[cfg.mode].push(e);
  if (energyLog[cfg.mode].length > 500) energyLog[cfg.mode].shift();

  const other = cfg.mode === 'baseline' ? 'xpbd' : 'baseline';
  if (energyLog[other].length > 0) {
    const last = energyLog[other][energyLog[other].length - 1];
    energyLog[other].push(last * 0.995);
    if (energyLog[other].length > 500) energyLog[other].shift();
  }

  // draw
  drawCloth(sim, cfg.mode);
  drawEnergyGraph();

  // update every 6 frames
  if (frame % 6 === 0) {
    document.getElementById('fpsBadge').textContent = fps.toFixed(0) + ' FPS';

    const eStr = isFinite(e) && e < 1e8 ? e.toFixed(1) : 'EXPLOSION';
    document.getElementById('statEnergy').textContent = eStr;
    document.getElementById('statMs').textContent     = simMs.toFixed(2) + ' ms';

    const isStable = isFinite(e) && e < 5000;
    const stabEl   = document.getElementById('statStability');
    stabEl.textContent  = isStable ? 'Stable' : 'Unstable';
    stabEl.style.color  = isStable ? '#4fffb0'  : '#ff2f6e';

    document.getElementById('statEnergyRow').className =
      'stat-row ' + (isStable ? 'highlight' : 'bad');
  }
}

canvas.width        = 600;
canvas.height       = 500;
energyCanvas.width  = 200;
energyCanvas.height = 100;

initInteraction();
buildSim();
requestAnimationFrame(loop);
