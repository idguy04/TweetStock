#import pandas as pd
# import numpy as np
import datetime
import os, sys, shutil
from flask import Flask, jsonify, request
from flask_restful import Resource, Api, reqparse
from numpy import NaN
from requests import put, get, post, delete
from flask_cors import CORS
#from tensorflow.keras.models import load_model
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer # sentiment score
from TwitterAPI import TwitterAPI, TwitterOAuth, TwitterRequestError, TwitterConnectionError, TwitterPager
import tweepy # tweeter API
import math

MODEL_PATH  = '' # get the 'tweetstock_model.h5' file path here.
SERVER_PORT = 5000 # port which the server will run on.
TWITTER_VERSION = 2 # twitter version.
N_PAST = 1 # days on which the model was train to precict based on.
MAX_TWEETS_RESULTS = 100 # max results for first tweets query.
MIN_TWEET_STATS_SUM = 100
MIN_USER_FOLLOWERS = 100 # min user followers num to be included

def connect_to_twitter(version = TWITTER_VERSION): # v2 for now
    consumer_key = 'mymakG2knztQ2GYaTNaRGTIOi'
    consumer_secret = 'lGXmXu9K7DQftUjvVempNg1vGjS362zbKo7p12yaa5RrBelIlj'
    access_token = '561299890-kjoCtIBYvSHeIVfhYEbHfNXHAqVklnMze2Wce1JT'
    access_token_secret = 'U1fR9nx24H1Eo3dvlLYO9LhDxwYWWZ5x2JEltgA4xUy6o'
    if version == 2:
        return TwitterAPI (consumer_key, consumer_secret, access_token,
                            access_token_secret, api_version='2')
    elif version == 1: 
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        return tweepy.API(auth)

def WriteToLog(msg):
    with open("/home/pi/Desktop/FinalProject/FlaskServer/Data/Logs.txt", mode='w', encoding='utf-8') as f:
        for tweet in msg:
            f.write(f'{tweet}\n')

def get_n_past_date(num_of_days):
    today = datetime.datetime.now()
    if num_of_days > 0 :
        num_of_days *= -1
    delta = datetime.timedelta(num_of_days)
    date = today + delta
    return date.isoformat('T')+'Z'


# Step 1
def get_tweets(ticker, max_results = 10, n_past = 1, twitter_version=TWITTER_VERSION):
    print("Getting Tweets")
    if '$' in ticker:
        ticker = ticker.replace('$','')
    
    tweets = []
    result_type = 'popular'

    if twitter_version == 1:
        temp_tweets = twitter.search_tweets(q=ticker, count=max_results, result_type=result_type)
        for tweet in temp_tweets:
            #print(f'{tweet._json}')
            t = tweet._json
            user = t['user']
            tweets.append({
                'tweet_id': t['id'],
                'created_at': '', # handle!
                'text':t['text'],
                'n_likes':t['favorite_count'],
                'n_retweets':t['retweet_count'],
                'n_replies': 0,
                'user': {
                    'user_id':user['id'],
                    'screen_name':user['screen_name'],
                    'description':user['description'],
                    'n_followers':user['n_followers']
                }
            })
    elif twitter_version == 2:
        prms = {
            'tweet.fields':'public_metrics,author_id,created_at',   
            'start_time': get_n_past_date(n_past),
            'query':ticker,
            'max_results' : max_results,    
            # 'user.fields':'public_metrics,description,username',
            #'exclude': 'retweets,replies',
            #'result_type' : result_type
        } # TAKE CARE OF EXCLUDING REPLIES
        
        try:
            temp_tweets = twitter.request(resource = 'tweets/search/recent' , params = prms)
        

            for tweet in temp_tweets:
                res = twitter.request(resource = "users/:"+tweet['author_id'], params={'user.fields':'public_metrics,description,username'}).json()
                #print(res)
                u_data = res['data']

                t_metrics = tweet['public_metrics']
                tweets.append({
                    'tweet_id': tweet['id'],
                    'created_at': tweet['created_at'],
                    'text':tweet['text'],
                    'n_likes':t_metrics['like_count'],
                    'n_retweets':t_metrics['retweet_count'],
                    'n_replies': t_metrics['reply_count'],
                    'user': {
                        'user_id':u_data['id'],
                        'screen_name':u_data['username'],
                        'description':u_data['description'],
                        'n_followers':u_data['public_metrics']['followers_count']
                    }
                })
        except Exception as err:
            print("HERE!")
            raise Exception("") from err        

    return tweets

