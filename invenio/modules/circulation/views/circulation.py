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

import invenio.modules.circulation.models as models

from flask import Blueprint, render_template, request, redirect
from invenio.modules.circulation.configs.config_utils import (
        ValidationExceptions)


blueprint = Blueprint('circulation', __name__, url_prefix='/circulation',
                      template_folder='../templates',
                      static_folder='../static')


@blueprint.route('/', methods=['GET'])
def circulation():
    start_date = datetime.date.today()
    end_date = start_date + datetime.timedelta(weeks=4)
    return render_template('circulation/circulation.html',
                           active_nav='circulation',
                           items=[], users=[], records=[],
                           start_date=start_date.isoformat(),
                           end_date=end_date.isoformat(),
                           loan=None,
                           request=None,
                           ret=None)


@blueprint.route('/circulation/<search_string>', methods=['GET'])
def circulation_search(search_string):
    (item_ids, user_ids, record_ids,
     start_date, end_date, search) = get_circulation_state(search_string)

    if search:
        item_ids += [x.id for x in models.CirculationItem.search(**search)]
        user_ids += [x.id for x in models.CirculationUser.search(**search)]
        record_ids += [str(x.id) for x
                       in models.CirculationRecord.search(**search)]

        new_url = ':'.join([','.join(item_ids),
                            ','.join(user_ids),
                            ','.join(record_ids),
                            start_date.isoformat(), end_date.isoformat(), ''])

        return redirect('/circulation/circulation/' + new_url)
    else:
        items = [models.CirculationItem.get(x) for x in item_ids]
        users = [models.CirculationUser.get(x) for x in user_ids]
        records = [models.CirculationRecord.get(x) for x in record_ids]

        res = circulation_try_actions(items, users, records,
                                      start_date, end_date)

        return render_template('circulation/circulation.html',
                               active_nav='circulation',
                               items=items, users=users, records=records,
                               start_date=start_date, end_date=end_date,
                               loan=res['loan'],
                               request=res['request'],
                               ret=res['return'])


def get_circulation_state(search_string):
    # <item_ids>-<user_ids>-<record_ids>-<s_date>-<e_date>-<search_string>
    (item_ids, user_ids, record_ids,
     start_date, end_date, search) = search_string.split(':', 5)

    item_ids = item_ids.split(',') if item_ids else []
    user_ids = user_ids.split(',') if user_ids else []
    record_ids = record_ids.split(',') if record_ids else []

    start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

    try:
        search = dict(part.split(':') for part in search.split(' '))
    except ValueError:
        search = {}

    return (item_ids, user_ids, record_ids, start_date, end_date, search)


def circulation_try_actions(items, users, records, start_date, end_date):
    res = {'loan': [], 'request': [], 'return': [],
           'record_items': {'loan': [], 'request': []}}

    if users and len(users) == 1:
        user = users[0]
        if items:
            for action in ['loan', 'request']:
                try:
                    user.validate_run(action,
                                      user=user, items=items,
                                      start_date=start_date, end_date=end_date)
                    res[action].append(True)
                except ValidationExceptions as e:
                    res[action].extend([(ex[0], str(ex[1]))
                                        for ex in e.exceptions])

        # Do some magic for the records...
        for record in records:
            _res = {'loan': [], 'request': []}
            for item in record.items:
                for action in ['loan', 'request']:
                    try:
                        user.validate_run(action,
                                          user=user, items=[item],
                                          start_date=start_date,
                                          end_date=end_date)
                        _res[action].append(True)
                        res['record_items'][action].append(item.id)
                    except ValidationExceptions as e:
                        _res[action].extend([(ex[0], str(ex[1]))
                                             for ex in e.exceptions])

            if True in _res['loan']:
                res['loan'].append(True)
            else:
                res['loan'].extend([("general", "The item can't be loaned.")])
            if True in _res['request']:
                res['request'].append(True)
            else:
                res['request'].extend([("general",
                                        "The item can't be requested.")])

    for item in items:
        try:
            item.validate_run('return', item=item)
            res['return'].append(True)
        except KeyError as e:
            res['return'].extend([("general", "The item can't be returned")])
        except ValidationExceptions as e:
            res['return'].extend([(ex[0], str(ex[1])) for ex in e.exceptions])

    def check(val):
        return map(lambda x: x is True, val)

    for x in ['loan', 'request', 'return']:
        res[x] = all(check(res[x])) if len(res[x]) > 0 else None

    return res


def get_valid_items_from_records(action, user, records, start_date, end_date):
    res = []
    for record in records:
        for item in record.items:
            try:
                user.validate_run(action,
                                  user=user, items=[item],
                                  start_date=start_date,
                                  end_date=end_date)
                res.append(item)
                break
            except Exception:
                pass
    return res


@blueprint.route('/api/circulation/run_action', methods=['POST'])
def api_circulation_run_action():
    data = json.loads(request.get_json())
    action = data['action']

    search_string = data['circulation_state']
    (item_ids, user_ids, record_ids,
     start_date, end_date, search) = get_circulation_state(search_string)

    if action == 'loan' or action == 'request':
        user = models.CirculationUser.get(user_ids[0])
        items = [models.CirculationItem.get(x) for x in item_ids]
        records = [models.CirculationRecord.get(x) for x in record_ids]

        items += get_valid_items_from_records(action, user, records,
                                              start_date, end_date)

        user.run(action,
                 user=user, items=items,
                 start_date=start_date, end_date=end_date)
    elif action == 'return':
        items = [models.CirculationItem.get(x) for x in item_ids]
        for item in items:
            item.run('return', item=item)

    return ('', 200)


def datetime_serial(obj):
    if isinstance(obj, datetime.date):
        return obj.isoformat()
