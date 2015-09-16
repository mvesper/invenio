import datetime

from itertools import starmap


class DateException(Exception):
    def __init__(self, suggested_dates, contained_dates):
        self.suggested_dates = suggested_dates
        self.contained_dates = contained_dates

    def __str__(self):
        tmp = ['{0} - {1}'.format(start, end)
               for start, end in self.suggested_dates[:-1]]
        tmp.append('{0} - ...'.format(self.suggested_dates[-1]))
        return 'The date is already taken, try: ' + ' or '.join(tmp)


class ValidationExceptions(Exception):
    def __init__(self, exceptions):
        self.exceptions = exceptions

    def __str__(self):
        return '\n'.join(['{0}: {1}'.format(x, str(y))
                          for x, y in self.exceptions])


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
            return None, None
            # TODO
            # raise Exception('No available dates')

        return cls._convert_to_datetime(start, end)
