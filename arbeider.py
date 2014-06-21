#!/usr/bin/env python2
# (c) 2014 Wicher Minnaard <wicher@nontrivialpursuit.org>
# License: GPLv3 (see LICENSE file)

from __future__ import print_function
from icalendar import Calendar
from collections import namedtuple

import sys, argparse, datetime, operator, re, time, pytz


WD = 7 # #days in week. you never know if this might change!
ISOFMT = '%Y-%m-%dT%H:%M:%S'
jetzt = datetime.datetime.utcnow()
mytz = pytz.timezone(time.tzname[0])
jetzt = jetzt.replace(tzinfo=mytz)
curyear, curweek, curday = jetzt.isocalendar()
verbose = False
event = namedtuple('event', 'start end summ desc')


class Arbeider():
	def __init__(self, data, sumrex, desrex, start=None, end=None, groupby=None):
		self.events = self.parsecal(data)
		self.sumrex = sumrex
		self.desrex = desrex
		self.start = start
		self.end = end
		self.groupby = groupby
		chatty('Total # events: {}'.format(len(self.events)))
		chatty('Start date    : {}'.format(self.start.isoformat() if self.start else None))
		chatty('End date      : {}'.format(self.end.isoformat() if self.end else None))
		self.run()


	def parsecal(self, data):
		rawevents = Calendar.from_ical(data.read()).walk(name='VEVENT')

		def sanitext(couldbetext):
			return (couldbetext if couldbetext else u'')

		def date2datetime(d_or_dt):
				if isinstance(d_or_dt, datetime.datetime): return d_or_dt
				return datetime.datetime(*d_or_dt.timetuple()[:3], tzinfo=mytz) # create datetime from date
		events = [event(date2datetime(ev.get('DTSTART').dt), date2datetime(ev.get('DTEND').dt), sanitext(ev.get('SUMMARY')), sanitext(ev.get('DESCRIPTION'))) for ev in rawevents]
		return events


	def run(self):
		#first, get all matches.
		matches = [ev for ev in self.events if self.match(ev)]

		def timesum(events):
			return reduce(lambda x,y: x + (y.end - y.start), events, datetime.timedelta())

		def evkeyfn():
			fnmap = {'d': lambda event: (event.desc,),
					 's': lambda event: (event.summ,),
					 'b': lambda event: (event.summ, event.desc)
					}
			return fnmap[self.groupby]

		if not matches: return #done, no matches
		#summate time in these matches, possibly grouped
		if self.groupby:
			evgrouped = {}
			evfn = evkeyfn()
			for ev in matches:
				key = evfn(ev)
				if key in evgrouped:
					evgrouped[key].append(ev)
				else:
					evgrouped[key] = [ev]
			self.pprint({group: timesum(evlist) for group,evlist in evgrouped.items()})
		else:
			self.pprint({(u'Total',):timesum(matches)})


	def pprint(self, outdata):
		#create table, calc widths
		
		def hms(tdelta):
			totsecs = int(tdelta.total_seconds()) # strip microseconds
			s = totsecs % 60
			totsecs -= s
			m = totsecs % 3600
			totsecs -= m
			return (totsecs/3600, m/60, s)

		def maxlens(seqseqs):
			maxlens = []
			for seq in seqseqs:
				thelens = map(len, seq)
				if len(thelens) > len(maxlens): #extend maxlens if necessary
					maxlens.extend((len(thelens) - len(maxlens)) * [0])
				maxlens = map(max, zip(maxlens, thelens))
			return maxlens

		#stabilize to sorted list
		out = sorted(outdata.items(), key=lambda a: a[1].total_seconds(), reverse=True)
		out = [ (key, hms(tdelta)) for (key,tdelta) in out ]

		#determine max width of keys
		keylens = maxlens([key for key,tdelta in out])
		keytpl = u" / ".join([ u"{{{0}:<{1}}}".format(i, thelen) for i, thelen in enumerate(keylens)])
		#determine max width of hour field
		hlen = max([len(str(v[0])) for k,v in out])
		timetpl = u"{{0:{0}}}:{{1:02}}:{{2:02}}".format(hlen)

		output = u'\n'.join([u'{0}  |  {1}'.format(keytpl.format(*k), timetpl.format(*v)) for (k,v) in out])
		print(output)


	def match(self, event):
		# Match the rexes: ANY of the sumrexes *AND* ANY of the desrexes

		def rexy(rexes, obj):
			for rex in rexes:
				if rex.search(obj): return True #only one needs to match

		# apply any rexes and break early if none of them match
		if self.sumrex and not rexy(sumrex, event.summ): return
		if self.desrex and not rexy(desrex, event.desc): return

		# Match the datetimes
		if self.start:
			if (self.start > event.end)  : return #event ends before our period starts
			if (self.start > event.start): return #event starts earlier than our period
		if self.end:
			if (self.end   < event.end)  : return #event stops after our period starts

		return True # If we made it to here, all tests were positive


