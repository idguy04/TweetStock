# import pandas as pd
#from urllib.request import DataHandler
from pandas import DataFrame as pd_DataFrame, merge as pd_merge, to_datetime as pd_to_datetime
from numpy import array as np_array, split as np_split
from tensorflow import convert_to_tensor as ctt, float32 as tf_float32
from math import log, inf
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.model_selection import train_test_split
from csv import reader as csv_reader
import Helper
'''
This class will be used to coordinate the work between
the ModelTrainer.py and TweetStockModel.py .
It will contain every method which is used to handle data.
'''


'''
# TWITTER_VERSION = 2             # twitter version.
# MAX_TWEETS_RESULTS = 100        # max results for first tweets query.
# MAX_USER_TWEETS_RESULT = 100    # max results for use engagement tweets
'''
# days on which the model was train to precict based on.
N_PAST = 1
TSM_MIN_TWEET_STATS_SUM = 25        # min tweet filtering sum of stats
TSM_MIN_USER_FOLLOWERS = 100        # min user followers num to be included
# SCALING
SCALING = 'min_max'
# MT_SCALING_PARAMS = {
#     "Tweet_Comments": (0, 565),
#     "Tweet_Retweets": (0, 990),
#     "Tweet_Likes": (0, 988)  # ,
#     # "User_Engagement": (0, 1000)
# }
MT_SCALING_PARAMS = {
    "Tweet_Comments": [[0.0], [10.0]],
    "Tweet_Retweets": [[0.0], [10.0]],
    "Tweet_Likes": [[0.0], [10.0]],
    "User_Engagement": [[0.0], [0.64]]
}
TSM_SCALING_PARAMS = {
    "reply_count": [[0.0], [10.0]],  # 565],
    "retweet_count": [[0.0], [10.0]],  # 990],
    "like_count": [[0.0], [10.0]],  # 988]  # ,
    "User_Engagement": [[0.0], [0.64]]
}

# log2
MT_ENGAGEMENT_SCALING_PARAMS = {
    'eng_total_retweets': [[0.0], [19.32]],
    'eng_total_likes': [[0.0], [22.35]],
    'eng_total_replies': [[0.0], [16.8]],
    'followers_count': [[0.0], [24.5]],
    'eng_tweets_length': [[0.0], [100.0]]
}
TSM_ENGAGEMENT_SCALING_PARAMS = {
    "reply_count": [[0.0], [19.32]],
    "retweet_count": [[0.0], [22.35]],
    "like_count": [[0.0], [16.8]],
    'follower_count': [[0.0], [24.5]],
    'eng_tweets_length': [[0.0], [100.0]]
}

# ENGAGEMENT_SCALING_PARAMS - other versions
"""
# log3
# ENGAGEMENT_SCALING_PARAMS = {
#     'eng_total_retweets': (0.0, 12.188),
#     'eng_total_likes': (0.0, 14.1),
#     'eng_total_replies': (0.0, 10.6),
#     'followers_count': (0.0, 15.47),
#     'eng_tweets_length': (0.0, 100.0)
# }
# log3-followers| log2-else
# ENGAGEMENT_SCALING_PARAMS = {
#     'eng_total_retweets': [[0.0], [19.32]],
#     'eng_total_likes': [[0.0], [22.35]],
#     'eng_total_replies': [[0.0], [16.8]],
#     'followers_count': [[0.0], [15.5]],
#     'eng_tweets_length': [[0.0], [100.0]]
# }
"""
INCLUDE_REPLIES = True

