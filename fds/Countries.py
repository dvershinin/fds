import json
import os

from six import add_metaclass
from .Country import Country


class Singleton(type):
    _instances = {}


    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


@add_metaclass(Singleton)
class Countries(object):

    def __init__(self):
        countries_data_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'data',
            'countries.json'
        )

        # indexed by common name, storing actual Country class
        self.countries = {}

        with open(countries_data_file) as jsonFile:
            data = json.load(jsonFile)
            for c in data:
                commonName = c['name']['common']
                country = Country(commonName, c)
                self.countries[commonName] = country


    def getByName(self, name):
        # assume the country exists if we pass some string
        if not name:
            return False

        customNameMap = {
            'Taiwan (China)': 'Taiwan',
            'Hong Kong (China)': 'Hong Kong'
        }
        # custom map countries.json common name to country name displayed in cupidmedia
        if name in customNameMap.keys():
            name = customNameMap[name]

        if name in self.countries:
            return self.countries[name]
        else:
            return Country(name)
