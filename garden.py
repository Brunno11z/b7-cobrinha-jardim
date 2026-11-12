"""Jardim 3D otimizado, geração de áudio procedural WAV e malha tubular da cobrinha."""
import math, os, struct, wave, random
from pathlib import Path
from ursina import *
from ursina.shaders import basic_lighting_shader

ROOT = Path(__file__).resolve().parent

def generate_sfx():
    assets = ROOT / 'assets'
    assets.mkdir(parents=True, exist_ok=True)
    rate = 22050

    # 1. Som de comer maçã (mordida crocante com estalo e ressonância doce)
    eat_path = assets / 'eat_apple.wav'
    if not eat_path.exists() or eat_path.stat().st_size < 1000:
        samples = []
        dur = 0.28
        total = int(rate * dur)
        for i in range(total):
            t = i / rate
            env = math.exp(-t * 22.0)
            crunch = (random.random() * 2.0 - 1.0) * math.exp(-t * 35.0)
            tone1 = math.sin(2.0 * math.pi * 580.0 * t) * math.exp(-t * 18.0)
            tone2 = math.sin(2.0 * math.pi * 880.0 * t) * math.exp(-t * 24.0)
            val = (crunch * 0.65 + tone1 * 0.35 + tone2 * 0.25) * env
            samples.append(int(max(-1.0, min(1.0, val)) * 32767.0))
        with wave.open(str(eat_path), 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(struct.pack(f'<{len(samples)}h', *samples))

    # 2. Som de bomba (explosão grave e impacto)
    bomb_path = assets / 'bomb.wav'
    if not bomb_path.exists() or bomb_path.stat().st_size < 1000:
        samples = []
        dur = 0.65
        total = int(rate * dur)
        for i in range(total):
            t = i / rate
            env = math.exp(-t * 7.5)
            noise = (random.random() * 2.0 - 1.0) * env
            sub = math.sin(2.0 * math.pi * max(40.0, 160.0 - t * 180.0) * t) * env
            val = noise * 0.65 + sub * 0.55
            samples.append(int(max(-1.0, min(1.0, val)) * 32767.0))
        with wave.open(str(bomb_path), 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(struct.pack(f'<{len(samples)}h', *samples))

    # 3. Som de vitória (fanfarra brilhante de meta atingida)
    vic_path = assets / 'victory.wav'
    if not vic_path.exists() or vic_path.stat().st_size < 1000:
        samples = []
        dur = 1.15
        total = int(rate * dur)
        freqs = [(0.0, 523.25), (0.18, 659.25), (0.36, 783.99), (0.55, 1046.5)]
        for i in range(total):
            t = i / rate
            val = 0.0
            for start_t, f in freqs:
                if t >= start_t:
                    note_t = t - start_t
                    env = math.exp(-note_t * 5.0)
                    val += math.sin(2.0 * math.pi * f * note_t) * env * 0.32
                    val += math.sin(2.0 * math.pi * f * 2.0 * note_t) * env * 0.10
            samples.append(int(max(-1.0, min(1.0, val)) * 32767.0))
        with wave.open(str(vic_path), 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(struct.pack(f'<{len(samples)}h', *samples))

generate_sfx()

def build_garden():
    ground = Entity(
        model='plane',
        scale=(18, 1, 24),
        color=color.rgb32(95, 175, 45),
        position=(0, 0, 0),
        shader=basic_lighting_shader
    )
    grass_tex = ROOT / 'assets' / 'grass.png'
    if grass_tex.exists():
        ground.texture = Texture(grass_tex)
        ground.texture_scale = (6, 8)

    # Cerca de madeira rústica e pedras decorativas
    for z in (-10.5, 10.5):
        for x in range(-8, 9, 2):
            Entity(model='cube', scale=(.25, 1.1, .25), position=(x, .55, z), color=color.rgb32(140, 95, 55), shader=basic_lighting_shader)
        Entity(model='cube', scale=(17, .16, .12), position=(0, .85, z), color=color.rgb32(120, 80, 45), shader=basic_lighting_shader)
        Entity(model='cube', scale=(17, .16, .12), position=(0, .45, z), color=color.rgb32(120, 80, 45), shader=basic_lighting_shader)

    for x in (-8.5, 8.5):
        for z in range(-10, 11, 2):
            Entity(model='cube', scale=(.25, 1.1, .25), position=(x, .55, z), color=color.rgb32(140, 95, 55), shader=basic_lighting_shader)
        Entity(model='cube', scale=(.12, .16, 21), position=(x, .85, 0), color=color.rgb32(120, 80, 45), shader=basic_lighting_shader)
        Entity(model='cube', scale=(.12, .16, 21), position=(x, .45, 0), color=color.rgb32(120, 80, 45), shader=basic_lighting_shader)

    # Flores e cogumelos coloridos no jardim
    flower_colors = [
        color.rgb32(255, 105, 180),
        color.rgb32(255, 215, 0),
        color.rgb32(255, 69, 0),
        color.rgb32(138, 43, 226),
        color.rgb32(0, 191, 255)
    ]
    random.seed(42)
    for _ in range(40):
        fx = random.uniform(-7.5, 7.5)
        fz = random.uniform(-9.5, 9.5)
        if abs(fx) < 2.0 and abs(fz) < 2.0:
            continue
        stem = Entity(model='cylinder', scale=(.05, .45, .05), position=(fx, .22, fz), color=color.rgb32(40, 140, 30))
        Entity(parent=stem, model='sphere', scale=(5.0, .4, 5.0), position=(0, .48, 0), color=random.choice(flower_colors))
        Entity(parent=stem, model='sphere', scale=(2.0, .8, 2.0), position=(0, .52, 0), color=color.yellow)

    # Pedras estilizadas no contorno
    for _ in range(16):
        rx = random.choice([-7.8, 7.8]) + random.uniform(-.4, .4)
        rz = random.uniform(-9.0, 9.0)
        s = random.uniform(.5, 1.1)
        Entity(model='sphere', scale=(s*1.2, s*.7, s), position=(rx, .3, rz), color=color.rgb32(135, 145, 140), shader=basic_lighting_shader)

class TubeSnake:
    """Malha 3D contínua que acompanha a trajetória percorrida pelo jogador."""
    def __init__(self, rings=200, sides=12):
        self.rings = rings
        self.sides = sides
        self.triangles = []
        for i in range(self.rings - 1):
            for k in range(self.sides):
                a = i * self.sides + k
                b = i * self.sides + (k + 1) % self.sides
                c = a + self.sides
                d = b + self.sides
                self.triangles.extend([(a, c, b), (b, c, d)])
        self.mesh = Mesh(vertices=[], triangles=[], colors=[], static=False)
        self.entity = Entity(model=self.mesh, double_sided=True, shader=basic_lighting_shader)

    def update_mesh(self, points, progress=0.0, elapsed=0.0):
        """Reconstrói os anéis tubulares da cobra ao longo dos pontos da espinha."""
        if len(points) < 2:
            return

        base_radius = 0.36 + progress * 0.12
        verts = []
        cols = []

        back_color = color.rgb32(24, 74, 255)
        belly_color = color.rgb32(107, 228, 197)

        n_pts = len(points)

        for i in range(self.rings):
            # Interpola ponto ao longo da lista de pontos
            idx_float = (i / (self.rings - 1)) * (n_pts - 1)
            idx0 = int(idx_float)
            idx1 = min(n_pts - 1, idx0 + 1)
            frac = idx_float - idx0

            p0 = points[idx0]
            p1 = points[idx1]
            p = Vec3(
                p0[0] + frac * (p1[0] - p0[0]),
                p0[1] + frac * (p1[1] - p0[1]),
                p0[2] + frac * (p1[2] - p0[2])
            )

            # Vetor tangente para orientar o anel
            if idx0 < n_pts - 1:
                tangent = Vec3(p0[0] - p1[0], p0[1] - p1[1], p0[2] - p1[2])
            else:
                tangent = Vec3(p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])

            if tangent.length() < 0.0001:
                tangent = Vec3(0, 0, 1)
            tangent = tangent.normalized()

            # Base ortonormal
            side = Vec3(tangent.z, 0, -tangent.x)
            if side.length() < 0.001:
                side = Vec3(1, 0, 0)
            side = side.normalized()
            up = Vec3.cross(tangent, side).normalized()

            # Conicidade na cauda e transição na cabeça
            t = i / (self.rings - 1)
            if t > 0.85:
                taper = max(0.10, 1.0 - ((t - 0.85) / 0.15) ** 1.3)
            elif t < 0.06:
                taper = 0.82 + 0.18 * (t / 0.06)
            else:
                taper = 1.0

            radius = base_radius * taper

            # Micro-ondulação de escamas para sensação orgânica de movimento
            wave_subtle = math.sin(t * 18.0 - elapsed * 8.0) * 0.02 * (1.0 - t * 0.4)
            p = p + side * wave_subtle

            for k in range(self.sides):
                theta = k * math.tau / self.sides
                cos_t = math.cos(theta)
                sin_t = math.sin(theta)

                offset = side * (cos_t * radius) + up * (sin_t * radius)
                verts.append(p + offset)

                # Dorso azul superior e ventre verde-água inferior
                if sin_t < -0.15:
                    cols.append(belly_color)
                else:
                    cols.append(back_color)

        self.mesh.vertices = verts
        self.mesh.triangles = self.triangles
        self.mesh.colors = cols
        self.mesh.generate()
