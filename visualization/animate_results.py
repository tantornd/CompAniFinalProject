import argparse
import os
import sys

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.gridspec import GridSpec

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


DARK_BG   = "#050508"
PANEL_BG  = "#0a0a10"
COLOR_B   = "#ff2f6e"   # baseline
COLOR_X   = "#7b2fff"   # XPBD

def load_results(result_dir: str):
    pos_path    = os.path.join(result_dir, "positions.npz")
    energy_path = os.path.join(result_dir, "energy_log.npz")

    if not os.path.exists(pos_path):
        raise FileNotFoundError(
            f"{pos_path} not found — run `python src/main.py` first to generate data.")

    pos_data = np.load(pos_path, allow_pickle=True)
    N = int(pos_data["N"][0])
    baseline_pos = pos_data["baseline"]
    xpbd_pos     = pos_data["xpbd"] 

    energy_data = np.load(energy_path) if os.path.exists(energy_path) else None
    baseline_e  = energy_data["baseline_energy"] if energy_data else None
    xpbd_e      = energy_data["xpbd_energy"]     if energy_data else None

    return N, baseline_pos, xpbd_pos, baseline_e, xpbd_e


def draw_cloth_frame(ax, positions, N: int, color: str, alpha_base: float = 0.25):
    ax.cla()
    ax.set_facecolor(PANEL_BG)
    ax.set_aspect("equal")
    ax.set_xlim(positions[:, 0].min() - 0.05, positions[:, 0].max() + 0.05)
    ax.set_ylim(positions[:, 1].min() - 0.05, positions[:, 1].max() + 0.05)
    ax.axis("off")

    # draw edges
    for j in range(N):
        for i in range(N):
            p = j * N + i
            x, y = positions[p]
            if i + 1 < N:
                q = j * N + i + 1
                ax.plot([x, positions[q, 0]], [y, positions[q, 1]],
                        color=color, alpha=0.4, lw=0.6)
            if j + 1 < N:
                q = (j + 1) * N + i
                ax.plot([x, positions[q, 0]], [y, positions[q, 1]],
                        color=color, alpha=0.4, lw=0.6)

    # highlight pin row
    for i in range(N):
        ax.plot(positions[i, 0], positions[i, 1], "o",
                color="white", markersize=3, alpha=0.9, zorder=5)

def plot_energy(baseline_e, xpbd_e, out_path: str = None):
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(PANEL_BG)

    frames = np.arange(len(baseline_e))
    b_plot = np.where(np.isfinite(baseline_e), baseline_e, np.nan)
    x_plot = np.where(np.isfinite(xpbd_e),    xpbd_e,    np.nan)

    ax.plot(frames, b_plot, color=COLOR_B, lw=1.2, label="Baseline (Mass-Spring)")
    ax.plot(frames, x_plot, color=COLOR_X, lw=1.2, label="Proposed (XPBD)")
    ax.set_xlabel("Frame", color="#c8c8e0")
    ax.set_ylabel("Total Energy", color="#c8c8e0")
    ax.set_title("Energy Over Time — Baseline vs XPBD", color="white", pad=12)
    ax.legend(facecolor=PANEL_BG, edgecolor="#1a1a2e", labelcolor="#c8c8e0")
    ax.grid(alpha=0.15, color="#1a1a2e")
    ax.tick_params(colors="#5a5a7a")
    fig.tight_layout()

    if out_path:
        fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
        print(f"Saved energy plot → {out_path}")
    else:
        plt.show()
    plt.close(fig)

# side by side

