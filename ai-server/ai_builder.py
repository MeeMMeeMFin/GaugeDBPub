import pandas as pd
from sklearn.model_selection import train_test_split
from data_pull_tools import get_database, query_by_dates, Converter
import tensorflow as tf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from numpy import array as np_array
import pickle

DATA_KEYS = {"_id":0,"recommendationid":1, "author":1, "review":1, "timestamp_created":1, "timestamp_updated":1, "voted_up":1, "votes_up":1, "votes_funny":1,
             "weighted_vote_score":1,"comment_count":1, "steam_purchase":1, "received_for_free":1, "written_during_early_access":1}


def make_data_keys(data_keys:dict) -> dict:
    converter = Converter("word_2_number")
    number_columns = {str(v): 1 for v in converter.data_converter.values()}
    data_keys.update(number_columns) # add number dictionary
    return data_keys

# https://youtu.be/i_LwzRVP7bg?t=10709
def plot_loss(history):
    plt.plot(history.history["loss"], label="loss")
    plt.xlabel("epoch")
    plt.ylabel("MSE")
    plt.legend()
    plt.grid(True)
    plt.savefig(f'MSE_epoch_loss_learning.png')
    plt.show()


def drop_zero_columns(df:pd.DataFrame):
    drobbed = [column for column in df.columns.values if len(df[column].value_counts())==1]
    df.drop(columns=drobbed, inplace=True)
    print(f'Drobbed {len(drobbed)} columns', end='\r', flush=True)


def calculate_changes(df:pd.DataFrame, columns:list):
    for column in columns:
        df[f'total_{column}'] = df[column].cumsum()
        df[f'total_{column}_percent'] = df[f'total_{column}'].pct_change().fillna(0)
        df.drop(columns=[f'total_{column}'],inplace=True)

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

# Can probably skip reshape if its done before input
def custom_evaluate(model, x, y, low= -1, high= 1, debug=False):
    x_shape = len(x[0])
    predictions = [model.predict(day_data.reshape(1,x_shape), verbose=0)[0][0] for day_data in x]
    accuracy = 0
    for i, prediction in enumerate(predictions):
        temp = round(prediction)
        if temp == y[i]:
            accuracy +=1
            if debug:
                print(f'Guessed: {temp} correct:{y[i]}')
        elif temp >= y[i]+low and temp <= y[i]+high:
            accuracy +=1
            if debug:
                print(f'Guessed: {temp} correct:{y[i]}')
    accuracy = accuracy/len(y)
    return accuracy


def create_ai_datas(data_keys:dict, database = "results", type_data = "raw_number_graph", type_version="1.0") -> tuple:
    """
    Creates a tuple of ai trainable data and the correct answers of that data

    Args:
        data_keys (dict, optional): Data columns.
        database (str, optional): Database name. Defaults to "results".
        type_data (str, optional): Data type to be used in data training. Defaults to "raw_number_graph".
        type_version (str, optional): Collection versio type. Defaults to "1.0".

    Returns:
        tuple(pd.Dataframe, list): Ai trainable data and correct answers (INDEX SENSITIVE)
    """
    db = get_database()[database]
    collections =  list(db.list_collection_names())
    for skip in ["initial", "games_list_4_AI_USES_NOT_A_GAME"]:
        try:
            collections.remove(skip)
        except:
            pass
    collections = [table for table in collections if f'{type_data}_{type_version}' in table]
    data_keys = make_data_keys(data_keys)
    datas = {}
    data_keys["_id"] = 0
    for game_data in collections:
        datas[game_data] = check_ready_data_exists(database, data_keys, collection_name=game_data)
    correct = []
    for data in datas.values():
        correct.extend(data.voted_up.values[1:]) # Skip first days result for those can't be predicted
        calculate_changes(data, ["voted_up", "votes_up", "reviews_count"])
        data.drop(data.tail(1).index, inplace=True)
    ai_data = pd.concat(datas.values()).reset_index(drop=True).fillna(0)
    ai_data.drop(columns=["date"],inplace=True)
    return ai_data, correct

def build_ai(df:pd.DataFrame, correct = None):
    """
    Builds and saves a simple neural network into './

    Args:
        df (pd.DataFrame): Ai data
        correct (_type_, optional): Ai correct results. Defaults to None.

    Raises:
        IndexError: If given data is bad/incorrectly built
    """
    drop_zero_columns(df)
    if correct is None:
        correct = df.voted_up.values[1:] # skip first value for there is no data before release
        ai_data = df.to_numpy()[:-1] # skip last for we don't know tomorrow
    else:
        ai_data = df.to_numpy()
        correct = np_array(correct)
    correct.astype(dtype=float)
    with open("ai_columns.pkl", "wb") as pik:
        pickle.dump(df.columns.values ,pik)
    data_column_count = len(df.columns.values)
    works = len(correct) == len(ai_data)
    if works:
        print(works)
    else:
        raise IndexError("Data and correct answers are different lengths")
    X_train, X_test, y_train, y_test = train_test_split(ai_data, correct, test_size=0.25, random_state=42)
    noramlize_layer = tf.keras.layers.Normalization(input_shape=(data_column_count,), axis=None)
    noramlize_layer.adapt(X_train[0])
    model = tf.keras.Sequential([
        noramlize_layer,
        tf.keras.layers.Flatten(),
        #tf.keras.layers.Dense(512, activation='relu'),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(1)
    ])
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001),
                  loss="mean_absolute_error", #"mean_squared_error"
                  metrics=['accuracy'])
    #model.summary()
    model.fit(X_train,
                y_train,
                verbose=0,
                epochs=2)
    #plot_loss(history)
    accuracy = custom_evaluate(model, X_test, y_test, low=-3, high=3, debug=False)
    with open("ai_accuracy.pkl", "wb") as pik:
        pickle.dump(accuracy ,pik)
    model.save("./models/bad_ai_v1.keras")
    return accuracy

def forecast_today(game:str, data_type="raw_number_graph_1.0", model="bad_ai_v1", data_keys=DATA_KEYS) ->int:
    #TODO Pull data from database
    yesterday = datetime.today().date() - timedelta(days=1)
    the_day_before = yesterday - timedelta(days=1) # for calculating 1 day change
    data_keys = make_data_keys(data_keys)
    data_keys.update({"reviews_count":1})
    data = query_by_dates(game, data_type, str(the_day_before), str(yesterday), data_keys)
    calculate_changes(data, ["voted_up", "votes_up", "reviews_count"])
    with open("ai_columns.pkl", "rb") as pik:
        needed_columns = pickle.load(pik)
    for needed_column in needed_columns:
        if needed_column in data.columns:
            pass
        else:
            data[needed_column] = 0
    for wot in data.columns:
        if wot not in needed_columns:
            data.drop(columns=[wot],inplace=True)
    data = data.to_numpy()[-1]
    #TODO Load ai
    model = tf.keras.models.load_model(f'./models/{model}.keras')
    #TODO Predict with AI & yesterday's data
    prediction = model.predict(data.reshape(1,len(data)), verbose=0)
    return round(prediction[0][0])