import time
import traceback
from json import loads

from fake_useragent import UserAgent
from requests import get

from src.common.yaml_reader import conf_get
from src.common.constant import API_MATCH_HISTORY, API_MATCH_DETAILS, DEFINE_MONGO_MATCH_DOTA2_HISTORY, \
    DEFINE_MONGO_CLIENT_INFO
from src.common.log import logger
from src.common.mongodb import db_handler_get


API_KEY = conf_get('steam')['api_key']


class SteamInterface:

    def __init__(self):
        self.mongo = db_handler_get('default')
        # self.ua = UserAgent(use_cache_server=False)
        # self.headers = {"user-agent": self.ua.random}

    def get_match(self, account_id_64bit):
        """
        Returns:
        """
        _url = API_MATCH_HISTORY + '?key=%s' % API_KEY + '&account_id=%s' % account_id_64bit + '&matches_requested=3'
        match_result = []
        try:
            _matches = get(_url)
            matches_dict = loads(_matches.text)
            matches = matches_dict['result']['matches']
            if len(matches) > 0:
                for match in matches:
                    match_result.append(match['match_id'])
                return match_result
            else:
                logger.warning('get null match')
                return None
        except:
            logger.error(traceback.format_exc())
            return None

    def get_match_details(self, match_id):
        """
        Args:
            match_id:
        Returns:
        """
        try:
            _url = API_MATCH_DETAILS + '?key=%s' % API_KEY + '&match_id=%s' % match_id
            _details = get(_url)
            details_dict = loads(_details.text)
            return details_dict['result']
        except:
            logger.error(traceback.format_exc())
            return None

    def update_to_mongodb(self, results, account_id_32bit, account_id_64bit):
        """
        Args:
            results:
        Returns:
        """
        players = results['players']
        for player in players:
            if 'account_id' not in player:
                continue
            if player['account_id'] == account_id_32bit:
                if 'hero_damage' not in player:
                    continue
                record_info = {'match_id': results['match_id'],
                               'account_id_32bit': account_id_32bit,
                               'account_id_64bit': account_id_64bit,
                               'hero': player['hero_id'],
                               'level': player['level'],
                               'kills': player['kills'],
                               'deaths': player['deaths'],
                               'assists': player['assists'],
                               'hero_damage': player['hero_damage'],
                               'start_time': results['start_time'],
                               # 'first_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(results['start_time']))
                               }
                self.record_to_mongo(record_info)
                break

    def record_to_mongo(self, record_info):
        cond = {'match_id': record_info['match_id'], 'account_id_32bit': record_info['account_id_32bit'], 'account_id_64bit': record_info['account_id_64bit']}
        insert = record_info
        insert['first_time'] = int(time.time())
        insert['has_scored'] = 0
        update = {}
        self.mongo.write(DEFINE_MONGO_MATCH_DOTA2_HISTORY, cond, insert, update)

    def hours_to_update(self):
        client_list = self.mongo.read(DEFINE_MONGO_CLIENT_INFO, {'cldbid': {'$ne': 1}})
        for client in client_list:
            logger.info("client: %s" % client)
            account_id_32bit = client['account_id_32bit']
            account_id_64bit = client['account_id_64bit']
            match_list = self.get_match(account_id_64bit)
            if match_list:
                for match_id in match_list:
                    match_details = self.get_match_details(match_id)
                    self.update_to_mongodb(match_details, account_id_32bit, account_id_64bit)


def steam_interface_hours_to_update():
    si = SteamInterface()
    si.hours_to_update()