def chatty(string):
	if verbose: print(string, file=sys.stderr)


def weekparse(wno, relative=False):
	#see python-docs-2.7/library/datetime.html#strftime-strptime-behavior, note #4 for why we don't use straight %W in strptime().
	if relative:
		# it's a relative offset
		op = operator.sub if (wno < 0) else operator.add
		damals = op(jetzt, datetime.timedelta(WD * abs(wno)))
		year, week, day = damals.isocalendar()
	else:
		# absolute weeknumber
		year, week = curyear, wno
	weekstart = datetime.datetime.strptime('{} 1 {}'.format(year, week), '%Y %w %W')
	return weekstart.replace(tzinfo=mytz)


def dateparse(somestring):
	try:
		wno = int(somestring)
		#appy, it's a week number
		#maybe it's relative
		isumrexelative = (somestring[0] in ['+','-'])
		return weekparse(wno, relative=isumrexelative)
	except ValueError:
		pass #not a week number, try parsing as ISO date
	try:
		somedate = datetime.datetime.strptime(somestring, ISOFMT)
		return somedate.replace(tzinfo=mytz)
	except ValueError:
		return None #can't make sense of it
			


if __name__ == "__main__":
	description = "Look productive. Calculate time spent in events specified by regex and time bounds."
	epilog = """
	1. TIMESPEC is either an ISO datetime (eg '1982-08-05T07:53:30') or current year's week number (which, when signed, is taken to be relative to the current week number, so '-s -0 -e +1' will demarcate the timespan occupied by the current week).
	2. Events are matched if they are fully within the specified period (if any). 
	3. REGEXes are case-insensitive. 
	4. If REGEXes are specified multiple times, their subject match if any of the regexes match (= logical OR). 
	5. Description-regexes and subject-regexes are ANDed.
	"""

	parser = argparse.ArgumentParser(description=description, epilog=epilog)
	parser.add_argument('-f',  '--file', required=True, help="RFC5545 iCalendar file FILE (or '-' for stdin).", type=argparse.FileType('rb'), metavar="FILE")
	parser.add_argument('-s',  '--start', help="Start datetime TIMESPEC.", metavar="TIMESPEC")
	parser.add_argument('-sr', '--summary-regex', help="Match event summaries by regular expression REGEX.", metavar="REGEX", action='append', default=[])
	parser.add_argument('-dr', '--description-regex', help="Match event descriptions by regular expression REGEX.", metavar="REGEX", action='append', default=[])
	parser.add_argument('-e',  '--end', help="Stop datetime TIMESPEC.", metavar="TIMESPEC")
	parser.add_argument('-g',  '--groupby', help="Accumulate event time by SPEC: 'd' for 'description', 's' for summary, or 'b' for both. Like 'GROUP BY' in SQL.", metavar="SPEC", choices='dsb')
	parser.add_argument('-v',  '--verbose', action="store_true", help="Be chatty (on stderr).")
	args = parser.parse_args()
	verbose = args.verbose

	def datevalvalidate(arg):
		#parse/calc dates
		if arg != None:
			sometime = dateparse(arg)
			if not sometime: 
				parser.exit(status=1, message="Error: Could not parse TIMESPEC '{}'.".format(arg))
			return sometime

	dtstart = datevalvalidate(args.start)
	dtend = datevalvalidate(args.end)
	sumrex, desrex = ([re.compile(pat, re.I) for pat in pats] for pats in (args.summary_regex, args.description_regex))

	arb = Arbeider(args.file, sumrex, desrex, start=dtstart, end=dtend, groupby=args.groupby)

