import os, math, time as clock, queue, threading, logging, random
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

camera.position = (0, 16, -14)
camera.rotation_x = 48
camera.fov = 52

AmbientLight(color=color.rgba32(180, 180, 200, 255))
sun = DirectionalLight(color=color.rgba32(255, 220, 200, 255))
sun.look_at(Vec3(1, -2, 1))

from garden import build_garden, TubeSnake
build_garden()
snake = TubeSnake()

# Head structure with front-facing opening mouth ("abrir a boca de frente")
head = Entity(shader=basic_lighting_shader, model='sphere', scale=(.91, .77, 1.08), color=color.rgb32(24, 74, 255))

# Eyes
eye_entities = []
for x in (-.27, .27):
    eye = Entity(parent=head, model='sphere', position=(x, .30, .38), scale=(.35, .40, .32), color=color.white)
    Entity(parent=eye, model='sphere', position=(0, 0, .40), scale=.53, color=color.black)
    eye_entities.append(eye)

# Snout / Upper jaw
snout = Entity(parent=head, model='sphere', position=(0, 0.04, 0.44), scale=(0.82, 0.38, 0.82), color=color.rgb32(24, 74, 255), shader=basic_lighting_shader)

# Lower jaw (rotates and opens downward facing forward)
jaw = Entity(parent=head, model='sphere', position=(0, -0.16, 0.38), scale=(0.78, 0.28, 0.74), color=color.rgb32(107, 228, 197), shader=basic_lighting_shader)

# Red/crimson inner mouth cavity, expands when mouth opens de frente
mouth_inside = Entity(parent=head, model='sphere', position=(0, -0.06, 0.48), scale=(0.54, 0.02, 0.44), color=color.rgb32(185, 25, 45))

# Cute front fangs that appear when mouth opens
fang_l = Entity(parent=head, model='cone', position=(-0.16, -0.02, 0.68), scale=(0.045, 0.11, 0.045), rotation_x=180, color=color.white, enabled=False)
fang_r = Entity(parent=head, model='cone', position=(0.16, -0.02, 0.68), scale=(0.045, 0.11, 0.045), rotation_x=180, color=color.white, enabled=False)

# Cute forked tongue that flicks out
tongue = Entity(parent=head, model='cube', position=(0, -0.10, 0.72), scale=(0.09, 0.025, 0.34), color=color.rgb32(255, 95, 60))

# Nostrils
for x in (-.14, .14):
    Entity(parent=head, model='sphere', position=(x, 0.11, 0.82), scale=.045, color=color.rgb32(15, 50, 180))

trail = []
angle = 0.0
tick = 0.0
elapsed = 0.0
celebrate = 0.0
explosion = 0.0
epoch = 0
last_owner = ''
speech_end = 0.0
mouth_open = 0.0

fruit = Entity(shader=basic_lighting_shader, model='sphere', color=color.red, scale=.55, position=(3, .35, 0))
Entity(parent=fruit, model='cube', scale=(.12, .5, .12), position=(0, .6, 0), color=color.rgb32(90, 55, 20))
Entity(parent=fruit, model='sphere', scale=(.55, .15, .25), position=(.28, .65, 0), color=color.lime)
flash = Entity(model='sphere', scale=.01, color=color.orange, unlit=True, enabled=False)

# HUD
Entity(parent=camera.ui, model='quad', position=(0, .40), scale=(.72, .12), color=color.rgba32(17, 39, 26, 220))
Text('B7  |  COBRINHA JARDIM', position=(-.31, .445), scale=1.5, color=color.rgb32(216, 255, 166))
score = Text('', position=(-.31, .397), scale=1)
Entity(parent=camera.ui, model='quad', position=(0, .325), scale=(.62, .018), color=color.rgb32(50, 34, 44))
bar = Entity(parent=camera.ui, model='quad', origin=(-.5, 0), z=-.01, position=(-.31, .325), scale=(.001, .018), color=color.rgb32(255, 187, 40))
card = Entity(parent=camera.ui, model='quad', position=(0, -.31), scale=(.7, .19), color=color.rgba32(17, 39, 26, 235))
avatar_card = Entity(parent=camera.ui, model='quad', position=(-.285, -.295), scale=.08, color=color.rgb32(130, 24, 40))
owner = Text('B7', position=(-.22, -.247), scale=.85, color=color.rgb32(255, 130, 140))
bubble = Text(state.last, position=(-.22, -.28), scale=.9, wordwrap=34)
gift_icon = Entity(parent=camera.ui, model='quad', position=(.28, -.24), scale=.06, color=color.white, enabled=False)
status = Text('1: maçã   2: bomba   C: comentário   P: painel', position=(-.32, -.435), scale=.67, color=color.gray)
banner = Text('', origin=(0, 0), y=.20, scale=2, color=color.gold)

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
image_version = 0
feeding = 0.0

