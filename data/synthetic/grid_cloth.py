import numpy as np


def generate_grid(N: int, width: float = 1.0, height: float = 1.0, origin=(0.0, 0.0)):
    ox, oy = origin
    dx = width  / (N - 1)
    dy = height / (N - 1)

    pos = np.zeros((N * N, 2), dtype=np.float64)
    for j in range(N):
        for i in range(N):
            pos[j * N + i] = [ox + i * dx, oy + j * dy]

    pinned = np.zeros(N * N, dtype=bool)
    pinned[:N] = True  # pin entire top row

    return pos, pinned


def build_springs(N: int, pos: np.ndarray):
    springs = []

    def add(a, b):
        rest = float(np.linalg.norm(pos[b] - pos[a]))
        springs.append((a, b, rest))

    for j in range(N):
        for i in range(N):
            p = j * N + i
            if i + 1 < N:  add(p, j * N + i + 1)          # horizontal structural
            if j + 1 < N:  add(p, (j + 1) * N + i)        # vertical structural
            if i + 1 < N and j + 1 < N:                    # diagonal shear
                add(p, (j + 1) * N + i + 1)
                add(j * N + i + 1, (j + 1) * N + i)
            if i + 2 < N:  add(p, j * N + i + 2)           # horizontal bend
            if j + 2 < N:  add(p, (j + 2) * N + i)        # vertical bend

    return springs


def generate_cloth(N: int, width: float = 1.0, height: float = 1.0, origin=(0.0, 0.0)):
    pos, pinned = generate_grid(N, width, height, origin)
    springs = build_springs(N, pos)
    mass = np.ones(N * N, dtype=np.float64)
    mass[pinned] = np.inf

    return {
        "N": N,
        "positions": pos,
        "velocities": np.zeros_like(pos),
        "pinned": pinned,
        "mass": mass,
        "springs": springs,
    }


if __name__ == "__main__":
    cloth = generate_cloth(16)
    print(f"16x16 grid: {cloth['N']**2} vertices, {len(cloth['springs'])} springs")
    print(f"Pinned: {cloth['pinned'].sum()} vertices")
    print(f"Position range x: [{cloth['positions'][:,0].min():.3f}, {cloth['positions'][:,0].max():.3f}]")
    print(f"Position range y: [{cloth['positions'][:,1].min():.3f}, {cloth['positions'][:,1].max():.3f}]")
