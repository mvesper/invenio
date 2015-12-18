def generate():
    import invenio.modules.circulation.models as models
    import invenio.modules.circulation.api as api

    header = 'Dear Mr/Mrs/Ms {{name}}'
    content = '\nThis is a placeholder for what you have done :)\n'

    mt1 = api.mail_template.create('ill_request', 'ILL Request', header,
                                   content)
    mt2 = api.mail_template.create('ill_ordered', 'ILL is ordered', header,
                                   content)
    mt3 = api.mail_template.create('ill_declined', 'ILL declined', header,
                                   content)
    mt4 = api.mail_template.create('ill_delivery', 'ILL delivered', header,
                                   content)
    mt5 = api.mail_template.create('ill_extension_request',
                                   'ILL Extenion Request', header, content)
