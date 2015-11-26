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
import invenio.modules.circulation.aggregators as aggregators

from flask import Blueprint, render_template, request, flash

from invenio.modules.circulation.views.utils import datetime_serial

blueprint = Blueprint('entity', __name__, url_prefix='/circulation',
                      template_folder='../templates',
                      static_folder='../static')

apis = {'item': api.item, 'loan_cycle': api.loan_cycle, 'user': api.user,
        'event': api.event, 'loan_rule': api.loan_rule,
        'location': api.location, 'mail_template': api.mail_template}

models_entities = {'record': {'name': 'Record',
                              'class': models.CirculationRecord, '_pos': 0},
                   'user': {'name': 'User',
                            'class': models.CirculationUser, '_pos': 1},
                   'item': {'name': 'Item',
                            'class': models.CirculationItem, '_pos': 2},
                   'loan_cycle': {'name': 'Loan Cycle',
                                  'class': models.CirculationLoanCycle,
                                  '_pos': 3},
                   'location': {'name': 'Location',
                                'class': models.CirculationLocation,
                                '_pos': 4},
                   'event': {'name': 'Event',
                             'class': models.CirculationEvent, '_pos': 5},
                   'mail_template': {'name': 'Mail Template',
                                     'class': models.CirculationMailTemplate,
                                     '_pos': 6},
                   'loan_rule': {'name': 'Loan Rule',
                                 'class': models.CirculationLoanRule,
                                 '_pos': 7},
                   'loan_rule_match': {
                       'name': 'Loan Rule Match',
                       'class': models.CirculationLoanRuleMatch,
                       '_pos': 8}}

aggregators = {'record': aggregators.CirculationRecordAggregator,
               'user': aggregators.CirculationUserAggregator,
               'item': aggregators.CirculationItemAggregator,
               'loan_cycle': aggregators.CirculationLoanCycleAggregator,
               'location': aggregators.CirculationLocationAggregator,
               'event': aggregators.CirculationEventAggregator,
               'mail_template': aggregators.CirculationMailTemplateAggregator,
               'loan_rule': aggregators.CirculationLoanRuleAggregator,
               'loan_rule_match':
                   aggregators.CirculationLoanRuleMatchAggregator}


@blueprint.route('/entities')
def entities_overview():
    entities = [(val['name'], key) for key, val
                in sorted(models_entities.items(), key=lambda x: x[1]['_pos'])]
    return render_template('entities/overview.html',
                           active_nav='entities', entities=entities)


@blueprint.route('/entities/<entity>')
def entities_hub(entity):
    return render_template('entities/entity_hub.html',
                           active_nav='entities', entity=entity)


@blueprint.route('/entities/action/search/<entity>')
@blueprint.route('/entities/action/search/<entity>/<search>')
def entity_hub_search(entity, search=''):
    entities = models_entities[entity]['class'].search(search)

    return render_template('entities/'+entity+'.html',
                           active_nav='entities',
                           entities=entities, entity=entity)


@blueprint.route('/entities/<entity>/<id>')
def entity(entity, id):
    clazz = models_entities[entity]['class']
    aggregator = aggregators[entity]

    obj = clazz.get(id)
    aggregated = aggregator.get_aggregated_info(obj)

    aggregated['functions'] = _try_actions(entity, aggregated['functions'],
                                           obj)

    editor_data = json.dumps(clazz.get(id).jsonify(), default=datetime_serial)
    editor_schema = json.dumps(aggregator._json_schema,
                               default=datetime_serial)

    try:
        suggestions_config = json.dumps(aggregators[entity]._suggestions_config)
    except AttributeError:
        suggestions_config = json.dumps(None)

    return render_template('entities/'+entity+'_detail.html',
                           active_nav='entities',
                           editor_data=editor_data,
                           editor_schema=editor_schema,
                           aggregated=aggregated,
                           suggestions_config=suggestions_config)


def _try_actions(entity, functions, obj):
    try:
        _api = apis[entity]
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
    # entering the certain values is going to break and doesn't make sense,
    # so they will be removed here
    editor_schema = aggregators[entity]._json_schema

    for key in ['id', 'group_uuid', 'creation_date']:
        try:
            del editor_schema['properties'][key]
        except KeyError:
            pass

    try:
        suggestions_config = json.dumps(aggregators[entity]._suggestions_config)
    except AttributeError:
        suggestions_config = json.dumps(None)

    editor_schema = json.dumps(editor_schema, default=datetime_serial)
    return render_template('entities/entity_create.html',
                           active_nav='entities', obj={}, entity=entity,
                           editor_data={},
                           editor_schema=editor_schema,
                           suggestions_config=suggestions_config)


def extract_params(func):
    import inspect
    _args = inspect.getargspec(func).args

    def wrap():
        data = json.loads(request.get_json())
        return func(**{arg_name: data[arg_name] for arg_name in _args})

    wrap.func_name = func.func_name
    return wrap


@blueprint.route('/api/entity/get', methods=['POST'])
@extract_params
def api_entity_get(id, entity):
    clazz = models_entities[entity]['class']
    aggregator = aggregators[entity]

    res = {'schema': aggregator._json_schema,
           'data': clazz.get(id).jsonify()}

    return json.dumps(res, default=datetime_serial)


@blueprint.route('/api/entity/run_action', methods=['POST'])
@extract_params
def api_entity_run_action(id, entity, function):
    name = models_entities[entity]['name']
    obj = models_entities[entity]['class'].get(id)

    apis[entity].__getattribute__(function)([obj])
    msg = 'Successfully called {0} on {1} with id: {2}'
    msg = msg.format(function, name, id)
    flash(msg)
    return ('', 200)


@blueprint.route('/api/entity/search', methods=['POST'])
@extract_params
def api_entity_search(entity, search):
    objs = models_entities[entity]['class'].search(search)
    return json.dumps([x.jsonify() for x in objs], default=datetime_serial)


@blueprint.route('/api/entity/create', methods=['POST'])
@extract_params
def api_entity_create(entity, data):
    name = models_entities[entity]['name']

    entity = apis[entity].create(**data)
    flash('Successfully created a new {0} with id {1}.'.format(name,
                                                               entity.id))
    return ('', 200)


@blueprint.route('/api/entity/update', methods=['POST'])
@extract_params
def api_entity_update(id, entity, data):
    name = models_entities[entity]['name']
    clazz = models_entities[entity]['class']

    apis[entity].update(clazz.get(id), **data)

    flash('Successfully updated the {0} with id {1}.'.format(name, id))
    return ('', 200)


@blueprint.route('/api/entity/delete', methods=['POST'])
@extract_params
def api_entity_delete(id, entity):
    name = models_entities[entity]['name']
    clazz = models_entities[entity]['class']

    apis[entity].delete(clazz.get(id))

    flash('Successfully deleted the {0} with id {1}.'.format(name, id))
    return ('', 200)
