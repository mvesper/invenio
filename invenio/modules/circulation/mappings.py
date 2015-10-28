item_mappings = {'mappings': {
                    'circulation_item': {
                        '_all': {'enabled': True},
                        'properties': {
                            'id': {
                                'type': 'integer',
                                'index': 'not_analyzed'},
                            'record_id': {
                                'type': 'integer',
                                'index': 'not_analyzed'},
                            'location_id': {
                                'type': 'integer',
                                'index': 'not_analyzed'},
                            'isbn': {
                                'type': 'string',
                                'index': 'not_analyzed'},
                            'barcode': {
                                'type': 'string',
                                'index': 'not_analyzed'},
                            }
                        }
                    }
                 }

loan_cycle_mappings = {'mappings': {
                            'circulation_loan_cycle': {
                                '_all': {'enabled': True},
                                'properties': {
                                    'id': {
                                        'type': 'integer',
                                        'index': 'not_analyzed'},
                                    'group_uuid': {
                                        'type': 'string',
                                        'index': 'not_analyzed'},
                                    }
                                }
                            }
                       }

user_mappings = {'mappings': {
                    'circulation_user': {
                        '_all': {'enabled': True},
                        'properties': {
                            'id': {
                                'type': 'integer',
                                'index': 'not_analyzed'},
                            'invenio_user_id': {
                                'type': 'integer',
                                'index': 'not_analyzed'},
                            'ccid': {
                                'type': 'string',
                                'index': 'not_analyzed'},
                            }
                        }
                    }
                 }

location_mappings = {'mappings': {
                        'circulation_location': {
                            '_all': {'enabled': True},
                            'properties': {
                                'id': {
                                    'type': 'integer',
                                    'index': 'not_analyzed'},
                                'code': {
                                    'type': 'string',
                                    'index': 'not_analyzed'},
                                }
                            }
                        }
                     }

event_mappings = {'mappings': {
                    'circulation_event': {
                        '_all': {'enabled': True},
                        'properties': {
                            'id': {
                                'type': 'integer',
                                'index': 'not_analyzed'},
                            'user_id': {
                                'type': 'integer',
                                'index': 'not_analyzed'},
                            'item_id': {
                                'type': 'integer',
                                'index': 'not_analyzed'},
                            'loan_cycle_id': {
                                'type': 'integer',
                                'index': 'not_analyzed'},
                            'location': {
                                'type': 'integer',
                                'index': 'not_analyzed'},
                            'loan_rule_id': {
                                'type': 'integer',
                                'index': 'not_analyzed'},
                            'mail_template_id': {
                                'type': 'integer',
                                'index': 'not_analyzed'},
                            }
                        }
                    }
                  }

mail_template_mappings = {'mappings': {
                            'circulation_mail_template': {
                                '_all': {'enabled': True},
                                'properties': {
                                    'id': {
                                        'type': 'integer',
                                        'index': 'not_analyzed'},
                                    }
                                }
                            }
                          }

loan_rule_mappings = {'mappings': {
                        'circulation_loan_rule': {
                            '_all': {'enabled': True},
                            'properties': {
                                'id': {
                                    'type': 'integer',
                                    'index': 'not_analyzed'},
                                'user_group': {
                                    'type': 'string',
                                    'index': 'not_analyzed'},
                                },
                            }
                        }
                      }


mappings = {'Item': item_mappings,
            'Loan Cycle': loan_cycle_mappings,
            'User': user_mappings,
            'Location': location_mappings,
            'Event': event_mappings,
            'Mail Template': mail_template_mappings,
            'Loan Rule': loan_rule_mappings}
