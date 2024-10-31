import os
from pymongo import MongoClient, errors as mongoError
#from review_scrape import main as review_scrape
from preprocess_tools.review_scrape import review_get_generator
from preprocess_tools.preprocess import main as preprocess
from datetime import datetime
import requests
from dotenv import load_dotenv
from pandas import concat as pd_concat

load_dotenv()

data_keys = ["recommendationid", "author", "review", "timestamp_created", "timestamp_updated", "voted_up", "votes_up", "votes_funny",
             "weighted_vote_score","comment_count", "steam_purchase", "received_for_free", "written_during_early_access"]
#"developer_response", "timestamp_dev_responded"



def get_database() -> MongoClient:
    print("Making client")
    user = os.getenv('USER2_NAME')
    pwd = os.getenv('USER2_PWD')
    #print(f'{user}, {pwd}')
    CONNECTION_STRING = f'mongodb://{user}:{pwd}@database-server:27017/'
    client = MongoClient(CONNECTION_STRING)
    return client

def db_insert(collection, df):
    for data_row in df.to_dict("records"):
        try:
            collection.insert_one(data_row)
        except mongoError.DuplicateKeyError:
            collection.update_one({"_id":data_row["_id"]}, {"$set":data_row})

def find_game_by_name(game) -> tuple:
    str; url = "http://api.steampowered.com/ISteamApps/GetAppList/v0002/"
    dict; game_id_list = requests.get(url).json()

    if type(game) == int:
        identify = "appid"
    else:
        identify = "name"
        print("String input given")
    #print(game_id_list)
    for app in game_id_list["applist"]["apps"]:
        #print(app[identify])
        if app[identify] == game:
            return (app["appid"], app["name"])
    print("not found")
    return False, False

def pipeline_gener(url, days=None, data_keys=data_keys):
    """
    Creates data processing generator where in iteration happens:
    Pull a set of data -> preprocess -> store to database

    Args:
        game (int): Steam app id
        days (_type_, optional): How many days will be processed. Defaults to None.
        data_keys (_type_, optional): Data keys. Defaults to data_keys.
    """
    
    get_gener = review_get_generator(url, data_keys, days=days)

    # this * 100 == data rows per this generator iteration
    chunk_size = 10
    
    df, keep_going = next(get_gener)
    if not keep_going:
        yield df
    while keep_going:
        for x in range(chunk_size):
            df_temp, keep_going = next(get_gener)
            df = pd_concat([df, df_temp])
            if not keep_going:
                break
        yield df


def data_insert(game:str, days=None, data_keys=data_keys):

    chunk_size = 10 # this * 100 == data rows per this generator iteration
    # Check if game exists
    try:
        game = int(game)
        game, game_name = find_game_by_name(game)
        game_name = game_name.replace(" ", "_")
    except ValueError:
        game = game.replace("_", " ")
        game, game_name = find_game_by_name(game)
        game_name = game_name.replace(" ", "_")
        print(game, game_name)
        if game == False:
            raise ValueError("NOT FOUND. Check spelling.")
    #df = review_scrape(game, data_keys, days=days)
    url = f'https://store.steampowered.com/appreviews/{game}'
    get_gener = review_get_generator(url, data_keys, days=days)
    #pipe_gener = pipeline_gener(url, days=None, data_keys=data_keys)
    keep_going = True
    mydb = get_database()["gameDatas"]
    collection_list = mydb.list_collection_names()
    collection = mydb[game_name]
    while keep_going:
        df, keep_going = next(get_gener)
        if not keep_going: # incase only one iteration
            if len(df) != 0: # incase the one iteration had usable data
                df = preprocess(df)
                db_insert(collection, df)
            break
        for x in range(chunk_size):
            df_temp, keep_going = next(get_gener)
            if len(df_temp) != 0:
                df = pd_concat([df, df_temp])
            if not keep_going:
                break
        if len(df) != 0:
            df = preprocess(df)
            db_insert(collection, df)
    if game_name not in collection_list:
        collection = mydb['games_list_4_AI_USES_NOT_A_GAME']
        collection.insert_one({'_id': game_name, 'name':game_name, 'lastUpdated':datetime.now()})
    else:
        collection.update_one({'_id': game_name},{"$set":{'_id': game_name, 'name':game_name, 'lastUpdated':datetime.now()}}, upsert=True)
    del df
    return 0
