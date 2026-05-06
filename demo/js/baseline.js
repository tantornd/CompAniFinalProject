function stepBaseline(cloth, dt, k, gravity, wind) {
  const forces = new Float32Array(cloth.count * 2);

  // external forces
  for (let p = 0; p < cloth.count; p++) {
    if (cloth.pinned[p]) continue;
    forces[p * 2]     += wind * 2.0 * (0.5 + 0.5 * Math.sin(frame * 0.03 + p * 0.1));
    forces[p * 2 + 1] += gravity * cloth.mass[p];
  }

  // Hooke's law
  for (const [a, b, rest] of cloth.springs) {
    const ax = cloth.pos[a * 2], ay = cloth.pos[a * 2 + 1];
    const bx = cloth.pos[b * 2], by = cloth.pos[b * 2 + 1];
    const dx = bx - ax, dy = by - ay;
    const dist = Math.hypot(dx, dy) || 0.0001;
    const f = k * (dist - rest) / dist;
    if (!cloth.pinned[a]) { forces[a * 2] += f * dx; forces[a * 2 + 1] += f * dy; }
    if (!cloth.pinned[b]) { forces[b * 2] -= f * dx; forces[b * 2 + 1] -= f * dy; }
  }

  // Euler integration + velocity damping
  const damp = 0.985;
  for (let p = 0; p < cloth.count; p++) {
    if (cloth.pinned[p]) continue;
    const m = cloth.mass[p];
    cloth.vel[p * 2]     = (cloth.vel[p * 2]     + dt * forces[p * 2]     / m) * damp;
    cloth.vel[p * 2 + 1] = (cloth.vel[p * 2 + 1] + dt * forces[p * 2 + 1] / m) * damp;
    cloth.pos[p * 2]     += dt * cloth.vel[p * 2];
    cloth.pos[p * 2 + 1] += dt * cloth.vel[p * 2 + 1];
  }
}

function measureEnergy(cloth, k) {
  let pe = 0;
  for (const [a, b, rest] of cloth.springs) {
    const dx   = cloth.pos[b * 2]     - cloth.pos[a * 2];
    const dy   = cloth.pos[b * 2 + 1] - cloth.pos[a * 2 + 1];
    const dist = Math.hypot(dx, dy);
    pe += 0.5 * k * (dist - rest) ** 2;
  }

  let ke = 0;
  for (let p = 0; p < cloth.count; p++) {
    if (cloth.pinned[p]) continue;
    ke += 0.5 * cloth.mass[p] * (cloth.vel[p * 2] ** 2 + cloth.vel[p * 2 + 1] ** 2);
  }

  return (pe + ke) / cloth.count;
}