#--------- ModelTrainer.py - to combine ----------#
# COMBINED METHODS
"""
def mt_create_sequence(dataset, target, num_of_rows=N_PAST):
    '''Returns np array'''
    sequences = []

    start_idx = 0
    if target:
        labels = []
        features_df = dataset.drop(columns=target)
        labels_df = dataset[[target]]
        # Selecting "num_of_rows"
        for stop_idx in range(num_of_rows, len(dataset)):
            sequences.append(features_df.iloc[start_idx:stop_idx])
            labels.append(labels_df.iloc[stop_idx][0])
            start_idx += 1
        return np_array(sequences, dtype='object'), np_array(labels, dtype='object')
    else:
        # Selecting "num_of_rows"
        for stop_idx in range(num_of_rows, len(dataset)):
            sequences.append(dataset.iloc[start_idx:stop_idx])
            labels.append(dataset.iloc[stop_idx])
            start_idx += 1
        return np_array(sequences, dtype='object')
"""


def mt_scale_data(df, target='price_difference'):
    """
    Handles data scaling and aggregation (e.g. average) per day of the data
    """
    NONE_SCALABLE_MULTIPLIABLE_FEATURES = [
        'Date', target, "Tweet_Sentiment", "Positivity", "Neutral", "Negativity"]

    def is_scalable_multipliable_feature(feature):
        return feature not in NONE_SCALABLE_MULTIPLIABLE_FEATURES

    df_cols = df.columns
    dates_dict = {}
    for col in df_cols:
        dates_dict[col] = []

    df = df.groupby(by=['Date'])
    for date in df:
        sentiment_col = np_array(date[1]["Tweet_Sentiment"]).reshape(-1, 1)
        curr_day_avg_sentiment = sentiment_col.mean()
        curr_day = date[0]
        curr_day_target = date[1][target].iloc[0]
        dates_dict['Tweet_Sentiment'].append(curr_day_avg_sentiment)
        dates_dict['Date'].append(curr_day)
        dates_dict[target].append(curr_day_target)
        for col_name in df_cols:
            curr_day_col = np_array(date[1][col_name]).reshape(-1, 1)
            if is_scalable_multipliable_feature(col_name):
                curr_day_col *= sentiment_col

                scaler = MinMaxScaler()
                scaler.fit(MT_SCALING_PARAMS[col_name])
                curr_day_col = scaler.transform(curr_day_col)

                dates_dict[col_name].append(curr_day_col.mean())
            # if col_name == 'User_Engagement':
            #     print("hi")
    new_df = pd_DataFrame.from_dict(dates_dict)
    #Helper.save_df_to_csv(new_df, '/home/pi/FinalProject/FlaskServer/Data/Networks/', 'ScaledData.csv')
    return new_df


def mt_filter_users(df, follower_threshold=150):
    """
    -- 1. remove broken/bad eng score (user blocked public metrics)
    -- 2. removes users with less than follower_threshold
    """
    to_remove = []
    print("len before = " + str(len(df)))
    for i in range(len(df)):
        try:
            df['eng_score'][i] = float(df['eng_score'][i])
        except ValueError as ex:
            to_remove.append(i)
            print(ex)
        except:
            print('Problem getting eng_score at index', i)

    for i in range(len(df)):
        if df['eng_score'][i] == inf or df['followers_count'][i] < follower_threshold:
            to_remove.append(i)

    df.drop(to_remove, inplace=True)
    df.reset_index(drop=True, inplace=True)
    print("len after = " + str(len(df)))
    return df


def mt_filter_tweets(tweets_df, tweets_stats_threshold=25):
    """
    naive filtering based on comment+liikes+retweets < 25
    also gets rid of sentiments=0
    """
    print("----init_tweets----")
    print('len before', len(tweets_df))

    # filter the tweets
    temp_tweets = tweets_df[tweets_df['comment_num'] +
                            tweets_df['retweet_num'] + tweets_df['like_num'] > tweets_stats_threshold]
    temp_tweets = temp_tweets[temp_tweets['Compound'] != 0]
    temp_tweets = temp_tweets[temp_tweets['Neutral'] != 1]

    temp_tweets.reset_index(drop=True, inplace=True)
    print('len after', len(temp_tweets))
    print("\n\n")
    return temp_tweets


