# Cloth Simulation - Mass-Spring vs XPBD

**วิชา:** Computer Animation (2110512)  
**ภาคการศึกษา:** เทอมปลาย 2568  
**GitHub:** *tantornd*  
**Keywords:** Cloth Simulation, Position-Based Dynamics, XPBD, Mass-Spring, Real-time Animation

---

## Problem

Cloth simulation is fundamental to character animation be it cloaks, flags, and ghostly shrouds all require realistic deformable fabric behaviour. The classic **Mass-Spring** model is simple to implement but **numerically unstable** at large timesteps and high stiffness values: the simulation diverges and explodes, producing visible jitter and oscillation artifacts. This instability forces the use of very small timesteps (dt ≤ 0.005 s), making real-time simulation at physically accurate stiffness values impractical.

---

## Approach

- **Baseline:** Mass-Spring System with explicit Euler integration: spring forces computed via Hooke's law, integrated forward each step. Simple but conditionally stable (CFL bound: dt < √(2m/k)).
- **Proposed:** Extended Position-Based Dynamics (XPBD): replaces force integration with iterative constraint projection in position space. Compliance parameter α = 1/(k·dt²) decouples stiffness from timestep, achieving **unconditional stability**.

| | Baseline (Mass-Spring) | Proposed (XPBD) |
|---|---|---|
| Integration | Explicit Euler | Position-based constraint projection |
| Stability | Conditional (CFL bound) | Unconditional |
| Max usable dt | ~0.005 s | 0.033 s (30 FPS) |
| Complexity | O(n) per step | O(n · iterations) per step |
| Visual quality | Jitter at high stiffness | Smooth, controllable |

---

## Results

| Metric | Baseline | Proposed |
|---|---|---|
| Speedup (net, real-time) | - | **~6× larger usable timestep** |
| Runtime per step | 11.667 ms (16×16) | 82.767 ms (16×16) |
| Stability Improvement | Explodes at k≥800, dt=0.033 s | Stable at k=1200, dt=0.033 s |
| Energy error (dt=0.016, k=400) | 498.58 | 489.68 **(+1.8% improvement)** |
| Max stable timestep | 0.005 s | 0.033 s **(6× larger)** |
| Stable frames (300 total) | 300/300 at safe settings | 300/300 at all tested settings |

> At safe settings both algorithms are stable and the energy difference is small.
> The key advantage of XPBD is that it **remains stable** at timestep/stiffness values
> that cause the baseline to diverge immediately.

---

## How to Run

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Run the offline simulation** (generates energy logs and position data):
```bash
python src/main.py
```

Optional arguments:
```bash
python src/main.py --N 16 --frames 300 --dt 0.016 --k 400
python src/main.py --dt 0.033 --k 900   # stress-test: baseline will explode
```

**Run the scaling benchmark** (regenerates `experiments/results/runtime.csv` and `plots.png`):
```bash
python experiments/benchmark.py
```

**Animate and visualise results** (requires running `src/main.py` first):
```bash
# Display interactively
python visualization/animate_results.py

# Save as GIF + energy plot PNG
python visualization/animate_results.py --save
```
Output files: `experiments/results/animation.gif`, `experiments/results/energy_comparison.png`

**Run the interactive browser demo** - open directly, no server needed:
```
demo/index.html
```

**Run tests:**
```bash
pytest tests/test_simulation.py -v
```
