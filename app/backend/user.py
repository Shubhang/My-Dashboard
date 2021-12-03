################### DEPRECATED #####################
class User():

    def __init__(self, firstName, lastName):
        self.firstName = firstName
        self.lastName = lastName
        self.companies = {}
        self.__dashPreferences = {           # Default preferences
        'stocksInfo': True,
        'stocksGraph': True,
        'complianceSummaries': True,
        'summariesPerSector': 3
        }

        import datetime
        self.__creationDate = datetime.date.today()  #YYYY-MM-DD

    def __str__(self):
        return ' '.join([self.firstName, self.lastName])

    __repr__ = __str__

    @property
    def creationDate(self):
        return self.__creationDate
####################################################
