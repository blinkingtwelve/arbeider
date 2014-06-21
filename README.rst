
==================
arbeider
==================

About
-----

This is a GPLv3 (see ``LICENSE`` file) program with which you can run queries on `RFC5545 iCalendar <https://tools.ietf.org/html/rfc5545>`_ files.
For instance, you can calculate all time spent in the last three weeks on events which had *unicorn petting* in the description. You can group events based on their summary or description fields, which is convenient if you want to track time in iCalendar files.


Prerequisites
-------------

- `iCalendar python module <https://pypi.python.org/pypi/icalendar/3.7>`_ (3.7)

Author
-------

Wicher Minnaard <wicher@nontrivialpursuit.org>

Bugs
----

- It doesn't handle repeats (yet).
- The interface confuses even me and I wrote it.


Usage
-----
::

    usage: arbeider.py [-h] -f FILE [-s TIMESPEC] [-sr REGEX] [-dr REGEX]
                       [-e TIMESPEC] [-g SPEC] [-v]
    
    Look productive. Calculate time spent in events specified by regex and time
    bounds.
    
    optional arguments:
      -h, --help            show this help message and exit
      -f FILE, --file FILE  RFC5545 iCalendar file FILE (or '-' for stdin).
      -s TIMESPEC, --start TIMESPEC
                            Start datetime TIMESPEC.
      -sr REGEX, --summary-regex REGEX
                            Match event summaries by regular expression REGEX.
      -dr REGEX, --description-regex REGEX
                            Match event descriptions by regular expression REGEX.
      -e TIMESPEC, --end TIMESPEC
                            Stop datetime TIMESPEC.
      -g SPEC, --groupby SPEC
                            Accumulate event time by SPEC: 'd' for 'description',
                            's' for summary, or 'b' for both. Like 'GROUP BY' in
                            SQL.
      -v, --verbose         Be chatty (on stderr).
    
    1. TIMESPEC is either an ISO datetime (eg '1982-08-05T07:53:30') or current
    year's week number (which, when signed, is taken to be relative to the current
    week number, so '-s -0 -e +1' will demarcate the timespan occupied by the
    current week). 2. Events are matched if they are fully within the specified
    period (if any). 3. REGEXes are case-insensitive. 4. If REGEXes are specified
    multiple times, their subject match if any of the regexes match (= logical
    OR). 5. Description-regexes and subject-regexes are ANDed.
    
