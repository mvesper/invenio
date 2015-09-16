import uuid
import datetime

from invenio.modules.circulation.models import (CirculationUser,
                                                CirculationItem,
                                                CirculationLoanCycle)
from invenio.modules.circulation.api.utils import (DateManager,
                                                   DateException,
                                                   ValidationExceptions)
from invenio.modules.circulation.api.loan_cycle import finish_clcs


def _check_user(user):
    if not user:
        raise Exception('A user is required to loan an item.')
    if isinstance(user, (list, tuple)):
        raise Exception('An item can only be loaned to one user.')
    if not isinstance(user, CirculationUser):
        raise Exception('The item must be of the type CirculationUser.')


def _check_item(items, status=None):
    if not items:
        raise Exception('A item is required to loan an item.')
    if not isinstance(items, (list, tuple)):
        raise Exception('Items must be a list or tuple.')
    if not all(map(lambda x: isinstance(x, CirculationItem), items)):
        raise Exception('The items must be of the type CirculationItem.')
    if status:
        if not all(map(lambda x: x.current_status == status, items)):
            raise Exception('The items must have the status {0}.'
                            .format(status))


def _check_start_end_date(start_date, end_date):
    if start_date is None or end_date is None:
        raise Exception('Start date and end date need to be specified.')


def _check_loan_duration(user, items, start_date, end_date):
    def _get_allowed_loan_period(user, items):
        # TODO
        return 28
    desired_loan_period = end_date - start_date
    allowed_loan_period = _get_allowed_loan_period(user, items)
    if desired_loan_period.days > allowed_loan_period:
        msg = ('The desired loan period ({0} days) exceeds '
               'the allowed period of {1} days.')
        raise Exception(msg.format(desired_loan_period.days,
                                   allowed_loan_period))


def _get_affected_loan_cycles(statuses, items):
    def filter_func(x):
        return x.current_status not in statuses
    clc_list = [CirculationLoanCycle.search(item=item.id) for item in items]
    clc_list = [item for sub_list in clc_list for item in sub_list]
    return filter(filter_func, clc_list)


def _get_requested_dates(lcs):
    return [(lc.start_date, lc.end_date) for lc in lcs]


def _check_loan_start(start_date):
    if start_date != datetime.date.today():
        raise Exception('For a loan, the start date must be today.')

def _check_loan_period(user, items, start_date, end_date):
    lcs = _get_affected_loan_cycles(['finished', 'canceled'], items)
    requested_dates = _get_requested_dates(lcs)
    _start, _end = DateManager.get_contained_date(start_date, end_date,
                                                  requested_dates)
    available_start_date = _start
    desired_start_date = start_date

    available_end_date = _end
    desired_end_date = end_date

    if available_start_date != desired_start_date or available_end_date != desired_end_date:
        suggested_dates = DateManager.get_date_suggestions(requested_dates)
        contained_dates = (_start, _end)
        raise DateException(suggested_dates=suggested_dates,
                            contained_dates=contained_dates)


def try_loan_items(user, items, start_date, end_date, waitlist=False):
    exceptions = []
    try:
        _check_item(items, 'on_shelf')
    except Exception as e:
        exceptions.append(('items', e))

    try:
        _check_user(user)
    except Exception as e:
        exceptions.append(('user', e))

    try:
        _check_loan_start(start_date)
    except Exception as e:
        exceptions.append(('start_date', e))

    try:
        _check_loan_period(user, items, start_date, end_date)
    except DateException as e:
        exceptions.append(('date_suggestion', e))
    except Exception as e:
        exceptions.append(('date', e))

    if exceptions:
        raise ValidationExceptions(exceptions)


def loan_items(user, items, start_date, end_date, waitlist=False):
    try:
        try_loan_items(user, items, start_date, end_date, waitlist)
        desired_start_date = start_date
        desired_end_date = end_date
    except ValidationExceptions as e:
        if [x[0] for x in e.exceptions] == ['date_suggestion'] and waitlist:
            _start, _end = e.exceptions[0][1].contained_dates
            desired_start_date = start_date
            desired_end_date = end_date
            start_date = _start
            end_date = _end
            # TODO: Do some loan specific checks here...
            if _start != desired_start:
                raise e
        else:
            raise e

    group_uuid = str(uuid.uuid4())
    for item in items:
        item.current_status = 'on_loan'
        item.save()
        CirculationLoanCycle.new(current_status='on_loan',
                                 item=item, user=user,
                                 start_date=start_date,
                                 end_date=end_date,
                                 desired_start_date=desired_start_date,
                                 desired_end_date=desired_end_date,
                                 issued_date=datetime.datetime.now(),
                                 group_uuid=group_uuid)


def try_request_items(user, items, start_date, end_date, waitlist=False):
    exceptions = []
    try:
        _check_item(items)
    except Exception as e:
        exceptions.append(('items', e))

    try:
        _check_user(user)
    except Exception as e:
        exceptions.append(('user', e))

    try:
        _check_loan_period(user, items, start_date, end_date)
    except DateException as e:
        exceptions.append(('date_suggestion', e))
    except Exception as e:
        exceptions.append(('date', e))

    if exceptions:
        raise ValidationExceptions(exceptions)


def request_items(user, items, start_date, end_date, waitlist=False):
    try:
        try_request_items(user, items, start_date, end_date, waitlist)
        desired_start_date = start_date
        desired_end_date = end_date
    except ValidationExceptions as e:
        if [x[0] for x in e.exceptions] == ['date_suggestion'] and waitlist:
            _start, _end = e.exceptions[0][1].contained_dates
            desired_start_date = start_date
            desired_end_date = end_date
            start_date = _start
            end_date = _end
        else:
            raise e

    group_uuid = str(uuid.uuid4())
    for item in items:
        item.current_status = 'on_loan'
        CirculationLoanCycle.new(current_status='requested',
                                 item=item, user=user,
                                 start_date=start_date,
                                 end_date=end_date,
                                 desired_start_date=desired_start_date,
                                 desired_end_date=desired_end_date,
                                 issued_date=datetime.datetime.now(),
                                 group_uuid=group_uuid)


def try_return_items(items):
    exceptions = []
    try:
        _check_item(items, 'on_loan')
    except Exception as e:
        exceptions.append(('items', e))

    if exceptions:
        raise ValidationExceptions(exceptions)


def return_items(items):
    try:
        try_return_items(items)
    except ValidationExceptions as e:
        raise e

    for item in items:
        item.current_status = 'on_shelf'
        item.save()
        clc = CirculationLoanCycle.search(item=item,
                                          current_status='on_loan')[0]
        finish_clcs([clc])
