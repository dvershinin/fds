from __future__ import unicode_literals

import json
import os

import six
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
        # index of two-letter codes to common name
        self.names_by_code = {}

        with open(countries_data_file) as jsonFile:
            data = json.load(jsonFile)
            for c in data:
                commonName = c['name']['common']
                country = Country(commonName, c)
                self.countries[commonName] = country
                self.names_by_code[c['cca2'].lower()] = commonName


    def __iter__(self):
        return six.itervalues(self.countries)

    def get_continents(self):
        out = []
        for name in self.countries:
            country = self.countries[name]
            region = country.data['region']
            if region == "Americas":
                region = country.data['subregion']
            if region in ['Caribbean', 'Central America']:
                region = 'North America'
            if region not in out:
                out.append(region)
        return out

    def print_all_continents(self):
        regions = self.get_continents()
        for r in regions:
            print(r)

    def get_by_name(self, name):
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
            return None

    def print_all(self):
        for c in self.countries:
            print(c)

