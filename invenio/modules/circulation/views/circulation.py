# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Circulation interface."""

import datetime
import json

import invenio.modules.circulation.api.circulation as api
import invenio.modules.circulation.models as models

from operator import itemgetter
from flask import Blueprint, render_template, request, redirect, flash

from invenio.modules.circulation.api.utils import ValidationExceptions
from invenio.modules.circulation.views.utils import (get_date_period,
                                                     filter_params,
                                                     _get_cal_heatmap_dates,
                                                     _get_cal_heatmap_range)
from invenio.modules.circulation.config import DEFAULT_LOAN_PERIOD


blueprint = Blueprint('circulation', __name__, url_prefix='/circulation',
                      template_folder='../templates',
                      static_folder='../static')


@blueprint.route('/', methods=['GET'])
def circulation():
    start_date, end_date = get_date_period(datetime.date.today(),
                                           DEFAULT_LOAN_PERIOD)

    return render_template('circulation/circulation.html',
                           active_nav='circulation',
                           items=[], users=[], records=[],
                           start_date=start_date.isoformat(),
                           end_date=end_date.isoformat(),
                           loan=None, request=None, ret=None,
                           cal_data=json.dumps({}), cal_range=4,
                           waitlist=False, delivery='Pick up')


@blueprint.route('/circulation/<search_string>', methods=['GET'])
def circulation_search(search_string):
    (item_ids, user_ids, record_ids,
     start_date, end_date,
     waitlist, delivery, search) = _get_circulation_state(search_string)

    if search:
        user_ids += [str(x.id) for x in
                     models.CirculationUser.search(search)]
        item_tmp = [str(x.id) for x in
                    models.CirculationItem.search(search)]
        record_tmp = [str(x.id) for x
                      in models.CirculationRecord.search(search)]

        # If the search returns results for items and records, the records
        # are prefered
        item_tmp = [] if item_tmp and record_tmp else item_tmp

        item_ids += item_tmp
        record_ids += record_tmp

        new_url = _build_circulation_state(item_ids, user_ids, record_ids,
                                           start_date, end_date,
                                           waitlist, delivery, '')

        return redirect('/circulation/circulation/' + new_url)
    else:
        items = [models.CirculationItem.get(x) for x in item_ids]
        users = [models.CirculationUser.get(x) for x in user_ids]
        records = [models.CirculationRecord.get(x) for x in record_ids]

        _enhance_record_data(records)

        _users = users[0] if (users and len(users) == 1) else users
        _res = _circulation_try_actions(items, _users, records,
                                        start_date, end_date, waitlist)

        action_button_states = _get_action_button_state(_res)
        _res = _remove_valid_actions(_res)

        item_warnings = _get_warnings(_res, ['items_status'])
        date_warnings = _get_warnings(_res, ['start_date', 'date_suggestion'])

        global_cal_data = json.dumps(_get_cal_heatmap_dates(items))
        global_cal_range = _get_global_cal_range(items, end_date)

        return render_template('circulation/circulation.html',
                               active_nav='circulation',
                               items=items, users=users, records=records,
                               start_date=start_date, end_date=end_date,
                               loan=action_button_states['loan'],
                               request=action_button_states['request'],
                               ret=action_button_states['return'],
                               cal_data=global_cal_data,
                               cal_range=global_cal_range,
                               waitlist=waitlist, delivery=delivery,
                               item_warnings=item_warnings,
                               date_warnings=date_warnings)


def _check(val):
    return map(lambda x: x is True, val)


def _get_global_cal_range(items, end_date):
    def _get_latest_end_date(items):
        query = 'item_id:{0}'
        return [x.end_date for item in items
                for x
                in models.CirculationLoanCycle.search(query.format(item.id))]
    try:
        latest_end_date = max(_get_latest_end_date(items))
    except ValueError:
        latest_end_date = end_date
    latest_end_date = max(latest_end_date, end_date)
    return latest_end_date.month - datetime.date.today().month + 1


def _get_warnings(_res, categories):
    return [(action, message) for action, messages in _res.items()
            for category, message in messages if category in categories]


def _remove_valid_actions(_res):
    return {key: value for key, value in _res.items()
            if not all(_check(value))}


def _get_action_button_state(_res):
    return {key: (all(_check(value)) if len(value) > 0 else None)
            for key, value in _res.items()}


def _enhance_record_data(records):
    q = 'record_id:{0}'
    for record in records:
        record.items = models.CirculationItem.search(q.format(record.id))
        for item in record.items:
            item.cal_data = json.dumps(_get_cal_heatmap_dates([item]))
            item.cal_range = _get_cal_heatmap_range([item])


def _build_circulation_state(item_ids, user_ids, record_ids,
                             start_date, end_date, waitlist, delivery, search):
    return ':'.join([','.join(item_ids),
                     ','.join(user_ids),
                     ','.join(record_ids),
                     start_date.isoformat(), end_date.isoformat(),
                     str(waitlist), delivery, search])


def _get_circulation_state(search_string):
    # <item_ids>:<user_ids>:<record_ids>:<s_date>:<e_date>:<waitlist>:<delivery>:<search_string>
    (item_ids, user_ids, record_ids,
     start_date, end_date,
     waitlist, delivery, search) = search_string.split(':', 7)

    item_ids = item_ids.split(',') if item_ids else []
    user_ids = user_ids.split(',') if user_ids else []
    record_ids = record_ids.split(',') if record_ids else []

    start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

    waitlist = True if waitlist.lower() == 'true' else False

    return (item_ids, user_ids, record_ids,
            start_date, end_date, waitlist, delivery, search)


def _circulation_try_actions(items, user, records,
                             start_date, end_date, waitlist):
    res = {'loan': [], 'request': [], 'return': []}
    funcs = {'loan': api.try_loan_items, 'request': api.try_request_items,
             'return': api.try_return_items}

    if items:
        for key, func in funcs.items():
            try:
                filter_params(func, user=user, items=items,
                              start_date=start_date, end_date=end_date,
                              waitlist=waitlist, delivery=None)
                res[key].append(True)
            except ValidationExceptions as e:
                res[key].extend([(ex[0], str(ex[1])) for ex in e.exceptions])

    return res


@blueprint.route('/api/circulation/run_action', methods=['POST'])
def api_circulation_run_action():
    def _get_message(action):
        if action == 'loan':
            lm = 'The item(s): {0} were successfully loaned to the user: {1}.'
            return lm.format(', '.join(x.barcode for x in items), user.ccid)
        elif action == 'request':
            rm = 'The item(s): {0} were successfully requested by the user: {1}.'
            return rm.format(', '.join(x.barcode for x in items), user.ccid)
        elif action == 'return':
            rm = 'The item(s): {0} where successfully returned.'
            return rm.format(', '.join(x.barcode for x in items))

    funcs = {'loan': api.loan_items,
             'request': api.request_items,
             'return': api.return_items}
    data = json.loads(request.get_json())

    action, search_string = itemgetter('action', 'circulation_state')(data)

    (item_ids, user_ids, record_ids,
     start_date, end_date,
     waitlist, delivery, search) = _get_circulation_state(search_string)

    user = models.CirculationUser.get(user_ids[0]) if user_ids else None
    items = [models.CirculationItem.get(x) for x in item_ids]

    filter_params(funcs[action],
                  user=user, items=items,
                  start_date=start_date, end_date=end_date,
                  waitlist=waitlist, delivery=delivery)

    flash(_get_message(action))
    return ('', 200)
