from invenio.modules.circulation.models import CirculationLoanCycle
from invenio.modules.circulation.api.utils import (DateManager,
                                                   ValidationExceptions)


def _check_status(statuses, objs):
    if not all(map(lambda x: x.current_status in statuses, objs)):
        raise Exception('The object is in the wrong state.')


def try_finish_clcs(clcs):
    exceptions = []
    try:
        _check_status(['on_loan'], clcs)
    except Exception as e:
        exceptions.append(('clc', e))

    if exceptions:
        raise ValidationExceptions(exceptions)


def finish_clcs(clcs):
    try:
        try_finish_clcs(clcs)
    except ValidationExceptions as e:
        raise e

    for clc in clcs:
        clc.current_status = 'finished'
        clc.save()
        update_waitlist(clc)


def try_cancel_clcs(clcs):
    pass


def cancel_clcs(clcs):
    try:
        try_finish_clcs(clcs)
    except ValidationExceptions as e:
        raise e

    for clc in clcs:
        clc.current_status = 'canceled'
        clc.save()
        update_waitlist(clc)


def _get_nearest_affected_clc(start_date, end_date, involved_clcs):
    involved_clcs = sorted(involved_clcs, key=lambda x: x.issued_date)
    for clc in involved_clcs:
        if start_date <= clc.desired_start_date <= end_date:
            # start_date affected
            return clc
        elif start_date <= clc.desired_end_date <= end_date:
            # end_date affected
            return clc
        elif (clc.desired_start_date <= start_date <= clc.desired_end_date and
              clc.desired_start_date <= end_date <= clc.desired_end_date):
            return clc


def update_waitlist(clc):
    def check_clcs(_clc):
        return (_clc.issued_date < clc.issued_date and
                _clc.current_status not in ['finished', 'canceled'] and
                _clc.id != clc.id)

    involved_clcs = filter(check_clcs,
                           CirculationLoanCycle.search(item=clc.item))
    affected_clc = _get_nearest_affected_clc(clc.start_date, clc.end_date,
                                             involved_clcs)

    if not affected_clc:
        return

    involved_clcs.remove(affected_clc)

    start_date = affected_clc.desired_start_date
    end_date = affected_clc.desired_end_date
    requested_dates = [(lc.start_date, lc.end_date) for lc in involved_clcs]
    _start, _end = DateManager.get_contained_date(start_date, end_date,
                                                  requested_dates)

    # We then update the dates accordingly :)
    if _start < affected_clc.start_date:
        if _start < affected_clc.desired_start_date:
            affected_clc.start_date = affected_clc.desired_start_date
        else:
            affected_clc.start_date = _start

    if _end > affected_clc.end_date:
        if _end > affected_clc.desired_end_date:
            affected_clc.end_date = affected_clc.desired_end_date
        else:
            affected_clc.end_date = _end
