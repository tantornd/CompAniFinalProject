"""Cloth mesh representation with adjacency/constraint graph."""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from data.synthetic.grid_cloth import generate_cloth


class ClothMesh:
    """Holds all mutable simulation state for one cloth instance."""

    def __init__(self, N: int, width: float = 1.0, height: float = 1.0, origin=(0.0, 0.0)):
        data = generate_cloth(N, width, height, origin)

        self.N = N
        self.vertex_count = N * N
        self.positions  = data["positions"].copy()    # (V, 2) float64
        self.velocities = data["velocities"].copy()   # (V, 2) float64
        self.pinned     = data["pinned"].copy()        # (V,)   bool
        self.mass       = data["mass"].copy()          # (V,)   float64  (inf for pinned)
        self.springs    = data["springs"]              # list[(a, b, rest)]

        # Precompute adjacency list for fast neighbor queries
        self._adj = [[] for _ in range(self.vertex_count)]
        for a, b, _ in self.springs:
            self._adj[a].append(b)
            self._adj[b].append(a)

    # ── Accessors ─────────────────────────────────────────────────────────────

    def neighbors(self, vertex_idx: int):
        return self._adj[vertex_idx]

    def spring_count(self):
        return len(self.springs)

    def free_vertices(self):
        return np.where(~self.pinned)[0]

    # ── State helpers ──────────────────────────────────────────────────────────

    def reset(self, width: float = 1.0, height: float = 1.0, origin=(0.0, 0.0)):
        data = generate_cloth(self.N, width, height, origin)
        self.positions  = data["positions"].copy()
        self.velocities = data["velocities"].copy()

    def kinetic_energy(self) -> float:
        ke = 0.0
        for i in self.free_vertices():
            m = self.mass[i]
            vx, vy = self.velocities[i]
            ke += 0.5 * m * (vx * vx + vy * vy)
        return ke

    def potential_energy(self, stiffness: float) -> float:
        pe = 0.0
        for a, b, rest in self.springs:
            delta = self.positions[b] - self.positions[a]
            dist  = float(np.linalg.norm(delta))
            pe   += 0.5 * stiffness * (dist - rest) ** 2
        return pe

    def total_energy(self, stiffness: float) -> float:
        return self.kinetic_energy() + self.potential_energy(stiffness)

    def __repr__(self):
        return (f"ClothMesh(N={self.N}, vertices={self.vertex_count}, "
                f"springs={self.spring_count()}, pinned={self.pinned.sum()})")


if __name__ == "__main__":
    mesh = ClothMesh(16)
    print(mesh)
    print(f"Neighbors of vertex 0: {mesh.neighbors(0)}")
    print(f"Free vertices: {len(mesh.free_vertices())}")
    print(f"KE at rest: {mesh.kinetic_energy():.4f}")
    print(f"PE at rest (k=400): {mesh.potential_energy(400):.4f}")
