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

from flask import Blueprint, render_template, request, flash

from invenio.modules.circulation.views.utils import (datetime_serial,
                                                     send_signal,
                                                     flatten)

blueprint = Blueprint('entity', __name__, url_prefix='/circulation',
                      template_folder='../templates',
                      static_folder='../static')


@blueprint.route('/entities')
def entities_overview():
    from invenio.modules.circulation.signals import entities_overview

    entities = flatten(send_signal(entities_overview,
                                   'entities_overview', None))

    return render_template('entities/overview.html',
                           active_nav='entities', entities=entities)


@blueprint.route('/entities/<entity>')
def entities_hub(entity):
    return render_template('entities/entity_hub.html',
                           active_nav='entities', entity=entity)


@blueprint.route('/entities/action/search/<entity>')
@blueprint.route('/entities/action/search/<entity>/<search>')
def entity_hub_search(entity, search=''):
    from invenio.modules.circulation.signals import entities_hub_search

    entities, template = send_signal(entities_hub_search, entity, search)[0]

    return render_template(template,
                           active_nav='entities',
                           entities=entities, entity=entity)


@blueprint.route('/entities/<entity>/<id>')
def entity(entity, id):
    from invenio.modules.circulation.signals import (
            entity as _entity,
            entity_suggestions as _entity_suggestions,
            entity_aggregations as _entity_aggregations)

    obj = send_signal(_entity, entity, id)[0]
    try:
        suggestions_config = send_signal(_entity_suggestions, entity, None)[0]
    except IndexError:
        suggestions_config = {}
    aggregations = send_signal(_entity_aggregations, entity, id)

    editor_data = json.dumps(obj.jsonify(), default=datetime_serial)
    editor_schema = json.dumps(obj._json_schema, default=datetime_serial)

    return render_template('entities/entity_detail.html',
                           active_nav='entities',
                           editor_data=editor_data,
                           editor_schema=editor_schema,
                           aggregations=flatten(aggregations),
                           suggestions_config=json.dumps(suggestions_config))


@blueprint.route('/entities/action/create/<entity>')
def entity_new(entity):
    from invenio.modules.circulation.signals import (
            entity_class,
            entity_suggestions as _entity_suggestions)

    clazz = send_signal(entity_class, entity, None)[0]
    suggestions_config = send_signal(_entity_suggestions, entity, None)[0]

    editor_schema = clazz._json_schema
    # entering certain values is going to break and doesn't make sense,
    # so they will be removed here
    for key in ['id', 'group_uuid', 'creation_date']:
        try:
            del editor_schema['properties'][key]
        except KeyError:
            pass
    editor_schema = json.dumps(editor_schema, default=datetime_serial)

    return render_template('entities/entity_create.html',
                           active_nav='entities', obj={}, entity=entity,
                           editor_data={},
                           editor_schema=editor_schema,
                           suggestions_config=json.dumps(suggestions_config))


def extract_params(func):
    import inspect
    _args = inspect.getargspec(func).args

    def wrap():
        data = json.loads(request.get_json())
        return func(**{arg_name: data[arg_name] for arg_name in _args})

    wrap.func_name = func.func_name
    return wrap


@blueprint.route('/api/entity/search', methods=['POST'])
@extract_params
def api_entity_search(entity, search):
    from invenio.modules.circulation.signals import entity_class

    clazz = send_signal(entity_class, entity, None)[0]
    objs = clazz.search(search)
    return json.dumps([x.jsonify() for x in objs], default=datetime_serial)


@blueprint.route('/api/entity/create', methods=['POST'])
@extract_params
def api_entity_create(entity, data):
    from invenio.modules.circulation.signals import entity_name, apis

    name = send_signal(entity_name, entity, None)[0]
    api = send_signal(apis, entity, None)[0]

    entity = api.create(**data)

    flash('Successfully created a new {0} with id {1}.'.format(name,
                                                               entity.id))
    return ('', 200)


@blueprint.route('/api/entity/update', methods=['POST'])
@extract_params
def api_entity_update(id, entity, data):
    from invenio.modules.circulation.signals import (
            entity_class, entity_name, apis)

    clazz = send_signal(entity_class, entity, None)[0]
    name = send_signal(entity_name, entity, None)[0]
    api = send_signal(apis, entity, None)[0]

    api.update(clazz.get(id), **data)

    flash('Successfully updated the {0} with id {1}.'.format(name, id))
    return ('', 200)


@blueprint.route('/api/entity/delete', methods=['POST'])
@extract_params
def api_entity_delete(id, entity):
    from invenio.modules.circulation.signals import (
            entity_class, entity_name, apis)

    clazz = send_signal(entity_class, entity, None)[0]
    name = send_signal(entity_name, entity, None)[0]
    api = send_signal(apis, entity, None)[0]

    api.delete(clazz.get(id))

    flash('Successfully updated the {0} with id {1}.'.format(name, id))
    return ('', 200)