if os.getenv('B7_SMOKE'):
    state.submit({'type': 'gift', 'gift_id': '5655', 'count': 25, 'user': 'Bruno'})

def input(key):
    if key in ('1', '2'):
        kind = 'apple' if key == '1' else 'bomb'
        gift = next((g for g in state.config['gifts'] if g['kind'] == kind), None)
        if gift:
            state.submit({'type': 'gift', 'gift_id': gift['id'], 'user': 'Teste B7', 'count': 1})
    if key == 'c':
        state.submit({'type': 'comment', 'user': 'Bruno', 'comment': 'Oi cobrinha! Como você está?'})
    if key == 'p':
        import webbrowser
        webbrowser.open('http://127.0.0.1:8765')
    if key == 'escape':
        application.quit()

def update():
    global angle, tick, elapsed, celebrate, explosion, epoch, speech_end, image_version, feeding, mouth_open
    dt = min(time.dt, .05)
    elapsed += dt

    # Movimento harmônico contínuo; nunca colide com ela mesma!
    progress = state.points / max(1, state.config['goal'])
    angle += dt * state.config['speed'] * .35
    head.position = TubeSnake.point(angle, progress)

    # Orientação e inclinação suave da cabeça
    eps = 0.015
    p_next = TubeSnake.point(angle + eps, progress)
    direction = p_next - head.position
    head.rotation_y = math.degrees(math.atan2(direction.x, direction.z))
    head.rotation_x = -math.degrees(math.atan2(direction.y, math.hypot(direction.x, direction.z)))

    tick += dt
    if tick >= .025:
        trail.insert(0, Vec3(head.position))
        del trail[600:]
        tick = 0

    # Atualiza o corpo longo da cobra (preenche a tela ao comer maçãs)
    snake.update(angle, progress, elapsed)

    # Animação de abrir a boca de frente ("abrir a boca de frente")
    mouth_target = 0.0
    if feeding > 0:
        # Mastigação rítmica de frente ao engolir maçãs
        chomp_phase = (1.2 - feeding) * 8.5
        mouth_target = 0.85 * max(0.0, math.sin(chomp_phase))
    elif elapsed < speech_end:
        # Articulação ao falar com a IA Groq
        mouth_target = 0.48 * abs(math.sin(elapsed * 16))

    mouth_open = lerp(mouth_open, mouth_target, dt * 20)
    jaw.y = -0.16 - mouth_open * 0.16
    jaw.rotation_x = mouth_open * 28
    mouth_inside.scale_y = 0.02 + mouth_open * 0.38
    mouth_inside.y = -0.06 - mouth_open * 0.08
    fang_l.enabled = (mouth_open > 0.12)
    fang_r.enabled = (mouth_open > 0.12)
    tongue.z = 0.72 + (math.sin(elapsed * 24) * 0.12 if mouth_open > 0.15 else 0.0)
    tongue.y = -0.10 - mouth_open * 0.08

    # Fruta decorativa e animação de comer
    fruit.y = .4 + math.sin(elapsed * 3) * .08
    fruit.rotation_y += dt * 60
    if feeding > 0:
        feeding -= dt
        # A maçã voa diretamente para a boca aberta da cobrinha
        mouth_pos = head.position + Vec3(direction.x, 0, direction.z).normalized() * 0.5
        fruit.position = lerp(fruit.position, mouth_pos, dt * 6.5)
        fruit.scale = max(.08, feeding * .55)
        if feeding <= 0:
            fruit.position = (random.uniform(-4, 4), .4, random.uniform(-4, 4))
            fruit.scale = .55

    if state.epoch != epoch:
        epoch = state.epoch
        trail.clear()

    for _ in range(20):
        try:
            e = state.events.get_nowait()
        except queue.Empty:
            break
        try:
            result = state.apply(e)
        except Exception:
            logging.exception('Evento inválido')
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
            feeding = 1.2
            fruit.scale = .65
            fruit.position = (head.x + 1.8, .5, head.z + 1.2)
            banner.text = '+' + str(result['amount']) + ' MAÇÃS!'
            celebrate = 1.8
            play_sfx('eat_apple', state)

        if result.get('wins'):
            celebrate = 4.0
            banner.text = 'META COMPLETA! NOVA RODADA!'
            play_sfx('victory', state)

    for _ in range(10):
        try:
            m = state.output.get_nowait()
        except queue.Empty:
            break
        speech_end = elapsed + min(12, len(m['text']) / 14)

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

    with state.lock:
        score.text = f"MAÇÃS {state.points}/{state.config['goal']}     METAS {state.wins}"
        bar.scale_x = max(.001, .62 * state.points / state.config['goal'])
        owner.text = state.user[:28]
        bubble.text = state.last

    if os.getenv('B7_SMOKE') and elapsed > 3:
        base.screenshot(namePrefix='preview.png', defaultFilename=False)
        application.quit()

app.run()
