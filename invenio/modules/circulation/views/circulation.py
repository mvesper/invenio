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


blueprint = Blueprint('circulation', __name__, url_prefix='/circulation',
                      template_folder='../templates',
                      static_folder='../static')


@blueprint.route('/', methods=['GET'])
def circulation():
    start_date = datetime.date.today()
    end_date = start_date + datetime.timedelta(weeks=4)

    cal_data = json.dumps({})
    cal_range = 4
    return render_template('circulation/circulation.html',
                           active_nav='circulation',
                           items=[], users=[], records=[],
                           start_date=start_date.isoformat(),
                           end_date=end_date.isoformat(),
                           loan=None,
                           request=None,
                           ret=None,
                           cal_data=cal_data, cal_range=cal_range,
                           waitlist=False, delivery='Pick up')


@blueprint.route('/circulation/<search_string>', methods=['GET'])
def circulation_search(search_string):
    (item_ids, user_ids, record_ids,
     start_date, end_date,
     waitlist, delivery, search) = get_circulation_state(search_string)

    search = ' '.join('{0}:{1}'.format(key, value) for key, value in search.items())

    if search:
        item_ids += [str(x.id) for x in
                     models.CirculationItem.search(search)]
        user_ids += [str(x.id) for x in
                     models.CirculationUser.search(search)]
        record_ids += [str(x.id) for x
                       in models.CirculationRecord.search(search)]

        new_url = ':'.join([','.join(item_ids),
                            ','.join(user_ids),
                            ','.join(record_ids),
                            start_date.isoformat(),
                            end_date.isoformat(),
                            str(waitlist), delivery, ''])

        return redirect('/circulation/circulation/' + new_url)
    else:
        items = [models.CirculationItem.get(x) for x in item_ids]
        users = [models.CirculationUser.get(x) for x in user_ids]
        records = [models.CirculationRecord.get(x) for x in record_ids]

        q = 'record_id:{0}'
        for record in records:
            # TODO: kinda ugly to get the items like that
            record.items = models.CirculationItem.search(q.format(record.id))
            for item in record.items:
                item.cal_data = json.dumps(_get_cal_heatmap_dates([item]))
                item.cal_range = _get_cal_heatmap_range([item])

        # TODO
        _users = users[0] if (users and len(users) == 1) else users
        _res = circulation_try_actions(items, _users, records,
                                       start_date, end_date)

        def check(val):
            return map(lambda x: x is True, val)

        res = {}
        for key, value in _res.items():
            res[key] = all(check(value)) if len(value) > 0 else None

        for key, value in _res.items():
            if all(check(value)):
                del _res[key]

        item_warnings = []
        for action, messages in _res.items():
            for category, message in messages:
                if category in ['items_status']:
                    item_warnings.append((action, message))

        date_warnings = []
        for action, messages in _res.items():
            for category, message in messages:
                if category in ['start_date', 'date_suggestion']:
                    date_warnings.append((action, message))
            

        """
        if users and len(users) == 1:
            res = circulation_try_actions(items, users[0], records,
                                          start_date, end_date)
        else:
            res = {'loan': [], 'request': [], 'return': []}
        """

        cal_data = json.dumps(_get_cal_heatmap_dates(items))
        try:
            latest_end_date = max(_get_latest_end_date(items))
        except ValueError:
            latest_end_date = end_date
        latest_end_date = max(latest_end_date, end_date)
        cal_range = latest_end_date.month - datetime.date.today().month + 1

        return render_template('circulation/circulation.html',
                               active_nav='circulation',
                               items=items, users=users, records=records,
                               start_date=start_date, end_date=end_date,
                               loan=res['loan'],
                               request=res['request'],
                               ret=res['return'],
                               cal_data=cal_data, cal_range=cal_range,
                               waitlist=waitlist, delivery=delivery,
                               item_warnings=item_warnings,
                               date_warnings=date_warnings)


