#!/usr/bin/env python
import argparse
import csv
import datetime
import sys

import tekniskaverken

parser = argparse.ArgumentParser(description='TekniskaVerken CLI')
parser.add_argument('-u', '--username', help='Username')
parser.add_argument('-p', '--password', help='Password')
parser.add_argument('--service', help='The requested service (eg. fjarrvarme, el, vatten, avfall). Availability depends on the provided account.')
parser.add_argument('--period', choices=['daily', 'monthly', 'yearly'])
parser.add_argument('--since', help='Starting point. Format: "YYYY-MM-DD" for daily, "YYYY-MM" for montly, "YYYY" for yearly.')
parser.add_argument('--until', help='End point. Format: "YYYY-MM-DD" for daily, "YYYY-MM" for montly, "YYYY" for yearly.')

args = parser.parse_args()

FMTS = {'daily': "%Y-%m-%d",
        'monthly': "%Y-%m",
        'yearly': "%Y"}

APIS = {'daily': tekniskaverken.TekniskaVerken.get_daily,
        'monthly': tekniskaverken.TekniskaVerken.get_monthly,
        'yearly': tekniskaverken.TekniskaVerken.get_yearly}

since = datetime.datetime.strptime(args.since, FMTS[args.period])
until = datetime.datetime.strptime(args.until, FMTS[args.period])
api = APIS[args.period]

t = tekniskaverken.TekniskaVerken(args.username, args.password)

with sys.stdout as f:
    writer = csv.writer(f)
    for r in api(t, args.service, since, until):
        writer.writerow([r[0].strftime(FMTS[args.period]), r[1]])
