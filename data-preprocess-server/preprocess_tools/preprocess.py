import os
import re
from ast import literal_eval
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()



DRAWING_CHARACTERS = ['⢒', '⢷', '⣄', '⠿', '⢢', '⠘', '⡆', '⠖', '⠛', '⠊', '⣧', '⠹', '⠢', '⠄', '⠱',
                      '⢳', '⢧', '⠙', '⣻', '⠻', '⣆', '⠏', '⣿', '⢇', '⠒', '⢄', '⢠', '⠔', '⡴', '⠸', 
                      '⣏', '⡄', '⣇', '⢸', '⠐', '⢱', '⣹', '⡠', '⣤', '⡸', '⣼', '⣷', '⢆', '⠞', '⠟', 
                      '⡜', '⣀', '⠑', '⢖', '⣑', '⠬', '⡎', '⡀', '⠠', '⠎', '⣖', '⢡', '⢛', '⠇', '⠤',
                      '⠚', '⣠', '⠋', '⠃', '⡤', '⣛', '⣸', '⡔', '⢿', '⠦', '⢀', '⡿', '⢦', '⢝', '⠁',
                      '⠂', '⣜', '⢰', '⣴', '⢌', '⡥', '⣾', '⢲', '⣶', '⡣', '⠉', '⠈', '⡇','⢏', '⢃',
                      '⠗', '⢗', '⣟', '⢾', '⡏', '⠴', '⡟', '⡋', '⢘', '⢴', '⢻', '⣁', '⡌', '⠶', '⣦',
                      '⣰','⢹','⡶','⢐',]
# https://stackoverflow.com/questions/3809401/what-is-a-good-regular-expression-to-match-a-url
#LINK_REGEX = "https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"
#LINK_REGEX = "^https?:\\/\\/(?:www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)$"
LINK_REGEX = '([^\s]+)?https?([^\s]+)(?:\))?'
RAITING_MAPPING = {"1/10": "1 out of 10", "2/10": "2 out of 10", "3/10": "3 out of 10", "4/10": "4 out of 10", 
                   "5/10": "5 out of 10", "6/10": "6 out of 10", "7/10": "7 out of 10", "8/10": "8 out of 10",
                   "9/10": "9 out of 10", "10/10": "10 out of 10","0/10": "zero out of 10", }
MAPPING_MULTIWORDS = {"and/or": "and or maybe"," + ":"and", '/':" or ", "&": "and"}


# Made with ./templates/template1.txt in mind
def graph_to_review(review:str):
    # '\u2610' == ☐
    sectored = "".join([line.strip('\u2611') for line in review.split('\n') if '\u2610' not in line and len(line) != 0])
    result = []
    for line in sectored.split("---{")[1:]:
        result.append(line[1:].replace("}---", "is/are/for"))
    return result

def replace_mapping(review):
    review = re.sub(LINK_REGEX, "META_INFORMATION_JUST_A_LINK",review)
    for map_choice, replacement in RAITING_MAPPING.items():
        review = review.replace(map_choice, replacement)
    for map_choice, replacement in MAPPING_MULTIWORDS.items():
        review = review.replace(map_choice, replacement)
    review = re.sub(r'\[[\D]+\]', "", review) # [url][quote]
    return review

#DRAWING_CHARACTERS = ['\u28FF', '\u2824', '\u28BF', '\u280B']
def clip_picture(review:str):
    for character in DRAWING_CHARACTERS:
        #print(f'{character} \u2192 ""')
        review = review.replace(character, '')
    if len(review.strip('\n')) < 2:
        review = "META_INFORMATION_JUST_A_PICTURE"
    return review

#def author_unravel(df):
#    df = pd.concat([df,pd.DataFrame.from_records(df.author)],axis=1)
#    df.drop(columns="author",inplace=True)
#    return df

def check_contents(review:str):
    if review.isalpha():
        return
    if review.count('\u28FF'): # ⣿ pics
        pass

def get_dictionary(model="word_2_number") -> dict:
    user = os.getenv('USER2_NAME')
    pwd = os.getenv('USER2_PWD')
    #print(f'{user}, {pwd}')
    #CONNECTION_STRING = f'mongodb://{user}:{pwd}@localhost:27017/'
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

word_2_number = Converter("word_2_number")

# https://stackoverflow.com/questions/483666/reverse-invert-a-dictionary-mapping
def update_dictionary(word) -> bool:
    db = get_dictionary()
    payload = {"word":word,"number":word_2_number.word_counter+1}
    db.insert_one(payload)
    word_2_number.update()

def word_conversion(word):
    if word not in word_2_number.data_converter:#.keys():
        update_dictionary(word)
        word_2_number.update()
        return word_2_number.data_converter[word]
    return word_2_number.data_converter[word]

def convert_word2number(review):
    try:
        assert type(review) !=float
    except AssertionError as bad:
        print(f'review:  {review}  \n\n\n\n')
        raise AssertionError(f'review:  {review}  \n\n\n\n')
    return list(map(word_conversion, review))

def main(df:pd.DataFrame, testing_purpose=False):
    print("Preprocessing...")

    if not testing_purpose:
        df.review = pd.Series(map(replace_mapping,df.review))
        # re.escape()
        df.review = df.review.str.replace(r'(\s)*([a-zA-Z]*([^\x00-\x7F])+([a-zA-Z]|[^\x00-\x7F])*)(\s)?', regex=True, repl='') # Words with non english letters out
        df.review = df.review.str.replace(r'[!?]+', '.', regex=True) # !?!?!?!?
        df.review = df.review.str.strip(',')
        df.review = df.review.str.replace(r'((?=[^.?!\s])\W)+', '',regex=True) # ;)   :)
        df.review = df.review.str.replace(r'([\s]+)?[.]+([\s]?)+', " . ", regex=True) # \n. \t\t
        df.review = df.review.str.lower()
        #df.review = pd.Series(map(replace_mapping,df.review))
        temp = df.columns.values
        df.review = df.review.str.split()
        assert df.review.isna().all() == False
        #bad_df = df.loc[df.review.isna()]
        df = df.loc[~df.review.isna()] # TODO temporary fix for when processing game that already is in database
        assert len(df) != 0
        assert len(df.columns.values) == len(temp)
        df.review = pd.Series(map(convert_word2number,df.review)) #df.review.map(word_conversion)
        #raise AssertionError(bad_df.review.values)
    df["timestamp_created"] = pd.to_datetime(df["timestamp_created"],unit='s')
    df["timestamp_updated"] = pd.to_datetime(df["timestamp_updated"],unit='s')
    df.reset_index(inplace=True, drop=True)
    if "author" in df.columns:
        df = pd.concat([df,pd.DataFrame.from_records(df["author"])],axis=1)
        df.drop(columns="author", inplace=True)
    df.rename(columns={"recommendationid":'_id'},inplace=True)
    print("Preprocessed!")
    return df
