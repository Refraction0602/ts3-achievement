import telnetlib
import time
import traceback

from src.common.log import logger


class TelnetClient:

    def __init__(self, password):
        self.tn = telnetlib.Telnet()
        self.host = '127.0.0.1.224'
        self.port = 10011
        self.username = 'serveradmin'
        self.password = password
        self.client_info = {}
        self.channel_group_list = {}
        self.channel_list = {}

        self.__init_server_info()

    def __login_host(self):
        try:
            self.tn.open(host=self.host, port=self.port, timeout=10)
        except:
            logger.warning('连接到服务器失败: %s' % traceback.format_exc())

        connect_result = self.tn.read_very_eager().decode('utf8').replace('\n\r', '')
        logger.info('连接结果: %s %s' % (type(connect_result), connect_result))
        if 'TS3Welcome' in connect_result:
            self.tn.write(('login %s %s\n' % (self.username, self.password)).encode())
            time.sleep(0.1)
            login_result = self.tn.read_very_eager().decode('utf8').replace('\n\r', '')
            if 'msg=ok' in login_result:
                logger.info('登录结果: %s %s' % (type(login_result), login_result))
                return True
        return False

    def __execute_command(self, command):
        self.tn.write(command.encode() + b'\n')
        time.sleep(0.1)
        command_result = self.tn.read_very_eager().decode('utf8').replace('\n\r', '')
        logger.info('命令执行结果: %s' % command_result)
        return command_result

    def __get_server_id(self):
        command_result = self.__execute_command('serverlist')
        server_id = command_result.split(' ')[0].split('=')[1]
        return int(server_id)

    @staticmethod
    def __get_value(filed):
        return filed.split('=')[1]

    def __init_server_info(self):
        while 1:
            if self.__login_host():
                server_id = self.__get_server_id()
                self.__execute_command('use %s' % server_id)
                # 初始化客户端信息
                command_result = self.__execute_command('clientlist')
                client_list = command_result.split('|')
                for client in client_list:
                    _client = client.split(' ')
                    client_nick_name = self.__get_value(_client[3])
                    client_clid = self.__get_value(_client[0])
                    client_database_id = self.__get_value(_client[2])
                    self.client_info[client_clid] = (client_nick_name, client_database_id)

                # 初始化server_channel_group信息
                command_result = self.__execute_command('channelgrouplist')
                channel_group_list = command_result.split('|')
                for channel_group in channel_group_list:
                    _channel_group = channel_group.split(' ')
                    cgid = self.__get_value(_channel_group[0])
                    name = self.__get_value(_channel_group[1])
                    self.channel_group_list[name] = cgid

                # 初始化server_channel信息
                command_result = self.__execute_command('channellist')
                channel_list = command_result.split('|')
                for channel in channel_list:
                    _channel = channel.split(' ')
                    cid = self.__get_value(_channel[0])
                    channel_name = self.__get_value(_channel[3])
                    self.channel_list[channel_name] = cid

            self.tn.close()
            if self.client_info and self.channel_group_list and self.channel_list:
                break
            time.sleep(1)

    def get_client_info(self):
        pass

    def main(self):
        logger.info('客户端信息: %s' % self.client_info)
        logger.info('channel组信息: %s' % self.channel_group_list)
        logger.info('channel信息: %s' % self.channel_list)