import asyncio, json, tornado.web, tornado.websocket, requests, time, datetime

API_KEY = "8d61d626f950c1146feee91d7a235f1188f6222a9c1a43dab8303844f003366c"

#   se la api key fosse scaduta consiglio fortemente di generarne un'altra presso apifootball.com

# dati identificativi della SERIE A
country_id = '5'
league_id = '207'

# richiede il palinsesto dei prossimi 7 giorni
start = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
stop = (datetime.datetime.now() + datetime.timedelta(days=7)).strftime("%Y-%m-%d")

clients = set()


class sportsHandler(tornado.web.RequestHandler):
    def get(self):
        url_palinsesto = f"https://apiv3.apifootball.com/?action=get_events&from={start}&to={stop}&country_id={country_id}&league_id={league_id}&APIkey={API_KEY}"
        response = requests.get(url_palinsesto)
        matches_data = response.json()

        # Passa i dati come JSON serializzato
        self.render("sports.html", matches_data=json.dumps(matches_data))


class matchHandler(tornado.web.RequestHandler):
    def get(self, match_id):
        url_partita = f"https://apiv3.apifootball.com/?action=get_events&match_id={match_id}&APIkey={API_KEY}"
        response = requests.get(url_partita)
        response_data = response.json()

        # Controllo che la partita esiste
        if 'error' in response_data or not response_data:
            self.set_status(404)
            self.write("match not found")
        else:
            # Passa i dati come JSON serializzato
            self.render("match.html", match_data_json=json.dumps(response_data[0]))


class leagueHandler(tornado.web.RequestHandler):
    def get(self):
        url_classifica = f"https://apiv3.apifootball.com/?action=get_standings&league_id={league_id}&APIkey={API_KEY}"
        response = requests.get(url_classifica)
        league_data = response.json()
        self.render("league.html", league_data=league_data)


class WSHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        print("WebSocket aperto")
        clients.add(self)

    def on_close(self):
        print("WebSocket chiuso")
        clients.remove(self)

    def on_message(self, message):
        # Gestisci eventuali messaggi dal client
        pass


async def update_matches():
    """Aggiorna periodicamente le partite e invia aggiornamenti ai client WebSocket"""
    while True:
        await asyncio.sleep(30)  # Aggiorna ogni 30 secondi

        url_palinsesto = f"https://apiv3.apifootball.com/?action=get_events&from={start}&to={stop}&country_id={country_id}&league_id={league_id}&APIkey={API_KEY}"
        try:
            response = requests.get(url_palinsesto)
            matches_data = response.json()

            message = json.dumps({
                'type': 'update',
                'matches': matches_data
            })

            # Invia aggiornamenti a tutti i client connessi
            for client in clients:
                try:
                    client.write_message(message)
                except:
                    pass
        except Exception as e:
            print(f"Errore aggiornamento: {e}")


async def main():
    app = tornado.web.Application(
        [
            (r"/", tornado.web.RedirectHandler, {"url": "/sports"}),
            (r"/sports", sportsHandler),
            (r"/sports/([0-9]+)", matchHandler),
            (r"/sports/league", leagueHandler),
            (r"/ws/matches", WSHandler),
            (r"/styles/(.*)", tornado.web.StaticFileHandler, {"path": "styles"})
        ],
        template_path="templates",
        debug=True
    )

    app.listen(8888)
    print("Server Tornado avviato su http://localhost:8888/sports")

    asyncio.create_task(update_matches())

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
