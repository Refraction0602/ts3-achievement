# api
API_KEY = 'your_steam_api_key'
API_MATCH_HISTORY = 'https://api.steampowered.com/IDOTA2Match_570/GetMatchHistory/V001/'
API_MATCH_DETAILS = 'http://api.steampowered.com/IDOTA2Match_570/GetMatchDetails/v1'

# mongodb tables
DEFINE_MONGO_TIME_FIELDS = {'update_time': 1, 'first_time': 1, 'first_monitor_time': 1,
                            'this_monitor_time': 1, 'latest_report_time': 1, 'time': 1,
                            'generate_time': 1, 'latest_monitor_time': 1, 'start_time': 1}
DEFINE_MONGO_SERVER_GROUP = 'ts3_server_group'
DEFINE_MONGO_CLIENT_INFO = 'ts3_client_info'
DEFINE_MONGO_MATCH_DOTA2_HISTORY = 'ts3_match_dota2_history'
DEFINE_MONGO_STATIC_LEVEL = 'ts3_static_level'

# etc
CONFIG_PATH = '../../etc/'
