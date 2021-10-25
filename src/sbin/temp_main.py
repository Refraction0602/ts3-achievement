from src.modules.telnet_client import TelnetClient

if __name__ == '__main__':
    # 'p0IsEuDY'为ts3 ServerQuery密码
    tc = TelnetClient(password='p0IsEuDY')
    tc.main()