def calc_eng_score(scaled_log_n_rts, scaled_log_n_likes, scaled_log_n_replies, scaled_log_n_followers, n_tweets, ):
    eng = 0
    # Engagement score calculation
    if scaled_log_n_followers > 0 and n_tweets > 0:
        eng = ((scaled_log_n_rts+scaled_log_n_likes +
               scaled_log_n_replies)/scaled_log_n_followers)/n_tweets
    return eng


def mt_get_eng_score(users_df, include_replies=INCLUDE_REPLIES):
    ''' gets users df and returns the df with the engagement score calculated.
        df should have the following columns:  '''
    df = users_df.copy()

    col_names = ['eng_total_retweets', 'eng_total_likes',
                 'eng_total_replies', 'followers_count', 'eng_tweets_length']
    saving = {}

    for col_name in col_names:
        # log taking
        if col_name != 'eng_tweets_length':
            df[col_name] = [log(x+1, 2) for x in df[col_name]]

            # debugging
            """
            x_min, x_max = df[col_name].min(), df[col_name].max()
            saving[col_name] = (x_min, x_max)
            """
            # END debugging

            # min max scaling
            scaler = MinMaxScaler()
            scaler.fit(MT_ENGAGEMENT_SCALING_PARAMS[col_name])
            df[col_name] = scaler.transform(
                np_array(df[col_name]).reshape(-1, 1))

    for i in range(len(df)):
        rts = df['eng_total_retweets'][i]
        likes = df['eng_total_likes'][i]
        replies = df['eng_total_replies'][i]
        followers = df['followers_count'][i]
        total_tweets = df['eng_tweets_length'][i]

        if not include_replies:
            replies = 0

        df['eng_score'][i] = calc_eng_score(
            scaled_log_n_rts=rts, scaled_log_n_likes=likes, scaled_log_n_replies=replies, scaled_log_n_followers=followers, n_tweets=total_tweets)

    return df


def mt_transform_features_to_log(dnn_df):
    for col_name in ['Tweet_Likes', 'Tweet_Comments', 'Tweet_Retweets']:
        dnn_df[col_name] = [log(x+1, 2) for x in dnn_df[col_name]]
    return dnn_df

#------ ModelTrainer.py - seperate -------#


def mt_split_data(np_array_sequence, np_array_labels, train_random_state=4321, test_random_state=1234):
    '''
    - Returns randomly shuffled numpy_arrays.
    - Seperation between train_random_state seed and test_random_state seed
      is used to give the option to shuffle {train_data} + {validation_data} with a random seed
      and the {test_data} with a constant seed.
    '''
    testing_size, validation_size = 50, 50

    if len(np_array_sequence) < (testing_size + validation_size):
        Helper.write_to_log(
            f"DataHandler.py/mt_split_data: sequence is smaller than split sizes... {Helper.get_date_time_stringify(format='%d/%m/%Y-%H:%M:%S')}")
        return None

    # 1. split {data} to -> {train_data}, {test_data}; len({test_data}) == testing_size
    train_seq, test_seq, train_labels, test_labels = train_test_split(
        np_array_sequence, np_array_labels, test_size=testing_size/np_array_sequence.shape[0], random_state=int(test_random_state))
    # 2. split {train_data} to -> {train_data}, {validation_data}; len({validation_data}) == validation_size
    train_seq, validation_seq, train_labels, validation_labels = train_test_split(
        train_seq, train_labels, test_size=validation_size/train_seq.shape[0], random_state=int(train_random_state))

    # train_data, validation_data, test_data = np_split(dnn_df.sample(frac=1, random_state=42), [
    #     int(len(dnn_df)-testing_size-validation_size), int(len(dnn_df)-testing_size)])

    return train_seq, train_labels,  validation_seq, validation_labels, test_seq, test_labels


