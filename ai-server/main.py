from flask import Flask, request, Response
from feature_builders import build_data
from ai_builder import create_ai_datas, build_ai, forecast_today
from apiflask import APIFlask
import json

DATA_KEYS = {"_id":1,"recommendationid":1, "author":1, "review":1, "timestamp_created":1, "timestamp_updated":1, "voted_up":1, "votes_up":1, "votes_funny":1,
             "weighted_vote_score":1,"comment_count":1, "steam_purchase":1, "received_for_free":1, "written_during_early_access":1,"date":1,"reviews_count":1}





#app = Flask(__name__, template_folder="./microservices")
app = APIFlask(__name__, template_folder="./microservices")
app.config['LOCAL_SPEC_PATH'] = 'openapi.json'

from flask_swagger_ui import get_swaggerui_blueprint
SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')
API_URL = 'http://localhost:5002/api/OPENAPI_JSON'  # Our API url (can of course be a local resource)

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



#@app.get("/")
#def home():
#    return "<h1>Hello there.</h1>"

@app.get("/api/OPENAPI_JSON")
def get_openapi_json():
    with open("openapi.json", "r") as file:
        package = json.loads(file.read())
    return package

@app.get("/api/v1/number_graph_builder")
def build_raw_numbers():
    game = request.args.to_dict()["game_name"]
    #try:
    #    dates={"old_last_entry":request.args.to_dict()["old_last_entry"],
    #           "today":request.args.to_dict()["today"]}
    #except:
    #    dates=None
    #    pass
    build_data(str(game).replace(" ","_"), "raw_number")#, dates)
    return Response("Success", status=200)

@app.get("/api/v1/correlation_builder")
def build_correlation_matrix():
    game = request.args.to_dict()["game_name"]
    #try:
    build_data(str(game).replace(" ","_"), "correlation_matrix")
    return Response("Success", status=200)


@app.get("/api/v1/build_new_ai/raw_number_graph")
def re_build_ai():
    #try:
    ai_data, correct = create_ai_datas(DATA_KEYS, database = "results", type_data = "raw_number_graph", type_version="1.0")
    accuracy = build_ai(ai_data,correct=correct)
    return f'Model accuracy: {round(accuracy,3)} %'
    #except:
    #    return "<h1>Fail</h1>"


@app.get("/api/v1/today_forecast")
def today_prediction():
    game = request.args.to_dict()["game_name"]
    value = forecast_today(game)
    return {"number":value}


if __name__=='__main__':
    app.run()
