from flask import Flask, request, Response, render_template
import json
import requests
from flask_restful import Resource, Api
from apiflask import APIFlask
import json

DATA_KEYS = {"_id":1,"recommendationid":1, "author":1, "review":1, "timestamp_created":1, "timestamp_updated":1, "voted_up":1, "votes_up":1, "votes_funny":1,
             "weighted_vote_score":1,"comment_count":1, "steam_purchase":1, "received_for_free":1, "written_during_early_access":1,"date":1,"reviews_count":1}





#app = Flask(__name__, template_folder="./microservices")
app = APIFlask(__name__, template_folder="./microservices")
app.config['LOCAL_SPEC_PATH'] = 'openapi.json'

from flask_swagger_ui import get_swaggerui_blueprint
SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')
API_URL = 'http://localhost:5008/api/OPENAPI_JSON'  # Our API url (can of course be a local resource)

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


@app.get("/")
def home():
    return render_template("index.html")

@app.get("/api/OPENAPI_JSON")
def get_openapi_json():
    with open("openapi.json", "r") as file:
        package = json.loads(file.read())
    return package

@app.get("/check_existance")
def check_existance():
    game = request.args.to_dict()["game_name"]
    result = requests.get("http://admin-server:5006/api/v1/check_game", params={"game_name":game})
    if result.status_code==200:
        return Response("Exists", status=200)
    else:
        return Response("Doesn't exist", status=203)

@app.get("/api/v1/process_game") #process new game
def process_game():
    game = request.args.to_dict()["game_name"]
    response = requests.get("http://admin-server:5006/api/v1/process_game", params={"game_name":game})
    if response.status_code == 200:
        response.text
    elif response.status_code == 400:
        return Response(f'Check spelling on: {game}', status=400)
    return Response(response.text, status=response.status_code)

@app.get("/api/v1/build/raw_number_graph")
def tomorrow_forecasting():
    game = request.args.to_dict()["game_name"]
    response = requests.get("http://admin-server:5006/api/v1/build/raw_number_graph", params={"game_name":game})
    if response.status_code==200:
        return response.text
    else:
        return Response(response.text, status=response.status_code)

@app.get("/api/v1/build/number_correlation")
def build_correlation():
    game = request.args.to_dict()["game_name"]
    response = requests.get("http://admin-server:5006/api/v1/build/number_correlation", params={"game_name":game})
    if response.status_code==200:
        return response.text
    else:
        return Response(response.text, status=response.status_code)

@app.get("/api/v1/correlation_page")
def correlation_route():
    game = request.args.to_dict()["game_name"]
    return render_template("correlation.html", game_name=game)

@app.get("/api/v1/correlation_words_get")
def fetch_correlations():
    game = request.args.to_dict()["game_name"]
    word1 = request.args.to_dict()["word1"]
    word2 = request.args.to_dict()["word2"]
    word3 = request.args.to_dict()["word3"]
    word4 = request.args.to_dict()["word4"]
    word5 = request.args.to_dict()["word5"]
    data = requests.get("http://admin-server:5006/api/v1/get_correlation", params={"game_name":game, "word1":word1,"word2":word2,"word3":word3,"word4":word4,"word5":word5}).json()
    #data[word1]["0"]
    #data[word1]["4"]
    return data

@app.get("/api/v1/forecast/today_votes_up")
def today_prediction():
    game = request.args.to_dict()["game_name"]
    response_obj = requests.get("http://admin-server:5006/api/v1/forecast/today_votes_up", params={"game_name":game}).json()
    return response_obj

@app.get("/api/v1/build_new_ai/raw_number_graph")
def rebuild_ai():
    return requests.get("http://admin-server:5006/api/v1/build_new_ai/raw_number_graph").text


#@app.get("/microservices")
#def style_load():
#    return render_template(request.args.to_dict()["file"])

if __name__=='__main__':
    app.run()
