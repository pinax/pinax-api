import datetime
import re


_datetime_re = re.compile(r"^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})T"
r"(?P<hour>\d{2}):(?P<minute>\d{2})(:(?P<second>\d{2})(\.(?P<fraction>\d+))?)"
r"((?P<tzzulu>Z)|((?P<tzoffset>[\-+])(?P<tzhour>\d{2}):(?P<tzminute>\d{2})))$")


def parse(text):
    m = _datetime_re.match(text)

    if m:
        x = m.groupdict()
    else:
        raise ValueError("unable to parse text")

    class ZuluTZ(datetime.tzinfo):
        def utcoffset(self, dt):
            return datetime.timedelta(0)

    class OtherTZ(datetime.tzinfo):
        def __init__(self, tzoffset, tzhour, tzminute):
            minutes = int(tzhour) * 60 + int(tzminute)
            if tzoffset == "+":
                self.minutes = +minutes
            else:
                self.minutes = -minutes
        def utcoffset(self, dt):
            return datetime.timedelta(minutes=self.minutes)

    if x["tzzulu"]:
        tz = ZuluTZ()
    else:
        tz = OtherTZ(x["tzoffset"], x["tzhour"], x["tzminute"])

    return datetime.datetime(
        int(x["year"]),
        int(x["month"]),
        int(x["day"]),
        int(x["hour"]),
        int(x["minute"]),
        int(x["second"]),
        int(x["fraction"]),
        tz
    )


def encode(date):
    return date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
