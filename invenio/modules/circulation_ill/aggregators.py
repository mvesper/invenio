from invenio.modules.circulation.aggregators import (
        CirculationLoanCycleAggregator)


class IllLoanCycleAggregator(CirculationLoanCycleAggregator):
    _json_schema = {'type': 'object',
                    'title': 'Loan Cycle',
                    'properties': {
                        'id': {'type': 'integer'},
                        'item_id': {'type': 'integer'},
                        'user_id': {'type': 'integer'},
                        'group_uuid': {'type': 'string'},
                        'current_status': {'type': 'string'},
                        'start_date': {'type': 'string'},
                        'end_date': {'type': 'string'},
                        'issued_date': {'type': 'string'},
                        'requested_extension_end_date': {'type': 'string'},
                        }
                    }
