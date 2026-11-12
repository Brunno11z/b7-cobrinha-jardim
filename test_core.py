import unittest, json
from core import GameState, DEFAULT, validate

class Tests(unittest.TestCase):
    def setUp(self):
        self.s = GameState(json.loads(json.dumps(DEFAULT)))

    def gift(self, id, n=1, **kw):
        return self.s.apply(dict(type='gift', gift_id=id, count=n, user='Bruno', **kw))

    def test_goal(self):
        r = self.gift('5655', 235)
        self.assertEqual((self.s.points, self.s.wins), (35, 2))
        self.assertEqual(r['wins'], 2)

    def test_bomb_floor(self):
        self.gift('5655', 3)
        self.gift('bomb')
        self.assertEqual(self.s.points, 0)

    def test_duplicate(self):
        self.gift('5655', 5, event_id='a')
        self.gift('5655', 5, event_id='a')
        self.assertEqual(self.s.points, 5)

    def test_comment_no_points(self):
        self.s.apply({'type': 'comment', 'comment': '100 maçãs'})
        self.assertEqual(self.s.points, 0)

    def test_unknown(self):
        self.assertIsNone(self.gift('missing'))

    def test_validation(self):
        self.s.config['goal'] = 0
        with self.assertRaises(ValueError):
            validate(self.s.config)

    def test_groq_and_sound_config(self):
        self.assertEqual(self.s.config['ai_provider'], 'groq')
        self.assertEqual(self.s.config['model'], 'llama-3.3-70b-versatile')
        self.assertTrue(self.s.config['sound'])
        self.s.config['groq_api_key'] = 'gsk_test'
        c = validate(self.s.config)
        self.assertEqual(c['groq_api_key'], 'gsk_test')

    def test_reset(self):
        self.gift('5655', 10)
        self.assertEqual(self.s.points, 10)
        self.s.reset()
        self.assertEqual(self.s.points, 0)
        self.assertEqual(self.s.wins, 0)
        self.assertEqual(self.s.epoch, 1)

if __name__ == '__main__':
    unittest.main()
