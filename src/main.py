import argparse
import sys
import os
import time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.data_structures.constraint_graph import ClothMesh
from src.algorithms import baseline, proposed

def run_simulation(mode: str, N: int, frames: int, dt: float,
                   stiffness: float, gravity: float, wind: float):
    mesh = ClothMesh(N, width=1.0, height=1.0)

    energy_log    = np.zeros(frames)
    positions_log = np.zeros((frames, N * N, 2))

    step_fn = baseline.step_vectorized if mode == "baseline" else proposed.step_vectorized

    t0 = time.perf_counter()
    for f in range(frames):
        kwargs = dict(dt=dt, stiffness=stiffness, gravity=gravity, wind=wind, frame=f)
        if mode == "xpbd":
            kwargs["iterations"] = 8
        step_fn(mesh, **kwargs)

        energy_log[f]     = mesh.total_energy(stiffness)
        positions_log[f]  = mesh.positions.copy()

    elapsed = time.perf_counter() - t0
    return energy_log, positions_log, elapsed

def main():
    parser = argparse.ArgumentParser(description="Cloth Simulation engine")
    parser.add_argument("--N",       type=int,   default=16,    help="Grid dimension NxN")
    parser.add_argument("--frames",  type=int,   default=300,   help="Frames to simulate")
    parser.add_argument("--dt",      type=float, default=0.016, help="Timestep (seconds)")
    parser.add_argument("--k",       type=float, default=400.0, help="Spring stiffness")
    parser.add_argument("--gravity", type=float, default=9.8,   help="Gravity (m/s²)")
    parser.add_argument("--wind",    type=float, default=0.3,   help="Wind magnitude")
    parser.add_argument("--out",     type=str,   default="experiments/results",
                        help="Output directory for results")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    print(f"Cloth Simulation  N={args.N}  frames={args.frames}  dt={args.dt}  k={args.k}")
    print("-" * 60)

    results = {}
    for mode in ("baseline", "xpbd"):
        print(f"Running {mode}...", end=" ", flush=True)
        energy, positions, elapsed = run_simulation(
            mode, args.N, args.frames, args.dt, args.k, args.gravity, args.wind
        )
        results[mode] = {"energy": energy, "positions": positions, "elapsed": elapsed}

        stable_frames = int(np.isfinite(energy).sum())
        mean_energy   = float(np.nanmean(energy[np.isfinite(energy)])) if stable_frames > 0 else float("nan")
        print(f"{elapsed:.2f}s  stable={stable_frames}/{args.frames}  mean_energy={mean_energy:.2f}")

    # save logs
    energy_path = os.path.join(args.out, "energy_log.npz")
    np.savez(energy_path,
             baseline_energy=results["baseline"]["energy"],
             xpbd_energy=results["xpbd"]["energy"])
    print(f"\nSaved energy log → {energy_path}")

    # save final positions
    pos_path = os.path.join(args.out, "positions.npz")
    np.savez(pos_path,
             baseline=results["baseline"]["positions"],
             xpbd=results["xpbd"]["positions"],
             N=np.array([args.N]))
    print(f"Saved positions  → {pos_path}")

    # print summary
    b_e = results["baseline"]["energy"]
    x_e = results["xpbd"]["energy"]
    b_mean = float(np.nanmean(b_e[np.isfinite(b_e)])) if np.isfinite(b_e).any() else float("nan")
    x_mean = float(np.nanmean(x_e[np.isfinite(x_e)])) if np.isfinite(x_e).any() else float("nan")
    if b_mean > 0 and np.isfinite(x_mean):
        improvement = (1 - x_mean / b_mean) * 100
        print(f"\nEnergy improvement (XPBD vs Baseline): {improvement:+.1f}%")

    speedup = results["baseline"]["elapsed"] / results["xpbd"]["elapsed"]
    print(f"Runtime ratio  baseline/xpbd: {speedup:.3f}x")


if __name__ == "__main__":
    main()
