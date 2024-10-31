import os
from datetime import date
from datetime import datetime
from pymongo import MongoClient
import requests
import json
from dotenv import load_dotenv
load_dotenv()


def get_database(connection = "database-server") -> MongoClient:
    print("Making client")
    user = os.getenv('USER1_NAME')
    pwd = os.getenv('USER1_PWD')
    #print(f'{user}, {pwd}')
    CONNECTION_STRING = f'mongodb://{user}:{pwd}@{connection}:27017/'
    client = MongoClient(CONNECTION_STRING)
    return client

def get_dictionary(model="word_2_number") -> dict:
    user = os.getenv('USER1_NAME')
    pwd = os.getenv('USER1_PWD')
    #print(f'{user}, {pwd}')
    CONNECTION_STRING = f'mongodb://{user}:{pwd}@database-server:27017/'
    client = MongoClient(CONNECTION_STRING)
    database = client['dictionary']
    dictionary = database[model]
    return dictionary


def when_processed_save(game_name:str, method:str, date:str)->None:
    """
    When process any game update local processed_games.json

    Args:
        game_name (str): Name of game being handled
        method (str): What operation is being done (processed, number_graph, correlation)
        date (str): Current date
    """
    with open("./processed_games.json", "r") as outfile:
        games = json.load(outfile)
    try:
        games[game_name][method] = date
    except KeyError: # New game
        games[game_name] = {method:date}
    with open("./processed_games.json", "w") as outfile:
        outfile.write(json.dumps(games))

def get_processed_date(game_name:str, method:str) -> str:
    with open("./processed_games.json", "r") as outfile:
        try:
            games = json.load(outfile)
        except json.JSONDecodeError:
            raise KeyError
    return games[game_name][method]

def days_since_processed(game_name:str, method:str) -> int:
    """_summary_

    Args:
        game_name (str): Game name
        method (str): What operation (processed, number_graph, correlation)

    Raises:
        KeyError: _description_

    Returns:
        int: _description_
    """
    today = date.today()
    try:
        temp = get_processed_date(game_name, method)
        assert type(temp) == str
        processed_date = datetime.strptime(temp,"%Y-%m-%d").date()
        assert type(today) == type(processed_date)
        days_2_process = today - processed_date
        return days_2_process.days
    except KeyError:
        raise KeyError

def game_exists(game_name) -> dict:
    str; url = "http://api.steampowered.com/ISteamApps/GetAppList/v0002/"
    dict; game_id_list = requests.get(url).json()
    for app in game_id_list["applist"]["apps"]:
        if game_name == app["appid"] or game_name == app["name"]:
            return True
    return False


def pull_correlation(game:str, words:list) -> dict:
    assert type(words) == list
    assert type(words[0]) == str
    db = get_database()["results"]
    #assert f'{game}_corr_1.0' == f'Hollow_Knight_corr_1.0'
    collection = db[f'{game}_corr_1.0']
    word_2_number = {} # The magic stored here
    for item in list(get_dictionary().find({},{"_id":0,"word":1,"number":1})):
        word_2_number[item["word"]] = item["number"]
    number_2_word = {str(v): str(k) for k, v in word_2_number.items()}
    temp = []
    for word in words:
        try:
            int(word)
            dict; temp1 = collection.find_one({"_id":str(word)})
        except ValueError:
            try:
                dict; temp1 = collection.find_one({"_id":str(word_2_number[word])})
            except KeyError: # For "voted_up" & "voted_funny" and such
                dict; temp1 = collection.find_one({"_id":word})
        temp.append(temp1)
    # temp = [{ word: { item1:0.602, item2:0.5854 }}]
    del word_2_number
    del temp1
    assert type(temp) == list
    assert len(list(temp[0].keys())) > 5 # passed vibe check
    #if type(temp[0]) != dict:
    #    raise TypeError(f'{str(type(temp[0]))}')






    results = {word:{} for word in words}
    for key in temp[0].keys(): # loops all keys/words
        if key == "_id":
            continue
        for i, word in enumerate(words): # loops thru words in order to store them
            try: # for None values
                try:
                    results[word].update({number_2_word[key]:temp[i][key]})
                except KeyError:
                    results[word].update({key:temp[i][key]})
            except TypeError: # for None values
                results[word].update({key:0})





    # Sorting by value
    #assert len(list(results["fun"].keys())) > 5 # sus
    for word in words:
        results[word] = dict(sorted(results[word].items(), key=lambda item:item[1],reverse=True))
        results[word] = {str(i):[key,results[word][key]] for i, key in enumerate(results[word].keys())}
    #   results[word] = {word: { 0:[item1,0.75 ], 1:[item2,0.73]}}
    return results