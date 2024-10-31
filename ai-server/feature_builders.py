from data_pull_tools import get_database, get_start_index, convert_number2word, Converter
from datetime import datetime, timedelta, date as date_dtype

from nltk import download as stopword_downloader
stopword_downloader('stopwords')
from nltk.corpus import stopwords

import pandas as pd
import numpy as np
import requests
import pickle

def drop_stopword_columns(df:pd.DataFrame)->pd.DataFrame:
    """
    Drops column and index of stopwords in a correlation matrix.

    Args:
        df (pd.DataFrame): correlation matrix
        stop_words (_type_): stop words

    Returns:
        pd.DataFrame: _description_
    """
    stop_words = set(stopwords.words("english"))
    i = 0
    i_max = len(list(stop_words))
    for stop in list(stop_words):
        if stop in df.columns:
            df = df.drop(stop).drop(stop, axis=1)
            print(f'{i}/{i_max} stop word were found in data.', end='\r', flush=True)
            i += 1
    return df


def combine_reviews_by_date_gen(data_reviews:pd.DataFrame, dates:np.ndarray)->list:
    """_summary_
    Combines same dated times' review data into single list.

    Args:
        data_reviews (pd.DataFrame): dataframe with index: "timestamp_updated" or "timpestamp_created" and "review" column data
        dates (np.ndarray): pd.DataFrame.index.unique().values

    Yields:
        list: 1-dimentional list of review words.
    """
    for date in dates:
        try:
            yield [val for sublist in data_reviews[date] for val in sublist]
        except TypeError:
            yield data_reviews[date]

def filter_bad_datas(df:pd.DataFrame, show_result=True)->pd.DataFrame:
    """
    Removes columns with only nan or zero(0) values.

    Args:
        correlations (pd.DataFrame): Correlation matrix

    Returns:
        pd.DataFrame: Cleaned correlation matrix
    """
    print("Cleaning columns...")
    good_columns = ["steam_purchase","received_for_free","written_during_early_access"]
    i = 0
    i_max = len(df.columns.values)
    for column in df.columns.values:
        if column in good_columns: # Skips good_columns
            continue
        if df[column].isnull().all().all(): # Deletes columns full of nan values
            df.drop(columns=[column], inplace=True)
            i += 1
            continue
        if df[column].eq(0).all().all(): # Deletes columns full of zeroes
            df.drop(columns=[column], inplace=True)
            i += 1
    if show_result:
        print(f'Dropped {i}/{i_max} data columns')
    del i
    if len(df.columns.values)== 0:
        raise TypeError("Data only had nan values")
    return df

def save_data(game, df:pd.DataFrame, method:str, database:str, first_process=False):
    collection_name = f'{game}_{method}'
    if first_process:
        start_index = 0
    else:
        start_index = get_start_index(database, collection_name)
        assert start_index > 0

    # if index date
    if isinstance(df.index.values[0], date_dtype):
        print("date index fixing")
        #df["date"] = df.index.values
        df.reset_index(names="date",inplace=True)
        df["_id"] = df["date"].astype(str)
        df.drop(columns="date",inplace=True)
        df.index += start_index
    # if index numeral
    elif isinstance(df.index.values[0], np.integer):
        df.index += start_index
        df["_id"] = df.index.values
    else: 
        raise ValueError("INDEX SKIPPED")
    if "timestamp_updated" in df.columns:
        df["date"] = df["timestamp_updated"].astype(str)
        df.drop(columns="timestamp_udpated")
    
    df.columns = df.columns.astype(str)
    db = get_database()[database]
    collection = db[collection_name]
    print("Saving data...")
    try:
        collection.insert_many(df.to_dict('records'))
    except:
        raise ValueError(str(df.dtypes))
    print("Data saved successfully!")

def review_to_column(df:pd.DataFrame):
    """_summary_
    Places dataframe review data into the appropriate columns
    Args:
        df (pandas.Dataframe): review data with the words processed to numbers
        and the word columns still in number form.

    Returns:
        pandas.Dataframe: word columns filled with data
    """
    #df.to_csv("data_before.csv",sep=";")
    for row, review in enumerate(df.review):
        try:
            counted = np.unique(review, return_counts=True)
        except TypeError as mistake:
            #df.to_csv("type_error_data.csv",sep=";")
            raise mistake
        for val_count, column_val in enumerate(counted[0]):
            df.loc[df.index[row], column_val] = counted[1][val_count]
        del counted
    return df

