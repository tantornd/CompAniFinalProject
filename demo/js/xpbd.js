function stepXPBD(cloth, dt, k, gravity, wind, iters) {
  const N          = cloth.count;
  const compliance = 1.0 / (k * dt * dt);
  const est        = new Float32Array(N * 2);

  // predict positions w external forces
  for (let p = 0; p < N; p++) {
    if (cloth.pinned[p]) {
      est[p * 2]     = cloth.pos[p * 2];
      est[p * 2 + 1] = cloth.pos[p * 2 + 1];
      continue;
    }
    const windF    = wind * 2.0 * (0.5 + 0.5 * Math.sin(frame * 0.03 + p * 0.1));
    est[p * 2]     = cloth.pos[p * 2]     + cloth.vel[p * 2]     * dt + windF   * dt * dt;
    est[p * 2 + 1] = cloth.pos[p * 2 + 1] + cloth.vel[p * 2 + 1] * dt + gravity * dt * dt;
  }

  // iterative constraint projection
  const lambdas = new Float32Array(cloth.springs.length);
  for (let iter = 0; iter < iters; iter++) {
    for (let s = 0; s < cloth.springs.length; s++) {
      const [a, b, rest] = cloth.springs[s];
      const dx   = est[b * 2]     - est[a * 2];
      const dy   = est[b * 2 + 1] - est[a * 2 + 1];
      const dist = Math.hypot(dx, dy) || 0.0001;
      const C    = dist - rest;
      const wa   = cloth.pinned[a] ? 0 : 1 / cloth.mass[a];
      const wb   = cloth.pinned[b] ? 0 : 1 / cloth.mass[b];
      const dL   = (-C - compliance * lambdas[s]) / (wa + wb + compliance);
      lambdas[s] += dL;
      const nx = dx / dist, ny = dy / dist;
      if (!cloth.pinned[a]) { est[a * 2] -= wa * dL * nx; est[a * 2 + 1] -= wa * dL * ny; }
      if (!cloth.pinned[b]) { est[b * 2] += wb * dL * nx; est[b * 2 + 1] += wb * dL * ny; }
    }
  }

  // derive velocities + commit position
  const invDt = 1 / dt;
  for (let p = 0; p < N; p++) {
    if (cloth.pinned[p]) continue;
    cloth.vel[p * 2]     = (est[p * 2]     - cloth.pos[p * 2])     * invDt * 0.99;
    cloth.vel[p * 2 + 1] = (est[p * 2 + 1] - cloth.pos[p * 2 + 1]) * invDt * 0.99;
    cloth.pos[p * 2]     = est[p * 2];
    cloth.pos[p * 2 + 1] = est[p * 2 + 1];
  }
}
