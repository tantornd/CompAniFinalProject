# Cloth Simulation — Interactive Browser Demo

Open `index.html` directly in any modern browser.

## Controls

| Control | Effect |
|---|---|
| **Algorithm** toggle | Switch between Mass-Spring Baseline and XPBD Proposed in real-time |
| **Timestep (Δt)** slider | Increase to expose baseline instability at large steps |
| **Stiffness** slider | High values cause baseline to explode; XPBD remains stable |
| **Wind** slider | Animated lateral force on the cloth |
| **Gravity** slider | Downward acceleration |
| **Grid Size** slider | 8×8 → 28×28 (64 – 784 vertices) |
| **↺ Reset Cloth** | Reinitialise cloth to rest position |
| **Chaos Blast** | Apply a random velocity impulse to stress-test stability |
| **Drag** on cloth | Click-drag any free vertex to interact |

## What to observe

1. Set Stiffness to **1000+** and Timestep to **0.030s**, then switch to Baseline and watch it explode.  
   Switch to XPBD at the same settings and it remains stable.

2. The **Energy Error** graph (right panel) shows real time total mechanical energy.  
   Baseline oscillates wildly; XPBD converges smoothly.

3. Increase Grid Size to stress-test rendering performance (the simulation stays smooth).