import numpy as np


def step(mesh, dt: float, stiffness: float, gravity: float, wind: float, frame: int = 0):
    """
    Args:
        mesh      : ClothMesh instance (mutated in-place)
        dt        : timestep in seconds
        stiffness : spring stiffness k
        gravity   : gravitational acceleration (m/s²)
        wind      : wind force magnitude
        frame     : current frame index (used for animated wind)
    """
    V = mesh.vertex_count
    forces = np.zeros((V, 2), dtype=np.float64)
    for p in range(V):
        if mesh.pinned[p]:
            continue
        wind_x = wind * 2.0 * (0.5 + 0.5 * np.sin(frame * 0.03 + p * 0.1))
        forces[p, 0] += wind_x
        forces[p, 1] += gravity * mesh.mass[p]

    for a, b, rest in mesh.springs:
        pa = mesh.positions[a]
        pb = mesh.positions[b]
        delta = pb - pa
        dist  = float(np.linalg.norm(delta))
        if dist < 1e-8:
            continue
        f_mag = stiffness * (dist - rest) / dist
        f_vec = f_mag * delta
        if not mesh.pinned[a]:
            forces[a] += f_vec
        if not mesh.pinned[b]:
            forces[b] -= f_vec
    damp = 0.985
    for p in range(V):
        if mesh.pinned[p]:
            continue
        m = mesh.mass[p]
        mesh.velocities[p] = (mesh.velocities[p] + dt * forces[p] / m) * damp
        mesh.positions[p]  += dt * mesh.velocities[p]


def step_vectorized(mesh, dt: float, stiffness: float, gravity: float, wind: float, frame: int = 0):
    V  = mesh.vertex_count
    pos = mesh.positions
    vel = mesh.velocities
    pin = mesh.pinned
    mass = mesh.mass

    forces = np.zeros((V, 2), dtype=np.float64)
    wind_anim = wind * 2.0 * (0.5 + 0.5 * np.sin(frame * 0.03 + np.arange(V) * 0.1))
    forces[:, 0] = np.where(pin, 0.0, wind_anim)
    forces[:, 1] = np.where(pin, 0.0, gravity * mass)

    springs = mesh.springs
    for a, b, rest in springs:
        d  = pos[b] - pos[a]
        dn = float(np.linalg.norm(d))
        if dn < 1e-8:
            continue
        fv = stiffness * (dn - rest) / dn * d
        if not pin[a]: forces[a] += fv
        if not pin[b]: forces[b] -= fv

    free = ~pin
    vel[free] = (vel[free] + dt * (forces[free] / mass[free, None])) * 0.985
    pos[free] += dt * vel[free]
