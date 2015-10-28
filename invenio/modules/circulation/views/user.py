import datetime
import json

import invenio.modules.circulation.api as api
import invenio.modules.circulation.models as models
import invenio.modules.circulation.aggregators as aggregators

from invenio.modules.circulation.views.utils import (datetime_serial,
                                                     extract_params)
from invenio.modules.circulation.api.utils import ValidationExceptions

from flask import Blueprint, render_template, request, flash


blueprint = Blueprint('user', __name__, url_prefix='/circulation',
                      template_folder='../templates',
                      static_folder='../static')


@blueprint.route('/user/<user_id>', methods=['GET'])
def users_current_holds(user_id):
    query = 'user:{0} current_status:{{0}}'.format(user_id)

    _query = query.format(models.CirculationLoanCycle.STATUS_ON_LOAN)
    _current_loans = models.CirculationLoanCycle.search(_query)
    current_loans = []
    for clc in _current_loans:
        tmp = {'clc': clc,
               'cal_data': json.dumps(_get_cal_heatmap_dates([clc.item])),
               'cal_range': _get_cal_heatmap_range([clc.item])}
        current_loans.append(tmp)


    _query = query.format(models.CirculationLoanCycle.STATUS_REQUESTED)
    _current_requests = models.CirculationLoanCycle.search(_query)
    current_requests = []
    for clc in _current_requests:
        tmp = {'clc': clc,
               'cal_data': json.dumps(_get_cal_heatmap_dates([clc.item])),
               'cal_range': _get_cal_heatmap_range([clc.item])}
        current_requests.append(tmp)

    editor_data = json.dumps(models.CirculationUser.get(user_id).jsonify(),
                             default=datetime_serial)
    editor_schema = json.dumps(aggregators.CirculationUserAggregator._json_schema,
                               default=datetime_serial)

    return render_template('user/current_holds.html',
                           editor_data=editor_data,
                           editor_schema=editor_schema,
                           current_loans=current_loans,
                           current_requests=current_requests)


def _get_cal_heatmap_dates(items):
    def to_seconds(date):
        return int(date.strftime("%s"))

    def get_date_range(start_date, end_date):
        delta = (end_date - start_date).days
        res = []
        for day in range(delta+1):
            res.append(start_date + datetime.timedelta(days=day))
        return res

    for item in items:
        query = 'item:{0}'.format(item.id)
        res = set() 
        for clc in models.CirculationLoanCycle.search(query):
            date_range = get_date_range(clc.start_date, clc.end_date)
            for date in date_range:
                res.add((str(to_seconds(date)), 1))

        return dict(res)


def _get_cal_heatmap_range(items):
    min_dates = []
    max_dates = []
    for item in items:
        query = 'item:{0}'.format(item.id)
        clcs = models.CirculationLoanCycle.search(query)
        if not clcs:
            continue
        min_dates.append(min(clc.start_date for clc in clcs))
        max_dates.append(max(clc.end_date for clc in clcs))

    if not min_dates or not max_dates:
        return 0

    return min(max_dates).month - max(min_dates).month + 1


@blueprint.route('/user/<user_id>/record/<record_id>', methods=['GET'])
@blueprint.route('/user/<user_id>/record/<record_id>/<state>', methods=['GET'])
def user_record_actions(user_id, record_id, state=None):
    user = models.CirculationUser.get(user_id)
    record = models.CirculationRecord.get(record_id)
    record._items = []
    if state:
        start_date, end_date, waitlist, delivery = state.split(':')
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        waitlist = True if waitlist == 'true' else False
    else:
        start_date = datetime.date.today()
        end_date = start_date + datetime.timedelta(weeks=4)
        waitlist = False
        delivery = 'Pick Up'

    query = 'record_id:{0}'.format(record_id)
    for item in models.CirculationItem.search(query):
        warnings = []
        try:
            api.circulation.try_request_items(user=user, items=[item],
                                              start_date=start_date,
                                              end_date=end_date,
                                              waitlist=waitlist)
            request = True
        except ValidationExceptions as e:
            exceptions = [x[0] for x in e.exceptions]
            if exceptions == ['date_suggestion'] and waitlist:
                request = True
            else:
                request = False
                for category, exception in e.exceptions:
                    category = '{0}-{1}'.format(item.barcode, category)
                    warnings.append((category, exception.message))

        record._items.append({'item': item,
                              'request': request,
                              'cal_data': json.dumps(_get_cal_heatmap_dates([item])),
                              'cal_range': _get_cal_heatmap_range([item]),
                              'warnings': json.dumps(warnings)})

    cal_range = _get_cal_heatmap_range(x['item'] for x in record._items)
    cal_range = max(cal_range, (end_date.month - start_date.month + 1))

    return render_template('user/user_record_actions.html',
                           user=user, record=record,
                           start_date=start_date.isoformat(),
                           end_date=end_date.isoformat(),
                           waitlist=waitlist, delivery=delivery,
                           cal_range=cal_range, cal_data={})


