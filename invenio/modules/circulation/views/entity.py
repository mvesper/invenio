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

import json

import invenio.modules.circulation.models as models

from flask import Blueprint, render_template, request

from invenio.modules.circulation.views.utils import (get_name_link_class,
                                                     datetime_serial)

blueprint = Blueprint('entity', __name__, url_prefix='/circulation',
                      template_folder='../templates',
                      static_folder='../static')


@blueprint.route('/entities')
def entities_overview():
    entities = [(name, link) for name, link, _ in models.entities]
    return render_template('entities/overview.html',
                           active_nav='entities', entities=entities)


@blueprint.route('/entities/<entity>')
def entities_hub(entity):
    return render_template('entities/entity_hub.html',
                           active_nav='entities', entity=entity)


@blueprint.route('/entities/<entity>/search/<search>')
def entity_hub_search(entity, search):
    _, link, clazz = get_name_link_class(models.entities, entity)

    search = dict(part.split(':') for part in search.split(' '))

    entities = clazz.search(**search)
    return render_template('entities/'+link+'.html',
                           active_nav='entities', entities=entities)


@blueprint.route('/entities/<entity>/<id>')
def entity(entity, id):
    _, __, clazz = get_name_link_class(models.entities, entity)

    # TODO
    funcs = []

    return render_template('entities/entity_detail.html',
                           active_nav='entities',
                           functions=funcs)


@blueprint.route('/entities/<entity>/create')
def entity_new(entity):
    return render_template('entities/entity_create.html',
                           active_nav='entities', obj={})


@blueprint.route('/api/entity/get', methods=['POST'])
def api_entity_get():
    data = json.loads(request.get_json())

    _, __, clazz = get_name_link_class(models.entities, data['entity'])

    res = {'schema': clazz._json_schema,
           'data': clazz.get(data['id']).jsonify()}
    return json.dumps(res, default=datetime_serial)


@blueprint.route('/api/entity/get_functions', methods=['POST'])
def api_entity_get_functions():
    data = json.loads(request.get_json())

    _, __, clazz = get_name_link_class(models.entities, data['entity'])

    # TODO
    funcs = []
    res = {'data': funcs}
    return json.dumps(res)


@blueprint.route('/api/entity/get_json_schema', methods=['POST'])
def api_entity_get_json_schema():
    data = json.loads(request.get_json())

    _, __, clazz = get_name_link_class(models.entities, data['entity'])

    return json.dumps({'schema': clazz._json_schema})


@blueprint.route('/api/entity/run_action', methods=['POST'])
def api_entity_run_action():
    data = json.loads(request.get_json())

    _, __, clazz = get_name_link_class(models.entities, data['entity'])

    obj = clazz.get(data['id'])
    func = data['function']
    params = {obj.get_function_parameters(func)[0]: obj}
    obj.run(func, **params)
    return ('', 200)


@blueprint.route('/api/entity/search', methods=['POST'])
def api_entity_search():
    data = json.loads(request.get_json())

    _, __, clazz = get_name_link_class(models.entities, data['entity'])

    if data['search']:
        objs = clazz.search(**data['search'])
    else:
        objs = clazz.get_all()

    return json.dumps([x.jsonify() for x in objs], default=datetime_serial)


@blueprint.route('/api/entity/create', methods=['POST'])
def api_entity_create():
    data = json.loads(request.get_json())

    _, __, clazz = get_name_link_class(models.entities, data['entity'])

    clazz.new(**data['data'])
    return ('', 200)


@blueprint.route('/api/entity/update', methods=['POST'])
def api_entity_update():
    data = json.loads(request.get_json())
    id = data['id']
    entity = data['entity']
    data = data['data']

    _, __, clazz = get_name_link_class(models.entities, entity)

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

    _, __, clazz = get_name_link_class(models.entities, data['entity'])
    obj = clazz.get(data['id'])
    obj.delete()

    return ('', 200)
