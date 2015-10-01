from invenio.modules.circulation.models import (CirculationLoanCycle,
                                                CirculationEvent)
from invenio.modules.circulation.api.utils import (DateManager,
                                                   ValidationExceptions)
from invenio.modules.circulation.api.utils import update as _update
from invenio.modules.circulation.api.event import create as create_event


def create(item, user, current_status, start_date, end_date,
           desired_start_date, desired_end_date, issued_date):

    clc = CirculationLoanCycle.new(item=item, user=user,
                                   current_status=current_status,
                                   start_date=start_date, end_date=end_date,
                                   desired_start_date=desired_start_date,
                                   desired_end_date=desired_end_date,
                                   issued_date=issued_date)

    create_event(loan_cycle=clc, event=CirculationEvent.EVENT_CLC_CREATE)


def update(clc, **kwargs):
    current_items, changed = _update(clc, **kwargs)
    if changed:
        changes_str = ['{0}: {1} -> {2}'.format(key,
                                                current_items[key],
                                                changed[key])
                       for key in changed]
        create_event(loan_cycle=clc, event=CirculationEvent.EVENT_ITEM_CHANGE,
                     description=', '.join(changes_str))


def delete(clc):
    create_event(loan_cycle=clc, event=CirculationEvent.EVENT_CLC_DELETE)
    clc.delete()


def _check_status(statuses, objs):
    if not all(map(lambda x: x.current_status in statuses, objs)):
        raise Exception('The object is in the wrong state.')


"""
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
        create_event(loan_cycle=clc, event=CirculationEvent.EVENT_CLC_FINISHED)

        update_waitlist(clc)
"""


def try_cancel_clcs(clcs):
    exceptions = []

    if exceptions:
        raise ValidationExceptions(exceptions)


def cancel_clcs(clcs):
    try:
        try_finish_clcs(clcs)
    except ValidationExceptions as e:
        raise e

    for clc in clcs:
        clc.current_status = 'canceled'
        clc.save()
        create_event(loan_cycle=clc, event=CirculationEvent.EVENT_CLC_CANCELED)

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

    create_event(None, None, affected_clc, CirculationEvent.EVENT_CLC_UPDATED)


def try_overdue_clcs(clcs):
    exceptions = []
    try:
        _check_status(['on_loan'], clcs)
    except Exception as e:
        exceptions.append(('clc', e))

    if exceptions:
        raise ValidationExceptions(exceptions)


def overdue_clcs(clcs):
    try:
        try_overdue_clcs(clcs)
    except ValidationExceptions as e:
        raise e

    for clc in clcs:
        clc.current_status = 'overdue'
        clc.save()
        create_event(loan_cycle=clc, event=CirculationEvent.EVENT_CLC_OVERDUE)


def try_return_ill_clcs(clcs):
    pass


def return_ill_clcs(clcs):
    try:
        try_return_ill_clcs(clcs)
    except ValidationExceptions as e:
        raise e


def try_request_loan_extension(clcs):
    exceptions = []
    try:
        _check_status(['overdue'], clcs)
    except Exception as e:
        exceptions.append(('clc', e))

    if exceptions:
        raise ValidationExceptions(exceptions)


def request_loan_extension(clcs):
    try:
        try_request_loan_extension(clcs)
    except ValidationExceptions as e:
        raise e

    for clc in clcs:
        clc.current_status = 'loan_extension_requested'
        clc.save()
        create_event(loan_cycle=clc,
                     event=CirculationEvent.EVENT_CLC_REQUEST_LOAN_EXTENSION)


def try_loan_extension(clcs):
    exceptions = []
    try:
        _check_status(['loan_extension_requested'], clcs)
    except Exception as e:
        exceptions.append(('clc', e))

    if exceptions:
        raise ValidationExceptions(exceptions)


def loan_extension(clcs):
    try:
        try_loan_extension(clcs)
    except ValidationExceptions as e:
        raise e

    for clc in clcs:
        clc.current_status = 'on_loan'
        clc.save()
        create_event(loan_cycle=clc,
                     event=CirculationEvent.EVENT_CLC_LOAN_EXTENSION)


schema = {}