def animate(N, baseline_pos, xpbd_pos, baseline_e, xpbd_e, save_path: str = None):
    plt.style.use("dark_background")
    fig = plt.figure(figsize=(14, 6), facecolor=DARK_BG)
    gs  = GridSpec(2, 2, figure=fig, height_ratios=[3, 1], hspace=0.35, wspace=0.1)

    ax_b  = fig.add_subplot(gs[0, 0])  # baseline cloth
    ax_x  = fig.add_subplot(gs[0, 1])  # XPBD cloth
    ax_eg = fig.add_subplot(gs[1, :])  # energy graph

    ax_b.set_title("Baseline (Mass-Spring)", color=COLOR_B, fontsize=11)
    ax_x.set_title("Proposed (XPBD)",        color=COLOR_X, fontsize=11)
    ax_eg.set_facecolor(PANEL_BG)
    ax_eg.set_xlabel("Frame", color="#c8c8e0", fontsize=9)
    ax_eg.set_ylabel("Energy", color="#c8c8e0", fontsize=9)
    ax_eg.tick_params(colors="#5a5a7a", labelsize=8)
    ax_eg.grid(alpha=0.15, color="#1a1a2e")

    frames_total = min(len(baseline_pos), len(xpbd_pos))
    frame_idx = np.arange(frames_total)

    if baseline_e is not None:
        b_safe = np.where(np.isfinite(baseline_e[:frames_total]), baseline_e[:frames_total], np.nan)
        x_safe = np.where(np.isfinite(xpbd_e[:frames_total]),    xpbd_e[:frames_total],    np.nan)
        ax_eg.plot(frame_idx, b_safe, color=COLOR_B, lw=0.8, alpha=0.6, label="Baseline")
        ax_eg.plot(frame_idx, x_safe, color=COLOR_X, lw=0.8, alpha=0.6, label="XPBD")
        ax_eg.legend(facecolor=PANEL_BG, edgecolor="#1a1a2e",
                     labelcolor="#c8c8e0", fontsize=8, loc="upper right")

    vline_b = ax_eg.axvline(0, color=COLOR_B, lw=1.2, alpha=0.8)
    vline_x = ax_eg.axvline(0, color=COLOR_X, lw=1.2, alpha=0.8, linestyle="--")

    def update(f):
        draw_cloth_frame(ax_b, baseline_pos[f], N, COLOR_B)
        draw_cloth_frame(ax_x, xpbd_pos[f],     N, COLOR_X)
        ax_b.set_title(f"Baseline (Mass-Spring)  frame {f}", color=COLOR_B, fontsize=10)
        ax_x.set_title(f"Proposed (XPBD)          frame {f}", color=COLOR_X, fontsize=10)
        vline_b.set_xdata([f, f])
        vline_x.set_xdata([f, f])
        return []

    step = max(1, frames_total // 150)  # cap at ~150
    ani = animation.FuncAnimation(
        fig, update, frames=range(0, frames_total, step),
        interval=50, blit=False
    )

    if save_path:
        writer = animation.PillowWriter(fps=20)
        ani.save(save_path, writer=writer, dpi=100)
        print(f"Saved animation → {save_path}")
    else:
        plt.show()

    plt.close(fig)

def main():
    parser = argparse.ArgumentParser(description="Visualize cloth simulation results")
    parser.add_argument("--input", type=str,
                        default=os.path.join(os.path.dirname(__file__), "..", "experiments", "results"),
                        help="Directory containing positions.npz and energy_log.npz")
    parser.add_argument("--save", action="store_true",
                        help="Save outputs to files instead of displaying interactively")
    args = parser.parse_args()

    result_dir = os.path.normpath(args.input)

    try:
        N, baseline_pos, xpbd_pos, baseline_e, xpbd_e = load_results(result_dir)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"Loaded  N={N}  frames={len(baseline_pos)}")

    if args.save:
        energy_out = os.path.join(result_dir, "energy_comparison.png")
        anim_out   = os.path.join(result_dir, "animation.gif")
        if baseline_e is not None:
            plot_energy(baseline_e, xpbd_e, out_path=energy_out)
        animate(N, baseline_pos, xpbd_pos, baseline_e, xpbd_e, save_path=anim_out)
    else:
        if baseline_e is not None:
            plot_energy(baseline_e, xpbd_e)
        animate(N, baseline_pos, xpbd_pos, baseline_e, xpbd_e)


if __name__ == "__main__":
    main()
