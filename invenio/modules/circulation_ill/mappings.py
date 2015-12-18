def add_copy_to(mappings):
    name = mappings['mappings'].keys()[0]
    full_text = {'type': 'string'}
    mappings['mappings'][name]['properties']['global_fulltext'] = full_text
    for key, value in mappings['mappings'][name]['properties'].items():
        try:
            value['copy_to'].append('global_fulltext')
        except AttributeError:
            value['copy_to'] = [value['copy_to'], 'global_fulltext']
        except KeyError:
            value['copy_to'] = ['global_fulltext']


ill_loan_cycle_mappings = {
        'mappings': {
            'ill_loan_cycle': {
                '_all': {'enabled': True},
                'properties': {
                    'id': {
                        'type': 'string',
                        'index': 'not_analyzed'},
                    'group_uuid': {
                        'type': 'string',
                        'index': 'not_analyzed'},
                    'end_date': {
                        'type': 'date',},
                    'global_fulltext': {
                        'type': 'string',},
                    }
                }
            }
        }
add_copy_to(ill_loan_cycle_mappings)


mappings = {'Ill Loan Cycle': ill_loan_cycle_mappings}
