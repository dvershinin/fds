from __future__ import unicode_literals

import configparser
import os

from appdirs import user_config_dir


def is_root():
    return os.geteuid() == 0


def get_config_path():
    if is_root():
        return '/etc/fds.conf'
    return user_config_dir('fds')


class Config(configparser.ConfigParser):
    __instance = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if Config.__instance is None:
            Config()
        return Config.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if Config.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            super(Config, self).__init__(
                converters={'list': lambda x: [i.strip() for i in x.split(',')]}
            )
            Config.__instance = self
            self.read(get_config_path())
