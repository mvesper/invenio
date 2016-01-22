import uuid
import datetime

from invenio.modules.circulation.models import (CirculationUser,
                                                CirculationItem,
                                                CirculationLoanCycle,
                                                CirculationEvent)
from invenio.modules.circulation.api.utils import (DateManager,
                                                   DateException,
                                                   ValidationExceptions,
                                                   email_notification,
                                                   get_loan_period,
                                                   check_field_in,
                                                   _check_loan_duration,
                                                   _check_loan_period)
from invenio.modules.circulation.api.loan_cycle import update_waitlist
from invenio.modules.circulation.api.event import create as create_event


def _check_user(user):
    if not user:
        raise Exception('A user is required to loan an item.')
    if isinstance(user, (list, tuple)):
        raise Exception('An item can only be loaned to one user.')
    if not isinstance(user, CirculationUser):
        raise Exception('The item must be of the type CirculationUser.')


def _check_items(items):
    if not items:
        raise Exception('A item is required to loan an item.')
    if not isinstance(items, (list, tuple)):
        raise Exception('Items must be a list or tuple.')
    if not all(map(lambda x: isinstance(x, CirculationItem), items)):
        raise Exception('The items must be of the type CirculationItem.')


def _check_start_end_date(start_date, end_date):
    if start_date is None or end_date is None:
        raise Exception('Start date and end date need to be specified.')


'''
def _get_affected_loan_cycles(statuses, items):
    def filter_func(x):
        return x.current_status not in statuses
    #clc_list = [CirculationLoanCycle.search(item=item.id) for item in items]
    clc_list = [CirculationLoanCycle.search('item:{0}'.format(item.id))
                for item in items]
    clc_list = [item for sub_list in clc_list for item in sub_list]
    return filter(filter_func, clc_list)
'''


'''
def _get_requested_dates(lcs):
    return [(lc.start_date, lc.end_date) for lc in lcs]
'''


def _check_loan_start(start_date):
    if start_date != datetime.date.today():
        raise Exception('For a loan, the start date must be today.')


def _check_request_start(start_date):
    if start_date < datetime.date.today():
        raise Exception('To request, the start date must be today or later.')

'''
def _check_loan_period(user, items, start_date, end_date):
    lcs = _get_affected_loan_cycles(['finished', 'canceled'], items)
    requested_dates = _get_requested_dates(lcs)
    _start, _end = DateManager.get_contained_date(start_date, end_date,
                                                  requested_dates)
    available_start_date = _start
    desired_start_date = start_date

    available_end_date = _end
    desired_end_date = end_date

    avd_start_date = available_start_date != desired_start_date
    avd_end_date = available_end_date != desired_end_date
    if avd_start_date or avd_end_date:
        suggested_dates = DateManager.get_date_suggestions(requested_dates)
        contained_dates = (_start, _end)
        raise DateException(suggested_dates=suggested_dates,
                            contained_dates=contained_dates)
'''


def try_loan_items(user, items, start_date, end_date,
                   waitlist=False, delivery=None):
    exceptions = []
    try:
        _check_items(items)
    except Exception as e:
        exceptions.append(('items', e))

    try:
        check_field_in('current_status',
                       [CirculationItem.STATUS_ON_SHELF],
                       'The item is in the wrong status')(objs=items)
    except Exception as e:
        exceptions.append(('items_status', e))

    try:
        _check_user(user)
    except Exception as e:
        exceptions.append(('user', e))

    try:
        _check_loan_start(start_date)
    except Exception as e:
        exceptions.append(('start_date', e))

    try:
        _check_loan_duration(user, items, start_date, end_date)
    except Exception as e:
        exceptions.append(('duration', e))

    try:
        _check_loan_period(user, items, start_date, end_date)
    except DateException as e:
        exceptions.append(('date_suggestion', e))
    except Exception as e:
        exceptions.append(('date', e))

    if exceptions:
        raise ValidationExceptions(exceptions)


