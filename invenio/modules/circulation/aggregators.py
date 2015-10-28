# coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013 CERN.
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

import inspect

import invenio.modules.circulation.api as api

from invenio.modules.circulation.models import (CirculationItem,
                                                CirculationLoanCycle,
                                                CirculationEvent)


class BaseAggregator(object):
    @classmethod
    def get_aggregated_info(cls, obj):
        return {'schema': cls._json_schema, 'functions': {}}

    @classmethod
    def _get_entity_functions(cls, module):
        def is_mod_function(mod, func):
            return inspect.isfunction(func) and inspect.getmodule(func) == mod

        res = []
        for name in dir(module):
            if (name[0].isupper() or name[0] == '_' or name.startswith('try')):
                continue
            if is_mod_function(module, getattr(module, name)):
                res.append(name)

        return res


class CirculationRecordAggregator(BaseAggregator):
    _json_schema = {'type': 'object',
                    'title': 'Record',
                    'properties': {
                        'id': {'type': 'integer'},
                        'title': {'type': 'string'},
                        'abstract': {'type': 'string', 'format': 'textarea'},
                        'authors': {
                            'type': 'array',
                            'format': 'table',
                            'items': {
                                'type': 'string',
                                'title': 'Authors',
                                }
                            }
                        }
                    }

    @classmethod
    def get_aggregated_info(cls, obj):
        return {
                'schema': cls._json_schema,
                'functions': [],
                'additions': {
                    '_items': cls._get_items(obj),
                    }
                }

    @classmethod
    def _get_items(cls, obj):
        return CirculationItem.search('record_id:{0}'.format(obj.id))


class CirculationItemAggregator(BaseAggregator):
    _json_schema = {'type': 'object',
                    'title': 'Item',
                    'properties': {
                        'id': {'type': 'integer'},
                        'record_id': {'type': 'integer'},
                        'location_id': {'type': 'integer'},
                        'isbn': {'type': 'string'},
                        'barcode': {'type': 'string'},
                        'collection': {'type': 'string'},
                        'shelf_number': {'type': 'string'},
                        'description': {'type': 'string'},
                        'item_group': {'type': 'string'},
                        'current_status': {'type': 'string'},
                        'volume': {'type': 'string'},
                        }
                    }

    @classmethod
    def get_aggregated_info(cls, obj):
        return {
                'schema': cls._json_schema,
                'functions': api.item.schema,
                'additions': {
                    'record': obj.record,
                    'loan_cycles': cls._get_loan_cycles(obj),
                    }
                }

    @classmethod
    def _get_loan_cycles(cls, obj):
        return CirculationLoanCycle.search('item:{0}'.format(obj.id))


class CirculationLoanCycleAggregator(BaseAggregator):
    _json_schema = {'type': 'object',
                    'title': 'Loan Cycle',
                    'properties': {
                        'id': {'type': 'integer'},
                        'group_uuid': {'type': 'string'},
                        'current_status': {'type': 'string'},
                        'start_date': {'type': 'string'},
                        'end_date': {'type': 'string'},
                        'desired_start_date': {'type': 'string'},
                        'desired_end_date': {'type': 'string'},
                        'issued_date': {'type': 'string'},
                        }
                    }

    @classmethod
    def get_aggregated_info(cls, obj):
        return {
                'schema': cls._json_schema,
                'functions': api.loan_cycle.schema,
                'additions': {
                        'item': obj.item,
                        'user': obj.user,
                        'events': cls._get_events(obj),
                    }
                }

    @classmethod
    def _get_events(cls, obj):
        query = 'loan_cycle:{0}'.format(obj.id)
        return sorted(CirculationEvent.search(query),
                      key=lambda x: x.creation_date)


class CirculationUserAggregator(BaseAggregator):
    _json_schema = {'type': 'object',
                    'title': 'User',
                    'properties': {
                        'id': {'type': 'integer'},
                        'invenio_user_id': {'type': 'integer'},
                        'ccid': {'type': 'string'},
                        'name': {'type': 'string'},
                        'address': {'type': 'string'},
                        'mailbox': {'type': 'string'},
                        'email': {'type': 'string'},
                        'phone': {'type': 'string'},
                        'notes': {'type': 'string'},
                        'user_group': {'type': 'string'}
                        }
                    }

    @classmethod
    def get_aggregated_info(cls, obj):
        return {
                'schema': cls._json_schema,
                'functions': {},
                'additions': {
                        'current_items': cls._get_current_items(obj),
                        'loan_cycles': cls._get_loan_cycles(obj),
                    }
                }

    @classmethod
    def _get_current_items(cls, obj):
        query = 'user:{0}'.format(obj.id)
        return [x.item for x in CirculationLoanCycle.search(query)
                if x.current_status == 'active']

    @classmethod
    def _get_loan_cycles(cls, obj):
        query = 'user:{0}'.format(obj.id)
        return CirculationLoanCycle.search(query)


class CirculationLocationAggregator(BaseAggregator):
    _json_schema = {'type': 'object',
                    'title': 'Location',
                    'properties': {
                        'id': {'type': 'integer'},
                        'name': {'type': 'string'},
                        'code': {'type': 'string'},
                        'notes': {'type': 'string',
                                  'format': 'textarea',
                                  'options': {'expand_height': True}},
                        }
                    }


class CirculationEventAggregator(BaseAggregator):
    _json_schema = {'type': 'object',
                    'title': 'Event',
                    'properties': {
                        'id': {'type': 'integer'},
                        'user_id': {'type': 'integer'},
                        'item_id': {'type': 'integer'},
                        'loan_cycle_id': {'type': 'integer'},
                        'location': {'type': 'integer'},
                        'loan_rule_id': {'type': 'integer'},
                        'mail_template_id': {'type': 'integer'},
                        'event': {'type': 'string'},
                        'description': {'type': 'string'},
                        'creation_date': {'type': 'string'},
                        }
                    }


class CirculationMailTemplateAggregator(BaseAggregator):
    _json_schema = {'type': 'object',
                    'title': 'Mail Template',
                    'properties': {
                        'id': {'type': 'integer'},
                        'template_name': {'type': 'string'},
                        'subject': {'type': 'string'},
                        'header': {'type': 'string'},
                        'content': {'type': 'string',
                                    'format': 'textarea',
                                    'options': {'expand_height': True}},
                        }
                    }


class CirculationLoanRuleAggregator(BaseAggregator):
    _json_schema = {'type': 'object',
                    'title': 'Loan Rule',
                    'properties': {
                        'id': {'type': 'integer'},
                        'item_group': {'type': 'string'},
                        'user_group': {'type': 'string'},
                        'location_code': {'type': 'string'},
                        'loan_period': {'type': 'integer'},
                        }
                    }


# Display Name , link name, entity
aggregators = [('Record', 'record', CirculationRecordAggregator),
               ('User', 'user', CirculationUserAggregator),
               ('Item', 'item', CirculationItemAggregator),
               ('Loan Cycle', 'loan_cycle', CirculationLoanCycleAggregator),
               ('Location', 'location', CirculationLocationAggregator),
               ('Event', 'event', CirculationEventAggregator),
               ('Mail Template', 'mail_template',
                CirculationMailTemplateAggregator),
               ('Loan Rule', 'loan_rule',
                CirculationLoanRuleAggregator)]