DATA_KEYS = {"_id":0,"recommendationid":1, "author":1, "review":1, "timestamp_created":1, "timestamp_updated":1, "voted_up":1, "votes_up":1, "votes_funny":1,
             "weighted_vote_score":1,"comment_count":1, "steam_purchase":1, "received_for_free":1, "written_during_early_access":1}

CORRELATION_MATRIX_VERSION = "1.0"
def correlation_matrix(df:pd.DataFrame, save=True, game=None, result_return=False):
    """
    V1.0
    Processes steam review data into simple word correlation matrix

    Args:
        df (pd.DataFrame): Steam game review data in pandas dataftame format.
    """
    # Args check
    if save:
        if type(game)==str:
            pass
        else:
            raise TypeError("Can't save to database without game name! Add input game='game_name' or save=False")
    converter = Converter("word_2_number")
    
    if "date" not in df.columns: # TODO MAKE MORE RELIABLE
        df = raw_number_data(df, save=save, game=game, result_return=True, converter=converter)
    else:
        print("Given ready processed data.")
    word_2_number = converter.data_converter
    number_2_word = {v: k for k, v in word_2_number.items()}
    df.rename(columns=number_2_word,inplace=True)
    try:
        df = df.drop(columns=["steam_purchase","received_for_free","written_during_early_access"]).corr()
    except KeyError:
        raise KeyError(df.columns.values)
    df = drop_stopword_columns(df)
    if save:
        save_data(game, df, f'corr_{CORRELATION_MATRIX_VERSION}', "results")
    if result_return:
        return df

def check_ready_data_exists(database:str, data_keys:dict, collection_name=None):
    if collection_name == None:
        raise TypeError("feature_builders.py function check_if_exist() broken")
    db = get_database()[database]
    #print(client.list_database_names())
    collection_list = db.list_collection_names()
    if collection_name in collection_list:
        collection = db[collection_name]
        df = pd.DataFrame(list(collection.find({},data_keys)))
        if len(df.index.values) == 0:
            raise ValueError()
        return df
    else:
        raise ValueError("Not existing")


def get_start_index(db, coll:str):
    if isinstance(db,str):
        mydoc = get_database()[db][coll].find({},{"_id":1}).sort("_id",-1)
    else:
        mydoc = db[coll].find({},{"_id":1}).sort("_id",-1)
    try:
        return mydoc[0]["_id"] + 1
    except:
        return 0

def save_data(game, df:pd.DataFrame, method:str, database:str, first_process=False):
    collection_name = f'{game}_{method}'
    if first_process:
        start_index = 0
    else:
        start_index = get_start_index(database, collection_name)
        assert start_index > 0
    if isinstance(df.index[0], date_dtype):
        print("date index fixing")
        #df["date"] = df.index.values
        df.reset_index(names="date",inplace=True)
        df["date"] = df["date"].astype(str)
        df.index += start_index
        df["_id"] = df.index.values
    elif "timestmap_updated" in df.columns:
        # date: '2021-09-09'
        df["date"] = df["timestamp_updated"].dt.strftime("%Y-%m-%d")
        df.drop(columns="timestamp_updated",inplace=True)
    # if already str date index
    elif isinstance(df.index[0], str):
        df["date"] = df.index.values
        df.reset_index(inplace=True, drop=True)
        df.index += start_index
        df["_id"] = df.index.values
    else:
        df.index += start_index
        df["_id"] = df.index.values
    
    df.columns = df.columns.astype(str)
    db = get_database()[database]
    collection = db[collection_name]
    print("Saving data...")
    collection.insert_many(df.to_dict('records'))
    print("Data saved successfully!")


def split_big_days(data, big_day, batch_size)->list[dict]:
    big_day = datetime.combine(big_day, datetime.min.time()) # https://stackoverflow.com/questions/1937622/convert-date-to-datetime-in-python
    temp = []
    #print(type(big_day))
    #print(type(data.timestamp_updated[0]))
    data = data.loc[(data.timestamp_updated>=big_day) & (data.timestamp_updated<big_day + timedelta(days=1))]
    temp_amount = 0
    gathering = False
    start_time = datetime
    for date, amount in zip(data.timestamp_updated, data.amount):
        temp_amount += amount
        if amount >= batch_size and not gathering:
            temp.append({"start":date,"end":date + timedelta(hours=1),"last":False})
            temp_amount = 0
        elif amount >= batch_size and gathering:
            temp.append({"start":start_time,"end":datetime.combine(date, datetime.min.time()),"last":True}) # gathering
            temp.append({"start":date,"end":date + timedelta(hours=1),"last":False}) # new
            gathering = False
            temp_amount = 0
        elif temp_amount >= batch_size and gathering:
            temp.append({"start":start_time,"end":date,"last":True})
            temp_amount = 0
        elif not gathering:
            gathering = True
            start_time = datetime.combine(date, datetime.min.time())
    else:
        #print(type(start_time))
        if gathering: # If ended while still under batch size
            temp.append({"start":start_time,"end":date,"last":True})
        else: # If last hour was a big one
            temp[-1]["last"] = True
    return temp

