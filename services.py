"""Serviços em segundo plano: IA Groq/xAI, voz TTS, painel web HTTP e TikTok."""
import os, json, time, threading, queue, logging, io, base64, hashlib, wave, struct
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from PIL import Image
import requests
from core import ROOT, validate, save

# --- Sistema de Efeitos Sonoros WAV Não-Bloqueante ---
def play_sfx(name, state=None):
    if state and not state.config.get('sound', True):
        return
    def _run():
        try:
            sound_path = ROOT / 'assets' / f'{name}.wav'
            if not sound_path.exists():
                return
            if os.name == 'nt':
                import winsound
                winsound.PlaySound(str(sound_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                pass
        except Exception:
            logging.exception(f'Erro ao reproduzir som {name}')
    threading.Thread(target=_run, daemon=True).start()

class Voice:
    def __init__(self, state):
        self.state = state
        self.queue = queue.Queue(40)
        self.busy = False
        threading.Thread(target=self._worker, daemon=True).start()

    def add(self, ev):
        try:
            self.queue.put_nowait(ev)
        except queue.Full:
            pass

    def _ai_response(self, prompt):
        cfg = self.state.config
        provider = cfg.get('ai_provider', 'groq')
        groq_key = os.getenv('GROQ_API_KEY') or cfg.get('groq_api_key', '')
        xai_key = os.getenv('XAI_API_KEY') or cfg.get('xai_api_key', '')

        if provider == 'groq' and groq_key:
            model = cfg.get('model') or 'llama-3.3-70b-versatile'
            url = 'https://api.groq.com/openai/v1/chat/completions'
            headers = {
                'Authorization': f'Bearer {groq_key}',
                'Content-Type': 'application/json'
            }
            body = {
                'model': model,
                'messages': [
                    {
                        'role': 'system',
                        'content': 'Você é a Cobrinha Jardim da live do TikTok B7. Responda em português brasileiro de forma carinhosa, fofa, divertida, animada e em no máximo 1 ou 2 frases curtas (máximo 25 palavras) para a live ser rápida.'
                    },
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 60,
                'temperature': 0.75
            }
            try:
                r = requests.post(url, headers=headers, json=body, timeout=4.0)
                if r.ok:
                    data = r.json()
                    return data['choices'][0]['message']['content'].strip()
                logging.warning(f"Groq API erro {r.status_code}: {r.text}")
            except Exception as e:
                logging.warning(f"Falha na requisição Groq: {e}")

        if xai_key:
            model = 'grok-4.7'
            url = 'https://api.x.ai/v1/chat/completions'
            headers = {
                'Authorization': f'Bearer {xai_key}',
                'Content-Type': 'application/json'
            }
            body = {
                'model': model,
                'messages': [
                    {
                        'role': 'system',
                        'content': 'Você é a Cobrinha Jardim da live do TikTok B7. Responda em português brasileiro de forma carinhosa, fofa e em no máximo 1 ou 2 frases curtas.'
                    },
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 60,
                'temperature': 0.7
            }
            try:
                r = requests.post(url, headers=headers, json=body, timeout=4.0)
                if r.ok:
                    data = r.json()
                    return data['choices'][0]['message']['content'].strip()
            except Exception as e:
                logging.warning(f"Falha na requisição xAI: {e}")

        return None

    def _worker(self):
        engine = None
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty('rate', 185)
            engine.setProperty('volume', 0.95)
        except Exception:
            logging.warning('TTS pyttsx3 não disponível neste ambiente')

        while True:
            ev = self.queue.get()
            u = ev.get('user', 'Visitante')
            t = ev.get('type')

            if t == 'bomb':
                prompt = f"O usuário {u} jogou uma bomba teste na cobrinha! Reaja com susto cômico e peça maçãs doces para sarar."
                fallback = f"Ai {u}! Uma bomba! Manda maçãs pra cobrinha se recuperar!"
            elif t == 'comment':
                comment_text = ev.get('text', '')
                prompt = f"O espectador {u} comentou na live: '{comment_text}'. Responda com simpatia e alegria."
                fallback = f"Oi {u}! Um abraço carinhoso da Cobrinha pra você!"
            else:
                amt = ev.get('amount', 1)
                gift_name = ev.get('gift', 'maçã')
                wins = ev.get('wins', 0)
                if wins > 0:
                    prompt = f"O usuário {u} enviou {gift_name} x{ev.get('count', 1)} e BATEU A META DA LIVE! Comemore a vitória efusivamente!"
                    fallback = f"Sensacional {u}! Batemos a meta da rodada! Obrigado pelo apoio!"
                else:
                    prompt = f"O usuário {u} deu {gift_name} x{ev.get('count', 1)} somando {amt} maçãs para a cobrinha comer. Agradeça alegremente."
                    fallback = f"Obrigada {u} pelas {amt} maçãs deliciosas! Adorei!"

            ai_text = self._ai_response(prompt)
            final_text = ai_text if ai_text else fallback

            with self.state.lock:
                self.state.last = final_text

            self.state.output.put_nowait({'text': final_text, 'user': u})

            if engine and self.state.config.get('voice', True):
                try:
                    self.busy = True
                    engine.say(final_text)
                    engine.runAndWait()
                except Exception:
                    logging.exception('Erro na fala TTS')
                finally:
                    self.busy = False

# --- Servidor HTTP do Painel com CORS completo e suporte a todas interações ---
def start_panel(state):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def send(self, obj, status=200):
            body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Accept')
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self):
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Accept')
            self.end_headers()

        def do_GET(self):
            if self.path == '/api/state':
                return self.send(state.snapshot())
            if self.path == '/' or self.path.startswith('/?'):
                data = (ROOT / 'panel.html').read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send({'error': 'Não encontrado'}, 404)

        def do_POST(self):
            try:
                length = int(self.headers.get('Content-Length', 0))
                if not 0 <= length <= 4_200_000:
                    raise ValueError('Pedido muito grande')
                raw_data = self.rfile.read(length) if length > 0 else b'{}'
                data = json.loads(raw_data.decode('utf-8')) if raw_data else {}

                if self.path == '/api/config':
                    c = validate(data)
                    with state.lock:
                        save(c)
                        state.config = c
                    return self.send({'ok': True, 'msg': 'Configurações salvas com sucesso!'})

                if self.path == '/api/event':
                    if data.get('type') not in ('gift', 'comment'):
                        raise ValueError('Tipo de evento inválido')
                    count = int(data.get('count', 1))
                    if not 1 <= count <= 10000:
                        raise ValueError('Quantidade de presentes deve ser entre 1 e 10000')
                    state.submit(data)
                    return self.send({'ok': True, 'msg': 'Evento enviado para a cobrinha!'})

                if self.path == '/api/test-sound':
                    sfx_name = data.get('sound', 'eat_apple')
                    play_sfx(sfx_name, state)
                    return self.send({'ok': True, 'msg': f'Som {sfx_name} reproduzido com sucesso!'})

                if self.path == '/api/reset':
                    state.reset()
                    return self.send({'ok': True, 'msg': 'Rodada reiniciada!'})

                if self.path == '/api/upload':
                    raw = base64.b64decode(data['data'])
                    im = Image.open(io.BytesIO(raw))
                    im.thumbnail((256, 256))
                    name = 'gift_' + hashlib.sha256(raw).hexdigest()[:20] + '.png'
                    im.convert('RGBA').save(ROOT / 'assets' / name)
                    return self.send({'ok': True, 'path': 'assets/' + name})

                return self.send({'error': 'Rota não encontrada'}, 404)
            except Exception as ex:
                logging.exception('Erro no processamento do painel')
                return self.send({'error': str(ex)}, 400)

    server = HTTPServer(('0.0.0.0', 8765), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server

# --- Conector TikTok Live ---
def start_tiktok(state):
    def _run():
        username = state.config.get('username', '').strip()
        if not username:
            state.connection = 'Painel local pronto (TikTok desconectado)'
            return
        try:
            from TikTokLive import TikTokLiveClient
            from TikTokLive.events import ConnectEvent, DisconnectEvent, GiftEvent, CommentEvent

            client = TikTokLiveClient(unique_id=username)

            @client.on(ConnectEvent)
            async def on_connect(event):
                state.connection = f'Conectado à live de {username}!'

            @client.on(DisconnectEvent)
            async def on_disconnect(event):
                state.connection = f'Live de {username} desconectada'

            @client.on(GiftEvent)
            async def on_gift(event):
                streakable = event.gift.streakable
                if streakable and not event.gift.streak_end:
                    return
                avatar_url = event.user.avatar.urls[0] if event.user and event.user.avatar else ''
                state.submit({
                    'type': 'gift',
                    'gift_id': str(event.gift.info.id),
                    'count': event.gift.count,
                    'user': event.user.nickname or event.user.unique_id,
                    'avatar': avatar_url,
                    'image': event.gift.image.urls[0] if event.gift.image else '',
                    'event_id': f"{event.user.unique_id}_{event.gift.info.id}_{event.gift.repeat_count}"
                })

            @client.on(CommentEvent)
            async def on_comment(event):
                avatar_url = event.user.avatar.urls[0] if event.user and event.user.avatar else ''
                state.submit({
                    'type': 'comment',
                    'user': event.user.nickname or event.user.unique_id,
                    'comment': event.comment,
                    'avatar': avatar_url
                })

            state.connection = f'Conectando ao @{username}...'
            client.run()
        except Exception as e:
            state.connection = f'Erro no TikTok: {e}'
            logging.exception('Falha TikTok')

    threading.Thread(target=_run, daemon=True).start()

def image_file(url):
    if not url.startswith('http'):
        p = ROOT / url
        return str(p) if p.exists() else None
    name = hashlib.sha256(url.encode()).hexdigest()[:24] + '.png'
    p = ROOT / 'assets' / name
    if p.exists():
        return str(p)
    try:
        r = requests.get(url, timeout=3.5)
        if r.ok:
            im = Image.open(io.BytesIO(r.content))
            im.thumbnail((128, 128))
            im.convert('RGBA').save(p)
            return str(p)
    except Exception:
        pass
    return None
