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


    def getNation(self):
        nationOverrides = {
            'Philippines': 'Filipina',
        }
        if self.name in nationOverrides.keys():
            return nationOverrides[self.name]

        if self.demonym:
            return self.demonym

        return self.name