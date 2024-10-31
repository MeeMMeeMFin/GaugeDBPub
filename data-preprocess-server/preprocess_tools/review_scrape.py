import pandas as pd
#import numpy as np
import requests
from datetime import date, timedelta
import time

def df_build(raw_data:list, data_keys:list):
    df = pd.DataFrame(columns = data_keys)
    for review in raw_data:
        try:
            df.loc[len(df)] = [review[key] for key in data_keys]
        except KeyError:
            break
    return df

def review_get_generator(url:str, data_keys:dict, days=None):
    """
    1. First GET
    2. Build df
    3. Check df dates
    4. Yield df and (True/False)
    5. Start loop
    6. Get
    7. Build df
    8. Check df dates
    9. Yield df and (True/False)
    10. Loop steps 6-9, until no more data or caught up since last process

    Args:
        url (str): Get url
        data_keys (dict): data_keys
        days (_type_, optional): How many days old data will be used. Defaults to None.

    Raises:
        ConnectionRefusedError: _description_

    Returns:
        df (pandas.Dataframe): Steam app review data in pandas dataframe
        bool: If process can be continued
    """
    #?json=1&filter=recent&num_per_page=30&language=english&purchase_type=all&day_range=365
    parameters = {"json": 1, "filter":"recent", "num_per_page":100, "language": "english", "purchase_type":"all", "day_range":365, "cursor":"*"}
    same_date_stage = False
    # 1.
    response = requests.get(url, params=parameters)
    if days:
        limit = date.today() - timedelta(days=days)
        limit_unix = time.mktime(limit.timetuple())
    if response.ok:
        response = response.json()# = json.loads(response.text)
        # 2.
        df = df_build(response["reviews"], data_keys)
        # 3.
        df = df.loc[(date.today() != pd.to_datetime(df["timestamp_updated"], unit="s").dt.date)]
        if days:
            if limit_unix > df["timestamp_updated"].values[-1]:
                # skip today's and already processed days' data
                df = df.loc[(date.today() != pd.to_datetime(df["timestamp_updated"], unit="s").dt.date)
                            & (limit <= pd.to_datetime(df["timestamp_updated"], unit="s").dt.date)]
                # 4
                yield df, False
        if len(df) != 0: # if first query only gave same dates data then it will start loop before returns
            yield df, True
        else:
            same_date_stage = True
    else:
        raise ConnectionRefusedError(f'Error: {response}')
    # 5.
    # How many get requests sent to valve servers
    iterations = round(response["query_summary"]["total_reviews"] / parameters["num_per_page"])
    print(f'{iterations+1} get calls. Or until data is caught up.')

    for i in range(iterations): # 10.
        #print(f'{i}/{iterations}', end='\r')
        #print(response["cursor"])
        #query = start_request + f'&cursor={response["cursor"]}'
        parameters["cursor"] = response["cursor"]
        # 6.
        response = requests.get(url, params=parameters)
        if response.ok:
            response = response.json()
            #7.
            df = df_build(response["reviews"], data_keys)
            # 8.
            if same_date_stage:
                df = df.loc[(date.today() != pd.to_datetime(df["timestamp_updated"], unit="s").dt.date)]
                if len(df) == 0: # Still same date
                    continue
                else:
                    same_date_stage = False
            if days:
                if limit_unix > df["timestamp_updated"].values[-1]:
                    # skip today's and already processed days' data
                    df = df.loc[(date.today() != pd.to_datetime(df["timestamp_updated"], unit="s").dt.date)
                                & (limit <= pd.to_datetime(df["timestamp_updated"], unit="s").dt.date)]
                    #9.
                    yield df, False
        yield df, True
    else: # if no processable data
        yield [], False

