import tornado.ioloop
import tornado.web
import tornado.websocket
import json
import random
import asyncio

matches = {}
clients = set()


def randomize_matches(teams, num_matches):
    stati = ['live', 'scheduled']
    sports = list(teams.keys())
    print(sports)
    matches = []

    for i in range(1, num_matches + 1):
        sport = random.choice(sports)
        team1, team2 = random.sample(teams[sport], 2)
        status = random.choice(stati)
        matches.append(
            (str(i), sport, team1, team2, status)
        )

    return matches

def read_json(file):
    with open(file) as f:
        read = json.load(f)
    return read

class Match:

    def __init__(self, match_id, sport, home_team, away_team, status='scheduled'):
        self.id = match_id
        self.sport = sport
        self.home_team = home_team
        self.away_team = away_team
        self.home_score = 0
        self.away_score = 0
        self.status = status
        self.events = []
        self.time = 0

        if sport == 'basketball':
            if status == 'scheduled':
                self.quarter = 1
                self.time = 0
            elif status == 'finished':
                self.quarter = 4
                self.time = 12
            else:
                self.quarter = random.randint(2, 3)
                self.time = random.randint(5, 8)


        elif sport == 'judo':
            self.max_time = 4
            self.time = 0 if status == 'scheduled' else random.randint(0, 180)
            self.ippon = False
            self.wazari_home = 0
            self.wazari_away = 0
            self.shido_home = 0
            self.shido_away = 0


        if status == 'live':
            self._add_initial_events()

    def _add_initial_events(self):
        if self.sport == 'basketball' and self.time > 5:
            self.home_score = random.randint(40, 80)
            self.away_score = random.randint(40, 80)
            for _ in range(random.randint(3, 6)):
                self.events.append({
                    'id': len(self.events) + 1,
                    'minute': random.randint(1, self.time),
                    'quarter': random.randint(1, self.quarter),
                    'type': 'basket',
                    'team': random.choice(['home', 'away']),
                    'points': random.choice([2, 3])
                })

        elif self.sport == 'judo' and self.time > 30:
            if random.random() < 0.3:
                self.wazari_home = random.randint(0, 1)
                self.wazari_away = random.randint(0, 1)
                self.shido_home = random.randint(0, 2)
                self.shido_away = random.randint(0, 2)


    def update(self):
        if self.status != 'live':
            return None

        event = None

        if self.sport == 'basketball':
            self.time += 1

            if random.random() < 0.18:
                team = random.choice(['home', 'away'])
                points = random.choices([2, 3], weights=[0.65, 0.35])[0]
                player= random.randint(1,15)
                if team=="home":
                    teamname=self.home_team

                else:
                    teamname=self.away_team

                if team == 'home':
                    self.home_score += points
                else:
                    self.away_score += points

                event = {
                    'id': len(self.events) + 1,
                    'minute': self.time,
                    'quarter': self.quarter,
                    'type': 'basket',
                    'team': team,
                    'player': f'{teamname}# {player}',
                    'points': points
                }
                self.events.append(event)


            elif random.random() < 0.05:
                event_type = random.choice(['foul', 'timeout', 'steal', 'block'])
                team = random.choice(['home', 'away'])
                player = random.randint(1, 15)
                if team == "home":
                    teamname = self.home_team

                else:
                    teamname = self.away_team
                event = {
                    'id': len(self.events) + 1,
                    'minute': self.time,
                    'quarter': self.quarter,
                    'type': event_type,
                    'team': team,
                    'player': f'{teamname}# {player}'
                }
                self.events.append(event)

            if self.time % 12 == 0:
                if self.quarter == 4:
                    self.status = 'finished'
                    print("..")
                else:
                    self.quarter += 1
                    self.time=0
                    event = {
                        'id': len(self.events) + 1,
                        'minute': self.time,
                        'type': 'quarter_end',
                        'quarter': self.quarter - 1
                    }
                    self.events.append(event)


        elif self.sport == 'judo':
            self.time += 1

            if not self.ippon and random.random() < 0.015:
                team = random.choice(['home', 'away'])
                self.ippon = True

                if team == 'home':
                    self.home_score = 10
                else:
                    self.away_score = 10

                event = {
                    'id': len(self.events) + 1,
                    'time': self.time,
                    'type': 'ippon',
                    'team': team,
                    'technique': random.choice(read_json("judo.json"))
                }
                self.events.append(event)
                self.status = 'finished'

            elif random.random() < 0.025:
                team = random.choice(['home', 'away'])

                if team == 'home':
                    self.wazari_home += 1
                    if self.wazari_home >= 2:
                        self.home_score = 10
                        self.status = 'finished'
                else:
                    self.wazari_away += 1
                    if self.wazari_away >= 2:
                        self.away_score = 10
                        self.status = 'finished'

                event = {
                    'id': len(self.events) + 1,
                    'time': self.time,
                    'type': 'wazari',
                    'team': team,
                    'technique': random.choice(read_json("judo.json"))
                }
                self.events.append(event)


            elif random.random() < 0.02:
                team = random.choice(['home', 'away'])

                if team == 'home':
                    self.shido_home += 1
                    if self.shido_home >= 3:
                        self.away_score = 10
                        self.status = 'finished'
                else:
                    self.shido_away += 1
                    if self.shido_away >= 3:
                        self.home_score = 10
                        self.status = 'finished'

                event = {
                    'id': len(self.events) + 1,
                    'time': self.time,
                    'type': 'shido',
                    'team': team,
                    'reason': random.choice(['False attack', 'Passivity', 'Gripping violation', 'Out of bounds'])
                }
                self.events.append(event)


            if self.time >= 240:
                self.status = 'finished'
                score_home = self.wazari_home * 5
                score_away = self.wazari_away * 5
                self.home_score = score_home
                self.away_score = score_away


        return event

    def to_dict(self):
        data = {
            'id': self.id,
            'sport': self.sport,
            'homeTeam': self.home_team,
            'awayTeam': self.away_team,
            'homeScore': self.home_score,
            'awayScore': self.away_score,
            'status': self.status,
            'time': self.time,
            'events': self.events
        }

        if self.sport == 'basketball':
            data['quarter'] = self.quarter

        elif self.sport == 'judo':
            data['maxTime'] = 240
            data['wazariHome'] = self.wazari_home
            data['wazariAway'] = self.wazari_away
            data['shidoHome'] = self.shido_home
            data['shidoAway'] = self.shido_away
            data['ippon'] = self.ippon


        return data


