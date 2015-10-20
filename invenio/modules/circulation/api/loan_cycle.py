import datetime

from invenio.modules.circulation.models import (CirculationLoanCycle,
                                                CirculationEvent)
from invenio.modules.circulation.api.utils import (DateManager,
                                                   ValidationExceptions,
                                                   try_functions,
                                                   check_field_in,
                                                   check_field_op)
from invenio.modules.circulation.api.utils import update as _update
from invenio.modules.circulation.api.event import create as create_event


def create(item, user, current_status, start_date, end_date,
           desired_start_date, desired_end_date,
           requsted_extension_end_date, issued_date):

    clc = CirculationLoanCycle.new(item=item, user=user,
                                   current_status=current_status,
                                   start_date=start_date, end_date=end_date,
                                   desired_start_date=desired_start_date,
                                   desired_end_date=desired_end_date,
                                   requested_extension_end_date=requested_extension_end_date,
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


try_cancel_clcs = try_functions(
        ('status', check_field_in('current_status',
                                  [CirculationLoanCycle.STATUS_REQUESTED],
                                  'Object(s) is/are in the wrong state'))
        )


def cancel_clcs(clcs):
    try:
        try_cancel_clcs(objs=clcs)
    except ValidationExceptions as e:
        raise e

    for clc in clcs:
        clc.current_status = CirculationLoanCycle.STATUS_CANCELED
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
        """
        Must be issued later, valid status and not the current clc
        """
        return (_clc.issued_date >= clc.issued_date and
                _clc.current_status not in ['finished', 'canceled'] and
                _clc.id != clc.id)

    """
    involved_clcs = filter(check_clcs,
                           CirculationLoanCycle.search(item=clc.item))
    """
    query = 'item:{0}'.format(clc.item.id)
    involved_clcs = filter(check_clcs,
                           CirculationLoanCycle.search(query))
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
    _update = {}
    if _start < affected_clc.start_date:
        if _start < affected_clc.desired_start_date:
            _update['start_date'] = affected_clc.desired_start_date
        else:
            _update['start_date'] = _start

    if _end > affected_clc.end_date:
        if _end > affected_clc.desired_end_date:
            _update['end_date'] = affected_clc.desired_end_date
        else:
            _update['end_date'] = _end

    if _update:
        update(affected_clc, **_update)
    # TODO: mail the other guy


try_overdue_clcs = try_functions(
        ('status', check_field_in('current_status',
                                  [CirculationLoanCycle.STATUS_ON_LOAN],
                                  'Object(s) is/are in the wrong state')),
        ('status', check_field_op('additional_statuses', '__contains__',
                                  CirculationLoanCycle.STATUS_OVERDUE,
                                  'Object is already overdue',
                                  negate=True)),
        ('end_date', check_field_op('end_date', '__lt__',
                                    datetime.date.today(),
                                    'The LoanCycle(s) is/are not overdue.'))
        )


def overdue_clcs(clcs):
    try:
        try_overdue_clcs(objs=clcs)
    except ValidationExceptions as e:
        raise e

    for clc in clcs:
        clc.additional_statuses.append(CirculationLoanCycle.STATUS_OVERDUE)
        clc.save()
        create_event(loan_cycle=clc, event=CirculationEvent.EVENT_CLC_OVERDUE)


try_request_loan_extension = try_functions(
        ('status', check_field_in('current_status',
                                  [CirculationLoanCycle.STATUS_ON_LOAN],
                                  'Object(s) is/are in the wrong state')),
        ('status', check_field_op('additional_statuses', '__contains__',
                                  (CirculationLoanCycle
                                   .STATUS_LOAN_EXTENSION_REQUESTED),
                                  'Extension is already requested.',
                                  negate=True)),
        )


def request_loan_extension(clcs, requested_end_date):
    try:
        try_request_loan_extension(objs=clcs)
    except ValidationExceptions as e:
        raise e

    for clc in clcs:
        clc.requested_extension_end_date = requested_end_date
        clc.additional_statuses.append(CirculationLoanCycle
                                       .STATUS_LOAN_EXTENSION_REQUESTED)
        clc.save()
        create_event(loan_cycle=clc,
                     event=CirculationEvent.EVENT_CLC_REQUEST_LOAN_EXTENSION)


SLER = CirculationLoanCycle.STATUS_LOAN_EXTENSION_REQUESTED
try_loan_extension = try_functions(
        ('status', check_field_in('current_status',
                                  [CirculationLoanCycle.STATUS_ON_LOAN],
                                  'Object(s) is/are in the wrong state')),
        ('status', check_field_op('additional_statuses', '__contains__',
                                  (CirculationLoanCycle
                                   .STATUS_LOAN_EXTENSION_REQUESTED),
                                  'A loan extension was not requested.')),
        )


def loan_extension(clcs):
    try:
        try_loan_extension(objs=clcs)
    except ValidationExceptions as e:
        raise e

    for clc in clcs:
        try:
            clc.additional_statuses.remove(CirculationLoanCycle.STATUS_OVERDUE)
        except ValueError:
            pass
        clc.additional_statuses.remove(CirculationLoanCycle
                                       .STATUS_LOAN_EXTENSION_REQUESTED)
        clc.desired_end_date = clc.requested_extension_end_date
        clc.end_date = clc.requested_extension_end_date
        clc.save()
        create_event(loan_cycle=clc,
                     event=CirculationEvent.EVENT_CLC_LOAN_EXTENSION)


schema = {}
