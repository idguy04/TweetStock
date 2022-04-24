
from flask import Flask, jsonify, request, Response
from flask_restful import Api
from flask_cors import CORS
from TweetStockModel import TweetStockModel as tsm
import time
import os
# ----------------------------------------------------------------------------------------------- #
# get the 'tweetstock_model.h5' file path here.
#MODEL_PATH = r'D:\GoogleDrive\Alon\לימודים\TweetStockApp\FlaskServer\Data\Networks\2\AMZN_acc_0.66_npast_3_epoch_2_opt_rmsprop_num_7775.h5'
# '/home/pi/FinalProject/FlaskServer/Data/Networks/1/ticker_AMZN_opt_rmsprop_acc_0.653_TweetStock_model_#18.h5')
SERVER_PORT = 13543  # 5000 # port which the server will run on.
TWITTER_VERSION = 2  # twitter version.
N_PAST = 1  # days on which the model was train to precict based on.
MAX_TWEETS_RESULTS = 100  # max results for first tweets query.
MIN_TWEET_STATS_SUM = 25   # default = 25
MIN_USER_FOLLOWERS = 100  # min user followers num to be included
# ----------------------------------------------------------------------------------------------- #
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'media.ruppin.ac.il'
CORS(app)  # , resources={r"*": {"origins": "*"}})
api = Api(app)
# ----------------------------------------------------------------------------------------------- #


@app.route('/getPrediction', methods=['GET'])
def get_prediction():
    if os.name == 'nt':
        delimiter = '\\'
        prefix = ''
    elif os.name == 'posix':
        delimiter = '/'
        prefix = '/home/pi/FinalProject/FlaskServer/'

    # 'features': 1 --> ['Tweet_Comments', 'Tweet_Retweets','Tweet_Likes', 'Positivity', 'Negativity', 'Neutral']
    # 'features': 2 --> ['Tweet_Sentiment','Tweet_Comments', 'Tweet_Retweets', 'Tweet_Likes']
    models = {
        'AAPL': {
            'path': f'{prefix}SelectedModels{delimiter}AAPL{delimiter}AAPL_acc_0.633_npast_1_epoch_4_opt_rmsprop_num_3848.h5',
            'features': 1
        },
        'AMZN': {
            'path': f'{prefix}SelectedModels{delimiter}AMZN{delimiter}AMZN_acc_0.673_npast_1_epoch_7_opt_rmsprop_num_1396.h5',
            'features': 1
        },
        'GOOG': {
            'path': f'{prefix}SelectedModels{delimiter}GOOG{delimiter}GOOG_acc_0.612_npast_1_epoch_10_opt_adam_num_2283.h5',
            'features': 1
        },
        'GOOGL': {
            'path': f'{prefix}SelectedModels{delimiter}GOOGL{delimiter}GOOGL_acc_1.0_npast_1_epoch_4_opt_adam_num_3147.h5',
            'features': 1
        },
        'MSFT': {
            'path': f'{prefix}SelectedModels{delimiter}MSFT{delimiter}MSFT_acc_0.612_npast_1_epoch_4_opt_adam_num_4359.h5',
            'features': 2
        },
        'TSLA': {
            'path': f'{prefix}SelectedModels{delimiter}TSLA{delimiter}TSLA_acc_0.633_npast_1_epoch_4_opt_adam_num_804.h5',
            'features': 1
        }
    }

    args = request.args.to_dict()
    ticker = args['ticker'].upper()
    #ticker = 'TSLA'
    if ticker not in models:
        return Response('{"msg": "Model Not Found"}', status=204, mimetype='application/json')
        # return '{"msg": "Model Not Found"}', 201

    model = tsm(
        model_path=models[ticker]['path'], model_ticker=ticker, features_version=models[ticker]['features'])
    client_result, sql_Ticker_and_Pred_Table_DF, sql_Ticker_Stats_Table_DF = model.get_prediction()
    return jsonify(client_result)


# ----------------------------------------------------------------------------------------------- #
if __name__ == '__main__':
    # get_npm stprediction()
    app.run(host='0.0.0.0', port=SERVER_PORT, debug=True, use_reloader=False)

# while True:
#     now = datetime.now()
#     if now.hour % 4 == 0 :
#         runscraper()
#     time.sleep(3600)