def initialize_matches():
    global matches
    teams = read_json("teams.json")
    matches_data = randomize_matches(teams, random.randint(6,15))
    for match_id, sport, home, away, status in matches_data:
        matches[match_id] = Match(match_id, sport, home, away, status)


class MatchWebSocket(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        clients.add(self)
        print(f"WebSocket opened. Total clients: {len(clients)}")
        lista = []
        for m in matches.values():
            lista.append(m.to_dict())
        self.write_message(json.dumps({
            'type': 'init',
            'matches': lista
        }))

    def on_close(self):
        clients.discard(self)
        print(f"WebSocket closed. Total clients: {len(clients)}")



class MatchesHandler(tornado.web.RequestHandler):
    def set_default_header(self):
        self.set_header("Content-Type", "application/json")

    def options(self):
        self.set_status(204)
        self.finish()

    def get(self):
        matches_list = []
        for m in matches.values():
            matches_list.append(m.to_dict())
        data = {
            "matches": matches_list
        }
        self.write(json.dumps(data))


class MatchDetailHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")

    def get(self, match_id):
        match = matches.get(match_id)
        if match:
            self.write(json.dumps(match.to_dict()))
        else:
            self.set_status(404)
            self.write(json.dumps({'error': 'Match not found'}))


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")


async def update_matches():
    while True:
        await asyncio.sleep(1)

        updates = []
        for match in matches.values():
            event = match.update()
            if event or match.status == 'live':
                updates.append(match.to_dict())

        if updates and clients:
            message = json.dumps({
                'type': 'update',
                'matches': updates
            })

            for client in clients:
                try:
                    client.write_message(message)
                except:
                    pass


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/ws", MatchWebSocket),
        (r"/api/matches", MatchesHandler),
        (r"/api/matches/([^/]+)", MatchDetailHandler),
        (r"/templates/(.*)", tornado.web.StaticFileHandler, {"path": "./templates"}),
    ],
        template_path="./templates",
        debug=True)


if __name__ == "__main__":
    initialize_matches()

    app = make_app()
    app.listen(8888)

    print("🏀 Server started on http://localhost:8888")
    print("📊 Sports: Basketball, Judo")
    print("🔴 Live matches running...")

    tornado.ioloop.IOLoop.current().spawn_callback(update_matches)

    tornado.ioloop.IOLoop.current().start()