@blueprint.route('/api/user/run_action', methods=['POST'])
def run_action():
    funcs = {'lose': api.item.lose_items,
             'extension': api.loan_cycle.loan_extension,
             'cancel': api.loan_cycle.cancel_clcs,
             'request': api.circulation.request_items}
    data = json.loads(request.get_json())

    if data['type'] == 'item':
        if data['action'] == 'lose':
            items = [models.CirculationItem.get(data['item_id'])]
            func = funcs[data['action']]
            func(items)
            msg = 'The item: {0} was successfully reported as lost.'
            msg = msg.format(', '.join(x.barcode for x in items))
        elif data['action'] == 'request':
            user = models.CirculationUser.get(data['user_id'])
            items = [models.CirculationItem.get(data['item_id'])]
            func = funcs[data['action']]
            start_date = datetime.datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(data['end_date'], '%Y-%m-%d').date()
            func(user, items, start_date, end_date)
            msg = 'The item: {0} was successfully requested.'
            msg = msg.format(', '.join(x.barcode for x in items), user.ccid)
    elif data['type'] == 'clc':
        if data['action'] == 'cancel':
            clc = models.CirculationLoanCycle.get(data['clc_id'])
            func = funcs[data['action']]
            func([clc])
            msg = 'The request on the item: {0} was successfully canceled.'
            msg = msg.format(clc.item.barcode)
        elif data['action'] == 'extension':
            clc = models.CirculationLoanCycle.get(data['clc_id'])
            func = funcs[data['action']]
            func([clc])
            msg = 'Successfully requested an loan extension on item {0}.'
            msg = msg.format(clc.item.barcode)

    flash(msg)
    return ('', 200)

@blueprint.route('/api/user/run_current_hold_action', methods=['POST'])
@extract_params
def run_current_hold_action(action, clc_id, requested_end_date):
    funcs = {'loss': api.item.lose_items,
             'extension': api.loan_cycle.loan_extension,
             'cancel': api.loan_cycle.cancel_clcs}
    clc = models.CirculationLoanCycle.get(clc_id)

    if action == 'extension':
        requested_end_date = datetime.datetime.strptime(requested_end_date, "%Y-%m-%d").date()

        funcs[action]([clc], requested_end_date)
        msg = 'Successfully extended the loan for item {0} until {1}.'
        msg = msg.format(clc.item.barcode, requested_end_date)
    elif action == 'loss':
        funcs[action]([clc.item])
        msg = 'The item: {0} was successfully reported as lost.'
        msg = msg.format(clc.item.barcode)
    elif action == 'cancel':
        funcs[action]([clc])
        msg = 'The request on the item: {0} was successfully canceled.'
        msg = msg.format(clc.item.barcode)

    flash(msg)
    return ('', 200)


@blueprint.route('/api/user/try_action', methods=['POST'])
@extract_params
def try_action(action, clc_id, requested_end_date):
    requested_end_date = datetime.datetime.strptime(requested_end_date, "%Y-%m-%d").date()

    if action == 'extension':
        clcs = [models.CirculationLoanCycle.get(clc_id)]
        try:
            api.loan_cycle.try_loan_extension(clcs, requested_end_date)
            return json.dumps({'status': 200})
        except ValidationExceptions as e:
            pass
        return json.dumps({'status': 400})