def mt_get_merged(tweets_df, users_df, stocks_df, exclude_TSLA=False):
    ''' Get the merged tweets users and stocks pd_DataFrame - returns the merged df '''
    print("---get_merged----")
    # --> merge stocks_2019 with tweets_2019 by ticker and date
    temp_merged_df = pd_merge(stocks_df, tweets_df, on=[
        'Date', 'ticker_symbol'], how='inner')
    # --> and users to it
    temp_users = users_df.copy()
    temp_users.rename(columns={'screen_name': 'writer'}, inplace=True)
    merged_df = pd_merge(temp_merged_df, temp_users,
                         on=['writer'], how='inner')
    if exclude_TSLA:
        print('with TSLA', len(merged_df))
        merged_df = merged_df[merged_df['ticker_symbol'] != 'TSLA']
        print('without TSLA', len(merged_df))
    # clear nulls
    merged_df.dropna(axis=0, inplace=True)
    merged_df.reset_index(drop=True, inplace=True)
    print("\n\n")
    return merged_df


def mt_get_price_diff(stocks_df):
    ''' gets the close price diff (today-yesterday) 1 = up, 0 = down '''
    temp_stocks = stocks_df.reset_index(drop=True)
    temp_stocks['price_difference'] = [
        0.0 for i in range(len(temp_stocks))]

    temp = {}

    for i in range(1, len(temp_stocks)):
        # Next Close - Today Close
        # today = float(temp_stocks['Close'][i])
        # yesterday = float(temp_stocks['Close'][i-1])
        # # try getAvg(high,low)
        # price_diff = today-yesterday

        price_diff = float(temp_stocks['Close'][i]) - \
            float(temp_stocks['Open'][i])
        temp[i] = price_diff
        #temp_stocks['price_difference'][i] = price_diff

        temp_stocks['price_difference'][i] = 1 if price_diff >= 0 else 0

        # if (price_diff>=0): temp_stocks['price_difference'][i] = 1
        # else: temp_stocks['price_difference'][i] = 0

    temp_stocks.drop([0], inplace=True)
    temp_stocks.reset_index(drop=True, inplace=True)

    Helper.save_dict_to_csv(
        temp, '/home/pi/FinalProject/FlaskServer/Data/Networks/test/', 'price_diff')

    return temp_stocks


def sort_df_by_dates(df, date_col_name='Date', format='%d/%m/%Y'):
    df[date_col_name] = pd_to_datetime(df[date_col_name], format=format)
    return df.sort_values(by=date_col_name).reset_index(drop=True)


#------ TweetStockModel.py - to combine -------#
# COMBINED METHODS
"""
def tsm_create_sequence(dataset):
    return np_array(dataset)
"""


def tsm_transform_features_to_log(df):
    for col_name in ['n_replies', 'n_retweets', 'n_likes']:
        df[col_name] = [log(x+1, 2) for x in df[col_name]]
    return df


def tsm_get_scale_and_mean(df, feature_set, n_past=N_PAST, scaling=SCALING):
    def is_scalable_feature(f):
        return f in feature_set or f == 's_compound'

    def is_sentiment_feature(f):
        return f in ['s_compound', 's_neg', 's_pos', 's_neu']

    if n_past == 1:
        df_dict = {}
        for col in df.columns:
            if is_scalable_feature(col):
                df_dict[col] = []
                f = df[col] * \
                    df["s_compound"] if not is_sentiment_feature(
                        col) else df[col]
                scaler = MinMaxScaler() if scaling == 'min_max' else StandardScaler()
                df_dict[col].append(scaler.fit_transform(
                    np_array(f).reshape(-1, 1)).mean())
        return pd_DataFrame.from_dict(df_dict)
    else:
        return "N_past is not 1 @ get_scale_and_mean()"


def tsm_filter_tweets(tweets, threshold=TSM_MIN_TWEET_STATS_SUM):
    # print(f"Filtering Tweets of {self.ticker} for {self.ip}")
    tweets_to_remove = []
    # print("len before", len(tweets))
    for tweet in tweets:
        if tweet['s_compound'] == 0.0 or tweet['s_neu'] == 1.0 or tweet['n_retweets'] + tweet['n_likes'] + tweet['n_replies'] < threshold:
            tweets_to_remove.append(tweet)

    for tweet in tweets_to_remove:
        tweets.remove(tweet)

    # print("len after", len(tweets))
    # for tweet in tweets:
    #     print(tweet['s_neu'])
    return tweets


