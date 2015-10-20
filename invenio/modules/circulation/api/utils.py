import datetime

from jinja2 import Template
from itertools import starmap

from invenio.ext.email import send_email
from invenio.modules.circulation.models import (CirculationMailTemplate,
                                                CirculationLoanRule)


def check_field_in(field_name, values, message):
    def wrapper(objs):
        def check(obj):
            return obj.__getattribute__(field_name) in values
        if not all(map(check, objs)):
            raise Exception(message)
    return wrapper


def check_field_op(field_name, operator, values, message, negate=False):
    def wrapper(objs):
        def check(obj):
            attr = obj.__getattribute__(field_name)
            oper = attr.__getattribute__(operator)
            if negate:
                return not oper(values)
            return oper(values)
        if not all(map(check, objs)):
            raise Exception(message)
    return wrapper


def try_functions(*funcs):
    def wrapper(**kwargs):
        exceptions = []
        for name, func in funcs:
            try:
                func(**kwargs)
            except Exception as e:
                exceptions.append((name, e))

        if exceptions:
            raise ValidationExceptions(exceptions)
    return wrapper


def update(obj, **kwargs):
    current_items = {key: obj.__getattribute__(key) for key in dir(obj)
                     if not callable(obj.__getattribute__(key)) and not
                     key.startswith("__")}

    changed = {}

    for key, value in kwargs.items():
        if value != current_items[key]:
            try:
                obj.__setattr__(key, value)
            except Exception:
                pass
            changed[key] = value

    if changed:
        obj.save()

    return current_items, changed


def email_notification(template_name, sender, receiver, **kwargs):
    try:
        # cmt = CirculationMailTemplate.search(template_name=template_name)[0]
        query = 'template_name:{0}'.format(template_name)
        cmt = CirculationMailTemplate.search(query)[0]
    except IndexError:
        return

    subject = Template(cmt.subject).render(**kwargs)
    header = Template(cmt.header).render(**kwargs)
    content = Template(cmt.content).render(**kwargs)

    send_email(sender, receiver,
               subject=subject,
               header=header,
               content=content)


def get_loan_period(user, items):
    try:
        res = []
        for item in items:
            """
            clr = CirculationLoanRule.search(user_group=user.user_group,
                                             item_group=item.item_group,
                                             location_code=item.location.code)
            """
            query = 'user_group:{0} item_group:{1} location_code:{2}'
            query = query.format(user.user_group, item.item_group,
                                 item.location.code)
            clr = CirculationLoanRule.search(query)[0]
            res.append(clr.loan_period)
        return max(res)
    except IndexError:
        return 0


class DateException(Exception):
    def __init__(self, suggested_dates, contained_dates):
        self.suggested_dates = suggested_dates
        self.contained_dates = contained_dates

    def __str__(self):
        """
        TODO
        tmp = ['{0} - {1}'.format(start, end)
               for start, end in self.suggested_dates[:-1]]
        tmp.append('{0} - ...'.format(self.suggested_dates[-1]))
        return 'The date is already taken, try: ' + ' or '.join(tmp)
        """
        return 'The date is already taken.'


class ValidationExceptions(Exception):
    def __init__(self, exceptions):
        self.exceptions = exceptions

    def __str__(self):
        return '\n'.join(['{0}: {1}'.format(x, str(y))
                          for x, y in self.exceptions])


class DateManager(object):
    _start = datetime.date(1970, 1, 1)

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
    def _build_timeline(cls, requested_period, periods):
        periods = sorted(periods, key=lambda x: x[0])
        periods = list(starmap(cls._convert_to_days, periods))
        requested_period = cls._convert_to_days(*requested_period)
        periods_and_requested = periods + [requested_period]
        period_min = min(periods_and_requested, key=lambda x: x[0])[0]
        period_max = max(periods_and_requested, key=lambda x: x[1])[1]

        time_line = []
        for x in range(period_min, period_max):
            for start, end in periods:
                if start <= x <= end:
                    time_line.append(1)
                    break
            else:
                time_line.append(0)

        return period_min, time_line

    @classmethod
    def get_contained_date(cls, requested_start, requested_end, periods):
        try:
            timeline_start, timeline = cls._build_timeline((requested_start,
                                                            requested_end),
                                                           periods)
        except ValueError:
            return requested_start, requested_end

        req_start_day, req_end_day = cls._convert_to_days(requested_start,
                                                          requested_end)

        start_in_timeline = req_start_day - timeline_start
        end_in_timeline = req_end_day - timeline_start

        start, end = None, None

        for i, day in enumerate(timeline[start_in_timeline:end_in_timeline]):
            if day == 0:
                if start is None:
                    start = start_in_timeline+i
            elif day == 1:
                if start is not None and end is None:
                    end = start_in_timeline+i-1

        if start is None and end is None:
            raise DateException(None, None)
        elif start is not None and end is None:
            return cls._convert_to_datetime(timeline_start+start, req_end_day)
        else:
            return cls._convert_to_datetime(timeline_start+start,
                                            timeline_start+end)

    @classmethod
    def get_date_suggestions(cls, periods):
        if not periods:
            return [datetime.date.today()]
        today = datetime.date.today()
        try:
            timeline_start, timeline = cls._build_timeline((today, today),
                                                           periods)
        except ValueError:
            return []

        res = []
        start, end = None, None

        for i, day in enumerate(timeline):
            if day == 0:
                if start is None:
                    start = i
            elif day == 1:
                if start is not None and end is None:
                    end = i-1

            if start is not None and end is not None:
                res.append((timeline_start+start, timeline_start+end))
                start, end = None, None

        if start is None and end is None:
            res.append((timeline_start+len(timeline)+1, None))
        elif start is not None:
            res.append((timeline_start+start, timeline_start+len(timeline)))

        return list(starmap(cls._convert_to_datetime, res))


class CirculationTestBase(object):
    def create_test_data(self):
        import invenio.modules.circulation.api as api
        import invenio.modules.circulation.models as models
        self.cl = api.location.create('CCL', 'CERN CENTRAL LIBRARY', '')
        self.clr = api.loan_rule.create(models.CirculationItem.GROUP_BOOK,
                                        models.CirculationUser.GROUP_DEFAULT,
                                        self.cl.code, 28)
        self.cu = api.user.create(1, 934657, 'John Doe', '3 1-014', 'C27800',
                                  'john.doe@cern.ch', '+41227141337', '',
                                  models.CirculationUser.GROUP_DEFAULT)
        self.ci = api.item.create(30, self.cl.id, '978-1934356982',
                                  'CM-B00001338', 'books', '13.37', 'Vol 1',
                                  'no desc',
                                  models.CirculationItem.STATUS_ON_SHELF,
                                  models.CirculationItem.GROUP_BOOK)
        self.clcs = []

    def delete_test_data(self):
        for clc in self.clcs:
            clc.delete()
        self.cu.delete()
        self.ci.delete()
        self.cl.delete()
        self.clr.delete()

    def create_dates(self, start_days=0, start_weeks=0,
                     end_days=0, end_weeks=4):
        start_date = (datetime.date.today() +
                      datetime.timedelta(days=start_days, weeks=start_weeks))
        end_date = (start_date +
                    datetime.timedelta(days=end_days, weeks=end_weeks))
        return start_date, end_date
