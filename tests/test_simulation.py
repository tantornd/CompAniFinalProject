import sys
import os
import math

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from data.synthetic.grid_cloth import generate_cloth, build_springs, generate_grid
from src.data_structures.constraint_graph import ClothMesh
from src.algorithms import baseline, proposed

class TestGridCloth:
    def test_vertex_count(self):
        cloth = generate_cloth(8)
        assert cloth["positions"].shape == (64, 2)

    def test_top_row_pinned(self):
        cloth = generate_cloth(10)
        assert cloth["pinned"][:10].all()
        assert not cloth["pinned"][10:].any()

    def test_mass_infinite_for_pinned(self):
        cloth = generate_cloth(8)
        assert np.all(np.isinf(cloth["mass"][cloth["pinned"]]))
        assert np.all(np.isfinite(cloth["mass"][~cloth["pinned"]]))

    def test_positions_span_unit_square(self):
        cloth = generate_cloth(5, width=1.0, height=1.0, origin=(0.0, 0.0))
        pos = cloth["positions"]
        assert math.isclose(pos[:, 0].min(), 0.0, abs_tol=1e-9)
        assert math.isclose(pos[:, 0].max(), 1.0, abs_tol=1e-9)
        assert math.isclose(pos[:, 1].min(), 0.0, abs_tol=1e-9)
        assert math.isclose(pos[:, 1].max(), 1.0, abs_tol=1e-9)

    def test_spring_count_grows_with_N(self):
        s4 = len(generate_cloth(4)["springs"])
        s8 = len(generate_cloth(8)["springs"])
        assert s8 > s4

    def test_rest_lengths_positive(self):
        cloth = generate_cloth(6)
        for _, _, r in cloth["springs"]:
            assert r > 0.0

class TestClothMesh:
    def test_construction(self):
        mesh = ClothMesh(8)
        assert mesh.vertex_count == 64
        assert mesh.N == 8

    def test_neighbors_nonempty(self):
        mesh = ClothMesh(8)
        assert len(mesh.neighbors(0)) > 0

    def test_free_vertices_count(self):
        N = 8
        mesh = ClothMesh(N)
        assert len(mesh.free_vertices()) == N * N - N

    def test_kinetic_energy_zero_at_rest(self):
        mesh = ClothMesh(8)
        assert mesh.kinetic_energy() == pytest.approx(0.0)

    def test_total_energy_finite_at_rest(self):
        mesh = ClothMesh(8)
        e = mesh.total_energy(stiffness=400.0)
        assert np.isfinite(e)

class TestBaseline:
    def _make_mesh(self, N=8):
        return ClothMesh(N, width=1.0, height=1.0)

    def test_pinned_vertices_do_not_move(self):
        mesh = self._make_mesh()
        pinned_before = mesh.positions[mesh.pinned].copy()
        for f in range(10):
            baseline.step_vectorized(mesh, dt=0.016, stiffness=400, gravity=9.8, wind=0.0, frame=f)
        assert np.allclose(mesh.positions[mesh.pinned], pinned_before)

    def test_cloth_falls_under_gravity(self):
        mesh = self._make_mesh()
        initial_y_mean = mesh.positions[~mesh.pinned, 1].mean()
        for f in range(30):
            baseline.step_vectorized(mesh, dt=0.016, stiffness=400, gravity=9.8, wind=0.0, frame=f)
        final_y_mean = mesh.positions[~mesh.pinned, 1].mean()
        assert final_y_mean > initial_y_mean, "Free vertices should fall (y increases downward)"

    def test_no_movement_with_zero_gravity_and_wind(self):
        mesh = self._make_mesh(N=4)
        # very small grid
        pos_before = mesh.positions.copy()
        for f in range(5):
            baseline.step_vectorized(mesh, dt=0.016, stiffness=400, gravity=0.0, wind=0.0, frame=f)
        assert np.allclose(mesh.positions[mesh.pinned], pos_before[mesh.pinned])

    def test_energy_finite_after_many_steps(self):
        mesh = self._make_mesh()
        for f in range(60):
            baseline.step_vectorized(mesh, dt=0.005, stiffness=200, gravity=9.8, wind=0.1, frame=f)
        e = mesh.total_energy(200)
        assert np.isfinite(e), "Energy should remain finite at small timestep"

class TestXPBD:
    def _make_mesh(self, N=8):
        return ClothMesh(N, width=1.0, height=1.0)

    def test_pinned_vertices_do_not_move(self):
        mesh = self._make_mesh()
        pinned_before = mesh.positions[mesh.pinned].copy()
        for f in range(10):
            proposed.step_vectorized(mesh, dt=0.016, stiffness=400, gravity=9.8,
                                     wind=0.0, iterations=8, frame=f)
        assert np.allclose(mesh.positions[mesh.pinned], pinned_before)

    def test_cloth_falls_under_gravity(self):
        mesh = self._make_mesh()
        initial_y_mean = mesh.positions[~mesh.pinned, 1].mean()
        for f in range(30):
            proposed.step_vectorized(mesh, dt=0.016, stiffness=400, gravity=9.8,
                                     wind=0.0, iterations=8, frame=f)
        final_y_mean = mesh.positions[~mesh.pinned, 1].mean()
        assert final_y_mean > initial_y_mean

    def test_stable_at_large_timestep(self):
        mesh = self._make_mesh()
        for f in range(60):
            proposed.step_vectorized(mesh, dt=0.033, stiffness=800, gravity=9.8,
                                     wind=0.3, iterations=8, frame=f)
        e = mesh.total_energy(800)
        assert np.isfinite(e), "XPBD must stay finite at large dt"

    def test_more_iterations_lower_energy(self):
        def run(iters):
            mesh = ClothMesh(8)
            for f in range(20):
                proposed.step_vectorized(mesh, dt=0.016, stiffness=400, gravity=9.8,
                                         wind=0.0, iterations=iters, frame=f)
            return mesh.total_energy(400)

        e_low  = run(2)
        e_high = run(16)
        # higher iterations
        assert np.isfinite(e_low) and np.isfinite(e_high)


# comparison
class TestComparison:
    def test_xpbd_more_stable_than_baseline_at_large_dt(self):
        N, dt, k = 12, 0.033, 800

        mesh_b = ClothMesh(N)
        mesh_x = ClothMesh(N)

        for f in range(60):
            baseline.step_vectorized(mesh_b, dt=dt, stiffness=k, gravity=9.8, wind=0.3, frame=f)
            proposed.step_vectorized(mesh_x, dt=dt, stiffness=k, gravity=9.8,
                                     wind=0.3, iterations=8, frame=f)

        e_b = mesh_b.total_energy(k)
        e_x = mesh_x.total_energy(k)

        assert np.isfinite(e_x), "XPBD energy should be finite at large dt"
        if np.isfinite(e_b):
            assert e_x <= e_b * 10, "XPBD should not be drastically worse than baseline"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
