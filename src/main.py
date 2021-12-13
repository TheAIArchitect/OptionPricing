from ib_insync import IB, util, Index, Stock

from src.OptionChain import OptionChain
from src.VolatilityViewer import VolatilityViewer


if __name__ == "__main__":
    '''
    This uses ib_insync's synchronous mode.
    Note that in order to run this, you need to have IB's Trader Workstation or IB Gateway running.
    
    If reqNewOptionChains is True, option chains are updated and saved via Python's pickle module.
    Otherwise, the option chains for the required contract is loaded.
    
    If reqNewData is True, as of now, 1 day of hourly option midpoint price bars are pulled from IB,
    along with one day of the underlying's hourly bars.
    
    Data is saved in pickled files instead of SQLite for initial setup purposes;
    ideally, a database would be used.
    
    Option implied volatilities are then calculated for the under
    
    
    Because this isn't production code, there is not enough error checking here, and printing should be done with a logger instead.
    '''
    # Flags
    reqNewOptionChains = False
    reqNewData = False

    util.startLoop()

    ib = IB()
    ib.connect('127.0.0.1', 7519, clientId=1)
    #spx = Index('SPX', 'CBOE')
    aapl = Stock('AAPL', 'ISLAND')
    contracts = [aapl,]
    r = .0028  # 1 year t-bill rate as of 2021-12-10
    numContracts = len(contracts)

    oc = OptionChain(ib=ib, underlyingContract=contracts[0])
    if reqNewOptionChains:
        oc.reqOptionChains(saveChains=True)
    else:
        oc.loadOptionChain()

    print(oc.chain)

    oc.createOptionContracts(reqNewData=reqNewData)
    oc.getDaysToExpiry()
    ivMatrix = oc.calculateIVs('C', r=r)

    #print(oc.daysToExpiryList)


    volViewer = VolatilityViewer(daysToExpiry=oc.daysToExpiryList, strikes=oc.strikes, impliedVols=ivMatrix)




