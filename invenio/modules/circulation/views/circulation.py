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

from invenio.modules.circulation.views.utils import (get_date_period,
                                                     filter_params,
                                                     _get_cal_heatmap_dates,
                                                     send_signal,
                                                     flatten)
from invenio.modules.circulation.config import DEFAULT_LOAN_PERIOD


blueprint = Blueprint('circulation', __name__, url_prefix='/circulation',
                      template_folder='../templates',
                      static_folder='../static')


@blueprint.route('/', methods=['GET'])
@blueprint.route('/circulation/<search_string>', methods=['GET'])
def circulation_search(search_string=None):
    (item_ids, user_ids, record_ids,
     start_date, end_date,
     waitlist, delivery, search) = _get_circulation_state(search_string)

    data = {'item_ids': item_ids, 'user_ids': user_ids,
            'record_ids': record_ids,
            'start_date': start_date, 'end_date': end_date,
            'waitlist': waitlist, 'delivery': delivery, 'search': search}

    if search:
        from invenio.modules.circulation.signals import circulation_search

        res = send_signal(circulation_search, 'circulation_search', data)
        for u, i, r in res:
            user_ids += [str(x.id) for x in u]
            item_ids += [str(x.id) for x in i]
            record_ids += [str(x.id) for x in r]

        new_url = _build_circulation_state(item_ids, user_ids, record_ids,
                                           start_date, end_date,
                                           waitlist, delivery, '')

        return redirect('/circulation/circulation/' + new_url)
    else:
        from invenio.modules.circulation.signals import (
                circulation_state,
                circulation_actions)

        users, items, records = [], [], []

        res = send_signal(circulation_state, 'circulation_state', data)
        for u, i, r in res:
            users += u
            items += i
            records += r

        circ_actions = flatten(send_signal(circulation_actions,
                                           'circulation_actions', None))

        _user = users[0] if (users and len(users) == 1) else users

        _res = {}
        for name, action in circ_actions:
            _res[action] = _try_action(
                    action,
                    user=_user, items=items, records=records,
                    start_date=start_date, end_date=end_date,
                    waitlist=waitlist, delivery=delivery)

        action_buttons = _get_action_buttons(circ_actions, _res)

        item_warnings = _get_warnings(_res, ['items_status'])
        date_warnings = _get_warnings(_res, ['start_date', 'date_suggestion'])

        global_cal_data = json.dumps(_get_cal_heatmap_dates(items))
        global_cal_range = _get_global_cal_range(items, end_date)

        return render_template('circulation/circulation.html',
                               active_nav='circulation',
                               items=items, users=users, records=records,
                               start_date=start_date, end_date=end_date,
                               action_buttons=action_buttons,
                               cal_data=global_cal_data,
                               cal_range=global_cal_range,
                               waitlist=waitlist, delivery=delivery,
                               item_warnings=item_warnings,
                               date_warnings=date_warnings)


def _try_action(action, **kwargs):
    from invenio.modules.circulation.signals import try_action_signal

    return send_signal(try_action_signal, action, kwargs)[0]


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
    res = []
    for action, messages in _res.items():
        try:
            for category, message in messages:
                if category in categories:
                    res.append((action, message))
        except TypeError:
            pass

    return res


def _get_action_buttons(actions, _res):
    def _check(val):
        ignore = [('items', 'A item is required to loan an item.'),
                  ('user', 'A user is required to loan an item.')]
        for x in val:
            if x in ignore:
                return None

        return all(map(lambda x: x is True, val))

    res = []
    for name, action in actions:
        status = _res[action]
        if status is True or status is False or status is None:
            val = status
        else:
            val = _check(status) if len(status) > 0 else None
        res.append({'name': name, 'val': val, 'action': action})

    return res


def _build_circulation_state(item_ids, user_ids, record_ids,
                             start_date, end_date, waitlist, delivery, search):
    return ':'.join([','.join(item_ids),
                     ','.join(user_ids),
                     ','.join(record_ids),
                     start_date.isoformat(), end_date.isoformat(),
                     str(waitlist), delivery, search])


def _get_circulation_state(search_string):
    # <item_ids>:<user_ids>:<record_ids>:<s_date>:<e_date>:<waitlist>:<delivery>:<search_string>
    if not search_string:
        start_date, end_date = get_date_period(datetime.date.today(),
                                               DEFAULT_LOAN_PERIOD)
        return [], [], [], start_date, end_date, False, 'Pick up', ''

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


@blueprint.route('/api/circulation/run_action', methods=['POST'])
def api_circulation_run_action():
    from invenio.modules.circulation.signals import (run_action_signal,
                                                     convert_params) 

    data = json.loads(request.get_json())

    res = send_signal(convert_params, data['action'], data)
    for key, value in reduce(lambda x, y: dict(x, **y), res):
        data[key] = value

    message = send_signal(run_action_signal, data['action'], data)[0]

    flash(message)
    return ('', 200)