def calc_batches(data:pd.DataFrame, batch_size = 8000, maximum_difference=1000)->list[dict]:
    # [{"start":datetime(),"end":datetime(),"last":True/False}]
    print(len(data))
    # sort and amount
    data["amount"] = 1
    data_h = data.assign(timestamp_updated=data.timestamp_updated.dt.round("H"))
    data_h = data_h.groupby("timestamp_updated", sort=True, as_index=False).sum()
    data_h.timestamp_updated[0]
    data.timestamp_updated = data.timestamp_updated.dt.date
    #data.timestamp_updated = pd.to_datetime(df['timestamp_updated'], format='%d%b%Y:%H:%M:%S.%f')
    data = data.groupby("timestamp_updated", sort=True, as_index=False).sum().sort_values("timestamp_updated")
    data = data.sort_values("timestamp_updated")
    temp_amount = 0
    batches= []
    gathering = False
    start_time = datetime
    # start loop
    for date, amount in zip(data.timestamp_updated, data.amount):
        temp_amount += amount
        # check if too big
        if amount >= batch_size and not gathering:
            #print("big",date)
            #batches.append({"start":date,"end":date + timedelta(days=1),"last":False})
            batches.extend(split_big_days(data_h, date, batch_size))
            temp_amount = 0
        elif (amount >= batch_size and gathering) or (temp_amount > batch_size+maximum_difference):
            #print("big interruption",date)
            batches.append({"start":start_time,"end":datetime.combine(date, datetime.min.time()),"last":True}) # gathering
            batches.extend(split_big_days(data_h, date, batch_size))
            #batches.append({"start":date,"end":date + timedelta(days=1),"last":True}) # new
            temp_amount = 0
            gathering = False
        elif temp_amount >= batch_size and gathering:
            #print("gathering complete", {"start":start_time,"end":datetime.combine(date, datetime.min.time()),"last":True})
            batches.append({"start":start_time,"end":datetime.combine(date, datetime.min.time()),"last":True})
            temp_amount = 0
            gathering = False
        elif not gathering:
            gathering = True
            start_time = datetime.combine(date, datetime.min.time())
    else:
        #print(type(date))
        if gathering: # If ended while still under batch size
            #print("done",date)
            batches.append({"start":start_time,"end":datetime.combine(date, datetime.min.time()),"last":True})
        else: # If last hour was a big one
            batches[-1]["last"] = True
        del data
        del data_h
    return batches

def unravel_reviews(obj):
    #https://stackoverflow.com/questions/13730468/from-nd-to-1d-arrays
    return np.array(obj).ravel()




RAW_NUMBER_VERSION = "1.0"
def raw_number_data(df:pd.DataFrame):
    """
    V1.0
    Processes Steamstore review data into simple sum data by date.

    Example: 

    ```
    | date              | upvotes | good | ideal |
    | 25-12-2020        | 100     | 27   | 9     |
    ```

    Args:
        df (pd.DataFrame): Steam review dataframe from database.
        save (bool, optional): If true saves the result to database. Defaults to True.
    """
    df.dropna()
    df.timestamp_updated = df.timestamp_updated.dt.date
    df.timestamp_updated = df["timestamp_updated"].astype(str)
    #print(df.columns)
    df.replace({True: 1, False: 0},inplace=True)
    df["reviews_count"] = 1
    #GENERATOR
    df = df.drop(columns=["timestamp_created","weighted_vote_score"]).groupby("timestamp_updated").sum(numeric_only=False)
    df["review"] = df.review.map(lambda x: unravel_reviews(x)) # Meant for a single date's data
    df = review_to_column(df) # Works
    df.drop(columns=["review"],inplace=True)
    df.fillna(0,inplace=True)
    return df

