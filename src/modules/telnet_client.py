import telnetlib
import time
import traceback

from src.common.yaml_reader import conf_get
from src.common.constant import DEFINE_MONGO_SERVER_GROUP, DEFINE_MONGO_CLIENT_INFO
from src.common.mongodb import db_handler_get
from src.common.log import logger


class TelnetClient:
    """
    telnet 127.0.0.1 10011
    login serveradmin 7Kro0UlR
    use 1
    clientlist
    clientdbedit cldbid= client_description=
    """

    def __init__(self, password):
        self.mongo = db_handler_get('default')
        self.tn = telnetlib.Telnet()
        self.host = '127.0.0.1'
        self.port = 10011
        self.username = 'serveradmin'
        self.password = password
        self.server_group_list = []
        self.client_info = []
        self.channel_group_list = {}
        self.channel_list = {}

        # self.__update_server_info()

    def __login_host(self):
        try:
            self.tn.open(host=self.host, port=self.port, timeout=10)
        except:
            logger.warning('connect failed: %s' % traceback.format_exc())

        connect_result = self.tn.read_very_eager().decode('utf8').replace('\n\r', '')
        if 'TS3Welcome' in connect_result:
            # logger.info('login %s %s\n' % (self.username, self.password))
            self.tn.write(('login %s %s\n' % (self.username, self.password)).encode())
            time.sleep(0.1)
            login_result = self.tn.read_very_eager().decode('utf8').replace('\n\r', '')
            if 'msg=ok' in login_result:
                return True
        return False

    def __execute_command(self, command):
        self.tn.write(command.encode() + b'\n')
        time.sleep(0.1)
        command_result = self.tn.read_very_eager().decode('utf8').replace('\n\r', '')
        # logger.info('command result: %s' % command_result)
        return command_result

    def __get_server_id(self):
        command_result = self.__execute_command('serverlist')
        server_id = command_result.split(' ')[0].split('=')[1]
        return int(server_id)

    @staticmethod
    def __get_value(filed):
        result = filed.split('=')
        if len(result) > 1:
            return result[1]
        else:
            return None

    @staticmethod
    def __get_value_v2(filed):
        result = filed.split(':')
        if len(result) > 1:
            return result[1]
        else:
            return None

    def __update_server_info(self):
        for _ in range(0, 3):
            if self.__login_host():
                # # update server_channel_group
                # command_result = self.__execute_command('channelgrouplist')
                # channel_group_list = command_result.split('|')
                # for channel_group in channel_group_list:
                #     _channel_group = channel_group.split(' ')
                #     cgid = self.__get_value(_channel_group[0])
                #     name = self.__get_value(_channel_group[1])
                #     self.channel_group_list[name] = cgid
                #
                # # update server_channel
                # command_result = self.__execute_command('channellist')
                # channel_list = command_result.split('|')
                # for channel in channel_list:
                #     _channel = channel.split(' ')
                #     cid = self.__get_value(_channel[0])
                #     channel_name = self.__get_value(_channel[3])
                #     self.channel_list[channel_name] = cid

                # update server_group
                server_id = self.__get_server_id()
                self.__execute_command('use %s' % server_id)
                command_result = self.__execute_command('servergrouplist')
                server_group_list = command_result.split('|')
                for server_group in server_group_list:
                    group = server_group.split(' ')
                    sgid = self.__get_value(group[0])
                    name = self.__get_value(group[1])
                    sg = {'sgid': int(sgid), 'name': name}
                    self.server_group_list.append(sg)
            self.tn.close()
            if self.__login_host():
                # update client
                server_id = self.__get_server_id()
                self.__execute_command('use %s' % server_id)
                command_result = self.__execute_command('clientlist')
                client_list = command_result.split('|')
                for client in client_list:
                    _client = client.split(' ')
                    client_clid = self.__get_value(_client[0])
                    client_database_id = self.__get_value(_client[2])
                    client_nick_name = self.__get_value(_client[3])
                    command_result = self.__execute_command('clientinfo clid=%s' % client_clid)
                    client_info = [x for x in command_result.split(' ') if 'client_description' in x][0]
                    description = self.__get_value(client_info)
                    account_id_64bit, account_id_32bit = None, None
                    if description:
                        description_list = description.split(';')
                        account_id_64bit = [x for x in description_list if 'steam64' in x][0].split(')')[0]
                        account_id_64bit = self.__get_value_v2(account_id_64bit)
                        account_id_32bit = [x for x in description_list if 'steam32' in x][0].strip('()')
                        account_id_32bit = self.__get_value_v2(account_id_32bit)
                    client = {'clid': int(client_clid),
                              'cldbid': int(client_database_id),
                              'nick_name': client_nick_name,
                              'account_id_64bit': int(account_id_64bit) if account_id_64bit else None,
                              'account_id_32bit': int(account_id_32bit) if account_id_32bit else None}
                    self.client_info.append(client)
            self.tn.close()
            if self.server_group_list:
                for server_group in self.server_group_list:
                    cond = {'sgid': server_group['sgid']}
                    first_time = int(time.time())
                    insert = {'sgid': server_group['sgid'],
                              'name': server_group['name'],
                              'first_time': first_time,
                              'update_time': first_time}
                    update = {'name': server_group['name'], 'update_time': first_time}
                    self.mongo.write(DEFINE_MONGO_SERVER_GROUP, cond, insert, update)
            if self.client_info:
                for client in self.client_info:
                    cond = {'cldbid': client['cldbid']}
                    insert = client
                    first_time = int(time.time())
                    insert_ex = {'total_experience': 0,
                                 'level': 0,
                                 'first_time': first_time,
                                 'update_time': first_time}
                    insert.update(insert_ex)
                    update = {'clid': client['clid'],
                              'nick_name': client['nick_name'],
                              'account_id_32bit': client['account_id_32bit'],
                              'account_id_64bit': client['account_id_64bit'],
                              'update_time': first_time}
                    self.mongo.write(DEFINE_MONGO_CLIENT_INFO, cond, insert, update)
                break

    def set_channel_group(self, ready_to_set):
        """
        help servergroupaddclient
        Usage: servergroupaddclient sgid={groupID} cldbid={clientDBID}
               servergroupaddclient [-continueonerror] sgid={groupID} cldbid={clientDBID}|cldbid={clientDBID}

        Permissions:
          i_group_member_add_power
          i_group_needed_member_add_power

        Description:
          Adds one or more clients to the server group specified with `sgid`. Please note that a
          client cannot be added to default groups or template groups.

        Parameters:
          -continueonerror : continue processing on errors
          sgid : integer : id of server group
          cldbid : integer : id of client in database

        Example:
          servergroupaddclient sgid=16 cldbid=3
          error id=0 msg=ok
        :param ready_to_set:
        :return:
        """
        # logger.info("ready_to_set: %s" % ready_to_set)
        if self.__login_host():
            server_id = self.__get_server_id()
            self.__execute_command('use %s' % server_id)
            for data in ready_to_set:
                account_id_32bit = data['account_id_32bit']
                account_id_64bit = data['account_id_64bit']
                cldbid = self.mongo.read(DEFINE_MONGO_CLIENT_INFO, {'account_id_64bit': account_id_64bit})[0]['cldbid']
                if data['level'] != -1:
                    name = 'lv%s' % data['level']
                    sgid = self.mongo.read(DEFINE_MONGO_SERVER_GROUP, {'name': name})[0]['sgid']
                    if data['level'] > 1:
                        old_name = 'lv%s' % (data['level'] - 1)
                        old_sgid = self.mongo.read(DEFINE_MONGO_SERVER_GROUP, {'name': old_name})[0]['sgid']
                        command = 'servergroupdelclient sgid=%s cldbid=%s' % (old_sgid, cldbid)
                        logger.info("%s" % command)
                        self.__execute_command(command)
                    command = 'servergroupaddclient sgid=%s cldbid=%s' % (sgid, cldbid)
                    logger.info("%s" % command)
                    self.__execute_command(command)
                now_experience, to_the_next_level = data['now_experience'], data['to_the_next_level']
                new_description = '(steam32:%s;steam64:%s)经验：%s/%s' % (account_id_32bit, account_id_64bit, now_experience, to_the_next_level)
                logger.info("%s %s" % (cldbid, new_description))
                self.set_client_description(cldbid, new_description)
        self.tn.close()



    def set_client_description(self, cldbid, description):
        """
        help clientdbedit
        Usage: clientdbedit cldbid={clientDBID} [client_properties...]

        Permissions:
          b_client_modify_dbproperties
          b_client_modify_description
          b_client_set_talk_power

        Description:
          Changes a clients settings using given properties.
          For detailed information, see Client Properties.

        Parameters:
          cldbid : integer : id of client in database
          client_description : description of client

        Example:
          clientdbedit cldbid=56 client_description=Best\sguy\sever!
          error id=0 msg=ok


        error id=0 msg=ok
        :return:
        """
        # clientdbedit cldbid=17 client_description=(steam32:148400274;steam64:76561198108666002)
        command = 'clientdbedit cldbid=%s client_description=%s' % (cldbid, description)
        self.__execute_command(command)

    def hours_to_update(self):
        self.__update_server_info()

    def main(self):
        logger.info('server_group_list: %s' % self.server_group_list)


def telnet_client_hours_to_update():
    query_password = conf_get('ts3_server')['query_password']
    tc = TelnetClient(password=query_password)
    tc.hours_to_update()