# Step 2
def get_sentiment(tweets):
    print("Getting Sentiment")
    for tweet in tweets:
        tweet['sentiment'] = sentiment_analyzer.polarity_scores(tweet['text'])
        #tweets['subjectivity'] = sentiment_analyzer.subjectivity_scores(tweet['text']) # optional
    return tweets

# Step 3
def filter_tweets(tweets, threshold = MIN_TWEET_STATS_SUM):
    print("Filtering Tweets")
    for tweet in tweets:
        if tweet['n_retweets'] + tweet['n_likes'] + tweet['n_replies'] < threshold or tweet['sentiment']['compound'] == 0:
            tweets.remove(tweet)
    return tweets

# Step 4
def get_users_engagement(tweets, max_tweets_results = 100, twitter_version=TWITTER_VERSION):
    print("Getting user engagement")
    if twitter_version == 1:
        pass
    elif twitter_version == 2:
        prms = {
            'max_results':max_tweets_results,
            'exclude': 'retweets,replies',
            'tweet.fields': 'public_metrics',
        }

        for i,tweet in enumerate(tweets):
            try:
                u_tweets = twitter.request(resource='users/:'+tweet['user']['user_id']+'/tweets', params = prms)
                u_log_n_followers = math.log(tweet['user']['n_followers'],2)
                u_n_tweets, u_n_rts, u_n_replies, u_n_likes = 0, 0, 0, 0
                for u_tweet in u_tweets:
                    u_n_rts += u_tweet['public_metrics']['retweet_count']
                    u_n_replies += u_tweet['public_metrics']['reply_count']
                    u_n_likes += u_tweet['public_metrics']['like_count']
                    u_n_tweets += 1
                print(u_n_tweets, u_n_rts, u_n_replies, u_n_likes, u_log_n_followers)
                if math.log(u_log_n_followers,2) > 0 and u_n_tweets > 0:
                    eng = (u_n_rts + u_n_replies + u_n_likes)/math.log(u_log_n_followers,2)/u_n_tweets
                else: eng = 0
                tweets[i]['user']['engagement'] = eng
            
            except TwitterRequestError as err:  
                if "429" in str(err):
                    err_msg = "429 in err"
                    print(err_msg, err)
                    tweets[i]['user']['engagement'] = err_msg
                    #time.sleep(15*60) # sleep 15 mins
                else:
                    err_msg = "twitter request error"
                    print(err_msg, err)
                    tweets[i]['user']['engagement'] = err_msg
            except Exception as err:
                err_msg = "general exception"
                print(err_msg, err)
                tweets[i]['user']['engagement'] = err_msg

    return tweets

# Step 5
def filter_users(tweets,threshold=MIN_USER_FOLLOWERS):
    print("Filtering users")

    for tweet in tweets:
        user = tweet['user']
        if user['engagement'] == 0 or user['n_followers'] < threshold:
             tweets.remove(tweet)
    return tweets

# Step 6
def prep_data(data):
    print("Prepping model data")
    pass



app = Flask(__name__)
CORS(app,resources={r"*": {"origins": "*"}})
api = Api(app)

#debug
def get_prediction_dummy():
    ticker = "TSLA"
    # Step 1
    tweets = get_tweets('TSLA',max_results=MAX_TWEETS_RESULTS,n_past=N_PAST, twitter_version=TWITTER_VERSION)

    # Step 2
    sent_tweets = get_sentiment(tweets)

    # Step 3
    print("before tweet filtering:", len(sent_tweets))
    filteredT_sent_tweets = filter_tweets(sent_tweets, threshold=0)
    print("after tweet filtering:", len(filteredT_sent_tweets))

    # Step 4
    eng_filteredT_sent_tweets = get_users_engagement(filteredT_sent_tweets)

    # Step 5
    print("before user filtering:", len(eng_filteredT_sent_tweets))
    filteredU_eng_filteredT_sent_tweets = filter_users(eng_filteredT_sent_tweets)
    print("after user filtering:", len(filteredU_eng_filteredT_sent_tweets))
    


@app.route('/getPrediction', methods=['GET'])  # GET
def get_prediction():
    args = request.args.to_dict()
    ticker = args['ticker']

    tweets = get_tweets(ticker="TSLA", n_past=N_PAST)

    #model = load_model(MODEL_PATH)

    return jsonify(args)

if __name__ == '__main__':
    print("1")
    sentiment_analyzer = SentimentIntensityAnalyzer()
    print("2")
    twitter = connect_to_twitter()
    print("3")
    get_prediction_dummy() # debug
    app.run(host='0.0.0.0', port=SERVER_PORT, debug=True)
