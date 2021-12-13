from collections import deque
from datetime import time, datetime, timedelta
from typing import Union

import dateutil
import pandas_market_calendars as pmc
from dateutil.parser import parse
from dateutil.tz import tz
from ib_insync import Contract
import pandas as pd

class GlobalConfig:
    # From a different project; easier to eventually combine this with the original file if this is just replicated here rather than changing the references below.
    TZ_TIMEZONE = tz.gettz("America/New York")

class MarketCalendar:

    '''
    NOTE: The CME Equities calendar is *not* a subclass of the CMEExchange calendar, but a subclass of the NYSEExchange clandar.
        - Because of this, the CME special_closes do not apply to the CME Equities calendar, and for example, this calendar will return that the exchange is closed on Labor day, despite the fact that it closes at 1 pm Eastern.
        - To fix this, early closes and holidays need to be cross-checked between CMEExchange, NYSEExchange, and CME Equities.
            - Then, subclass the most appropriate calendar (CMEExchange or NYSE), and make any required modifications.
    '''

    def __init__(me):
        '''
        :calendarNameOrAlias can be 'GLOBEX' or 'CME_Equity',  for the CME Equities exchange.
         Check each pandas_market_calendars.exchange_calendar_xxx.py file for calendar names and aliases.
         :
         '''
        me.initExchangeOpenCloseTimeDict()
        me.calendarInitialized = False

    def initExchangeOpenCloseTimeDict(me):
        eoctd = {}
        me.openKey = "open"
        me.closeKey = "close"
        zeroHundred_AMNY = time(00, 00, tzinfo=tz.gettz("America/New York"))
        fourHundred_AMNY = time(4, 00, tzinfo=tz.gettz("America/New York"))  # 04:00 AMerica New York
        nineHundredThirty_AMNY = time(9, 30, tzinfo=tz.gettz("America/New York"))
        sixteenHundred_AMNY = time(16, 00, tzinfo=tz.gettz("America/New York"))
        twentyHundred_AMNY = time(20, 00, tzinfo=tz.gettz("America/New York"))
        seventeenHundred_AMNY = time(17, 00, tzinfo=tz.gettz("America/New York"))
        eighteenHundred_AMNY = time(18, 00, tzinfo=tz.gettz("America/New York"))
        eoctd["NYSE"] = {}
        eoctd["NYSE"]["STK"] = {me.openKey: fourHundred_AMNY, me.closeKey: twentyHundred_AMNY}
        eoctd["NASDAQ"] = {}
        eoctd["NASDAQ"]["STK"] = {me.openKey: fourHundred_AMNY, me.closeKey: twentyHundred_AMNY}  # Note: Might need to change this to ISLAND
        eoctd["AMEX"] = {}
        eoctd["AMEX"]["STK"] = {me.openKey: fourHundred_AMNY, me.closeKey: twentyHundred_AMNY}
        # open and close times for GLOBEX are set to [00:00, 00:00) because the specifics are set in the CME calendar file.
        eoctd["GLOBEX"] = {}
        eoctd["GLOBEX"]["FUT"] = {me.openKey: eighteenHundred_AMNY, me.closeKey: seventeenHundred_AMNY}
        eoctd["CBOE"] = {}
        eoctd["CBOE"]["OPT"] = {me.openKey: nineHundredThirty_AMNY, me.closeKey: sixteenHundred_AMNY}
        # Here, ARCA, CBOE, etc.
        me.exchangeOpenCloseTimeDict = eoctd


    def createCalendarByName(me, calendarNameOrAlias: str):
        ''' This creates a calendar with default open/close times '''
        me.exchangeCalendar = pmc.get_calendar(calendarNameOrAlias)
        me.calendarInitialized = True

    def createCalendarByContract(me, contract: Contract, useDefaultOpenClose: bool = True):
        me.dailyExchangeOpen = None
        me.dailyExchangeClose = None
        if contract.secType == "STK":
            me.exchange = contract.primaryExchange
        elif contract.secType == "FUT":
            me.exchange = contract.exchange  # This is required to create the pandas_market_calendars Calendar.
        elif contract.secType == "OPT":
            me.exchange = contract.exchange
        if not useDefaultOpenClose:
            exchangeOpenCloseTimeDict = me.exchangeOpenCloseTimeDict.get(me.exchange, None).get(contract.secType, None)
            me.dailyExchangeOpen = exchangeOpenCloseTimeDict.get(me.openKey, None)
            me.dailyExchangeClose = exchangeOpenCloseTimeDict.get(me.closeKey, None)
            if exchangeOpenCloseTimeDict is None:
                print(f"Could not find exchange open/close dict for exchange named '{me.exchange}' and security type: '{contract.secType}.")
                return
        me.exchangeCalendar = pmc.get_calendar(me.exchange, open_time=me.dailyExchangeOpen, close_time=me.dailyExchangeClose)
        me.calendarInitialized = True


    def createSchedule(me, scheduleStartDatetimeTz: datetime, scheduleEndDatetimeTz: datetime):
        ''' these start and end datetimes should generally run past the desired data start and end datetimes in both directions. '''
        me.exchangeSchedule = me.exchangeCalendar.schedule(start_date=scheduleStartDatetimeTz, end_date=scheduleEndDatetimeTz)
        print(f"Schedule for date range: {scheduleStartDatetimeTz} - {scheduleEndDatetimeTz}\n{me.exchangeSchedule}")

    def getMostRecentPreviousDateOpenFrom(me, referenceDatetimeTz: datetime):
        oneDay = timedelta(days=1)
        prevDay = referenceDatetimeTz.date() - oneDay
        while not pd.Timestamp(prevDay) in me.exchangeSchedule.index:
            prevDay = prevDay - oneDay
        prevDayPdTs = pd.Timestamp(prevDay)
        openDatetimeTz = me.exchangeSchedule.at[prevDayPdTs, "market_open"]
        closeDatetimeTz = me.exchangeSchedule.at[prevDayPdTs, "market_close"]
        return prevDay, openDatetimeTz, closeDatetimeTz

    def getNextOpenAfter(me, referenceDatetimeTz: datetime):
        # This function assumes that the market is closed at referenceDatetimeTz.
        referenceDatetimeUTC = referenceDatetimeTz.astimezone(tz=tz.tzutc())
        currentDay = pd.Timestamp(referenceDatetimeUTC.date())
        if currentDay in me.exchangeSchedule.index:
            currentOpenDatetimeTz = me.exchangeSchedule.at[currentDay, "market_open"]
            currentCloseDatetimeTz = me.exchangeSchedule.at[currentDay, "market_close"]
            # First, check to see if the reference time is during a break
            if 'break_start' in me.exchangeSchedule.columns:
                breakStartDatetimeTz = me.exchangeSchedule.at[currentDay, "break_start"]
                breakEndDatetimeTz = me.exchangeSchedule.at[currentDay, "break_end"]
                if referenceDatetimeTz >= breakStartDatetimeTz and referenceDatetimeTz < breakEndDatetimeTz:
                    nextOpenDate = currentDay #.astimezone(GlobalConfig.TZ_TIMEZONE)
                    nextOpenDatetimeTz = breakEndDatetimeTz.astimezone(GlobalConfig.TZ_TIMEZONE)
                    nextCloseDatetimeTz = currentCloseDatetimeTz.astimezone(GlobalConfig.TZ_TIMEZONE)
                    return nextOpenDate, nextOpenDatetimeTz, nextCloseDatetimeTz
            # If not, check to see if it opens later in the same day
            if currentOpenDatetimeTz > referenceDatetimeTz and referenceDatetimeTz < currentCloseDatetimeTz:
                return currentDay, currentOpenDatetimeTz, currentCloseDatetimeTz
        # f we reach this point, then we get the date, open, and close times for the next day the market is open.
        oneDay = timedelta(days=1)
        nextDay = currentDay  + oneDay
        while not pd.Timestamp(nextDay) in me.exchangeSchedule.index: # Not sure if this conversion to Timestamp is necessary here.
            nextDay = nextDay + oneDay
        nextOpenDate = pd.Timestamp(nextDay)
        # Note: perhaps this should return the close as the start of the trading break? Or return it as its own piece of information?
        nextOpenDatetimeTz = me.exchangeSchedule.at[nextOpenDate, "market_open"].astimezone(GlobalConfig.TZ_TIMEZONE)
        nextCloseDatetimeTz = me.exchangeSchedule.at[nextOpenDate, "market_close"].astimezone(GlobalConfig.TZ_TIMEZONE)
        return nextOpenDate, nextOpenDatetimeTz, nextCloseDatetimeTz


    def isMarketOpen(me, referenceDatetimeTz: datetime):
        isOpen = me.exchangeCalendar.open_at_time(me.exchangeSchedule, referenceDatetimeTz)
        return isOpen


    def adjustDataStart(me, proposedDataStart: datetime):
        '''
        The exchange schedule must have already been created. If the market is closed on proposedDataStart,
        the next 'market_open' datetimeTz (moving forward in time) will be returned.
        '''
        # Check to see if the market is open at proposedDataStart
        openAtProposedDataStart = me.exchangeCalendar.open_at_time(me.exchangeSchedule, proposedDataStart)
        if openAtProposedDataStart:
            return proposedDataStart
        else:
            # Find the next day the market is open, and return the datetime that it opens.
            theDate, openDatetimeTz, closeDatetimeTz = me.getNextOpenAfter(proposedDataStart)
            return openDatetimeTz


    def getOpenCloseTupleDeque(me, dataStartTz: datetime, dataEndTz: Union[datetime,None], setLastCloseToNone: bool, barSizeTimedelta: timedelta, timezone: dateutil.tz):
        '''
        These open/close tuples are returned in a list, [(open, close), (open, close), ...], are datetimetz dates,
        and can be used for whatever frequency and timezone specified, however timezone should be coordinated with the particular MarketCalendar.

        - dataStartTz must be set to the earliest you want it. It will be pushed foreward to the next market_open if the market is not open at dataStartTz
        - dataEndTz can be any datetimetz >= dataStartTz, or None. If None, datetime.now() is used.

        This function returns a deque of (open, close) datetimetz tuples, and an empty deque if there's an issue.
        :return:
        '''
        # Note: Should round the input dataStartTz down to the nearest barSizeTimedelta, and the dataEndTz up to the nearest one (if it isn't None).

        # Create the schedule with a buffer on each side.
        scheduleStartDatetimeTz = dataStartTz - timedelta(days=1)
        if dataEndTz is None:
            # Don't need much buffer here; this function will get recomputed once we reach the current time (as of when datetime.now() was called) if dataEnd is None.
            adjustedDataEndTz = datetime.now(tz=timezone)
        else:
            adjustedDataEndTz = dataEndTz
        scheduleEndDatetimeTz = adjustedDataEndTz + timedelta(days=1)
        me.createSchedule(scheduleStartDatetimeTz=scheduleStartDatetimeTz, scheduleEndDatetimeTz=scheduleEndDatetimeTz)

        # Adjust the start datetime to ensure the market is open, and we backtrack the requested number of bars.
        adjustedDataStartTz = me.adjustDataStart(proposedDataStart=dataStartTz)

        openCloseTupleDeque = deque()
        finishedAddingTuples = False
        intervalStr, intervalTimedelta = me.getPandasDateRangeFreqForQuerySize(barSizeTimedelta)
        # Note: This section will leave the deque empty in situations where a datetime range is selected that is less than 'intervalStr'. E.g., a two hour period, but intervalStr is "1D".
        for curTuple in me.exchangeSchedule.itertuples():
            #dr = pd.date_range(curTuple[1], curTuple[2], freq=intervalStr, tz=timezone, closed=None)
            dr = pd.date_range(curTuple[1], curTuple[2], freq=intervalStr, closed=None)
            for i in range(len(dr)-1):
                openDatetimeTz = dr[i].to_pydatetime()
                #print(f"open: {openDatetimeTz}")
                if (openDatetimeTz + intervalTimedelta) <= adjustedDataStartTz:
                    continue
                closeDatetimeTz = dr[i + 1].to_pydatetime()
                openCloseTuple = (openDatetimeTz.astimezone(timezone), closeDatetimeTz.astimezone(timezone))
                #print(openCloseTuple)
                openCloseTupleDeque.append(openCloseTuple)
                if closeDatetimeTz > adjustedDataEndTz or closeDatetimeTz > datetime.now(tz=timezone): # Second part of if statement was temp fix.
                    finishedAddingTuples = True
                    break
            if finishedAddingTuples:
                break
                #print(openCloseTuple)


        # Note: This (below) will likely have a problem if the adjustedDataStartTz is not at least a full barSizeSetting time period before/earlier than the close of the tuple (index 1).
        #    - Fix this. It may be fixed by rounding the dataStartTz down as recommended in the note above.


        # Now replace the first open and last close.
        if len(openCloseTupleDeque) > 0:
            # The first open will become adjustedDataStartTz -- we know the exchange is open.
            firstTuple = openCloseTupleDeque.popleft()
            updatedFirstTuple = (adjustedDataStartTz, firstTuple[1])
            openCloseTupleDeque.appendleft(updatedFirstTuple)

            # The last close will become adjustedDataEndTz if the exchange was open at that time, and if adjustedDataEndTz is not less than (earlier than) the open.
            # If adjustedDataEndTz is less than the open, set the close = open.
            #
            # It will become None if setLastCloseToNone is True.
            exchangeOpenAtDataEnd = me.exchangeCalendar.open_at_time(me.exchangeSchedule, adjustedDataEndTz)
            lastTuple = openCloseTupleDeque.pop() # This pops the rightmost (most recently added) element
            newClose = lastTuple[1]
            if setLastCloseToNone:
                newClose = None
            elif exchangeOpenAtDataEnd and adjustedDataEndTz >= lastTuple[0]:
                newClose = adjustedDataEndTz
            elif adjustedDataEndTz < lastTuple[0]:
                newClose = lastTuple[0]
            updatedLastTuple = (lastTuple[0], newClose) # keep the open, replace the close with None
            if updatedLastTuple[0] != updatedLastTuple[1]: # Again, don't add blocks with the same start and end datetimetz's
                openCloseTupleDeque.append(updatedLastTuple) # Put it back.
        return openCloseTupleDeque



    def getPandasDateRangeFreqForQuerySize(me, barSizeTimedelta: timedelta):
        '''
        barSizeTimedelta is the timedelta version of the size of the bar historical bars requested from IB (e.g., '5 secs').
        '''
        totalSeconds = barSizeTimedelta.total_seconds()
        if totalSeconds == 1:
            return "720S", timedelta(seconds=720)  # request 30 min of data at a time
        elif totalSeconds == 5:
            return "1H", timedelta(hours=1) # request 1 hour of data at a time
        elif totalSeconds >= 60:
            return "1D", timedelta(days=1) # If 1 minute bars or greater, get one day at a time.



    # Note: next -
    #   - Can move some stuff from IBHistoricalDataCollectionPlanner here.
    #       - Code to create the tuples; make the schedule cover past the start, and if market is closed, then start subtracting X timedeltas from last close to get new start.
    #   - Create marketOpen(), lastMarketClose(),
    #   - Need function to take a desired date range and modify it such that the start datetime is pushed back in time so that the
    #       originally desired number of bars is still returned. e.g., if end is 19:00 on a sunday, and start was 17:00 (an hour before open),
    #       the new start should be an hour before close on the last day the market was open.
    #       In order to work for more than one day, this will need to be in a while loop.

    def _computeDataStartWithBacktrack(me, proposedDataStart: datetime, numBarsToBacktrack: int, barSizeTimedelta: timedelta):
        '''
        Note: This is not used at the moment. It is only here for reference. I found a better way:
            - To backtrack, query the most recent bar, order by desc, set limit to number of bars to backtrack + 1,
                and use the date that corresponds to that bar
            - That way, we don't need to compute a data start with backtrack; the backtrack will be built in.

        Computes an adjusted start datetimetz that accounts for backtracking some number of bars.
        # Note: It is assumed that it has already been verified that proposedDataStart is within a time period that the market is open.
        '''
        # Compute the total timedelta to backtrack
        backtrackTimedelta = numBarsToBacktrack * barSizeTimedelta

        # Extract the date from the proposed start datetime, and get the market open time on that day.
        # Note: It is assumed that it has already been verified that proposedDataStart is within a time period that the market is open.
        date = pd.Timestamp(proposedDataStart.date())
        marketOpenDatetimeTz = me.exchangeSchedule.at[date, 'market_open']

        # The max amout we can backtrack on *that* day is from that time to market open.
        # If we need to backtrack farther than that (if remainingTimeToBacktrack is positive,
        # we need to keep looking (see while loop).
        maxBacktrackOnDate = (proposedDataStart - marketOpenDatetimeTz)
        remainingTimeToBacktrack = backtrackTimedelta - maxBacktrackOnDate

        # This keeps checking previous days, looking at the max time you can backtrack each day,
        # and stops once it has found a day where the remaining amount to backtrack is <= 0.
        # That means that on that day, we can take the residual amount to backtrack (starting from market close on that day),
        # and backtrack that amount starting from market close (this happens just outside of the loop).
        lastCheckedDatetime = proposedDataStart
        prevRemainingTimeToBacktrack = backtrackTimedelta
        marketClose = -1
        while remainingTimeToBacktrack > 0:
            # Find the next earlier/previous day that the market is open,
            #
            proposedDataStartDate: datetime.date = me.getMostRecentPreviousDateOpenFrom(referenceDatetimeTz=lastCheckedDatetime)
            marketClose = me.exchangeSchedule[proposedDataStartDate, "market_close"]
            marketOpen = me.exchangeSchedule[proposedDataStartDate, "market_open"]
            maxBacktrackOnDate = marketClose - marketOpen
            remainingTimeToBacktrack = remainingTimeToBacktrack - maxBacktrackOnDate
            proposedDataStart = marketClose
            prevRemainingTimeToBacktrack = remainingTimeToBacktrack

        # Once here, whether we executed the loop or not, we'll end up with the right starting datetime.
        adjustedDataStartWithBacktrack = proposedDataStart - prevRemainingTimeToBacktrack  # then subtract the actual amount to backtrack that remains (the prev...)
        return adjustedDataStartWithBacktrack