#def all_game_data(url:str, data_keys:dict, days=None) -> tuple:
#    #?json=1&filter=recent&num_per_page=30&language=english&purchase_type=all&day_range=365
#    parameters = {"json": 1, "filter":"recent", "num_per_page":100, "language": "english", "purchase_type":"all", "day_range":365, "cursor":"*"}
#    response = requests.get(url, params=parameters)
#    if days:
#        limit = date.today() - timedelta(days=days)
#        limit_unix = time.mktime(limit.timetuple())
#    if response.ok:
#        response = response.json()# = json.loads(response.text)
#        df = df_build(response["reviews"], data_keys)
#        if response["query_summary"]["total_reviews"] < parameters["num_per_page"]:
#            return df, [response["query_summary"]]
#        store_data = []
#        store_data.append(response["query_summary"])
#    else:
#        raise ConnectionRefusedError(f'Error: {response}')
#    
#    # How many get requests sent to valve servers
#    iterations = round(response["query_summary"]["total_reviews"] / parameters["num_per_page"])
#    print(f'{iterations+1} get calls. Or until data is caught up.')
#
#    for i in range(iterations):
#        #print(f'{i}/{iterations}', end='\r')
#        #print(response["cursor"])
#        #query = start_request + f'&cursor={response["cursor"]}'
#        parameters["cursor"] = response["cursor"]
#        response = requests.get(url, params=parameters)
#        if response.ok:
#            response = response.json()
#            try:
#                df = pd.concat([df,
#                        df_build(response["reviews"],data_keys)])
#                store_data.append(response["query_summary"])
#
#                
#                if days:
#                    if limit_unix > df["timestamp_updated"].values[-1]:
#                        # skip today's and already processed days' data
#                        df = df.loc[(date.today() != pd.to_datetime(df["timestamp_updated"], unit="s").dt.date)
#                                    & (limit <= pd.to_datetime(df["timestamp_updated"], unit="s").dt.date)]
#                        break
#
#
#            except KeyError:
#                print(response)
#    else:
#        df = df.loc[date.today() != pd.to_datetime(df["timestamp_updated"]).dt.date]
#        #print("Done")
#    
#    return df, store_data






def sampling_game_data(amount:int, url:str, data_keys:list) -> tuple:
    #?json=1&filter=recent&num_per_page=30&language=english&purchase_type=all&day_range=365
    parameters = {"json": 1, "filter":"recent", "num_per_page":100, "language": "english", "purchase_type":"all", "day_range":365, "cursor":"*"}
    #query = start_request + "&cursor=*"
    response = requests.get(url, params=parameters)
    #store_data = []
    if response.ok:
        response = response.json()# = json.loads(response.text)
        try:
            df = df_build(response["reviews"],data_keys)
        except KeyError:
            print(response)
        #store_data.append(response["query_summary"])
    else:
        raise ConnectionRefusedError(f'Error: {response}')
    loops = round(amount/parameters['num_per_page'])
    loops_print = loops
    digit_count = len(str(loops))
    print(f'Pulling data in {loops} batches')
    loops-=1
    while loops > 0:
        print(f'{loops:0{digit_count}d}/{loops_print}', end='\r', flush=True)
        #query = start_request + f'&cursor={response["cursor"]}'
        parameters["cursor"] = response["cursor"]
        response = requests.get(url, params=parameters)
        if response.ok:
            response = response.json()
            try:
                df = pd.concat([df,
                        df_build(response["reviews"],data_keys)])
                #store_data.append(response["query_summary"])
            except KeyError:
                print(response)
            loops -=1
    else:
        print(f'{0:0{digit_count}d}/{loops_print}')
        print("Done pulling data")
    return df#, store_data



def get_store_data(game_id) -> dict:
    parameters = {"json": 1, "filter":"recent", "num_per_page":1, "language": "english", "purchase_type":"all", "day_range":365, "cursor":"*"}
    str; url = f'https://store.steampowered.com/appreviews/{game_id}'
    dict; store_data = requests.get(url, params=parameters).json()["query_summary"]
    return store_data


{"minecraft": "Not here", "Webbed": {"processed": "2023-11-26", "number_graph": "2023-11-26"}, "Warframe": {"processed": "2023-11-26"}}
#def get_game_data(game_id:int, data_keys, days=0, sampling=False, amount=0) -> tuple:
#    url = f'https://store.steampowered.com/appreviews/{game_id}'#?json=1&filter=recent&num_per_page=30&language=english&purchase_type=all&day_range=365'
#    if sampling:
#        df, store_data = sampling_game_data(amount, url, data_keys)
#    elif not sampling:
#        df, store_data = all_game_data(url, data_keys, days=days)
#        pass
#    else:
#        raise KeyError("Enable valid sampling parameter.")
#    
#    return df, store_data



def find_game_by_max_min(n_max=1000, n_min=100) -> dict:
    str; url = "http://api.steampowered.com/ISteamApps/GetAppList/v0002/"
    dict; game_id_list = requests.get(url).json()
    for app in game_id_list["applist"]["apps"]:
        store_data = get_store_data(app["appid"])
        if store_data["total_reviews"] < n_max and store_data["total_reviews"] > n_min:
            print(f'found game with less than {n_max} but more than {n_min} reviews')
            print(f'Game: {app["name"]}\nAppid: {app["appid"]}')
            return app



#def main(game_id:int, data_keys:dict, days=0, sampling=False, amount=0) -> tuple:
#    if sampling:
#        df, store_data = get_game_data(game_id, data_keys, days=days, sampling=sampling, amount = amount)
#    else:
#        df, store_data = get_game_data(game_id, data_keys, days=days)
#    
#    return df, store_data