def tsm_filter_users(tweets, threshold=TSM_MIN_USER_FOLLOWERS):
    # print(f"Filtering users of {self.ticker} for {self.ip}")
    tweets_to_remove = []
    for tweet in tweets:
        if tweet['u_n_followers'] < threshold or tweet['u_engagement'] == 0:
            tweets_to_remove.append(tweet)

    for tweet in tweets_to_remove:
        tweets.remove(tweet)

    return tweets

# Checked (V)


def tsm_get_single_user_eng_score(user_tweets, user_followers, include_replies=INCLUDE_REPLIES):
    u_n_rts, u_n_replies, u_n_likes = 0, 0, 0
    stats = {
        'retweet_count': 0,
        'reply_count': 0,
        'like_count': 0
    }
    # get stats
    for tweet in user_tweets:
        for stat in stats:
            stats[stat] += tweet['public_metrics'][stat]
            # u_n_rts += tweet['public_metrics']['retweet_count']
            # u_n_replies += tweet['public_metrics']['reply_count']
            # u_n_likes += tweet['public_metrics']['like_count']

    stats['follower_count'] = user_followers
    # take log
    for stat in stats:
        stats[stat] = log(stats[stat] + 1, 2)

    # normalize
    for stat in stats:
        scaler = MinMaxScaler()
        scaler.fit(TSM_ENGAGEMENT_SCALING_PARAMS[stat])
        stats[stat] = scaler.transform(stats[stat])

    if not include_replies:
        stats['reply_count'] = 0

    return calc_eng_score(scaled_log_n_rts=stats['retweet_count'], scaled_log_n_likes=stats['like_count'], scaled_log_n_replies=stats['reply_count'], scaled_log_n_followers=stats['follower_count'], n_tweets=len(user_tweets))

#------ TweetStockModel.py - seperate -------#


def tsm_twitter_dict_res_to_df(data):
    try:
        temp = {}
        for key in data[0].keys():
            temp[key] = []
            for d in data:
                temp[key].append(d[key])
    except Exception as err:
        print('twitter_dict_res_to_df()', err)
        return None
    # print(temp)
    return pd_DataFrame.from_dict(temp)


def tsm_prep_data(df, feature_set):
    # 0.0 sort df by date
    df = sort_df_by_dates(df=df, date_col_name='created_at', format="")
    # 1.0 Scale Data & Get Mean
    df = tsm_get_scale_and_mean(tsm_transform_features_to_log(df), feature_set)
    # 1.1 Select features
    df = df[feature_set]

    # 2 Get df mean
    # print('before mean', df, len(df), df.shape)
    # df = self.get_scale_and_mean(df)
    # print('after mean', df, len(df), df.shape)

    # 3 Create sequence from df
    test_seq = create_sequence(df)
    # print('\n\n', test_seq, test_seq.shape)

    # 4 Scale data
    test_seq = test_seq.reshape(
        (len(test_seq), test_seq.shape[0] * test_seq.shape[1]))
    # scaled_test_seq = scale_seq(test_seq)

    # Return preped data
    return ctt(test_seq, dtype=tf_float32), df


def tsm_get_tweets_table_dict_result(tweets_df):
    features = ['tweet_id', 'u_engagement', 'n_likes', 'n_replies',
                'n_retweets', 's_pos', 's_neu', 's_neg', 's_compound']
    renames = {
        'u_engagement': 'user_engagement',
        'n_likes': 'tweet_likes',
        'n_replies': 'tweet_replies',
        'n_retweets': 'tweet_retweets',
        's_pos': 'sentiment_pos',
        's_neu': 'sentiment_neut',
        's_neg': 'sentiment_neg',
        's_compound': 'sentiment_compound'
    }
    return tweets_df[features].rename(columns=renames).to_dict(orient='records')


