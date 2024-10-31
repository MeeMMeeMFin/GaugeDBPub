from flask import Flask, request, Response
import requests
from datetime import date
from admin_tools import when_processed_save, get_processed_date, days_since_processed, game_exists, pull_correlation
from flask_restful import Resource, Api
from apiflask import APIFlask
import json


#app = Flask(__name__, template_folder="./microservices")
app = APIFlask(__name__, template_folder="./microservices")
app.config['LOCAL_SPEC_PATH'] = 'openapi.json'

from flask_swagger_ui import get_swaggerui_blueprint
SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')
API_URL = 'http://localhost:5006/api/OPENAPI_JSON'  # Our API url (can of course be a local resource)

# Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "Test application"
    },
    # oauth_config={  # OAuth config. See https://github.com/swagger-api/swagger-ui#oauth2-configuration .
    #    'clientId': "your-client-id",
    #    'clientSecret': "your-client-secret-if-required",
    #    'realm': "your-realms", 
    #    'appName': "your-app-name",
    #    'scopeSeparator': " ",
    #    'additionalQueryStringParams': {'test': "hello"}
    # }
)

app.register_blueprint(swaggerui_blueprint)

@app.get("/api/OPENAPI_JSON")
def get_openapi_json():
    with open("openapi.json", "r") as file:
        package = json.loads(file.read())
    return package

@app.get("/api/v1/check_game")
def check_existance():
    game = request.args.to_dict()["game_name"]
    if game_exists(game):
        return Response("Does exist", status=200)
    else:
        return Response("Doesn't exist or typo", status=203)

@app.get("/api/v1/check_process_game")
def check_process_game():
    game = request.args.to_dict()["game_name"]
    method = request.args.to_dict()["method"]
    try:
        days = days_since_processed(game, method)
        print("TOIMIIIIIIIIIIIIIII")
        days = str(days)
        return Response(f'{days}', status=200)
    except:
        return Response("Not processed", status=203)

@app.get("/api/v1/check_date_when")
def check_date_process():
    game = request.args.to_dict()["game_name"]
    method = request.args.to_dict()["method"]
    try:
        date_result = get_processed_date(game, method)
        return Response(date_result, status=200)
    except KeyError:
        return Response("Not processed yet", status=203)

@app.get("/api/v1/process_game") #process new game
def process_game(game=None):
    if not game:
        game = request.args.to_dict()["game_name"]
    game = game.replace(" ", "_")
    try:
        days = days_since_processed(game, "processed")
        if days == 0:
            return Response("Already processed", status=203)
    except KeyError:
        days = 0
    response = requests.get("http://preprocess-server:5001/api/v1/process_game", params={"game_name":game, "days":days})
    if response.status_code == 200:
        when_processed_save(game, "processed", str(date.today()))
        return Response("Done", status=200) #+ json.dumps(response.json())
    elif response.status_code == 400:
        return Response(f'Check spelling on: {game.replace("_", " ")}', status=400)
    return Response(response.text, status=response.status_code) #+ json.dumps(response.json())

@app.get("/api/v1/process_many_games")
def process_many_games():
    games = request.args.to_dict()["games"].split(",")
    results = {}
    for game in games:
        result = process_game(game).response[0] # bytes / b''
        results[game] = result.decode() # str
    return results

@app.get("/api/v1/build/raw_number_graph")
def build_raw_number_graph(game=None):
    if not game:
        game = request.args.to_dict()["game_name"]
    game = game.replace(" ", "_")
    response = requests.get("http://ai-server:5002/api/v1/number_graph_builder", params={"game_name":game})
    if response.status_code==200:
        when_processed_save(game, "number_graph", str(date.today()))
        return Response(response.text, status=response.status_code)
    else:
        return Response(response.text, status=response.status_code)

@app.get("/api/v1/build/many_raw_number_graph")
def build_many_many_graphs():
    games = request.args.to_dict()["games"].split(",")
    results = {}
    for game in games:
        result = build_raw_number_graph(game).response[0] # bytes / b''
        results[game] = result.decode() # str
    return results

@app.get("/api/v1/build/number_correlation")
def build_correlation():
    game = request.args.to_dict()["game_name"]
    game = game.replace(" ", "_")
    response = requests.get("http://ai-server:5002/api/v1/correlation_builder", params={"game_name":game})
    if response.status_code==200:
        when_processed_save(game, "correlation", str(date.today()))
        return response.text
    else:
        return Response(response.text, status=response.status_code)

@app.get("/api/v1/get_correlation")
def get_correlation():
    game = request.args.to_dict()["game_name"].replace(" ", "_")
    words = []
    for word in ["word1","word2","word3","word4","word5"]:
        words.append(request.args.to_dict()[word])
    try:
        correlations = pull_correlation(game, words)
    except:
        raise ValueError(print(words))
    #correlations["fun"]["0"]
    #correlations["fun"]["4"]
    return correlations

@app.get("/api/v1/forecast/today_votes_up")
def today_prediction():
    game = request.args.to_dict()["game_name"]
    response = requests.get("http://ai-server:5002/api/v1/today_forecast", params={"game_name":game})
    if response.status_code==200:
        response = response.json()
    else:
        raise AssertionError(response)
    return {"number":response["number"]}

@app.get("/api/v1/build_new_ai/raw_number_graph")
def rebuild_ai():
    return requests.get("http://ai-server:5002/api/v1/build_new_ai/raw_number_graph").text

if __name__=='__main__':
    app.run()
