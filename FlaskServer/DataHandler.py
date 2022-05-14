#import pandas as pd
from pandas import DataFrame as pd_DataFrame, merge as pd_merge, to_datetime as pd_to_datetime
from numpy import array as np_array, split as np_split
from tensorflow import convert_to_tensor as ctt, float32 as tf_float32
from math import log, inf
from sklearn.preprocessing import MinMaxScaler, StandardScaler
import Helper
'''
This class will be used to coordinate the work between 
the ModelTrainer.py and TweetStockModel.py .
It will contain every method which is used to handle data.
'''
TWITTER_VERSION = 2             # twitter version.
# days on which the model was train to precict based on.
N_PAST = 1
MAX_TWEETS_RESULTS = 100        # max results for first tweets query.
MAX_USER_TWEETS_RESULT = 100    # max results for use engagement tweets
MIN_TWEET_STATS_SUM = 25        # min tweet filtering sum of stats
MIN_USER_FOLLOWERS = 100        # min user followers num to be included

SCALING = 'min_max'


#------ ModelTrainer.py -------#

def mt_scale_data(df, target='price_difference', scaling=SCALING):
    """
    Handles data scaling and aggregation (e.g. average) per day of the data
    """
    def is_scalable_feature(feature):
        return feature != 'Date' and feature != target

    def is_sentiment_feature(feature):
        return feature == "Tweet_Sentiment" or feature == "Positivity" or feature == "Neutral" or feature == "Negativity"
    columns = df.columns
    df = df.groupby(by=['Date'])
    dates_dict = {}
    for col in columns:
        dates_dict[col] = []

    for date in df:
        dates_dict['Date'].append(date[0])
        dates_dict[target].append(date[1][target].iloc[0])
        for col in columns:
            if is_scalable_feature(col):
                if scaling == 'min_max':
                    scaler = MinMaxScaler()
                elif scaling == 'standard':
                    scaler = StandardScaler()

                to_append = date[1][col] * date[1]["Tweet_Sentiment"] if not is_sentiment_feature(
                    col) else date[1][col]
                #print("@TweetStockModel/scale_df()/to_append=", to_append)
                dates_dict[col].append(scaler.fit_transform(
                    np_array(to_append).reshape(-1, 1)).mean())

    return pd_DataFrame.from_dict(dates_dict)


def mt_split_data(dnn_df, version=2):
    '''

    '''
    if version == 1:
        testing_size = 50
        validation_size = 50
        training_size = len(dnn_df) - testing_size - validation_size

        train_data = dnn_df[:training_size]
        validation_data = dnn_df[training_size:training_size+validation_size]
        test_data = dnn_df[training_size+validation_size:]

    elif version == 2:
        validation_size = 50
        testing_size = 50
        train_data, validation_data, test_data = np_split(dnn_df.sample(frac=1, random_state=42), [
            int(len(dnn_df)-testing_size-validation_size), int(len(dnn_df)-testing_size)])
    return train_data, validation_data, test_data


def mt_create_sequence(dataset, target, num_of_rows=N_PAST):
    '''Returns np array'''
    sequences, labels = [], []

    start_idx = 0
    if target:
        features_df = dataset.drop(columns=target)
        labels_df = dataset[[target]]
        # Selecting "num_of_rows"
        for stop_idx in range(num_of_rows, len(dataset)):
            sequences.append(features_df.iloc[start_idx:stop_idx])
            labels.append(labels_df.iloc[stop_idx][0])
            start_idx += 1
    else:
        # Selecting "num_of_rows"
        for stop_idx in range(num_of_rows, len(dataset)):
            sequences.append(dataset.iloc[start_idx:stop_idx])
            labels.append(dataset.iloc[stop_idx])
            start_idx += 1
    return np_array(sequences, dtype='object'), np_array(labels, dtype='object')


def mt_get_price_diff(stocks_df):
    ''' gets the close price diff (today-yesterday) 1 = up, 0 = down '''
    temp_stocks = stocks_df.reset_index(drop=True)
    temp_stocks['price_difference'] = [
        0.0 for i in range(len(temp_stocks))]

    for i in range(1, len(temp_stocks)):
        # Next Close - Today Close
        # today = float(temp_stocks['Close'][i])
        # yesterday = float(temp_stocks['Close'][i-1])
        # # try getAvg(high,low)
        # price_diff = today-yesterday

        price_diff = float(temp_stocks['Close'][i]) - \
            float(temp_stocks['Open'][i])
        # temp_stocks['price_difference'][i] = price_diff
        temp_stocks['price_difference'][i] = 1 if price_diff >= 0 else 0
        # if (price_diff>=0): temp_stocks['price_difference'][i] = 1
        # else: temp_stocks['price_difference'][i] = 0

    temp_stocks.drop([0], inplace=True)
    temp_stocks.reset_index(drop=True, inplace=True)
    return temp_stocks


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