def postprocess_gener(game:str, batches:list[dict], data_keys=DATA_KEYS)->tuple[pd.DataFrame,bool]:
    #query start
    collection = get_database()["gameDatas"][game]
    for item in batches:
        data =[]
        #star, end, last
        #print({"timestamp_updated":{"$gte":item["start"], "$lt":item["end"]}})
        #print(type(item["start"]),type(item["end"]),type(item["last"]))

        assert isinstance(item["start"], datetime)
        assert isinstance(item["end"], datetime)
        assert isinstance(data_keys, dict)
        # pull
        data = list(collection.find({"timestamp_updated":{"$gte":item["start"], "$lt":item["end"]}}, data_keys))
        df = pd.DataFrame(data)
        del data
        assert df.index.size !=0
        #print(df.columns)



        # process
        df = raw_number_data(df)
        yield df, item["last"]

def number_graph_maker(game:str, data_keys=DATA_KEYS):
    # 1. calculate work area
    # 2. calculate batches
    # 3. make generator
    # 4. start loop
    # 5. get processed and ready_to_send
    # 6. if not ready combine until ready
    # 7. save to database
    # 8. loop 5-7


    # 1.
    response = requests.get("http://admin-server:5006/api/v1/check_date_when", params={"game_name": game, "method":"number_graph"})
    assert response.status_code < 501


    collection = get_database()["gameDatas"][game]
    if response.status_code == 200:
        last_processed = response.text.split("-")
        last_processed = datetime(int(last_processed[0]),int(last_processed[1]),int(last_processed[2]))
        df = pd.DataFrame(list(collection.find({"timestamp_updated":{"$gte": last_processed}}, {"_id":0,"timestamp_updated":1})))
        first_process = False
    else:
        first_process = True
        df = pd.DataFrame(list(collection.find({}, {"_id":0,"timestamp_updated":1})))
    assert df.index.size != 0
    if df.index.size < 2000:
        df = pd.DataFrame(list(collection.find({"timestamp_updated":{"$gte": last_processed}}, data_keys)))
        df = raw_number_data(df)
        save_data(game, df, f'raw_number_graph_{RAW_NUMBER_VERSION}', "results", first_process=first_process)
        return
    #print(df.columns)
    # 2.
    batches = calc_batches(df)

    # 3.
    gener = postprocess_gener(game, batches, data_keys=data_keys)
    # 4.
    for x in batches:
        # 5.
        df, last = next(gener)
        assert "timestamp_created" not in df.columns
        if last:
            # 7
            save_data(game, df, f'raw_number_graph_{RAW_NUMBER_VERSION}', "results", first_process=first_process)
            first_process = False
            continue
        while not last:
            # 6.
            temp_df, last = next(gener)
            df = pd.concat(df,temp_df)
        else:
            #7
            save_data(game, df, f'raw_number_graph_{RAW_NUMBER_VERSION}', "results", first_process=first_process)
        first_process = False
        del df
    return

PROCESS_METHODS = {"correlation_matrix": (CORRELATION_MATRIX_VERSION, correlation_matrix), "raw_number": (RAW_NUMBER_VERSION, number_graph_maker)}

#Check that game is processed
#Check that raw data is processed up to today

def build_data(game:str, method:str, dates=None): # TODO clean this up
    game = game.replace(" ", "_")
    data_keys = {"_id":0,"recommendationid":1, "author":1, "review":1, "timestamp_created":0, "timestamp_updated":1, "voted_up":1, "votes_up":1, "votes_funny":1,
             "weighted_vote_score":1,"comment_count":1, "steam_purchase":1, "received_for_free":1, "written_during_early_access":1}
    since_processed_query = requests.get("http://admin-server:5006/api/v1/process_game", params={"game_name":game})
    assert since_processed_query != 400
    PROCESS_METHODS["raw_number"][1](game=game)

    if method == "correlation_matrix": # check if the game has raw_number_Data
        converter = Converter("word_2_number")
        number_columns = {str(v): 1 for v in converter.data_converter.values()}
        data_keys.update(number_columns) # add number dictionary
        data_keys.update({"date":1}) # add date
        #if len(data_keys.values()) < 100:
        #    raise ValueError(data_keys)
        del converter
        try:
            df = check_ready_data_exists("results", data_keys, collection_name=f'{game}_raw_number_graph_1.0')
        except ValueError:
            pass
        del data_keys
        PROCESS_METHODS["correlation_matrix"][1](df, game=game, result_return=False)