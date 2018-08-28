# tekniskaverken-api
A Python wrapper for the tekniskaverken.se API

## Installation
From the command line, run
```
python setup.py install
```

## Usage
```python
import datetime

import tekniskaverken

username = 123456
password = 1234
t = tekniskaverken.TekniskaVerken(username, password)

print t.get_daily('fjarrvarme',
                    since=datetime.datetime(2013, 10, 10),
                    until=datetime.datetime(2015, 12, 15))

print t.get_yearly('vatten', since=2011, until=2015)
```

## CLI
The CLI provides the data to stdout as CSV.

```
usage: tv.py [-h] [-u USERNAME] [-p PASSWORD] [--service SERVICE]
             [--period {daily,monthly,yearly}] [--since SINCE] [--until UNTIL]

TekniskaVerken CLI

optional arguments:
  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
                        Username
  -p PASSWORD, --password PASSWORD
                        Password
  --service SERVICE     The requested service (eg. fjarrvarme, el, vatten,
                        avfall). Availability depends on the provided account.
  --period {daily,monthly,yearly}
  --since SINCE         Starting point. Format: "YYYY-MM-DD" for daily, "YYYY-
                        MM" for montly, "YYYY" for yearly.
  --until UNTIL         End point. Format: "YYYY-MM-DD" for daily, "YYYY-MM"
                        for montly, "YYYY" for yearly.
```
