import inspect
import datetime

from itertools import starmap
from functools import wraps

from jinja2 import Template

from invenio.ext.email import send_email
from invenio.modules.circulation.models import CirculationLoanCycle
from invenio.modules.circulation.models import CirculationEvent
from invenio.modules.circulation.models import CirculationMailTemplate


class DateException(Exception):
    def __init__(self, dates):
        self.dates = dates

    def __str__(self):
        tmp = ['{0} - {1}'.format(start, end)
               for start, end in self.dates[:-1]]
        tmp.append('{0} - ...'.format(self.dates[-1]))
        return 'The date is already taken, try: ' + ' or '.join(tmp)


class ValidationExceptions(Exception):
    def __init__(self, exceptions):
        self.exceptions = exceptions

    def __str__(self):
        return '\n'.join(['{0}: {1}'.format(x, str(y))
                          for x, y in self.exceptions])


class ConfigBase(object):
    parameters = []

    def validate(self, **kwargs):
            methods = inspect.getmembers(self, predicate=inspect.ismethod)
            checks = [x for x in methods if x[0].startswith('check')]

            errors = []
            for check, _ in checks:
                    try:
                            self.__getattribute__(check)(**kwargs)
                    except Exception as e:
                            errors.append((check, e))

            if errors:
                    raise ValidationExceptions(errors)


class DateManager(object):
    _start = datetime.date(2015, 1, 1)

    @classmethod
    def _convert_to_days(cls, start_date, end_date):
        start_days = (start_date - cls._start).days
        end_days = (end_date - cls._start).days
        return start_days, end_days

    @classmethod
    def _convert_to_datetime(cls, start_days, end_days):
        if end_days:
            return (cls._start + datetime.timedelta(days=start_days),
                    cls._start + datetime.timedelta(days=end_days))
        else:
            return cls._start + datetime.timedelta(days=start_days)

    @classmethod
    def _build_timeline(cls, periods):
        periods = sorted(periods, key=lambda x: x[0])
        periods = list(starmap(cls._convert_to_days, periods))
        _min = min(periods, key=lambda x: x[0])[0]
        _max = max(periods, key=lambda x: x[1])[1]

        time_line = []
        for x in range(_min, _max):
            for start, end in periods:
                if start <= x <= end:
                    time_line.append(1)
                    break
            else:
                time_line.append(0)

        return _min, time_line

    @classmethod
    def get_date_suggestions(cls, periods):
        _now = (datetime.date.today() - cls._start).days
        try:
            timeline_start, timeline = cls._build_timeline(periods)
        except ValueError:
            return []

        res = []
        start = None
        end = None
        active = False

        if _now < timeline_start:
            start = _now
            active = True

        for i, day in enumerate(timeline):
            if day:
                # This means 1, occupied day
                if active:
                    end = timeline_start + i - 1
                    active = False
                    res.append((start, end))
            else:
                # This means 0, free day
                if not active:
                    start = timeline_start + i
                    active = True

        res.append((timeline_start+len(timeline)+1, None))

        return list(starmap(cls._convert_to_datetime, res))

    @classmethod
    def get_contained_date(cls, requested_start, requested_end, periods):
        try:
            timeline_start, timeline = cls._build_timeline(periods)
        except ValueError:
            return requested_start, requested_end
        requested_start, requested_end = cls._convert_to_days(requested_start,
                                                              requested_end)
        timeline_end = timeline_start + len(timeline)

        start = None
        end = None
        active = False

        # CASE 1: Start and end before the actual timeline
        if (requested_start <= timeline_start and
                requested_end <= timeline_start):
            return cls._convert_to_datetime(requested_start, requested_end)
        # CASE 2: Start and end after the actual timeline
        elif (requested_start >= timeline_end and
              requested_end >= timeline_end):
            return cls._convert_to_datetime(requested_start, requested_end)

        # CASE 3:
        if requested_start <= timeline_start:
            active = True
            start = requested_start
            iter_start = 0
        else:
            iter_start = requested_start - timeline_start

        if requested_end > timeline_end:
            end = requested_end

        iter_end = requested_end - timeline_start

        for i, day in list(enumerate(timeline))[iter_start:iter_end]:
            if day:
                if active:
                    end = timeline_start + i - 1
                    break
            else:
                if not active:
                    active = True
                    start = timeline_start + i

        if start is not None and end is None:
            end = requested_end
        elif start is None and end is not None:
            start = timeline_end
        elif start is None and end is None:
            raise Exception('No available dates')

        return cls._convert_to_datetime(start, end)


# Temp stupid stuff

# Decorators
def email_notification(template_name=None, attributes={}):
    try:
        cmt = CirculationMailTemplate.search(template_name=template_name)[0]
    except IndexError:
        cmt = None

    def wrapper(func):
        @wraps(func)
        def wrapper1(*args, **kwargs):
            res = func(*args, **kwargs)

            if kwargs.get('_notify', True) and cmt:
                toaddr = kwargs['user'].email
                items = kwargs.get('items', [kwargs['item']])

                subject = Template(cmt.subject).render(**kwargs)
                header = Template(cmt.header).render(**kwargs)
                content = Template(cmt.content).render(items=items, **kwargs)

                send_email('martin.vesper@cern.ch', toaddr,
                           subject=subject,
                           header=header,
                           content=content)
            return res

        return wrapper1

    return wrapper


def create_task(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        # create a new task from what we know
        # What kind of tasks do we have?
        return res

    return wrapper

def create_event(storage,
                 name, user, item, library, loan_cycle,
                 start_date=None, end_date=None,
                 **kwargs):
    ce = CirculationEvent(name=name, user=user, item=item, library=library,
                          loan_cycle=loan_cycle,
                          start_date=start_date, end_date=end_date,
                          issued_date=datetime.datetime.now(),
                          **kwargs)
    storage.append(ce)

def log_event(event, attributes):
    #Probably not really useful, since too elaborate
    def wrapper(func):
        @wraps(func)
        def wrapper1(*args, **kwargs):
            res = func(*args, **kwargs)

            # and here we create a CirculationEvent object
            ce = CirculationEvent()
            ce.event = event
            for attribute in attributes:
                try:
                    ce.__setattr__(attribute, kwargs[attribute])
                except KeyError:
                    pass
            ce.date_issued = datetime.datetime.today()

            kwargs['_storage'].append(ce)

            return res

        return wrapper1

    return wrapper
