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

import invenio.modules.circulation.api as api
import invenio.modules.circulation.models as models

from flask import Blueprint, render_template, request, flash

from invenio.modules.circulation.aggregators import aggregators
from invenio.modules.circulation.views.utils import (get_name_link_class,
                                                     datetime_serial)

blueprint = Blueprint('entity', __name__, url_prefix='/circulation',
                      template_folder='../templates',
                      static_folder='../static')

apis = {'item': api.item, 'loan_cycle': api.loan_cycle, 'user': api.user,
        'event': api.event, 'loan_rule': api.loan_rule,
        'location': api.location, 'mail_template': api.mail_template}


@blueprint.route('/entities')
def entities_overview():
    entities = [(name, link) for name, link, _ in models.entities]
    return render_template('entities/overview.html',
                           active_nav='entities', entities=entities)


@blueprint.route('/entities/<entity>')
def entities_hub(entity):
    return render_template('entities/entity_hub.html',
                           active_nav='entities', entity=entity)

@blueprint.route('/entities/action/search/<entity>')
def entity_hub_search_all(entity):
    _, link, clazz = get_name_link_class(models.entities, entity)

    entities = clazz.get_all()

    return render_template('entities/'+link+'.html',
                           active_nav='entities', entities=entities, entity=entity)

@blueprint.route('/entities/action/search/<entity>/<search>')
def entity_hub_search(entity, search):
    _, link, clazz = get_name_link_class(models.entities, entity)

    search = dict(part.split(':') for part in search.split(' '))
    entities = clazz.search(**search)

    return render_template('entities/'+link+'.html',
                           active_nav='entities', entities=entities, entity=entity)


@blueprint.route('/entities/<entity>/<id>')
def entity(entity, id):
    _, link, clazz = get_name_link_class(models.entities, entity)
    _, __, aggregator = get_name_link_class(aggregators, entity)

    obj = clazz.get(id)
    aggregated = aggregator.get_aggregated_info(obj)

    aggregated['functions'] = _try_actions(link, aggregated['functions'], obj)

    return render_template('entities/'+link+'_detail.html',
                           active_nav='entities',
                           aggregated=aggregated)


def _try_actions(link, functions, obj):
    try:
        _api = apis[link]
    except KeyError:
        return []

    res = []
    for func, params in functions.items():
        try:
            _api.__getattribute__('try_'+func)([obj])
            res.append({'success': True, 'name': func, 'params': params})
        except Exception:
            res.append({'success': False, 'name': func, 'params': params})

    return res


@blueprint.route('/entities/action/create/<entity>')
def entity_new(entity):
    return render_template('entities/entity_create.html',
                           active_nav='entities', obj={}, entity=entity)


@blueprint.route('/api/entity/get', methods=['POST'])
def api_entity_get():
    data = json.loads(request.get_json())

    _, __, clazz = get_name_link_class(models.entities, data['entity'])
    _, __, aggregator = get_name_link_class(aggregators, data['entity'])

    res = {'schema': aggregator._json_schema,
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

    _, __, aggregator = get_name_link_class(aggregators, data['entity'])

    return json.dumps({'schema': aggregator._json_schema})


@blueprint.route('/api/entity/run_action', methods=['POST'])
def api_entity_run_action():
    data = json.loads(request.get_json())

    name, link, clazz = get_name_link_class(models.entities, data['entity'])

    _api = apis[link]

    obj = clazz.get(data['id'])
    func = data['function']

    """
    try:
        _api.__getattribute__(func)([obj])
        return ('', 200)
    except Exception:
        return ('', 500)
    """
    _api.__getattribute__(func)([obj])
    msg = 'Successfully called {0} on {1} with id: {2}'
    msg = msg.format(data['function'], name, data['id'])
    flash(msg)
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

    name, link, clazz = get_name_link_class(models.entities, data['entity'])
    
    entity = apis[link].create(**data['data'])
    """
    try:
        apis[link].create(**data['data'])
    except Exception:
        return ('', 500)
    """
    flash('Successfully created a new {0} with id {1}.'.format(name,
                                                               entity.id))
    return ('', 200)


@blueprint.route('/api/entity/update', methods=['POST'])
def api_entity_update():
    data = json.loads(request.get_json())

    name, link, clazz = get_name_link_class(models.entities, data['entity'])

    apis[link].update(clazz.get(data['id']), **data['data'])
    """
    try:
        apis[link].update(clazz.get(data['id']), **data['data'])
    except Exception:
        return ('', 500)
    """

    flash('Successfully updated the {0} with id {1}.'.format(name,
                                                             data['id']))
    return ('', 200)


@blueprint.route('/api/entity/delete', methods=['POST'])
def api_entity_delete():
    data = json.loads(request.get_json())

    name, link, clazz = get_name_link_class(models.entities, data['entity'])

    apis[link].delete(clazz.get(data['id']))
    """
    try:
        apis[link].delete(clazz.get(data['id']))
    except Exception:
        return ('', 500)
    """

    flash('Successfully deleted the {0} with id {1}.'.format(name,
                                                             data['id']))
    return ('', 200)
