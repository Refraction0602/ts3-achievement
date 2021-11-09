import csv

from src.common.yaml_reader import conf_get
from src.modules.telnet_client import TelnetClient
from src.common.constant import DEFINE_MONGO_STATIC_LEVEL, CONFIG_PATH, DEFINE_MONGO_CLIENT_INFO, \
    DEFINE_MONGO_MATCH_DOTA2_HISTORY
from src.common.log import logger
from src.common.mongodb import db_handler_get


class ScoreAndLevel:
    def __init__(self):
        self.mongo = db_handler_get('default')
        self.__init_static_level()

    def __init_static_level(self):
        table_content = self.mongo.read(DEFINE_MONGO_STATIC_LEVEL, {})
        if not table_content:
            logger.info('init_static_level is called')
            static_csv = CONFIG_PATH + 'static_level.csv'
            static_level_data = []
            with open(static_csv, 'r') as f:
                reader = csv.reader(f)
                for raw in reader:
                    if raw[0] == 'level':
                        continue
                    line = {'level': int(raw[0]), 'to_the_next_level': int(raw[1]), 'experience_difference': int(raw[2]), 'total_experience': int(raw[3])}
                    static_level_data.append(line)
            if static_level_data:
                self.mongo.write_many(DEFINE_MONGO_STATIC_LEVEL, static_level_data)

    def __level_up(self, total_experience):
        static_level_list = self.mongo.read(DEFINE_MONGO_STATIC_LEVEL, {'total_experience': {'$lt': total_experience}})
        if static_level_list:
            static_level = static_level_list[-1]
            new_level = static_level['level']
            to_the_next_level = static_level['to_the_next_level']
            now_experience = total_experience - static_level['total_experience']
            return new_level, now_experience, to_the_next_level

    def __experience(self):
        """
        experience = base_score(100) + kill_score(kills * 2) + assists_score(assists * 2) + damage_score(int(damage / 500))
        :return:
        """
        client_list = self.mongo.read(DEFINE_MONGO_CLIENT_INFO, {'cldbid': {'$ne': 1}, 'account_id_64bit': {'$ne': None}})
        if client_list:
            ready_to_set = []
            for client in client_list:
                account_id_32bit = client['account_id_32bit']
                account_id_64bit = client['account_id_64bit']
                total_experience = client['total_experience']
                level = client['level']
                cond = {'account_id_64bit': account_id_64bit, 'has_scored': 0}
                not_scored_match_list = self.mongo.read(DEFINE_MONGO_MATCH_DOTA2_HISTORY, cond)
                if not_scored_match_list:
                    match_experience = 0
                    for match in not_scored_match_list:
                        kills = match['kills']
                        assists = match['assists']
                        damage = match['hero_damage']
                        match_experience += (100 + kills * 2 + assists * 2 + int(damage / 500))
                    self.mongo.update_many(DEFINE_MONGO_MATCH_DOTA2_HISTORY, cond, {'has_scored': 1})
                    total_experience += match_experience

                    new_level, now_experience, to_the_next_level = self.__level_up(total_experience)
                    update = {'total_experience': total_experience}
                    if match_experience != 0:
                        update['level'] = new_level
                        single = {'account_id_32bit': account_id_32bit,
                                  'account_id_64bit': account_id_64bit,
                                  'level': new_level,
                                  'now_experience': now_experience,
                                  'to_the_next_level': to_the_next_level}
                        if new_level == level:
                            single['level'] = -1
                        ready_to_set.append(single)
                    self.mongo.write(DEFINE_MONGO_CLIENT_INFO, {'account_id_64bit': account_id_64bit}, {}, update)
            if ready_to_set:
                query_password = conf_get('ts3_server')['query_password']
                tc = TelnetClient(password=query_password)
                tc.set_channel_group(ready_to_set)

    def hours_to_update(self):
        self.__experience()


def score_and_level_hours_to_update():
    sal = ScoreAndLevel()
    sal.hours_to_update()