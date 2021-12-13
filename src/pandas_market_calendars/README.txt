This is originally from:
    - https://pypi.org/project/pandas-market-calendars/
    - https://github.com/rsheftel/pandas_market_calendars

I cloned the above github repo, and copied the main folder that this README is in, into FINDEV.

To update this, make changes to new code as needed (see NOTES below),
and then put the new pandas_market_calendars in place of this one (but keep this README).


NOTES:
    - Last updated: 2021-12-12
    - Added 'CBOE' to the NYSE Calendar alias
    - Last updated: 2021-01-12
    - Changed NYSE and CMEEquity... Calendars to use dateutil.tz instead of pytz.
        - *ALL NEW CALENDARS MUST USE datetutil.tz*.
    - Added 'AMEX' to the NYSE Calendar alias, may add others
    - Added 'GLOBEX' to the CMEEquity Calendar alias, may add others
    - Eventually will add more Calendars
    - Added timezone parameter to calendar_utils.py/date_range()
    - Commented out the import line for trading_calendars_mirror in calendar_registry.py
    - Added custom open_at_time() function in market_calendar.py