import pickle
from datetime import datetime

def saveObject(object, path):
    with open(path, "wb") as pickleLoc:
        pickle.dump(object, pickleLoc, protocol=pickle.HIGHEST_PROTOCOL) # Once this goes into a class, get rid of the magic number.

def loadObject(path):
    with open(path, "rb") as pickleLoc:
        return pickle.load(pickleLoc)

def expiryStrToDate(expiryStr):
    ''' input format expected to look like: "20211217" for December 17th, 2021. '''
    return datetime.strptime(expiryStr, "%Y%m%d").date()

def expiryStrToDatetime(expiryStr):
    ''' input format expected to look like: "20211217" for December 17th, 2021. '''
    return datetime.strptime(expiryStr, "%Y%m%d")

def getOCCKey(strike, right, expiration):
    '''
    The idea is that expiration is passed in as a Date object,
    but datetime would be fine too, as long as it is consistent.
    '''
    return f"{strike}-{right}-{expiration}"
