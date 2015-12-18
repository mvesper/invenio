import json
import datetime

from dateutil import relativedelta


def _get_cal_heatmap_dates(items):
    import invenio.modules.circulation_ill.models as models

    def to_seconds(date):
        return int(date.strftime("%s"))

    def get_date_range(start_date, end_date):
        delta = (end_date - start_date).days
        res = []
        for day in range(delta+1):
            res.append(start_date + datetime.timedelta(days=day))
        return res

    res = set()
    for item in items:
        query = 'item_id:{0}'.format(item.id)
        statuses = [models.IllLoanCycle.STATUS_FINISHED,
                    models.IllLoanCycle.STATUS_CANCELED]
        clcs = models.IllLoanCycle.search(query)
        clcs = filter(lambda x: x.current_status not in statuses, clcs)
        for clc in clcs:
            date_range = get_date_range(clc.start_date, clc.end_date)
            for date in date_range:
                res.add((str(to_seconds(date)), 1))

    return dict(res)


def _get_cal_heatmap_range(items):
    import invenio.modules.circulation_ill.models as models

    min_dates = []
    max_dates = []
    for item in items:
        query = 'item_id:{0}'.format(item.id)
        statuses = [models.IllLoanCycle.STATUS_FINISHED,
                    models.IllLoanCycle.STATUS_CANCELED]
        clcs = models.IllLoanCycle.search(query)
        clcs = filter(lambda x: x.current_status not in statuses, clcs)
        if not clcs:
            continue
        min_dates.append(min(clc.start_date for clc in clcs))
        max_dates.append(max(clc.end_date for clc in clcs))

    if not min_dates or not max_dates:
        return 0

    min_date = min(min_dates)
    max_date = max(max_dates)

    return relativedelta.relativedelta(max_date, min_date).months + 1


def _get_current(user_id, status):
    import invenio.modules.circulation_ill.models as models

    def make_dict(clc):
        return {'id': clc.id,
                'attributes': [clc.item.record.title,
                               clc.start_date,
                               clc.end_date],
                'cal_data': json.dumps(_get_cal_heatmap_dates([clc.item])),
                'cal_range': _get_cal_heatmap_range([clc.item])}

    query = 'user_id:{0} current_status:{1}'.format(user_id, status)

    return [make_dict(clc) for clc
            in models.IllLoanCycle.search(query)]
