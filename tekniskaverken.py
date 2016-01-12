#!/usr/bin/env python
# encoding: utf-8

import json
import re
import datetime

import requests


def requires_login(func):
    def login_wrapper(self, *args, **kwargs):
        if not self.logged_in:
            self.login()
        return func(self, *args, **kwargs)
    return login_wrapper


class TekniskaVerken(object):
    LOGIN_URL = 'https://mina-sidor.tekniskaverken.se/portalen/index.xml'
    JSON_URL = 'https://mina-sidor.tekniskaverken.se/_internal/kundportal/export/{lpid}/{apiname}.json'

    def __init__(self, user, passw):
        """
        :user Username for mina-sidor.tekniskaverken.se
        :passw Password for mina-sidor.tekniskaverken.se
        """
        self.login_data = {'uname': user, 'pword': passw, 'login': 'Välkommen+in'}
        self.session = requests.Session()
        self.logged_in = False
        self.lpids = None

    def login(self):
        """ Performs a login to 'mina-sidor.tekniskaverken.se' and stores
        the available lpids ('leveranspunkts-ID').
        """
        r = self.session.post(
            self.LOGIN_URL, data=self.login_data, verify=False)

        if 'Kunde inte logga in' in r.text:
            raise Exception("Login failed. Bad credentials?")

        # Get hold of available services (leveranspunkts-ID, lpid)
        lpid_data = re.findall(r'href="(\w+)\/info\/\?lpid=(\d+)"', r.text)
        if len(lpid_data) > 0:
            self.lpids = dict(lpid_data)

        self.logged_in = True
        return r

    @requires_login
    def get_raw(self, service, apiname, params_dict):
        """
        Returns the raw json decoded object as the Tekniskaverken API provides

        :service Eg. 'fjarrvarme', 'el', 'vatten', 'avfall', ...
        :apiname Eg. 'yearly', 'monthly', 'daily'
        :params_dice The params for the requested apiname, see other methods
        """
        assert(str(apiname) in ['yearly', 'monthly', 'daily'])

        if str(service) not in self.lpids:
            raise Exception("Requested service is not in your lpids (%s)"
                            % (", ".join(self.lpids)))

        r = self.session.get(self.JSON_URL.format(lpid=self.lpids[service],
                                                  apiname=apiname),
                             params=params_dict, verify=False)

        if r.status_code == 404:
            raise Exception("API page not found. Either login failed or the requested URL was not found.")

        return json.loads(r.text)

    def _first_of_next_month(self, d):
        next_day = 1

        next_month = (d.month % 12) + 1

        if next_month == 1:
            next_year = d.year + 1
        else:
            next_year = d.year

        return datetime.datetime(next_year, next_month, next_day)

    def get_daily(self, service, since, until):
        """ Get daily measurements for a given service

        The method fetches a from the first in the given month and until the
        first of the next month but returns only the range asked for. This
        seems to be needed to get the Tekniskaverken API to emit the requested
        range correctly. The returned list contains pairs of datetime.date
        objects and the value for the corresponding date.

        :service Eg. 'fjarrvarme', 'el', 'vatten', 'avfall', ...
        :since datetime object with the start date
        :until datetime object with the end date
        """
        fetch_since = datetime.datetime(since.year, since.month, 1)

        if until.day > 1:
            fetch_until = self._first_of_next_month(until)
        else:
            fetch_until = until

        fetch_months = []
        while fetch_since <= fetch_until:
            fetch_months.append(fetch_since)
            fetch_since = self._first_of_next_month(fetch_since)

        raw = self.get_raw(
            service, 'daily', {'months': [m.strftime("%Y-%m-%d") for m in fetch_months]})

        flattened_raw = []
        for x in [r['data'] for r in raw]:
            flattened_raw += x

        ret = []
        for x in flattened_raw:
            d = datetime.datetime(int(x['ar']), int(x['manad']), int(x['dag']))
            if since <= d <= until:
                ret.append((d, float(x['forbrukning'])))

        return sorted(ret, key=lambda r: r[0])

    def get_monthly(self, service, since, until):
        """ Get monthly measurements for a given service

        The returned list contains pairs of datetime.date objects and the
        value for the corresponding date.

        :service Eg. 'fjarrvarme', 'el', 'vatten', 'avfall', ...
        :since datetime object with the start date
        :until datetime object with the end date
        """

        raw = self.get_raw(
            service, 'monthly', {'years': range(since.year, until.year + 1)})

        flattened_raw = []
        for x in [r['value'] for r in raw]:
            flattened_raw += x

        ret = []
        for x in flattened_raw:
            d = datetime.datetime(int(x['ar']), int(x['manad']) + 1, 1)
            if since <= d <= until:
                ret.append((d, float(x['forbrukning'])))

        return sorted(ret, key=lambda r: r[0])

    def get_yearly(self, service, since, until, adjusted=False):
        """ Get yearly measurements for a given service

        The returned list contains pairs of a year and the
        corresponding value.

        :service Eg. 'fjarrvarme', 'el', 'vatten', 'avfall', ...
        :since Start year, inclusive
        :until End year, inclusive
        """

        if type(since) is not int:
            since = since.year
        if type(until) is not int:
            until = until.year

        raw = self.get_raw(
            service, 'yearly', {'from': since, 'to': until})

        if service == 'fjarrvarme':
            key = u'Verklig anv\ufffdndning' if not adjusted \
                else u'Normal\ufffdrskorrigerad anv\ufffdndning'
            values = raw[key]
        else:
            # Only one key should be available for the rest of the services
            # so just use that one, whichever it is.
            assert(len(raw.keys()) == 1)
            values = raw.values()[0]

        ret = []
        for x in values:
            d = datetime.datetime(int(x['ar']), 1, 1)
            ret.append((d, float(x['forbrukning'])))

        return sorted(ret, key=lambda r: r[0])