def mt_get_eng_score(users_df, include_followers=True, include_replies=False):
    ''' gets users df and returns the df with the engagement score calculated.
        df should have the following columns:  '''
    df = users_df
    for i in range(len(df)):
        rts = df['eng_total_retweets'][i]
        likes = df['eng_total_likes'][i]
        replies = df['eng_total_replies'][i]
        total_tweets = df['eng_tweets_length'][i]
        followers = df['followers_count'][i]

        new_replies = replies if include_replies else 0
        new_followers = log(
            followers, 2) if include_followers else 1
        df['eng_score'][i] = (
            (rts+likes+new_replies)/total_tweets)/new_followers
        # if include_followers:
        #   df['eng_score'][i] = ((rts+likes+replies)/total_tweets)/math.log(followers,2) if include_replies else ((rts+likes)/total_tweets)/followers
        # else:
        #   df['eng_score'][i] = ((rts+likes+replies)/total_tweets) if include_replies else ((rts+likes)/total_tweets)
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


def sort_df_by_dates(df, date_col_name='Date', format='%d/%m/%Y'):
    df[date_col_name] = pd_to_datetime(df[date_col_name], format=format)
    return df.sort_values(by=date_col_name).reset_index(drop=True)


#------ TweetStockModel.py -------#

def tsm_create_sequence(dataset):
    return np_array(dataset)


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


def tsm_filter_tweets(tweets, threshold=MIN_TWEET_STATS_SUM):
    #print(f"Filtering Tweets of {self.ticker} for {self.ip}")
    tweets_to_remove = []
    #print("len before", len(tweets))
    for tweet in tweets:
        if tweet['s_compound'] == 0.0 or tweet['s_neu'] == 1.0 or tweet['n_retweets'] + tweet['n_likes'] + tweet['n_replies'] < threshold:
            tweets_to_remove.append(tweet)

    for tweet in tweets_to_remove:
        tweets.remove(tweet)

    #print("len after", len(tweets))
    # for tweet in tweets:
    #     print(tweet['s_neu'])
    return tweets


def tsm_get_single_user_eng_score(user_tweets, user_followers):
    u_tweets = user_tweets
    u_log_n_followers = log(user_followers, 2)
    u_n_tweets, u_n_rts, u_n_replies, u_n_likes = 0, 0, 0, 0
    for u_tweet in u_tweets:
        u_n_rts += u_tweet['public_metrics']['retweet_count']
        u_n_replies += u_tweet['public_metrics']['reply_count']
        u_n_likes += u_tweet['public_metrics']['like_count']
        u_n_tweets += 1
    #print(u_n_tweets, u_n_rts, u_n_replies, u_n_likes, u_log_n_followers)
    eng = 0
    if log(u_log_n_followers, 2) > 0 and u_n_tweets > 0:
        eng = (u_n_rts + u_n_replies + u_n_likes) / \
            log(u_log_n_followers, 2)/u_n_tweets
    return eng


def tsm_filter_users(tweets, threshold=MIN_USER_FOLLOWERS):
    #print(f"Filtering users of {self.ticker} for {self.ip}")
    tweets_to_remove = []
    for tweet in tweets:
        if tweet['u_n_followers'] < threshold or tweet['u_engagement'] == 0:
            tweets_to_remove.append(tweet)

    for tweet in tweets_to_remove:
        tweets.remove(tweet)

    return tweets


def tsm_prep_data(df, feature_set):
    # 1 Select features
    df = tsm_get_scale_and_mean(df, feature_set)
    df = df[feature_set]

    # 2 Get df mean
    #print('before mean', df, len(df), df.shape)
    #df = self.get_scale_and_mean(df)
    #print('after mean', df, len(df), df.shape)

    # 3 Create sequence from df
    test_seq = tsm_create_sequence(df)
    #print('\n\n', test_seq, test_seq.shape)

    # 4 Scale data
    test_seq = test_seq.reshape(
        (len(test_seq), test_seq.shape[0] * test_seq.shape[1]))
    #scaled_test_seq = scale_seq(test_seq)

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
