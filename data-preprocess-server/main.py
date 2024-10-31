from flask import Flask, request, Response, render_template
from preprocess_tools.data_insert import data_insert
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
API_URL = 'http://localhost:5001/api/OPENAPI_JSON'  # Our API url (can of course be a local resource)

# Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "data_preprocess"
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

#@app.get("/35678653")
#def home():
#    return render_template('index.html')

@app.get("/api/v1/process_game")
def process_game():
    game = request.args.to_dict()["game_name"]
    days = int(request.args.to_dict()["days"])
    try:
        data_insert(str(game), days=days)
        return Response("good",status=200)
    except ValueError:
        return Response("Not found",status=203)



if __name__=='__main__':
    app.run()
