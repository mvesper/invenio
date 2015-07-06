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

import json

from flask import Blueprint, render_template, request 

import invenio.modules.circulation.api as api

import invenio.modules.circulation.models as models

blueprint = Blueprint('circulation', __name__, url_prefix='/circulation',
                      template_folder='templates', static_folder='static')


@blueprint.route('/', methods=['GET'])
def circulation():
    return render_template('circulation_circulation.html',
                           active_nav='circulation')

@blueprint.route('/', methods=['POST'])
def circulation_specific():
    data = json.loads(request.get_json())
    res = api.search(data.get('search'))
    data['users'] += [x.jsonify() for x in res['users']]
    data['items'] += [x.jsonify() for x in res['items']]
    return jsonify(**data)

@blueprint.route('/statistics')
def statistics():
    return render_template('circulation_statistics.html',
                           active_nav='statistics')

@blueprint.route('/tasks')
def tasks():
    return render_template('circulation_tasks.html',
                           active_nav='tasks')

@blueprint.route('/entities')
def entities_overview():
    entities = ['Item', 'User', 'Library', 'Loan Cycle',
                'Mail Template']
    entities = [(x, x.lower().replace(' ', '_')) for x in entities]
    return render_template('circulation_entities_overview.html',
                           active_nav='entities', entities=entities)

@blueprint.route('/entities/<entity>')
def entities(entity):
    return render_template('circulation_entities_hub.html',
                           active_nav='entities', entity=entity)

@blueprint.route('/entities/<entity>/<id>')
def entity(entity, id):
    _entity = ''.join(x.title() for x in entity.split('_'))
    clazz = models.__getattribute__('Circulation' + _entity)
    obj = clazz.search(id=id)[0]
    return render_template('circulation_entities_edit.html',
                           active_nav='entities',
                           obj=json.dumps(obj.jsonify(),
                                          sort_keys=True,
                                          indent=4))

@blueprint.route('/entities/create/<entity>/')
def entity_new(entity):
    return render_template('circulation_entities_create.html',
                           active_nav='entities', obj='{}')

@blueprint.route('/api/entity/search', methods=['POST'])
def api_entity_search():
    data = json.loads(request.get_json())
    entity = ''.join(x.title() for x in data['entity'].split('_'))
    clazz = models.__getattribute__('Circulation' + entity)
    if data['search']:
        objs = [x.jsonify() for x in clazz.search(**data['search'])]
    else:
        objs = [x.jsonify() for x in clazz.get_all()]
    return json.dumps(objs)

@blueprint.route('/api/entity/create', methods=['POST'])
def api_entity_create():
    data = json.loads(request.get_json())
    clazz = get_circulation_class(data['entity'])
    clazz.new(**json.loads(data['data']))
    return ('', 200)

@blueprint.route('/api/entity/update', methods=['POST'])
def api_entity_update():
    data = json.loads(request.get_json())
    id = data['id']
    entity = data['entity']
    data = json.loads(data['data'])

    clazz = get_circulation_class(entity)
    obj = clazz.search(id=id)[0]

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
    obj = clazz.search(id=id)[0]
    obj.delete()

    return ('', 200)

@blueprint.route('/api/circulation/search', methods=['POST'])
def api_circulation_search():
    data = json.loads(request.get_json())
    res = {'user': None, 'items': None, 'library': None}

    if data['search']:
        res['user'] = [x.jsonify() for x in 
                       models.CirculationUser.search(**data['search'])]
        res['items'] = [x.jsonify() for x in
                        models.CirculationItem.search(**data['search'])]
        res['library'] = [x.jsonify() for x in
                          models.CirculationLibrary.search(**data['search'])]

    return json.dumps(res)

@blueprint.route('/api/circulation/try_actions', methods=['POST'])
def api_circulation_try_actions():
    data = json.loads(request.get_json())

    library = [models.CirculationLibrary.search(id=x['id'])[0] for x in
               data['library']]
    user = [models.CirculationUser.search(id=x['id'])[0] for x in
            data['user']]
    items = [models.CirculationItem.search(id=x['id'])[0] for x in
               data['items']]
    start_date = data['start_date']
    end_date = data['end_date']

    if not library or len(library) > 1:
        return '409'
    if not user or len(user) > 1:
        return '409'

    user = user[0]
    library = library[0]

    try:
        user.validate_run('loan', user=user, items=items, library=library,
                          start_date=start_date, end_date=end_date)
    except Exception:
        return '409'

    try:
        user.validate_run('request', user=user, items=items, library=library,
                          start_date=start_date, end_date=end_date)
    except Exception:
        return '409'

    return '409'


def get_circulation_class(entity):
    entity = ''.join(x.title() for x in entity.split('_'))
    return models.__getattribute__('Circulation' + entity)
