class Cloth {
  constructor(N, W, H, originX, originY) {
    this.N     = N;
    this.count = N * N;
    this.pos    = new Float32Array(N * N * 2);
    this.prev   = new Float32Array(N * N * 2);
    this.vel    = new Float32Array(N * N * 2);
    this.mass   = new Float32Array(N * N).fill(1);
    this.pinned = new Uint8Array(N * N);
    this.springs = [];
    this.W = W;
    this.H = H;

    const dx = W / (N - 1);
    const dy = H / (N - 1);

    for (let j = 0; j < N; j++) {
      for (let i = 0; i < N; i++) {
        const idx = (j * N + i) * 2;
        this.pos[idx]     = originX + i * dx;
        this.pos[idx + 1] = originY + j * dy;
        this.prev[idx]    = this.pos[idx];
        this.prev[idx + 1] = this.pos[idx + 1];
      }
    }
    
    for (let i = 0; i < N; i++) {
      this.pinned[i] = 1;
      this.mass[i]   = Infinity;
    }

    this._buildSprings();
    this.constraintCount = this.springs.length;
  }

  _buildSprings() {
    const N   = this.N;
    const pos = this.pos;

    const add = (a, b) => {
      const ax = pos[a * 2], ay = pos[a * 2 + 1];
      const bx = pos[b * 2], by = pos[b * 2 + 1];
      this.springs.push([a, b, Math.hypot(bx - ax, by - ay)]);
    };

    for (let j = 0; j < N; j++) {
      for (let i = 0; i < N; i++) {
        if (i + 1 < N) add(j * N + i, j * N + i + 1);            // horizontal structural
        if (j + 1 < N) add(j * N + i, (j + 1) * N + i);         // vertical structural
        if (i + 1 < N && j + 1 < N) {                             // diagonal shear
          add(j * N + i,     (j + 1) * N + i + 1);
          add(j * N + i + 1, (j + 1) * N + i);
        }
        if (i + 2 < N) add(j * N + i, j * N + i + 2);            // horizontal bend
        if (j + 2 < N) add(j * N + i, (j + 2) * N + i);         // vertical bend
      }
    }
  }
}
