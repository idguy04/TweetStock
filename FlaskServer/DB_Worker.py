import numpy as np
import pandas as pd
from TweetStockModel import TweetStockModel as tsm
import time
import pandas_market_calendars as mcal
from datetime import datetime as dt
import os
import json
#from sqlalchemy import create_engine
import firebase_admin
from firebase_admin import credentials, db

# ----------------------------------------------------------------------------------------------- #
if os.name == 'nt':
    delimiter = '\\'
    prefix = f'{os.getcwd()}\\FlaskServer\\'
elif os.name == 'posix':
    delimiter = '/'
    prefix = '/home/pi/FinalProject/FlaskServer/'

PRED_cred = credentials.Certificate(
    f"{prefix}CONFIGS/tweetstockpred-firebase-adminsdk-nctp0-54e961d24e.json")

firebase_admin.initialize_app(PRED_cred, {
    'databaseURL': "https://tweetstockpred-default-rtdb.europe-west1.firebasedatabase.app/"
})

os.system(
    f'export GOOGLE_APPLICATION_CREDENTIALS="{prefix}CONFIGS/tweetstockpred-firebase-adminsdk-nctp0-54e961d24e.json"')
Tweets_cred = ""


MODELS = {
    # 'AAPL': {
    #     'path': f'{prefix}SelectedModels{delimiter}AAPL{delimiter}AAPL_acc_0.633_npast_1_epoch_4_opt_rmsprop_num_3848.h5',
    #     'features': 1
    # },
    # 'AMZN': {
    #     'path': f'{prefix}SelectedModels{delimiter}AMZN{delimiter}AMZN_acc_0.673_npast_1_epoch_7_opt_rmsprop_num_1396.h5',
    #     'features': 1
    # },
    # 'GOOG': {
    #     'path': f'{prefix}SelectedModels{delimiter}GOOG{delimiter}GOOG_acc_0.612_npast_1_epoch_10_opt_adam_num_2283.h5',
    #     'features': 1
    # },
    # 'GOOGL': {
    #     'path': f'{prefix}SelectedModels{delimiter}GOOGL{delimiter}GOOGL_acc_1.0_npast_1_epoch_4_opt_adam_num_3147.h5',
    #     'features': 1
    # },
    # 'MSFT': {
    #     'path': f'{prefix}SelectedModels{delimiter}MSFT{delimiter}MSFT_acc_0.612_npast_1_epoch_4_opt_adam_num_4359.h5',
    #     'features': 2
    # },
    'TSLA': {
        'path': f'{prefix}SelectedModels{delimiter}TSLA{delimiter}TSLA_acc_0.633_npast_1_epoch_4_opt_adam_num_804.h5',
        'features': 1
    }
}


def Main():
    # 'features': 1 --> ['Tweet_Comments', 'Tweet_Retweets','Tweet_Likes', 'Positivity', 'Negativity', 'Neutral']
    # 'features': 2 --> ['Tweet_Sentiment','Tweet_Comments', 'Tweet_Retweets', 'Tweet_Likes']

    while True:
        Get_predictions()
        # if (is_valid_day()):
        #     update_db()
        #     time.sleep(3 * 60 * 60)  # sleep 3 hours
        # else:
        #     print("invalid day")
        #     continue


def Get_Date_Time():
    return dt.now()


def Get_Date_Time_Stringify(format="%d_%m_%Y_%H"):
    return Get_Date_Time().strftime(format)


def write_to_log(msg):
    with open(f'LOG_{Get_Date_Time_Stringify()}', 'a+', encoding='utf-8') as f:
        f.write(msg)


def Get_predictions(models=MODELS):
    result = {
        'pred_df': {},
        'tweets_df': {}
    }
    for ticker in models.keys():
        # Run the model
        model = tsm(
            model_path=models[ticker]['path'], model_ticker=ticker, features_version=models[ticker]['features'])
        Ticker_and_Pred_Table_Dict, Ticker_Stats_Table_Dict = model.get_prediction()

        if Ticker_and_Pred_Table_Dict in (None, '', '[]', r'[{}]') or Ticker_Stats_Table_Dict in (None, '', '[]', r'[{}]'):
            print("Error Getting data from model!")
            break
        if len(Ticker_and_Pred_Table_Dict) == 1:
            result['pred_df'].update({ticker: Ticker_and_Pred_Table_Dict[0]})
        else:
            write_to_log(
                f'Ticker_and_Pred_Table_Dict returned greater than 1:\n{Ticker_and_Pred_Table_Dict}')

        if len(Ticker_Stats_Table_Dict) > 0:
            for tweet in Ticker_Stats_Table_Dict:
                result['tweets_df'].update(
                    {ticker: tweet})
        else:
            write_to_log(
                f'Ticker_Stats_Table_Dict returned null:\n{Ticker_Stats_Table_Dict}')

        # time.sleep(15*60)  # sleep 15 mins

    invalid_results = (None, '')
    if result['pred_df'] in invalid_results or result['tweets_df'] in invalid_results:
        print("@DB_Worker- bad results")
        return
    post_to_db(result['pred_df'], result["tweets_df"])


def df_to_json(df):
    return df.to_json(orient='records')


def post_to_db(pred_dict, tweets_dict):

    #pushtoDB(Tweets_cred, tables[1], "Tweets")
    def pushtoDB(dict_to_push, name):
        ref = get_db_ref(name)
        to_push = json.dumps(dict_to_push)
        ref.set(
            {
                name: {
                    to_push[0]
                }
            }
        )

    pushtoDB(pred_dict, "Prediction")
    #pushtoDB(PRED_cred, tweets_df, "Tweets")


def is_valid_day():
    '''
    This method converts israel's time to NY time, 
    and checks if the current date and time is during stock excange open hours (NYSE & NASDAQ)
    '''
    current_time = Get_Date_Time()
    year, month, day, hour, minute = current_time.year, current_time.month, current_time.day, current_time.hour, current_time.minute
    today, time = f'{year}-{month}-{day}', f'{hour}:{minute}'
    start_of_year, end_of_year = f'{year}-01-01', f'{year}-12-31'

    nyse = mcal.get_calendar('NYSE')

    try:
        schedule = nyse.schedule(
            start_date=today, end_date=today)
    except Exception as e:
        write_to_log(f'nyse.open_at_time says:\n{e}')
        return False

    timestamp = pd.Timestamp(
        f'{today} {time}', tz='Israel').tz_convert('America/New_York')  # convert israel time to NY time

    if not schedule.empty:
        try:
            if nyse.open_at_time(schedule, timestamp):
                return True
        except ValueError as ve:
            write_to_log(f'nyse.open_at_time says:\n{ve}')
            return False
    return False


def get_db_ref(root_name):
    return db.reference(f"/{root_name}")


# ----------------------------------------------------------------------------------------------- #
if __name__ == '__main__':
    Main()
