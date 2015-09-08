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

from flask import Blueprint, render_template, request
from invenio.modules.circulation.configs.config_utils import (
        ValidationExceptions)

from invenio.modules.circulation.circulation_lists import lists


blueprint = Blueprint('circulation', __name__, url_prefix='/circulation',
                      template_folder='templates', static_folder='static')


@blueprint.route('/', methods=['GET'])
def circulation():
    return render_template('circulation_circulation.html',
                           active_nav='circulation')


@blueprint.route('/lists')
def lists_overview():
    return render_template('circulation_lists.html',
                           active_nav='lists', lists=lists)


@blueprint.route('/lists/<list_link>')
def list_result(list_link):
    for name, link, clazz in lists:
        if link == list_link:
            break
    else:
        raise Exception('List unknown')

    res = clazz.run()
    return render_template(link+'.html', active_nav='lists', **res)


@blueprint.route('/entities')
def entities_overview():
    entities = [(name, link) for name, link, _ in models.entities]
    return render_template('circulation_entities_overview.html',
                           active_nav='entities', entities=entities)


@blueprint.route('/entities/<entity>')
def entities_hub(entity):
    return render_template('circulation_entities_hub.html',
                           active_nav='entities', entity=entity)


@blueprint.route('/entities/<entity>/<id>')
def entity(entity, id):
    return render_template('circulation_entities_detail.html',
                           active_nav='entities')


@blueprint.route('/entities/create/<entity>/')
def entity_new(entity):
    return render_template('circulation_entities_create.html',
                           active_nav='entities', obj='{}')


@blueprint.route('/api/entity/get', methods=['POST'])
def api_entity_get():
    data = json.loads(request.get_json())

    for name, link, clazz in models.entities:
        if link == data['entity']:
            break
    else:
        raise Exception('Unknown entity: {0}'.format(data['entity']))

    res = {'schema': clazz._json_schema,
           'data': clazz.get(data['id']).jsonify()}
    return json.dumps(res, default=datetime_serial)


@blueprint.route('/api/entity/get_functions', methods=['POST'])
def api_entity_get_functions():
    data = json.loads(request.get_json())

    for name, link, clazz in models.entities:
        if link == data['entity']:
            break
    else:
        raise Exception('Unknown entity: {0}'.format(data['entity']))

    funcs = [x for x in clazz.get(data['id']).get_available_functions()
             if x not in ['loan', 'request', 'return']]
    res = {'data': funcs}
    return json.dumps(res)


@blueprint.route('/api/entity/get_json_schema', methods=['POST'])
def api_entity_get_json_schema():
    data = json.loads(request.get_json())

    for name, link, clazz in models.entities:
        if link == data['entity']:
            break
    else:
        raise Exception('Unknown entity: {0}'.format(data['entity']))

    return json.dumps({'schema': clazz._json_schema})


@blueprint.route('/api/entity/run_action', methods=['POST'])
def api_entity_run_action():
    data = json.loads(request.get_json())

    for name, link, clazz in models.entities:
        if link == data['entity']:
            break
    else:
        raise Exception('Unknown entity: {0}'.format(data['entity']))

    obj = clazz.get(data['id'])
    func = data['function']
    params = {obj.get_function_parameters(func)[0]: obj}
    obj.run(func, **params)
    return ('', 200)


@blueprint.route('/api/entity/search', methods=['POST'])
def api_entity_search():
    data = json.loads(request.get_json())

    for name, link, clazz in models.entities:
        if link == data['entity']:
            break
    else:
        raise Exception('Unknown entity: {0}'.format(data['entity']))

    if data['search']:
        objs = clazz.search(**data['search'])
    else:
        objs = clazz.get_all()

    return json.dumps([x.jsonify() for x in objs], default=datetime_serial)


@blueprint.route('/api/entity/create', methods=['POST'])
def api_entity_create():
    data = json.loads(request.get_json())
    for name, link, clazz in models.entities:
        if link == data['entity']:
            break
    else:
        raise Exception('Unknown entity: {0}'.format(data['entity']))

    clazz.new(**data['data'])
    return ('', 200)