def tsm_get_pred_table_dict_result(prepared_df, prediction, ticker):
    # init dict
    res_dict = {}
    # push values
    res_dict['ticker'] = [ticker for i in range(len(prepared_df))]
    res_dict['prediction'] = [prediction for i in range(len(prepared_df))]
    for col in prepared_df:
        res_dict[col] = []
        for val in prepared_df[col]:
            res_dict[col].append(val)
    return pd_DataFrame.from_dict(res_dict).to_dict(orient='records')

#----------- COMBINED (TweetStockModel.py, ModelTrainer.py) ---------#


def create_sequence(dataset, target=None, num_of_rows=N_PAST):
    '''
    Creates a sequenced array from a dataframe sorted by date
    Returns np array
    '''
    sequences = []
    start_idx = 0
    # if num_of_rows > len(dataset):
    #     return None

    if target == None:
        for stop_idx in range(int(num_of_rows), len(dataset)):
            sequences.append(dataset.iloc[start_idx:stop_idx])
            start_idx += 1
        return np_array(sequences, dtype='object')

    labels = []
    features_dataset = dataset.drop(columns=target)
    labels_dataset = dataset[[target]]
    # Selecting "num_of_rows"
    for stop_idx in range(int(num_of_rows), len(dataset)):
        sequences.append(features_dataset.iloc[start_idx:stop_idx])
        labels.append(labels_dataset.iloc[stop_idx][0])
        start_idx += 1
    return np_array(sequences, dtype='object'), np_array(labels, dtype='object')

    # option 2
    """
    sequences = []

    if target == None:
        for start_idx, stop_idx in zip(range(0, len(dataset)-num_of_rows), range(num_of_rows, len(dataset))):
            sequences.append(dataset.iloc[start_idx:stop_idx])
        return np_array(sequences, dtype='object')

    labels = []
    features_dataset = dataset.drop(columns=target)
    labels_dataset = dataset[[target]]
    for start_idx, stop_idx in zip(range(0, len(dataset)-num_of_rows), range(num_of_rows, len(dataset))):
        sequences.append(features_dataset.iloc[start_idx:stop_idx])
        labels.append(labels_dataset.iloc[stop_idx][0])
    return np_array(sequences, dtype='object'), np_array(labels, dtype='object')
    """


# LOAD FEATURES CSV - used only by ModelTrainer.py
def str_to_array(array_shaped_str):
    """
    Recieves an array shaped str and returns it in a form of array
    it will remove [, ], ', " charachters from the string and transorm it to array
    """
    return remove_str_chars(array_shaped_str,  ['[', ']', "'", '"', ' ']).split(',')


def remove_str_chars(str, chars):
    for char in chars:
        str = str.replace(char, '')
    return str


def replace_str_chars(str, tuples_lst):
    '''
    example of @lst: lst = [ ( ']', '' ), ( ';', '|' ) ]
    '''
    for tuple in tuples_lst:
        str = str.replace(tuple[0], tuple[1])
    return str


def load_csv(path, csv_delimiter='|'):
    '''
    Loads a csv file from a given file,
    params: csv_path, csv_delimiter(default='|')
    returns it in a form of dictionary. 
    '''
    dictobj = {}
    try:
        with open(path, mode='r') as infile:
            reader = csv_reader(infile, delimiter=csv_delimiter)
            return dict((rows[0], int(rows[1])) if rows[1].isdigit() else (rows[0], rows[1]) for rows in reader)
    except Exception as err:
        print(err)
        return None
# END LOAD FEATURES CSV


def get_array_average(arr):
    return sum(arr) / len(arr)


# def mt_scale_data_old(df, target='price_difference'):
#     def is_scalable_feature(feature):
#         return feature != 'Date' and feature != target

#     def is_sentiment_feature(feature):
#         return feature == "Tweet_Sentiment" or feature == "Positivity" or feature == "Neutral" or feature == "Negativity"
#     # Start scaling

#     for col in df.columns:
#         scaler = MinMaxScaler()
