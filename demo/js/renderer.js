function drawCloth(cloth, mode) {
  const W      = canvas.width;
  const H      = canvas.height;
  const N      = cloth.N;
  const isXPBD = mode === 'xpbd';

  ctx.clearRect(0, 0, W, H);

  ctx.fillStyle = '#030305';
  ctx.fillRect(0, 0, W, H);

  const t = frame * 0.008;
  for (let i = 0; i < 3; i++) {
    const gx = W * (0.2 + 0.3 * Math.sin(t + i * 2.1));
    const gy = H * (0.3 + 0.3 * Math.cos(t * 0.7 + i * 1.5));
    const grad = ctx.createRadialGradient(gx, gy, 0, gx, gy, H * 0.4);
    grad.addColorStop(0, `rgba(${i === 0 ? '80,20,120' : i === 1 ? '20,40,100' : '60,10,80'},0.07)`);
    grad.addColorStop(1, 'transparent');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, W, H);
  }

  // cloth face fill
  for (let j = 0; j < N - 1; j++) {
    for (let i = 0; i < N - 1; i++) {
      const tl = j * N + i, tr = j * N + i + 1;
      const bl = (j + 1) * N + i, br = (j + 1) * N + i + 1;
      const alpha = 0.12 + 0.08 * (j / N);
      ctx.fillStyle = isXPBD
        ? `rgba(100,150,255,${alpha})`
        : `rgba(160,80,255,${alpha})`;

      ctx.beginPath();
      ctx.moveTo(cloth.pos[tl * 2], cloth.pos[tl * 2 + 1]);
      ctx.lineTo(cloth.pos[tr * 2], cloth.pos[tr * 2 + 1]);
      ctx.lineTo(cloth.pos[bl * 2], cloth.pos[bl * 2 + 1]);
      ctx.closePath();
      ctx.fill();

      ctx.beginPath();
      ctx.moveTo(cloth.pos[tr * 2], cloth.pos[tr * 2 + 1]);
      ctx.lineTo(cloth.pos[br * 2], cloth.pos[br * 2 + 1]);
      ctx.lineTo(cloth.pos[bl * 2], cloth.pos[bl * 2 + 1]);
      ctx.closePath();
      ctx.fill();
    }
  }

  // cloth edge lines
  ctx.lineWidth = 0.7;
  const t2 = frame * 0.02;
  for (let j = 0; j < N; j++) {
    for (let i = 0; i < N; i++) {
      const p     = j * N + i;
      const x     = cloth.pos[p * 2];
      const y     = cloth.pos[p * 2 + 1];
      const pulse = 0.5 + 0.5 * Math.sin(t2 + j * 0.4 + i * 0.3);
      const edgeColor = isXPBD
        ? `rgba(100,160,255,${0.3 + 0.15 * pulse})`
        : `rgba(180,100,255,${0.25 + 0.12 * pulse})`;

      if (i + 1 < N) {
        const q = j * N + i + 1;
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(cloth.pos[q * 2], cloth.pos[q * 2 + 1]);
        ctx.strokeStyle = edgeColor;
        ctx.stroke();
      }
      if (j + 1 < N) {
        const q = (j + 1) * N + i;
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(cloth.pos[q * 2], cloth.pos[q * 2 + 1]);
        ctx.strokeStyle = edgeColor;
        ctx.stroke();
      }
    }
  }

  // pin top edge
  for (let i = 0; i < N; i++) {
    const x = cloth.pos[i * 2];
    const y = cloth.pos[i * 2 + 1];
    const g = ctx.createRadialGradient(x, y, 0, x, y, 12);
    g.addColorStop(0, isXPBD ? 'rgba(80,160,255,0.8)' : 'rgba(200,80,255,0.8)');
    g.addColorStop(1, 'transparent');
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.arc(x, y, 12, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.arc(x, y, 3, 0, Math.PI * 2);
    ctx.fillStyle = '#fff'; ctx.fill();
  }

  // bottom
  const mid = Math.floor(N / 2);
  const bot = (N - 1) * N + mid;
  const bx  = cloth.pos[bot * 2];
  const by  = cloth.pos[bot * 2 + 1];
  const faceAlpha = 0.05 + 0.04 * Math.sin(frame * 0.04);
  const fr = ctx.createRadialGradient(bx, by, 0, bx, by, 50);
  fr.addColorStop(0, `rgba(200,220,255,${faceAlpha})`);
  fr.addColorStop(1, 'transparent');
  ctx.fillStyle = fr;
  ctx.beginPath(); ctx.arc(bx, by, 50, 0, Math.PI * 2); ctx.fill();
}

function drawEnergyGraph() {
  const W = energyCanvas.width;
  const H = energyCanvas.height;

  ectx.clearRect(0, 0, W, H);
  ectx.fillStyle = 'rgba(0,0,0,0.4)';
  ectx.fillRect(0, 0, W, H);

  const maxLen  = 120;
  const bl      = energyLog.baseline.slice(-maxLen);
  const xp      = energyLog.xpbd.slice(-maxLen);
  const allVals = [...bl, ...xp].filter(v => isFinite(v) && v < 1e8);
  if (allVals.length < 2) return;

  const maxV = Math.max(...allVals) || 1;

  const drawLine = (data, color) => {
    if (data.length < 2) return;
    ectx.beginPath();
    ectx.strokeStyle = color;
    ectx.lineWidth   = 1.5;
    for (let i = 0; i < data.length; i++) {
      const x = (i / (maxLen - 1)) * W;
      const y = H - (Math.min(data[i], maxV) / maxV) * (H - 4) - 2;
      i === 0 ? ectx.moveTo(x, y) : ectx.lineTo(x, y);
    }
    ectx.stroke();
  };

  drawLine(bl, '#ff2f6e');
  drawLine(xp, '#7b2fff');
}