@blueprint.route('/api/entity/update', methods=['POST'])
def api_entity_update():
    data = json.loads(request.get_json())
    id = data['id']
    entity = data['entity']
    data = data['data']

    for name, link, clazz in models.entities:
        if link == entity:
            break
    else:
        raise Exception('Unknown entity: {0}'.format(entity))

    obj = clazz.get(id)

    change = False
    for key, value in data.items():
        try:
            if obj.__getattribute__(key) != value:
                obj.__setattr__(key, value)
                change = True
        except AttributeError:
            obj.__setattr__(key, value)

    if change:
        obj.save()

    return ('', 200)


@blueprint.route('/api/entity/delete', methods=['POST'])
def api_entity_delete():
    data = json.loads(request.get_json())
    id = data['id']
    entity = data['entity']

    clazz = get_circulation_class(entity)
    obj = clazz.get(id)
    obj.delete()

    return ('', 200)


@blueprint.route('/api/circulation/search', methods=['POST'])
def api_circulation_search():
    data = json.loads(request.get_json())
    res = {'user': None, 'items': None, 'records': None}

    if data['search']:
        res['user'] = [x.jsonify() for x
                       in models.CirculationUser.search(**data['search'])]
        res['items'] = [x.jsonify() for x
                        in models.CirculationItem.search(**data['search'])]
        res['records'] = [x.jsonify() for x
                          in models.CirculationRecord.search(**data['search'])]

        res['user_schema'] = models.CirculationUser._json_schema
        res['item_schema'] = models.CirculationItem._json_schema
        res['record_schema'] = models.CirculationRecord._json_schema

    return json.dumps(res, default=datetime_serial)


@blueprint.route('/api/circulation/try_actions', methods=['POST'])
def api_circulation_try_actions():
    data = json.loads(request.get_json())

    users = [models.CirculationUser.get(x['id']) for x in data['user']]
    items = [models.CirculationItem.get(x['id']) for x in data['items']]
    records = [models.CirculationRecord.get(x['id']) for x in data['records']]
    start_date = data['start_date']
    start_date = datetime.datetime.strptime(start_date, '%d/%m/%Y').date()
    end_date = data['end_date']
    end_date = datetime.datetime.strptime(end_date, '%d/%m/%Y').date()

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
            _items = models.CirculationItem.search(record=record.id)

            _res = {'loan': [], 'request': []}
            for item in _items:
                found = False
                for action in ['loan', 'request']:
                    try:
                        user.validate_run(action,
                                          user=user, items=[item],
                                          start_date=start_date,
                                          end_date=end_date)
                        _res[action].append(True)
                        res['record_items'][action].append(item.id)
                        found = True
                    except ValidationExceptions as e:
                        _res[action].extend([(ex[0], str(ex[1]))
                                             for ex in e.exceptions])

                if found:
                    break

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

    return json.dumps(res, default=datetime_serial)


@blueprint.route('/api/circulation/run_action', methods=['POST'])
def api_circulation_run_action():
    data = json.loads(request.get_json())
    action = data['action']
    if action == 'loan' or action == 'request':
        user = models.CirculationUser.get(data['user'])
        items = [models.CirculationItem.get(x) for x in data['items']]
        start_date = data['start_date']
        start_date = datetime.datetime.strptime(start_date, '%d/%m/%Y').date()
        end_date = data['end_date']
        end_date = datetime.datetime.strptime(end_date, '%d/%m/%Y').date()

        user.run(action,
                 user=user, items=items,
                 start_date=start_date, end_date=end_date)
    elif action == 'return':
        items = [models.CirculationItem.get(x) for x in data['items']]
        for item in items:
            item.run('return', item=item)

    return ('', 200)


def get_circulation_class(entity):
    entity = ''.join(x.title() for x in entity.split('_'))
    return models.__getattribute__('Circulation' + entity)


def datetime_serial(obj):
    if isinstance(obj, datetime.date):
        return obj.isoformat()
