import os
import pandas as pd
from pymongo import MongoClient, errors as mongoError
from datetime import datetime, date
import requests
from dotenv import load_dotenv
load_dotenv()
#dasdsad
def get_database(connection = "database-server") -> MongoClient:
    print("Making client")
    user = os.getenv('USER3_NAME')
    pwd = os.getenv('USER3_PWD')
    #print(f'{user}, {pwd}')
    CONNECTION_STRING = f'mongodb://{user}:{pwd}@{connection}:27017/'
    client = MongoClient(CONNECTION_STRING)
    return client

def get_start_index(db, coll:str):
    if isinstance(db,str):
        mydoc = get_database()[db][coll].find({},{"_id":1}).sort("_id",-1)
    else:
        mydoc = db[coll].find({},{"_id":1}).sort("_id",-1)
    try:
        return mydoc[0]["_id"] + 1
    except:
        return 0

def get_dictionary(model="word_2_number") -> dict:
    user = os.getenv('USER3_NAME')
    pwd = os.getenv('USER3_PWD')
    #print(f'{user}, {pwd}')
    CONNECTION_STRING = f'mongodb://{user}:{pwd}@database-server:27017/'
    client = MongoClient(CONNECTION_STRING)
    database = client['dictionary']
    dictionary = database[model]
    return dictionary

class Converter():
    def __init__(self,model):
        self.data_converter = {} # The magic stored here
        for item in list(get_dictionary(model).find({},{"_id":0,"word":1,"number":1})):
            self.data_converter[item["word"]] = item["number"]
        self.model = model
        self.word_counter = len(self.data_converter.keys())
    def update(self):
        temp = list(get_dictionary(self.model).find({}))
    #  a = [1,2,3,4,5,6]
    #  b = [1,2,3,4,5,6,7,8,9]
    #  c = len(a)-len(b)
    #  b[c:]
    #  out: [7, 8, 9]
        start_index = self.word_counter - len(temp)
        if start_index == 0:
            del temp
            return
        for item in temp[start_index:]:
            self.data_converter[item["word"]] = item["number"]
        self.word_counter = len(temp)
        del temp


def number_into_word(word:int, number_2_word:dict)->str: # 1->"word"
    return number_2_word[word]

def list_to_words(words:list, number_2_word:dict)->str: # [1,2,3] -> "list to words"
    return " ".join(list(map(lambda word: number_into_word(word,number_2_word),words)))

def convert_number2word(review:list)->pd.Series:
    """_summary_
    This turns review data pulled from mongo into strings
    Args:
        review (list): list of list of integers:``[[1,2,3],[3,2,1]]``

    Returns:
        pd.Series: list of string in pandas series format:``["strings like","these are returned"]``
    """
    converter = Converter("word_2_number")
    word_2_number = converter.data_converter
    number_2_word = {v: k for k, v in word_2_number.items()}
    review = pd.Series(map(lambda x: list_to_words(x,number_2_word),review))
    del number_2_word
    del converter 
    return review

def get_last_date(game:str):
    collection = get_database()["gameDatas"][game]
    return collection.find_one({"timestamp_created":1}, sort=[("timestamp_created", -1)])["timestamp_created"]

def query_by_dates(game:str, data_type:str, start_date:str, end_date:str, data_keys:dict) -> pd.DataFrame:
    #TODO Check database for game
    game = game.replace(" ", "_")
    db = get_database()["results"]
    try:
        collection = db[f'{game}_{data_type}']
        df = pd.DataFrame(list(collection.find({"$or": [{"date":start_date},{"date": end_date}]}, data_keys)))
        if len(df) < 1:
            raise mongoError.CollectionInvalid()
    except mongoError.CollectionInvalid:
        #TODO request.get(build up to yesterdays data)
        response = requests.get("http://admin-server:5006/api/v1/process_game", params={"game_name":game})

        if response.status_code==200:
            response = requests.get("http://ai-server:5002/api/v1/number_graph_builder",
                                    params={"game_name":game, "today":str(datetime.today().date()), "old_last_entry":get_last_date(game)})
            if response.status_code==200:
                pass
        else:
            raise TypeError(f'Game "{game}" is not processed.')
        #Then this
        collection = db[f'{game}_{data_type}']
        df = pd.DataFrame(list(collection.find({"timestamp_created":{"$gte":start_date, "$lte": end_date}},data_keys)))
    return df