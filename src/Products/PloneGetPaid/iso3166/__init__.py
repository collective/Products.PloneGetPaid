from os.path import join

class CountriesStatesParser:

    def __init__(self,path):
        self._path = path
        self._countries = {}
        self._states = {}

    def parse(self):
        countriesFile = file(join(self._path,'countries.txt'))
        for line in countriesFile.readlines():
            if ':' not in line:
                continue
            self._parseCountry(line)

    def _parseCountry(self,line):
        code,name = line.split(':')
        code = code.strip()
        self._countries[code] = name.strip().decode('ISO-8859-1')
        self._states[code] = self._parseStatesOf(code)

    def _parseStatesOf(self,countryCode):
        statesFile = file(join(self._path,'iso.%s.txt' % countryCode))
        statesOf = []
        codes = [] # for avoiding duplicated codes (which exist in iso3166!!)
        for line in statesFile.readlines():
            if ':' not in line:
                continue
            code,name = line.split(':')
            code = code.strip()
            if code not in codes:
                codes.append(code)
                statesOf.append((name.strip().decode('ISO-8859-1'),code))
        statesOf.sort()
        return map(lambda (x,y):(y,x),statesOf)

    def getCountries(self):
        return self._countries.items()

    def getCountriesNameOrdered(self):
        invertedItems = map(lambda (x,y):(y,x),self._countries.items())
        invertedItems.sort()
        return map(lambda (x,y):(y,x),invertedItems)

    def getStatesOf(self,code):
        return self._states.get(code,[])

    def getStatesOfAllCountries(self):
        result = []
        for stateList in self._states.values():
            result.extend(stateList)
        return result

if __name__ == '__main__':
    c = CountriesStatesParser('iso3166')
    c.parse()
    w = c.getStatesOfAllCountries()
