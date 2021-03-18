from __future__ import unicode_literals
from builtins import chr


class Country:

    OFFSET = 127462 - ord('A')

    def getFlag(self):
        code = self.code
        if code:
            return chr(ord(code[0]) + Country.OFFSET) + chr(ord(code[1]) + Country.OFFSET)
        return False


    def __init__(self, name, data={}):
        self.name = name
        self.data = data
        self.demonym = 'foreign'
        self.code = None
        if data:
            self.code = data['cca2']
            self.demonym = data['demonym']

    def __str__(self):
        out = """
Name: {}
TLD: {}
        """.format(self.name, self.data['tld'])
        return out


    def getNation(self):
        nationOverrides = {
            'Philippines': 'Filipino',
        }
        if self.name in nationOverrides.keys():
            return nationOverrides[self.name]

        if self.demonym:
            return self.demonym

        return self.name

    def get_set_name(self, family=4):
        return 'fds-{}-{}'.format(self.code.lower(), family)