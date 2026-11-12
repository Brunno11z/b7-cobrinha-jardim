"""Cenário e malha tubular da B7 Cobrinha Jardim, com movimentos incríveis e crescimento dinâmico."""
import math, random, wave, struct
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
from ursina import *
from ursina.shaders import basic_lighting_shader

R = random.Random(77)

def generate_sfx(path, sample_rate, duration, generator_func):
    num_samples = int(sample_rate * duration)
    with wave.open(str(path), 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        data = bytearray()
        for i in range(num_samples):
            t = i / sample_rate
            val = max(-1.0, min(1.0, generator_func(t, duration)))
            sample = int(val * 32767)
            data.extend(struct.pack('<h', sample))
        wav.writeframes(data)

def prepare_assets():
    assets = Path(__file__).parent / 'assets'
    assets.mkdir(exist_ok=True)
    p = assets / 'grass.png'
    if not p.exists():
        im = Image.new('RGB', (512, 512))
        pix = im.load()
        for y in range(512):
            for x in range(512):
                n = R.randint(-9, 9)
                wave_val = int(5 * math.sin(x / 45) + 4 * math.cos(y / 39))
                pix[x, y] = (73 + n + wave_val, 137 + n + wave_val, 30 + n // 2)
        d = ImageDraw.Draw(im)
        for _ in range(2700):
            x, y = R.randrange(512), R.randrange(512)
            d.line((x, y, x + R.randint(-2, 2), y - R.randint(2, 7)), fill=(91, 155 + R.randrange(25), 35), width=1)
        for _ in range(25):
            x, y = R.randrange(512), R.randrange(512)
            for dx, dy in ((-3, 0), (3, 0), (0, 3), (0, -3)):
                d.ellipse((x + dx - 2, y + dy - 2, x + dx + 2, y + dy + 2), fill=(230, 234, 158))
            d.ellipse((x - 1, y - 1, x + 1, y + 1), fill=(245, 187, 35))
        im.save(p)

    p2 = assets / 'shadow.png'
    if not p2.exists():
        im = Image.new('RGBA', (96, 96))
        d = ImageDraw.Draw(im)
        d.ellipse((12, 12, 84, 84), fill=(18, 47, 5, 150))
        im = im.filter(ImageFilter.GaussianBlur(10))
        im.save(p2)

    # Audio assets
    s1 = assets / 'eat_apple.wav'
    if not s1.exists():
        def apple_bite(t, dur):
            s = 0.0
            if t < 0.18:
                env = math.exp(-t * 28.0)
                noise = (R.random() * 2 - 1) * 0.7
                click = math.sin(2 * math.pi * (800 - t * 2500) * t) * 0.5
                body = math.sin(2 * math.pi * 260 * t) * 0.3
                s += env * (noise + click + body)
            if t >= 0.10:
                t2 = t - 0.10
                env2 = math.exp(-t2 * 22.0)
                noise2 = (R.random() * 2 - 1) * 0.8
                click2 = math.sin(2 * math.pi * (1100 - t2 * 3200) * t2) * 0.6
                body2 = math.sin(2 * math.pi * 320 * t2) * 0.4
                s += env2 * (noise2 + click2 + body2)
            return s * 0.85
        generate_sfx(s1, 44100, 0.42, apple_bite)

    s2 = assets / 'bomb.wav'
    if not s2.exists():
        def bomb_explosion(t, dur):
            env = math.exp(-t * 4.5)
            bass = math.sin(2 * math.pi * (110 * math.exp(-t * 8.0) + 38) * t) * 0.7
            noise = (R.random() * 2 - 1) * math.exp(-t * 6.0) * 0.6
            sub = math.sin(2 * math.pi * 45 * t) * 0.4 * math.exp(-t * 3.0)
            return env * (bass + noise + sub) * 0.9
        generate_sfx(s2, 44100, 0.9, bomb_explosion)

    s3 = assets / 'victory.wav'
    if not s3.exists():
        def victory_chime(t, dur):
            notes = [523.25, 659.25, 783.99, 1046.50]
            s = 0.0
            for idx, freq in enumerate(notes):
                start = idx * 0.12
                if t >= start:
                    dt = t - start
                    env = math.exp(-dt * 4.0)
                    tone = math.sin(2 * math.pi * freq * dt) + 0.3 * math.sin(2 * math.pi * freq * 2 * dt)
                    s += env * tone * 0.25
            return s * 0.9
        generate_sfx(s3, 44100, 1.2, victory_chime)

    return str(p), str(p2)

def build_garden():
    grass, shadow = prepare_assets()
    Entity(model='plane', scale=80, texture=Texture(Path(grass)), texture_scale=(12, 12), color=color.white, y=-0.08)
    decorative = Entity()

    def part(**kw):
        return Entity(parent=decorative, shader=basic_lighting_shader, **kw)

    def flower(x, z, height, col):
        part(model='cube', position=(x, height / 2, z), scale=(0.045, height, 0.045), color=color.rgb32(42, 104, 19))
        for side in (-1, 1):
            part(model='sphere', position=(x + side * 0.22, height * 0.48, z), scale=(0.65, 0.09, 0.25), rotation_z=side * 25, color=color.rgb32(47, 143, 24))
        for k in range(7):
            a = k * math.tau / 7
            part(model='sphere', position=(x + 0.23 * math.cos(a), height, z + 0.23 * math.sin(a)), scale=(0.39, 0.14, 0.3), rotation_y=-a * 180 / math.pi, color=col)
        part(model='sphere', position=(x, height + 0.07, z), scale=(0.25, 0.12, 0.25), color=color.rgb32(255, 185, 25))
        Entity(model='quad', texture=Texture(Path(shadow)), rotation_x=90, position=(x + 0.18, -0.065, z + 0.15), scale=1.35, color=color.white)

    palette = [color.rgb32(255, 80, 112), color.rgb32(255, 207, 38), color.rgb32(110, 49, 224), color.rgb32(255, 242, 196)]
    for i in range(36):
        a = R.random() * math.tau
        r = R.uniform(5.5, 11.0)
        flower(math.cos(a) * r, math.sin(a) * r, R.uniform(0.55, 1.5), palette[i % 4])

    for i in range(65):
        x, z = R.uniform(-10, 10), R.uniform(-10, 10)
        part(model='sphere', position=(x, 0.065, z), scale=(0.15, 0.13, 0.15), color=R.choice([color.red, color.gold, color.azure, color.lime]))
        part(model='cube', position=(x, 0.16, z), scale=(0.025, 0.08, 0.025), color=color.rgb32(49, 94, 12))

    decorative.combine(auto_destroy=True)

class TubeSnake:
    def __init__(self):
        self.rings = 240
        self.sides = 12
        self.triangles = []
        for i in range(self.rings - 1):
            for k in range(self.sides):
                a = i * self.sides + k
                b = i * self.sides + (k + 1) % self.sides
                c = a + self.sides
                d = b + self.sides
                self.triangles.extend([(a, c, b), (b, c, d)])
        self.mesh = Mesh(vertices=[], triangles=[], static=False)
        self.entity = Entity(model=self.mesh, double_sided=True, color=color.white)

    @staticmethod
    def point(a, progress=0.0):
        # Curva multi-harmônica 3D contínua, suave e orgânica.
        # Nunca colide com ela mesma: separação vertical suave nos cruzamentos!
        # À medida que come maçãs, o raio expande e preenche a tela quase inteira!
        reach = 1.0 + progress * 0.22
        x = reach * (4.35 * math.sin(a) + 0.45 * math.sin(3 * a))
        z = reach * (3.45 * math.sin(2 * a) + 0.35 * math.cos(a))
        y = 0.38 + 0.15 * math.sin(2.5 * a)
        return Vec3(x, y, z)

    def update(self, angle, progress, elapsed=0.0):
        # O corpo cresce exponencialmente com as maçãs e chega a preencher quase toda a tela (até 15.5 radianos)
        length = 2.0 + progress * 13.5
        base_radius = 0.35 + progress * 0.10
        verts = []
        cols = []

        for i in range(self.rings):
            t = i / (self.rings - 1)
            a = angle - t * length
            p = self.point(a, progress)

            eps = 0.02
            p_next = self.point(a + eps, progress)
            tangent = (p_next - p).normalized()
            side = Vec3(tangent.z, 0, -tangent.x).normalized()
            up = Vec3.cross(tangent, side).normalized()

            # Movimento ondulatório lateral da coluna da cobra
            wave_val = math.sin(a * 4.0 - elapsed * 2.8) * 0.10 * (1.0 - t * 0.35)
            p = p + side * wave_val

            # Conicidade suave na cauda e transição na cabeça
            taper = 1.0
            if t > 0.82:
                taper = max(0.12, 1.0 - 0.88 * ((t - 0.82) / 0.18) ** 1.3)
            elif t < 0.08:
                taper = 0.84 + 0.16 * (t / 0.08)
            radius = base_radius * taper

            for k in range(self.sides):
                theta = k * math.tau / self.sides
                cos_t = math.cos(theta)
                sin_t = math.sin(theta)
                offset = side * (cos_t * radius) + up * (sin_t * radius)
                verts.append(p + offset)

                # Barriga verde-clara / turquesa original
                if sin_t < -0.22:
                    c = color.rgb32(104, 224, 185)
                else:
                    light = 0.65 + 0.35 * max(0.0, sin_t)
                    c = color.rgba(0.035 * light, 0.20 * light, 1.0 * light, 1.0)
                cols.append(c)

        self.mesh.vertices = verts
        self.mesh.triangles = self.triangles
        self.mesh.colors = cols
        self.mesh.generate()