def loan_items(user, items, start_date, end_date,
               waitlist=False, delivery=None):
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
            if _start != desired_start_date:
                raise e
        else:
            raise e
    
    if delivery is None:
        delivery = CirculationLoanCycle.DELIVERY_DEFAULT
    group_uuid = str(uuid.uuid4())
    res = []
    for item in items:
        item.current_status = CirculationItem.STATUS_ON_LOAN
        item.save()
        current_status = CirculationLoanCycle.STATUS_ON_LOAN
        clc = CirculationLoanCycle.new(current_status=current_status,
                                       item_id=item.id, item=item,
                                       user_id=user.id, user=user,
                                       start_date=start_date,
                                       end_date=end_date,
                                       desired_start_date=desired_start_date,
                                       desired_end_date=desired_end_date,
                                       issued_date=datetime.datetime.now(),
                                       group_uuid=group_uuid,
                                       delivery=delivery)
        res.append(clc)

        create_event(user_id=user.id, item_id=item.id, loan_cycle_id=clc.id,
                     event=CirculationEvent.EVENT_CLC_CREATED_LOAN)

    email_notification('item_loan', 'john.doe@cern.ch', user.email,
                       name=user.name, action='loaned',
                       items=[x.record.title for x in items])

    return res


def try_request_items(user, items, start_date, end_date,
                      waitlist=False, delivery=None):
    exceptions = []
    try:
        _check_items(items)
    except Exception as e:
        exceptions.append(('items', e))

    try:
        check_field_in('current_status',
                       [CirculationItem.STATUS_ON_SHELF,
                        CirculationItem.STATUS_ON_LOAN],
                       'The item is in the wrong status')(objs=items)
    except Exception as e:
        exceptions.append(('items_status', e))

    try:
        _check_user(user)
    except Exception as e:
        exceptions.append(('user', e))

    try:
        _check_request_start(start_date)
    except Exception as e:
        exceptions.append(('start_date', e))

    try:
        _check_loan_duration(user, items, start_date, end_date)
    except Exception as e:
        exceptions.append(('duration', e))

    try:
        _check_loan_period(user, items, start_date, end_date)
    except DateException as e:
        exceptions.append(('date_suggestion', e))
    except Exception as e:
        exceptions.append(('date', e))

    if exceptions:
        raise ValidationExceptions(exceptions)


def request_items(user, items, start_date, end_date,
                  waitlist=False, delivery=None):
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

    if delivery is None:
        delivery = CirculationLoanCycle.DELIVERY_DEFAULT

    group_uuid = str(uuid.uuid4())
    res = []
    for item in items:
        current_status = CirculationLoanCycle.STATUS_REQUESTED
        clc = CirculationLoanCycle.new(current_status=current_status,
                                       item=item, user=user,
                                       start_date=start_date,
                                       end_date=end_date,
                                       desired_start_date=desired_start_date,
                                       desired_end_date=desired_end_date,
                                       issued_date=datetime.datetime.now(),
                                       group_uuid=group_uuid,
                                       delivery=delivery)
        res.append(clc)

        create_event(user_id=user.id, item_id=item.id, loan_cycle_id=clc.id,
                     event=CirculationEvent.EVENT_CLC_CREATED_REQUEST)

    email_notification('item_loan', 'john.doe@cern.ch', user.email,
                       name=user.name, action='requested',
                       items=[x.record.title for x in items])

    return res


def try_return_items(items):
    exceptions = []
    try:
        _check_items(items)
    except Exception as e:
        exceptions.append(('items', e))

    try:
        check_field_in('current_status',
                       [CirculationItem.STATUS_ON_LOAN],
                       'The item is in the wrong status')(objs=items)
    except Exception as e:
        exceptions.append(('items_status', e))

    if exceptions:
        raise ValidationExceptions(exceptions)


def return_items(items):
    try:
        try_return_items(items)
    except ValidationExceptions as e:
        raise e

    from invenio.modules.circulation.views.utils import send_signal
    from invenio.modules.circulation.signals import item_returned

    for item in items:
        item.current_status = CirculationItem.STATUS_ON_SHELF
        item.save()
        try:
            on_loan = CirculationLoanCycle.STATUS_ON_LOAN
            query = 'item_id:{0} current_status:{1}'.format(item.id, on_loan)
            clc = CirculationLoanCycle.search(query)[0]
            clc.current_status = CirculationLoanCycle.STATUS_FINISHED
            clc.save()
            update_waitlist(clc)
            create_event(user_id=clc.user.id, item_id=item.id,
                         loan_cycle_id=clc.id,
                         event=CirculationEvent.EVENT_CLC_FINISHED)

            send_signal(item_returned, None, item.id)
        except IndexError:
            # if the above fails, and no one returns on the signal, something
            # went wrong
            if not send_signal(item_returned, None, item.id):
                raise
