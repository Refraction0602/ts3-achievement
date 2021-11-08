import os
import traceback

import yaml

from src.common.constant import CONFIG_PATH
from src.common.log import logger

__conf_path = CONFIG_PATH
__file_name = __conf_path + 'config.yaml'

# import warnings
#
# warnings.simplefilter('ignore', ruamel.yaml.error.UnsafeLoaderWarning)


def __get_config_file():
    """
    @return:
    """
    if not os.path.isdir(__conf_path):
        os.mkdir(__conf_path)
    config_file = open(__file_name, 'r', encoding='utf8')
    return config_file


def __set_config_file():
    """
    @return:
    """
    if not os.path.isdir(__conf_path):
        os.mkdir(__conf_path)
    config_file = open(__file_name, 'w', encoding='utf8')
    return config_file


def conf_get(target):
    """
    @param target:
    @return:
    """
    try:
        config_file = __get_config_file()
        file_data = config_file.read()
        config_file.close()
        data = yaml.load(file_data, Loader=yaml.Loader)['global']
        return data[target]
    except:
        logger.warning("conf_get %s fail!\n%s" % (target, traceback.format_exc()))
        return None