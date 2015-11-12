import datetime
import json

import invenio.modules.circulation.api as api
import invenio.modules.circulation.models as models
import invenio.modules.circulation.aggregators as aggrs

from invenio.modules.circulation.views.utils import (datetime_serial,
                                                     extract_params,
                                                     filter_params,
                                                     _get_cal_heatmap_dates,
                                                     _get_cal_heatmap_range)
from invenio.modules.circulation.api.utils import ValidationExceptions

from flask import Blueprint, render_template, flash


blueprint = Blueprint('user', __name__, url_prefix='/circulation',
                      template_folder='../templates',
                      static_folder='../static')


@blueprint.route('/user/<user_id>', methods=['GET'])
def users_current_holds(user_id):
    SL = models.CirculationLoanCycle.STATUS_ON_LOAN
    SR = models.CirculationLoanCycle.STATUS_REQUESTED
    current_loans = _get_current(user_id, SL)
    current_requests = _get_current(user_id, SR)

    editor_data = json.dumps(models.CirculationUser.get(user_id).jsonify(),
                             default=datetime_serial)
    editor_schema = json.dumps(aggrs.CirculationUserAggregator._json_schema,
                               default=datetime_serial)

    return render_template('user/current_holds.html',
                           editor_data=editor_data,
                           editor_schema=editor_schema,
                           current_loans=current_loans,
                           current_requests=current_requests)


def _get_current(user_id, status):
    def make_dict(clc):
        return {'clc': clc,
                'cal_data': json.dumps(_get_cal_heatmap_dates([clc.item])),
                'cal_range': _get_cal_heatmap_range([clc.item])}

    query = 'user_id:{0} current_status:{1}'.format(user_id, status)

    return [make_dict(clc) for clc
            in models.CirculationLoanCycle.search(query)]


@blueprint.route('/user/<user_id>/record/<record_id>', methods=['GET'])
@blueprint.route('/user/<user_id>/record/<record_id>/<state>', methods=['GET'])
def user_record_actions(user_id, record_id, state=None):
    #import ipdb; ipdb.set_trace()
    try:
        user = models.CirculationUser.get(user_id)
    except Exception:
        user = None
    record = models.CirculationRecord.get(record_id)

    start_date, end_date, waitlist, delivery = _get_state(state)

    record._items = _get_record_items(record_id, user,
                                      start_date, end_date,
                                      waitlist)

    cal_range = _get_cal_heatmap_range(x['item'] for x in record._items)
    cal_range = max(cal_range, (end_date.month - start_date.month + 1))

    return render_template('user/user_record_actions.html',
                           user=user, record=record,
                           start_date=start_date.isoformat(),
                           end_date=end_date.isoformat(),
                           waitlist=waitlist, delivery=delivery,
                           cal_range=cal_range, cal_data={})


def _get_state(state):
    if state:
        start_date, end_date, waitlist, delivery = state.split(':')
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        waitlist = True if waitlist == 'true' else False
    else:
        start_date = datetime.date.today()
        end_date = start_date + datetime.timedelta(weeks=4)
        waitlist = False
        delivery = 'Pick up'

    return start_date, end_date, waitlist, delivery


def _get_record_items(record_id, user, start_date, end_date, waitlist):
    items = []
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
                    warnings.append((category, exception.message))

        items.append({'item': item,
                      'request': request,
                      'cal_data': json.dumps(_get_cal_heatmap_dates([item])),
                      'cal_range': _get_cal_heatmap_range([item]),
                      'warnings': json.dumps(warnings)})

    return items


@blueprint.route('/api/user/run_action', methods=['POST'])
@extract_params
def run_action(action, user_id, item_id, clc_id, start_date, end_date,
               requested_end_date, waitlist, delivery):
    def _get_message(action):
        if action == 'lose':
            lm = 'The item: {0} was successfully reported as lost.'
            return lm.format(items[0].barcode)
        elif action == 'extension':
            em = 'Successfully requested an loan extension on item {0}.'
            return em.format(items[0].barcode)
        elif action == 'cancel':
            cm = 'The request on the item: {0} was successfully canceled.'
            return cm.format(clc.item.barcode)
        elif action == 'request':
            rm = 'The item: {0} were successfully requested by the user: {1}.'
            return rm.format(items[0].barcode, user.id)

    funcs = {'lose': api.item.lose_items,
             'extension': api.loan_cycle.loan_extension,
             'cancel': api.loan_cycle.cancel_clcs,
             'request': api.circulation.request_items}

    df = '%Y-%m-%d'
    dds = datetime.datetime.strptime

    user = models.CirculationUser.get(user_id) if user_id else None
    items = [models.CirculationItem.get(item_id)] if item_id else None
    clc = models.CirculationLoanCycle.get(clc_id) if clc_id else None
    start_date = dds(start_date, df).date() if start_date else None
    end_date = dds(end_date, df).date() if end_date else None
    requested_end_date = (dds(requested_end_date, df).date()
                          if requested_end_date else None)

    filter_params(funcs[action],
                  user=user, items=items, clcs=[clc],
                  start_date=start_date, end_date=end_date,
                  requested_end_date=requested_end_date,
                  waitlist=waitlist, delivery=delivery)

    flash(_get_message(action))
    return ('', 200)


@blueprint.route('/api/user/try_action', methods=['POST'])
@extract_params
def try_action(action, clc_id, requested_end_date):
    dds = datetime.datetime.strptime
    requested_end_date = dds(requested_end_date, "%Y-%m-%d").date()

    if action == 'extension':
        clcs = [models.CirculationLoanCycle.get(clc_id)]
        try:
            api.loan_cycle.try_loan_extension(clcs, requested_end_date)
            return json.dumps({'status': 200})
        except ValidationExceptions:
            pass
        return json.dumps({'status': 400})
