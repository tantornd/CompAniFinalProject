import argparse
import csv
import os
import sys
import time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.data_structures.constraint_graph import ClothMesh
from src.algorithms import baseline, proposed

GRID_SIZES = [8, 16, 32, 48]


def benchmark_grid(N: int, frames: int, dt: float = 0.016, k: float = 400.0,
                   gravity: float = 9.8, wind: float = 0.3):
    results = {}
    for mode in ("baseline", "xpbd"):
        mesh = ClothMesh(N, width=1.0, height=1.0)
        energy_log = []

        step_fn = baseline.step_vectorized if mode == "baseline" else proposed.step_vectorized

        t0 = time.perf_counter()
        for f in range(frames):
            kw = dict(dt=dt, stiffness=k, gravity=gravity, wind=wind, frame=f)
            if mode == "xpbd":
                kw["iterations"] = 8
            step_fn(mesh, **kw)
            e = mesh.total_energy(k)
            if np.isfinite(e):
                energy_log.append(e)

        elapsed_ms = (time.perf_counter() - t0) / frames * 1000

        mean_energy = float(np.mean(energy_log)) if energy_log else float("nan")
        results[mode] = {"ms_per_frame": elapsed_ms, "mean_energy": mean_energy}

    return results


def run_all(frames: int, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)

    rows = []
    print(f"{'N':>4}  {'Verts':>6}  {'Baseline ms':>11}  {'XPBD ms':>8}  {'Speedup':>7}  "
          f"{'B energy':>10}  {'X energy':>10}  {'Improvement':>11}")
    print("-" * 80)

    for N in GRID_SIZES:
        res = benchmark_grid(N, frames)
        b = res["baseline"]
        x = res["xpbd"]
        speedup = b["ms_per_frame"] / x["ms_per_frame"] if x["ms_per_frame"] > 0 else float("nan")

        if np.isfinite(b["mean_energy"]) and np.isfinite(x["mean_energy"]) and b["mean_energy"] > 0:
            improvement = (1 - x["mean_energy"] / b["mean_energy"]) * 100
        else:
            improvement = float("nan")

        rows.append({
            "N": N,
            "vertices":            N * N,
            "baseline_ms":         round(b["ms_per_frame"], 3),
            "xpbd_ms":             round(x["ms_per_frame"], 3),
            "speedup":             round(speedup, 3),
            "baseline_energy":     round(b["mean_energy"], 2),
            "xpbd_energy":         round(x["mean_energy"], 2),
            "energy_improvement_pct": round(improvement, 1),
        })

        imp_str = f"{improvement:+.1f}%" if np.isfinite(improvement) else "  n/a"
        print(f"{N:>4}  {N*N:>6}  {b['ms_per_frame']:>11.3f}  {x['ms_per_frame']:>8.3f}  "
              f"{speedup:>7.3f}  {b['mean_energy']:>10.2f}  {x['mean_energy']:>10.2f}  {imp_str:>11}")

    csv_path = os.path.join(out_dir, "runtime.csv")
    fieldnames = list(rows[0].keys())
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved → {csv_path}")

    _plot(rows, out_dir)
    return rows


def _plot(rows, out_dir: str):
    ns      = [r["N"] for r in rows]
    verts   = [r["vertices"] for r in rows]
    b_ms    = [r["baseline_ms"] for r in rows]
    x_ms    = [r["xpbd_ms"] for r in rows]
    b_en    = [r["baseline_energy"] for r in rows]
    x_en    = [r["xpbd_energy"] for r in rows]

    plt.style.use("dark_background")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    fig.patch.set_facecolor("#050508")
    for ax in (ax1, ax2):
        ax.set_facecolor("#0a0a10")

    # runtime scaling
    ax1.plot(verts, b_ms, "o-", color="#ff2f6e", label="Baseline (Mass-Spring)")
    ax1.plot(verts, x_ms, "o-", color="#7b2fff", label="Proposed (XPBD)")
    ax1.set_xlabel("Vertices")
    ax1.set_ylabel("Time (ms/frame)")
    ax1.set_title("Runtime Scaling")
    ax1.legend()
    ax1.grid(alpha=0.2)

    # energy comparison bar chart
    x_pos = np.arange(len(ns))
    width = 0.35
    # normalize energies
    max_e = max(b_en) if max(b_en) > 0 else 1.0
    ax2.bar(x_pos - width/2, [e/max_e for e in b_en], width, color="#ff2f6e", label="Baseline")
    ax2.bar(x_pos + width/2, [e/max_e for e in x_en], width, color="#7b2fff", label="XPBD")
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels([f"{n}×{n}" for n in ns])
    ax2.set_xlabel("Grid Size")
    ax2.set_ylabel("Normalized Energy Error")
    ax2.set_title("Stability Comparison")
    ax2.legend()
    ax2.grid(alpha=0.2, axis="y")

    fig.tight_layout()
    plot_path = os.path.join(out_dir, "plots.png")
    fig.savefig(plot_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"Saved → {plot_path}")
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cloth simulation scaling benchmark")
    parser.add_argument("--frames", type=int, default=60,  help="Frames per benchmark run")
    parser.add_argument("--out",    type=str, default=os.path.join(
        os.path.dirname(__file__), "results"), help="Output directory")
    args = parser.parse_args()

    run_all(args.frames, args.out)
