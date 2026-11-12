"""Estado independente da renderização; presentes finalizados entram uma vez."""
import json, threading, queue, time, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT = {
    'goal': 100,
    'speed': 2.5,
    'voice': True,
    'sound': True,
    'ai_provider': 'groq',
    'model': 'llama-3.3-70b-versatile',
    'groq_api_key': '',
    'xai_api_key': '',
    'username': '',
    'gifts': [
        {'id': '5655', 'name': 'Rosa', 'kind': 'apple', 'amount': 1, 'image': ''},
        {'id': 'bomb', 'name': 'Bomba teste', 'kind': 'bomb', 'amount': 10, 'image': ''}
    ]
}

class GameState:
    def __init__(self, config=None):
        self.config = config or json.loads(json.dumps(DEFAULT))
        self.points = 0
        self.wins = 0
        self.events = queue.Queue(500)
        self.output = queue.Queue(100)
        self.lock = threading.RLock()
        self.last = 'Bem-vindo! Manda uma maçã!'
        self.user = 'B7'
        self.avatar = ''
        self.gift_image = ''
        self.log = []
        self.seen = {}
        self.connection = 'Modo demonstração'
        self.epoch = 0

    def submit(self, e):
        self.events.put_nowait(e)

    def reset(self):
        with self.lock:
            self.points = 0
            self.wins = 0
            self.epoch += 1
            self.user = 'B7'
            self.last = 'Rodada reiniciada! Manda maçãs!'
            self.log.insert(0, "Rodada reiniciada pelo painel")
            self.log = self.log[:30]

    def apply(self, e):
        with self.lock:
            event_id = e.get('event_id')
            if event_id and event_id in self.seen:
                return None
            if event_id:
                self.seen[event_id] = time.monotonic()
                if len(self.seen) > 5000:
                    self.seen = {k: v for k, v in self.seen.items() if time.monotonic() - v < 600}
            self.user = str(e.get('user', 'Visitante'))[:50]
            self.avatar = str(e.get('avatar', ''))[:2048]
            if e.get('type') == 'comment':
                return {'type': 'comment', 'user': self.user, 'text': str(e.get('comment', ''))[:250]}
            gift = next((g for g in self.config['gifts'] if str(g['id']) == str(e.get('gift_id'))), None)
            if not gift:
                return None
            count = max(1, min(10000, int(e.get('count', 1))))
            amount = gift['amount'] * count
            self.gift_image = gift.get('image', '')
            if gift['kind'] == 'bomb':
                self.points = max(0, self.points - amount)
            else:
                self.points += amount
            goal = self.config['goal']
            victories = self.points // goal
            self.wins += victories
            self.points %= goal
            result = {
                'type': gift['kind'],
                'amount': amount,
                'count': count,
                'user': self.user,
                'gift': gift['name'],
                'wins': victories,
                'avatar': self.avatar,
                'image': self.gift_image
            }
            self.log.insert(0, f"{self.user}: {gift['name']} x{count}")
            self.log = self.log[:30]
            return result

    def snapshot(self):
        with self.lock:
            return {
                'points': self.points,
                'wins': self.wins,
                'goal': self.config['goal'],
                'last': self.last,
                'user': self.user,
                'connection': self.connection,
                'log': self.log,
                'config': self.config
            }

def validate(c):
    c['goal'] = int(c['goal'])
    c['speed'] = float(c['speed'])
    if not 1 <= c['goal'] <= 1000000 or not 0.2 <= c['speed'] <= 10:
        raise ValueError('Meta ou velocidade fora do limite')
    c['voice'] = bool(c.get('voice', True))
    c['sound'] = bool(c.get('sound', True))
    c['ai_provider'] = str(c.get('ai_provider', 'groq')).strip().lower()
    if c['ai_provider'] not in ('groq', 'xai'):
        c['ai_provider'] = 'groq'
    c['model'] = str(c.get('model', 'llama-3.3-70b-versatile')).strip()[:80]
    c['groq_api_key'] = str(c.get('groq_api_key', '')).strip()[:200]
    c['xai_api_key'] = str(c.get('xai_api_key', '')).strip()[:200]
    c['username'] = str(c.get('username', '')).strip()[:80]
    if not isinstance(c.get('gifts'), list) or len(c['gifts']) > 100:
        raise ValueError('Máximo 100 presentes')
    ids = set()
    for g in c['gifts']:
        g['id'] = str(g['id']).strip()
        g['amount'] = int(g['amount'])
        if not g['id'] or g['id'] in ids or g['kind'] not in ('apple', 'bomb') or not 1 <= g['amount'] <= 100000:
            raise ValueError('Confira ID único, tipo e quantidade de cada presente')
        ids.add(g['id'])
        g['name'] = str(g['name'])[:80]
        g['image'] = str(g.get('image', ''))[:2048]
    return c

def load():
    try:
        return validate({**DEFAULT, **json.loads((ROOT / 'config.json').read_text('utf-8'))})
    except (OSError, ValueError, TypeError, KeyError):
        return json.loads(json.dumps(DEFAULT))

def save(c):
    validate(c)
    p = ROOT / 'config.tmp'
    p.write_text(json.dumps(c, ensure_ascii=False, indent=2), 'utf-8')
    p.replace(ROOT / 'config.json')