def _get_latest_end_date(items):
    query = 'item:{0}'
    return [x.end_date for item in items
            for x in models.CirculationLoanCycle.search(query.format(item.id))]


def _get_cal_heatmap_dates(items):
    def to_seconds(date):
        return int(date.strftime("%s"))

    def get_date_range(start_date, end_date):
        delta = (end_date - start_date).days
        res = []
        for day in range(delta+1):
            res.append(start_date + datetime.timedelta(days=day))
        return res

    res = set() 
    for item in items:
        query = 'item:{0}'.format(item.id)
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


def get_circulation_state(search_string):
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

    try:
        search = dict(part.split(':') for part in search.split(' '))
    except ValueError:
        search = {}

    return (item_ids, user_ids, record_ids,
            start_date, end_date, waitlist, delivery, search)


def circulation_try_actions(items, user, records, start_date, end_date):
    res = {'loan': [], 'request': [], 'return': []}
    funcs = {'loan': api.try_loan_items, 'request': api.try_request_items}

    if items:
        for key, func in funcs.items():
            try:
                func(user, items, start_date, end_date)
                res[key].append(True)
            except ValidationExceptions as e:
                res[key].extend([(ex[0], str(ex[1])) for ex in e.exceptions])

        try:
            api.try_return_items(items)
            res['return'].append(True)
        except ValidationExceptions as e:
            res['return'].extend([(ex[0], str(ex[1])) for ex in e.exceptions])

    """
    # Do some magic for the records...
    for record in records:
        _res = {'loan': [], 'request': []}
        for item in record.items:
            for key, func in funcs.items():
                try:
                    func(user, [item], start_date, end_date)
                    _res[key].append(True)
                except ValidationExceptions as e:
                    _res[key].extend([(ex[0], str(ex[1]))
                                      for ex in e.exceptions])

        for key in funcs.keys():
            if True in _res[key]:
                res[key].append(True)
            else:
                res[key].extend([("general", "The item can't be loaned.")])
    """

    """
    def check(val):
        return map(lambda x: x is True, val)

    for key, value in res.items():
        res[key] = all(check(value)) if len(value) > 0 else None
    """

    return res


"""
def get_valid_items_from_records(action, user, records, start_date, end_date):
    funcs = {'loan': api.try_loan_items, 'request': api.try_request_items}

    res = []
    for record in records:
        for item in record.items:
            try:
                funcs[action](user, [item], start_date, end_date)
                res.append(item)
                break
            except Exception:
                pass
    return res
"""


@blueprint.route('/api/circulation/run_action', methods=['POST'])
def api_circulation_run_action():
    funcs = {'loan': api.loan_items,
             'request': api.request_items,
             'return': api.return_items}
    data = json.loads(request.get_json())

    action, search_string = itemgetter('action', 'circulation_state')(data)

    (item_ids, user_ids, record_ids,
     start_date, end_date,
     waitlist, delivery, search) = get_circulation_state(search_string)

    if action in ['loan', 'request']:
        user = models.CirculationUser.get(user_ids[0])
        records = [models.CirculationRecord.get(x) for x in record_ids]
        items = [models.CirculationItem.get(x) for x in item_ids]
        """
        items += get_valid_items_from_records(action, user, records,
                                              start_date, end_date)
        """

        funcs[action](user, items, start_date, end_date)
        msg = 'The item(s): {0} were successfully loaned to the user: {1}.'
        msg = msg.format(', '.join(x.barcode for x in items), user.ccid)
    elif action == 'return':
        items = [models.CirculationItem.get(x) for x in item_ids]
        funcs[action](items)
        msg = 'The item(s): {0} where successfully returned.'
        msg = msg.format(', '.join(x.barcode for x in items))

    flash(msg)
    return ('', 200)


def datetime_serial(obj):
    if isinstance(obj, datetime.date):
        return obj.isoformat()
