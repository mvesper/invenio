import datetime
import json

import invenio.modules.circulation.api as api
import invenio.modules.circulation.models as models

from flask import Blueprint, render_template, request, flash


blueprint = Blueprint('user', __name__, url_prefix='/circulation',
                      template_folder='../templates',
                      static_folder='../static')


@blueprint.route('/user/<user_id>', methods=['GET'])
def users_current_holds(user_id):
    current_loans = models.CirculationLoanCycle.search(user=user_id,
            current_status='on_loan')
    current_requests = models.CirculationLoanCycle.search(user=user_id,
            current_status='requested')
    aggregated = {'additions': {'current_loans': current_loans,
                                'current_requests': current_requests}}
    return render_template('user/current_holds.html',
                           aggregated=aggregated)


@blueprint.route('/user/<user_id>/record/<record_id>', methods=['GET'])
def user_record_actions(user_id, record_id):
    user = models.CirculationUser.get(user_id)
    record = models.CirculationRecord.get(record_id)
    start_date = datetime.date.today()
    end_date = start_date + datetime.timedelta(weeks=4)
    record._items = []
    for item in models.CirculationItem.search(record_id=record_id):
        request = try_action(api.circulation.try_loan_items, user=user, items=[item],
                             start_date=start_date, end_date=end_date)
        record._items.append({'item': item,
                              'request': request})
    return render_template('user/user_record_actions.html',
                           user=user, record=record,
                           start_date=start_date.isoformat(),
                           end_date=end_date.isoformat())


def try_action(func, **kwargs):
    try:
        func(**kwargs)
        return True
    except Exception:
        return False


@blueprint.route('/api/user/run_action', methods=['POST'])
def run_action():
    funcs = {'lose': api.item.lose_items,
             'extension': api.loan_cycle.request_loan_extension,
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
