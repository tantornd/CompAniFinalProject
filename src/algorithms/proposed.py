import numpy as np


def step(mesh, dt: float, stiffness: float, gravity: float, wind: float,
         iterations: int = 8, frame: int = 0):
    """
    Args:
        mesh       : ClothMesh instance (mutated in-place)
        dt         : timestep in seconds
        stiffness  : target spring stiffness (controls compliance)
        gravity    : gravitational acceleration (m/s²)
        wind       : wind force magnitude
        iterations : number of constraint projection iterations per step
        frame      : current frame index (used for animated wind)
    """
    V  = mesh.vertex_count
    pos = mesh.positions
    vel = mesh.velocities
    pin = mesh.pinned
    mass = mesh.mass
    compliance = 1.0 / (stiffness * dt * dt)

    est = np.empty_like(pos)
    for p in range(V):
        if pin[p]:
            est[p] = pos[p]
            continue
        wind_x = wind * 2.0 * (0.5 + 0.5 * np.sin(frame * 0.03 + p * 0.1))
        est[p, 0] = pos[p, 0] + vel[p, 0] * dt + wind_x * dt * dt
        est[p, 1] = pos[p, 1] + vel[p, 1] * dt + gravity      * dt * dt

    lambdas = np.zeros(len(mesh.springs), dtype=np.float64)

    for _ in range(iterations):
        for s, (a, b, rest) in enumerate(mesh.springs):
            d    = est[b] - est[a]
            dist = float(np.linalg.norm(d))
            if dist < 1e-8:
                continue
            C  = dist - rest
            wa = 0.0 if pin[a] else 1.0 / mass[a]
            wb = 0.0 if pin[b] else 1.0 / mass[b]
            denom = wa + wb + compliance
            if denom < 1e-12:
                continue
            dL = (-C - compliance * lambdas[s]) / denom
            lambdas[s] += dL
            n = d / dist
            if not pin[a]: est[a] -= wa * dL * n
            if not pin[b]: est[b] += wb * dL * n

    inv_dt = 1.0 / dt
    vel_damp = 0.99
    for p in range(V):
        if pin[p]:
            continue
        vel[p] = (est[p] - pos[p]) * inv_dt * vel_damp
        pos[p] = est[p]


def step_vectorized(mesh, dt: float, stiffness: float, gravity: float, wind: float,
                    iterations: int = 8, frame: int = 0):
    V   = mesh.vertex_count
    pos = mesh.positions
    vel = mesh.velocities
    pin = mesh.pinned
    mass = mesh.mass
    compliance = 1.0 / (stiffness * dt * dt)

    idx = np.arange(V)
    wind_anim = wind * 2.0 * (0.5 + 0.5 * np.sin(frame * 0.03 + idx * 0.1))
    est = pos.copy()
    free = ~pin
    est[free, 0] += vel[free, 0] * dt + wind_anim[free] * dt * dt
    est[free, 1] += vel[free, 1] * dt + gravity           * dt * dt

    lambdas = np.zeros(len(mesh.springs), dtype=np.float64)
    for _ in range(iterations):
        for s, (a, b, rest) in enumerate(mesh.springs):
            d    = est[b] - est[a]
            dist = float(np.linalg.norm(d))
            if dist < 1e-8:
                continue
            C  = dist - rest
            wa = 0.0 if pin[a] else 1.0 / mass[a]
            wb = 0.0 if pin[b] else 1.0 / mass[b]
            denom = wa + wb + compliance
            if denom < 1e-12:
                continue
            dL = (-C - compliance * lambdas[s]) / denom
            lambdas[s] += dL
            n = d / dist
            if not pin[a]: est[a] -= wa * dL * n
            if not pin[b]: est[b] += wb * dL * n

    vel[free] = (est[free] - pos[free]) / dt * 0.99
    pos[free] = est[free]
