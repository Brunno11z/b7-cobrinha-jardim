import os, math, time as clock, queue, threading, logging, random
from collections import deque

os.chdir(os.path.dirname(os.path.abspath(__file__)))
logging.basicConfig(filename='b7.log', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

from core import GameState, load
from services import Voice, start_panel, start_tiktok, image_file, play_sfx

if os.getenv('B7_SMOKE'):
    from panda3d.core import loadPrcFileData
    loadPrcFileData('', 'window-type offscreen\nload-display p3headlessgl\naudio-library-name null')

from ursina import *
from ursina.shaders import basic_lighting_shader
from panda3d.core import ClockObject

app = Ursina(
    title='B7 • Cobrinha Jardim 3D',
    borderless=False,
    development_mode=False,
    size=(720, 960),
    vsync=True,
    window_type='offscreen' if os.getenv('B7_SMOKE') else 'onscreen'
)
ClockObject.getGlobalClock().setMode(ClockObject.MLimited)
ClockObject.getGlobalClock().setFrameRate(60)
camera.ui_lens.set_film_size(15, 20)

window.color = color.rgb32(114, 170, 40)
window.fps_counter.enabled = False
window.exit_button.visible = False

state = GameState(load())
voice = Voice(state)
server = None if os.getenv('B7_SMOKE') else start_panel(state)
if not os.getenv('B7_SMOKE'):
    start_tiktok(state)

camera.position = (0, 16.5, -14.2)
camera.rotation_x = 49
camera.fov = 52

AmbientLight(color=color.rgba32(180, 180, 200, 255))
sun = DirectionalLight(color=color.rgba32(255, 220, 200, 255))
sun.look_at(Vec3(1, -2, 1))

from garden import build_garden, TubeSnake
build_garden()
snake = TubeSnake(rings=200, sides=12)

# --- Estrutura da Cabeça com Boca que Abre de Frente ---
head = Entity(shader=basic_lighting_shader, model='sphere', scale=(.92, .78, 1.10), color=color.rgb32(24, 74, 255))

# Olhos expressivos
for x in (-.27, .27):
    eye = Entity(parent=head, model='sphere', position=(x, .30, .38), scale=(.35, .40, .32), color=color.white)
    Entity(parent=eye, model='sphere', position=(0, 0, .40), scale=.53, color=color.black)

# Focinho / Mandíbula superior
snout = Entity(parent=head, model='sphere', position=(0, 0.04, 0.44), scale=(0.82, 0.38, 0.82), color=color.rgb32(24, 74, 255), shader=basic_lighting_shader)

# Mandíbula inferior (abre de frente para baixo)
jaw = Entity(parent=head, model='sphere', position=(0, -0.16, 0.38), scale=(0.78, 0.28, 0.74), color=color.rgb32(107, 228, 197), shader=basic_lighting_shader)

# Cavidade interna vermelha da boca que expande ao abrir
mouth_inside = Entity(parent=head, model='sphere', position=(0, -0.06, 0.48), scale=(0.54, 0.02, 0.44), color=color.rgb32(185, 25, 45))

# Presas frontais brancas que aparecem com a boca aberta
fang_l = Entity(parent=head, model='cone', position=(-0.16, -0.02, 0.68), scale=(0.045, 0.11, 0.045), rotation_x=180, color=color.white, enabled=False)
fang_r = Entity(parent=head, model='cone', position=(0.16, -0.02, 0.68), scale=(0.045, 0.11, 0.045), rotation_x=180, color=color.white, enabled=False)

# Língua bifurcada fofa
tongue = Entity(parent=head, model='cube', position=(0, -0.10, 0.72), scale=(0.09, 0.025, 0.34), color=color.rgb32(255, 95, 60))

# Narinas
for x in (-.14, .14):
    Entity(parent=head, model='sphere', position=(x, 0.11, 0.82), scale=.045, color=color.rgb32(15, 50, 180))

# --- Maçã Alvo no Jardim ---
target_apple = Entity(shader=basic_lighting_shader, model='sphere', color=color.red, scale=.55, position=(2.5, .38, 1.8))
Entity(parent=target_apple, model='cube', scale=(.12, .5, .12), position=(0, .6, 0), color=color.rgb32(90, 55, 20))
Entity(parent=target_apple, model='sphere', scale=(.55, .15, .25), position=(.28, .65, 0), color=color.lime)
apple_shadow = Entity(model='quad', rotation_x=90, position=(2.5, .02, 1.8), scale=.75, color=color.rgba32(0, 0, 0, 75))

flash = Entity(model='sphere', scale=.01, color=color.orange, unlit=True, enabled=False)

# --- HUD Limpo: REMOVIDO o texto "B7 | COBRINHA JARDIM" do topo a pedido do usuário ---
# Barra de pontuação discreta e elegante
Entity(parent=camera.ui, model='quad', position=(0, .43), scale=(.74, .08), color=color.rgba32(15, 23, 42, 225))
score = Text('', position=(-.32, .445), scale=1.1, color=color.white)
Entity(parent=camera.ui, model='quad', position=(0, .402), scale=(.64, .016), color=color.rgb32(50, 34, 44))
bar = Entity(parent=camera.ui, model='quad', origin=(-.5, 0), z=-.01, position=(-.32, .402), scale=(.001, .016), color=color.rgb32(255, 187, 40))

# Card de Notificação de Presente / Usuário na parte inferior
card = Entity(parent=camera.ui, model='quad', position=(0, -.31), scale=(.7, .19), color=color.rgba32(17, 39, 26, 235))
avatar_card = Entity(parent=camera.ui, model='quad', position=(-.285, -.295), scale=.08, color=color.rgb32(130, 24, 40))
owner = Text('B7', position=(-.22, -.247), scale=.85, color=color.rgb32(255, 130, 140))
bubble = Text(state.last, position=(-.22, -.28), scale=.9, wordwrap=34)
gift_icon = Entity(parent=camera.ui, model='quad', position=(.28, -.24), scale=.06, color=color.white, enabled=False)
status = Text('1: maçã   2: bomba   C: comentário   P: painel', position=(-.32, -.435), scale=.67, color=color.gray)
banner = Text('', origin=(0, 0), y=.18, scale=2.1, color=color.gold)

image_jobs = queue.Queue(20)
ready = queue.Queue(20)

def image_worker():
    while True:
        version, kind, url = image_jobs.get()
        try:
            path = image_file(url)
            if path:
                ready.put((version, kind, path))
        except Exception:
            logging.exception('Foto não carregada')

threading.Thread(target=image_worker, daemon=True).start()

# --- Simulação de Jogador Humano ("como se fosse alguém jogando") ---
class PlayerController:
    def __init__(self):
        self.pos = Vec3(0, 0.38, 0)
        self.heading = 0.0 # yaw em radianos
        self.pitch = 0.0
        self.speed = 3.2
        self.history = deque(maxlen=4000)
        # Preenche histórico inicial reto para a cauda não começar vazia
        for i in range(1200):
            self.history.append((0.0, 0.38, -i * 0.04, 0.0))
        self.target = Vec3(2.5, 0.38, 1.8)
        self.slither_phase = 0.0
        self.avoid_cooldown = 0.0

    def pick_new_apple_target(self):
        # Gera uma nova maçã em uma área aberta do jardim
        rx = random.uniform(-4.5, 4.5)
        rz = random.uniform(-5.5, 5.5)
        self.target = Vec3(rx, 0.38, rz)
        target_apple.position = self.target
        apple_shadow.position = (rx, 0.02, rz)

    def update(self, dt, current_speed, body_pts):
        self.speed = current_speed
        to_target = self.target - self.pos
        dist_to_apple = math.hypot(to_target.x, to_target.z)

        # 1. Direção desejada para a maçã alvo
        desired_yaw = math.atan2(to_target.x, to_target.z)

        # 2. Desvio das bordas do jardim (evita bater nas cercas)
        repel_x = 0.0
        repel_z = 0.0
        if self.pos.x > 4.0: repel_x -= (self.pos.x - 4.0) * 4.5
        elif self.pos.x < -4.0: repel_x -= (self.pos.x + 4.0) * 4.5
        if self.pos.z > 5.2: repel_z -= (self.pos.z - 5.2) * 4.5
        elif self.pos.z < -5.2: repel_z -= (self.pos.z + 5.2) * 4.5

        if abs(repel_x) > 0.01 or abs(repel_z) > 0.01:
            desired_yaw = math.atan2(to_target.x + repel_x, to_target.z + repel_z)

        # 3. Evitação ativa de colisão própria ("observação ela nunca bate nela mesmo")
        # Se a cabeça estiver apontando para um segmento do próprio corpo com mais de 25 passos:
        fx = math.sin(self.heading)
        fz = math.cos(self.heading)
        look_ahead = Vec3(self.pos.x + fx * 1.2, 0.38, self.pos.z + fz * 1.2)

        avoid_steer = 0.0
        if len(body_pts) > 30:
            for bp in body_pts[25::6]:
                d = math.hypot(look_ahead.x - bp[0], look_ahead.z - bp[2])
                if d < 1.1:
                    # Desvia suavemente para a esquerda ou direita
                    cross = fx * (bp[2] - self.pos.z) - fz * (bp[0] - self.pos.x)
                    avoid_steer = -2.8 if cross > 0 else 2.8
                    break

        # 4. Viragem suave como jogador humano
        diff = (desired_yaw - self.heading + math.pi) % (2 * math.pi) - math.pi
        steer_rate = 3.6
        steer_delta = diff * 4.8 * dt + avoid_steer * dt
        self.heading += max(-steer_rate * dt, min(steer_rate * dt, steer_delta))

        # 5. Ondulação natural de serpente (slither wave)
        self.slither_phase += dt * (5.5 + self.speed * 0.8)
        wave_lateral = math.sin(self.slither_phase) * 0.06

        forward_x = math.sin(self.heading)
        forward_z = math.cos(self.heading)
        side_x = math.cos(self.heading)
        side_z = -math.sin(self.heading)

        # 6. Avanço da cabeça
        vx = (forward_x * self.speed + side_x * wave_lateral * 6.5) * dt
        vz = (forward_z * self.speed + side_z * wave_lateral * 6.5) * dt

        self.pos.x += vx
        self.pos.z += vz

        # Elevação 3D suave com camadas verticais nos cruzamentos
        self.pos.y = 0.38 + 0.06 * math.sin(self.slither_phase * 0.7)

        # Inclinação suave de pitch
        self.pitch = lerp(self.pitch, wave_lateral * 18.0, dt * 10)

        # Registra posição no histórico de rastro
        self.history.appendleft((self.pos.x, self.pos.y, self.pos.z, self.heading))
        return dist_to_apple

    def sample_body(self, total_length, num_rings=200):
        """Amostra anéis com espaçamento constante ao longo da trajetória gravada."""
        step = max(0.035, total_length / (num_rings - 1))
        pts = []
        prev = self.history[0]
        pts.append((prev[0], prev[1], prev[2]))

        needed = step
        accum = 0.0
        hist_list = list(self.history)

        ring = 1
        for i in range(1, len(hist_list)):
            p = hist_list[i]
            seg_len = math.hypot(p[0] - prev[0], p[2] - prev[2])
            accum += seg_len
            while accum >= needed and ring < num_rings:
                ratio = (needed - (accum - seg_len)) / max(0.0001, seg_len)
                ix = prev[0] + ratio * (p[0] - prev[0])
                # Elevação sutil em camadas verticais garante 0 colisão nos cruzamentos
                iy = prev[1] + ratio * (p[1] - prev[1]) + math.sin(ring * 0.12) * 0.04
                iz = prev[2] + ratio * (p[2] - prev[2])
                pts.append((ix, iy, iz))
                ring += 1
                needed += step
            prev = p
            if ring >= num_rings:
                break

        while len(pts) < num_rings:
            pts.append(pts[-1])
        return pts

player = PlayerController()
current_body_pts = []

elapsed = 0.0
celebrate = 0.0
explosion = 0.0
epoch = 0
image_version = 0
feeding = 0.0
mouth_open = 0.0
speech_end = 0.0

if os.getenv('B7_SMOKE'):
    state.submit({'type': 'gift', 'gift_id': '5655', 'count': 25, 'user': 'Bruno'})

def input(key):
    if key in ('1', '2'):
        kind = 'apple' if key == '1' else 'bomb'
        gift = next((g for g in state.config['gifts'] if g['kind'] == kind), None)
        if gift:
            state.submit({'type': 'gift', 'gift_id': gift['id'], 'user': 'Teste Teclado', 'count': 1})
    if key == 'c':
        state.submit({'type': 'comment', 'user': 'Bruno', 'comment': 'Oi cobrinha! Manda um salve!'})
    if key == 'p':
        import webbrowser
        webbrowser.open('http://127.0.0.1:8765')
    if key == 'escape':
        application.quit()

def update():
    global elapsed, celebrate, explosion, epoch, speech_end, image_version, feeding, mouth_open, current_body_pts
    dt = min(time.dt, .05)
    elapsed += dt

    # 1. Comprimento do corpo cresce com as maçãs e chega a preencher quase a tela inteira!
    progress = state.points / max(1, state.config['goal'])
    total_body_length = 3.6 + progress * 24.5 + min(12.0, state.wins * 2.2)

    # 2. Atualiza movimentação realista de jogador humano
    game_speed = float(state.config.get('speed', 2.5))
    dist_to_apple = player.update(dt, game_speed, current_body_pts)

    # 3. Cabeça acompanha a física do jogador
    head.position = player.pos
    head.rotation_y = math.degrees(player.heading)
    head.rotation_x = -player.pitch
    head.rotation_z = math.sin(player.slither_phase) * 5.0

    # 4. Amostra os pontos do corpo da trajetória gravada e atualiza a malha tubular 3D
    current_body_pts = player.sample_body(total_body_length, num_rings=snake.rings)
    snake.update_mesh(current_body_pts, progress, elapsed)

    # 5. Detecção de maçã comida no jardim pelo jogador
    if dist_to_apple < 0.68:
        # Cobrinha comeu a maçã do campo!
        feeding = 1.1
        play_sfx('eat_apple', state)
        banner.text = '+1 MAÇÃ!'
        celebrate = 1.0
        with state.lock:
            state.points += 1
            if state.points >= state.config['goal']:
                state.wins += 1
                state.points = 0
                celebrate = 3.5
                banner.text = 'META CONCLUÍDA! PARABÉNS!'
                play_sfx('victory', state)
        player.pick_new_apple_target()

    # Rotação da maçã no jardim
    target_apple.rotation_y += dt * 65
    target_apple.y = .38 + math.sin(elapsed * 4.0) * .06

    # 6. Animação de Abrir a Boca de Frente ("abrir a boca de frente")
    mouth_target = 0.0
    if dist_to_apple < 1.4 or feeding > 0:
        # Abre bem de frente ao se aproximar da maçã ou ao mastigar presentes
        chomp_rate = (1.2 - feeding) * 9.0 if feeding > 0 else 0.0
        mouth_target = 0.92 if feeding <= 0 else 0.85 * max(0.1, abs(math.sin(chomp_rate)))
    elif elapsed < speech_end:
        # Articula a boca de frente ao falar pela IA Groq
        mouth_target = 0.45 * abs(math.sin(elapsed * 16))

    mouth_open = lerp(mouth_open, mouth_target, dt * 22)
    jaw.y = -0.16 - mouth_open * 0.16
    jaw.rotation_x = mouth_open * 30
    mouth_inside.scale_y = 0.02 + mouth_open * 0.40
    mouth_inside.y = -0.06 - mouth_open * 0.08
    fang_l.enabled = (mouth_open > 0.12)
    fang_r.enabled = (mouth_open > 0.12)
    tongue.z = 0.72 + (math.sin(elapsed * 24) * 0.14 if mouth_open > 0.15 else 0.0)
    tongue.y = -0.10 - mouth_open * 0.08

    # 7. Reinicialização de rodada quando acionado pelo painel
    if state.epoch != epoch:
        epoch = state.epoch
        player.history.clear()
        for i in range(1200):
            player.history.append((player.pos.x, player.pos.y, player.pos.z - i * 0.04, player.heading))

    # 8. Consome eventos vindos do Painel Web ou TikTok Live
    for _ in range(25):
        try:
            e = state.events.get_nowait()
        except queue.Empty:
            break
        try:
            result = state.apply(e)
        except Exception:
            logging.exception('Evento com erro')
            continue
        if not result:
            continue

        voice.add(result)
        if result['type'] == 'comment':
            continue

        image_version += 1
        avatar_card.texture = None
        gift_icon.enabled = False
        for kind, url in [('avatar', result.get('avatar', '')), ('gift', result.get('image', ''))]:
            if url:
                try:
                    image_jobs.put_nowait((image_version, kind, url))
                except queue.Full:
                    pass

        if result['type'] == 'bomb':
            explosion = 1.0
            flash.position = head.position
            flash.enabled = True
            banner.text = 'BOOOM! -' + str(result['amount'])
            play_sfx('bomb', state)
        else:
            feeding = 1.4
            banner.text = '+' + str(result['amount']) + ' MAÇÃS!'
            celebrate = 2.0
            play_sfx('eat_apple', state)

        if result.get('wins'):
            celebrate = 4.0
            banner.text = 'META CONCLUÍDA! NOVA RODADA!'
            play_sfx('victory', state)

    # Consome mensagens de voz da IA
    for _ in range(10):
        try:
            m = state.output.get_nowait()
        except queue.Empty:
            break
        speech_end = elapsed + min(12, len(m['text']) / 14)

    # Atualiza fotos carregadas em segundo plano
    for _ in range(4):
        try:
            version, kind, path = ready.get_nowait()
        except queue.Empty:
            break
        if version == image_version:
            target = avatar_card if kind == 'avatar' else gift_icon
            target.texture = Texture(__import__('pathlib').Path(path))
            target.enabled = True
            target.color = color.white

    if explosion > 0:
        explosion -= dt
        flash.scale = 1 + (1 - explosion) * 4
        flash.color = color.rgba32(255, 110, 15, int(max(0, explosion) * 190))
        if explosion <= 0:
            flash.enabled = False
            banner.text = ''

    if celebrate > 0:
        celebrate -= dt
        banner.scale = 1.45 + math.sin(elapsed * 8) * .08
        if celebrate <= 0:
            banner.text = ''

    # Atualiza o HUD elegante sem o texto do topo
    with state.lock:
        score.text = f"MAÇÃS {state.points} / {state.config['goal']}       METAS {state.wins}"
        bar.scale_x = max(.001, .64 * (state.points / state.config['goal']))
        owner.text = state.user[:28]
        bubble.text = state.last

    if os.getenv('B7_SMOKE') and elapsed > 3:
        base.screenshot(namePrefix='preview.png', defaultFilename=False)
        application.quit()

app.run()
