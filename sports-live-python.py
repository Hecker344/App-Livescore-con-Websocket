# server.py - Backend Tornado con Judo, Cricket e Basket
import tornado.ioloop
import tornado.web
import tornado.websocket
import json
import random
from datetime import datetime
import asyncio

matches = {}
clients = set()


def randomize_matches(teams, num_matches):
    stati = ['live', 'finished', 'scheduled']
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

        # Parametri specifici per sport
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
            self.max_time = 4  # 4 minuti
            self.time = 0 if status == 'scheduled' else random.randint(0, 180)  # in secondi
            self.ippon = False
            self.wazari_home = 0
            self.wazari_away = 0
            self.shido_home = 0
            self.shido_away = 0

        elif sport == 'cricket':
            self.innings = 1
            self.overs = 0
            self.balls = 0
            self.max_overs = 20  # T20
            self.wickets_home = 0
            self.wickets_away = 0
            self.current_batting = 'home'

        # Aggiungi eventi iniziali per match live
        if status == 'live':
            self._add_initial_events()

    def _add_initial_events(self):
        """Aggiungi alcuni eventi iniziali per match già iniziati"""
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

        elif self.sport == 'cricket' and self.overs > 0:
            self.home_score = random.randint(80, 150)
            self.wickets_home = random.randint(0, 4)
            self.overs = random.randint(5, 15)
            self.balls = random.randint(0, 5)

    def update(self):
        """Aggiorna lo stato del match"""
        if self.status != 'live':
            return None

        event = None

        if self.sport == 'basketball':
            self.time += 1

            # Genera canestri
            if random.random() < 0.18:  # 18% probabilità canestro
                team = random.choice(['home', 'away'])
                points = random.choices([2, 3], weights=[0.65, 0.35])[0]

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
                    'player': f'{self.home_team if team == "home" else self.away_team} #{random.randint(1, 15)}',
                    'points': points
                }
                self.events.append(event)

            # Eventi speciali basket
            elif random.random() < 0.05:
                event_type = random.choice(['foul', 'timeout', 'steal', 'block'])
                team = random.choice(['home', 'away'])

                event = {
                    'id': len(self.events) + 1,
                    'minute': self.time,
                    'quarter': self.quarter,
                    'type': event_type,
                    'team': team,
                    'player': f'{self.home_team if team == "home" else self.away_team} #{random.randint(1, 15)}'
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

            # Shido (penalità)
            elif random.random() < 0.02:  # 2% probabilità shido
                team = random.choice(['home', 'away'])

                if team == 'home':
                    self.shido_home += 1
                    if self.shido_home >= 3:  # 3 shido = squalifica
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

            # Fine tempo
            if self.time >= 240:  # 4 minuti
                self.status = 'finished'
                # Determina vincitore per punteggio
                score_home = self.wazari_home * 5
                score_away = self.wazari_away * 5
                self.home_score = score_home
                self.away_score = score_away

        elif self.sport == 'cricket':
            # Avanza ball
            self.balls += 1

            # Genera run o wicket
            if random.random() < 0.75:  # 75% probabilità run
                runs = random.choices([0, 1, 2, 3, 4, 6], weights=[0.25, 0.30, 0.20, 0.10, 0.10, 0.05])[0]

                if self.current_batting == 'home':
                    self.home_score += runs
                else:
                    self.away_score += runs

                if runs > 0:
                    event = {
                        'id': len(self.events) + 1,
                        'over': self.overs,
                        'ball': self.balls,
                        'type': 'boundary' if runs >= 4 else 'run',
                        'runs': runs,
                        'team': self.current_batting,
                        'batsman': f'{self.home_team if self.current_batting == "home" else self.away_team} Batsman {random.randint(1, 11)}'
                    }
                    self.events.append(event)

            # Wicket
            elif random.random() < 0.15:  # 15% probabilità wicket
                if self.current_batting == 'home':
                    self.wickets_home += 1
                else:
                    self.wickets_away += 1

                wicket_type = random.choice(['bowled', 'caught', 'lbw', 'run out', 'stumped'])

                event = {
                    'id': len(self.events) + 1,
                    'over': self.overs,
                    'ball': self.balls,
                    'type': 'wicket',
                    'wicket_type': wicket_type,
                    'team': self.current_batting,
                    'batsman': f'{self.home_team if self.current_batting == "home" else self.away_team} Batsman {random.randint(1, 11)}'
                }
                self.events.append(event)

                # Fine innings se 10 wicket
                if (self.current_batting == 'home' and self.wickets_home >= 10) or \
                        (self.current_batting == 'away' and self.wickets_away >= 10):
                    if self.innings == 1:
                        self.innings = 2
                        self.current_batting = 'away' if self.current_batting == 'home' else 'home'
                        self.overs = 0
                        self.balls = 0
                    else:
                        self.status = 'finished'

            # Fine over
            if self.balls >= 6:
                self.overs += 1
                self.balls = 0

                event = {
                    'id': len(self.events) + 1,
                    'over': self.overs - 1,
                    'type': 'over_complete',
                    'team': self.current_batting
                }
                self.events.append(event)

                # Fine innings per over completati
                if self.overs >= self.max_overs:
                    if self.innings == 1:
                        self.innings = 2
                        self.current_batting = 'away' if self.current_batting == 'home' else 'home'
                        self.overs = 0
                        self.balls = 0
                    else:
                        self.status = 'finished'

        return event

    def to_dict(self):
        """Converti match in dizionario"""
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

        elif self.sport == 'cricket':
            data['innings'] = self.innings
            data['overs'] = self.overs
            data['balls'] = self.balls
            data['maxOvers'] = self.max_overs
            data['wicketsHome'] = self.wickets_home
            data['wicketsAway'] = self.wickets_away
            data['currentBatting'] = self.current_batting

        return data


def initialize_matches():
    """Inizializza i match di esempio"""
    global matches

    teams = read_json("teams.json")

    matches_data = randomize_matches(teams, 8)

    for match_id, sport, home, away, status in matches_data:
        matches[match_id] = Match(match_id, sport, home, away, status)


# Handler WebSocket
class MatchWebSocket(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        clients.add(self)
        print(f"WebSocket opened. Total clients: {len(clients)}")

        # Invia stato iniziale
        self.write_message(json.dumps({
            'type': 'init',
            'matches': [m.to_dict() for m in matches.values()]
        }))

    def on_close(self):
        clients.discard(self)
        print(f"WebSocket closed. Total clients: {len(clients)}")


# Handler HTTP
class MatchesHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")

    def options(self):
        self.set_status(204)
        self.finish()

    def get(self):
        self.write(json.dumps({
            'matches': [m.to_dict() for m in matches.values()]
        }))


class MatchDetailHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")

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


# Funzione di aggiornamento periodico
async def update_matches():
    while True:
        await asyncio.sleep(2)  # Aggiorna ogni 2 secondi

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
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "./static"}),
    ],
        template_path="./templates",
        debug=True)


if __name__ == "__main__":
    initialize_matches()

    app = make_app()
    app.listen(8888)

    print("🏀 Server started on http://localhost:8888")
    print("📊 Sports: Basketball, Judo, Cricket")
    print("🔴 Live matches running...")

    # Avvia aggiornamenti periodici
    tornado.ioloop.IOLoop.current().spawn_callback(update_matches)

    tornado.ioloop.IOLoop.current().start()