if __name__ == "__main__":
    print("Good.")
    fmc = FINDEVMarketCalendar()
    fmc.createCalendarByName("GLOBEX")
    startDatetimeTz = parse('2020-05-10 18:00:00').astimezone(tz=GlobalConfig.TZ_TIMEZONE) - timedelta(weeks=2)
    endDatetimeTz = parse('2020-05-22 17:00:00').astimezone(tz=GlobalConfig.TZ_TIMEZONE) + timedelta(days=1)
    scheduleStartDatetimeTz = startDatetimeTz - timedelta(weeks=2)
    scheduleEndDatetimeTz = endDatetimeTz + timedelta(days=1)
    fmc.createSchedule(scheduleStartDatetimeTz=scheduleStartDatetimeTz, scheduleEndDatetimeTz=scheduleEndDatetimeTz)
    #mrpd = fmc.getMostRecentPreviousDateOpenFrom(startDatetimeTz)
    #print(mrpd)
    numBarsToBacktrack = 42
    barTimedelta = timedelta(hours=1)
    adjustedStartWithBacktrack = fmc._computeDataStartWithBacktrack(startDatetimeTz, numBarsToBacktrack=numBarsToBacktrack, barSizeTimedelta=barTimedelta)
    print(adjustedStartWithBacktrack)