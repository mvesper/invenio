def generate():
    import datetime

    import invenio.modules.circulation.models as models
    import invenio.modules.circulation.api as api

    location1 = api.location.create('ccl', 'CERN central librar', '')

    item1 = api.item.create(30, 1, 'isbn1', 'barcode1', 'books', 'shelf1',
                            'vol1', '', 'on_shelf',
                            models.CirculationItem.GROUP_BOOK)
    item2 = api.item.create(30, 1, 'isbn2', 'barcode2', 'books', 'shelf2',
                            'vol1', '', 'on_shelf',
                            models.CirculationItem.GROUP_BOOK)
    item3 = api.item.create(30, 1, 'isbn3', 'barcode3', 'books', 'shelf3',
                            'vol1', '', 'on_shelf',
                            models.CirculationItem.GROUP_BOOK)
    item4 = api.item.create(30, 1, 'isbn4', 'barcode4', 'books', 'shelf4',
                            'vol1', '', 'on_shelf',
                            models.CirculationItem.GROUP_BOOK)
    item5 = api.item.create(30, 1, 'isbn5', 'barcode5', 'books', 'shelf5',
                            'vol1', '', 'on_shelf',
                            models.CirculationItem.GROUP_BOOK)
    item6 = api.item.create(30, 1, 'isbn6', 'barcode6', 'books', 'shelf6',
                            'vol1', '', 'on_shelf',
                            models.CirculationItem.GROUP_BOOK)

    user = api.user.create(1, 'ccid1', 'John Doe', 'Random Street', 'Mailbox',
                           'john.doe@mail.com', 'phone1', '',
                           models.CirculationUser.GROUP_DEFAULT)


    header = 'Dear Mr/Mrs/Ms {{name}}'
    content = ('\nYou successfully {{action}} the following item(s)\n'
               '{% for item in items %}'
               '\t{{item}}\n'
               '{% endfor %}')
    mt1 = api.mail_template.create('item_loan', 'Loan confirmation', header,
                                   content)

    lr1 = api.loan_rule.create(models.CirculationItem.GROUP_BOOK,
                               models.CirculationUser.GROUP_DEFAULT,
                               'ccl', 28, True)

    # latest loaned item
    start_date = datetime.date.today()
    end_date = start_date + datetime.timedelta(weeks=4)

    api.circulation.loan_items(user, [item1], start_date, end_date)

    # Overdue item
    start_date = datetime.date.today()
    end_date = start_date + datetime.timedelta(weeks=4)
    start_date1 = datetime.date.today() - datetime.timedelta(weeks=5)
    end_date1 = start_date1 + datetime.timedelta(weeks=4)

    clc = api.circulation.loan_items(user, [item2], start_date, end_date)[0]
    clc.start_date = start_date1
    clc.end_date = end_date1
    clc.additional_statuses.append(models.CirculationLoanCycle.STATUS_OVERDUE)
    clc.save()

    # items on shelf pending request
    start_date = datetime.date.today() + datetime.timedelta(weeks=2)
    end_date = start_date + datetime.timedelta(weeks=4)

    api.circulation.request_items(user, [item3], start_date, end_date)

    # items on loan with pending request
    start_date = datetime.date.today()
    end_date = start_date + datetime.timedelta(weeks=4)
    api.circulation.loan_items(user, [item4], start_date, end_date)

    start_date = datetime.date.today() + datetime.timedelta(weeks=6)
    end_date = start_date + datetime.timedelta(weeks=4)
    api.circulation.request_items(user, [item4], start_date, end_date)

    # Overdue item with pending request
    start_date = datetime.date.today()
    end_date = start_date + datetime.timedelta(weeks=4)

    clc = api.circulation.loan_items(user, [item5], start_date, end_date)[0]
    clc.start_date = start_date1
    clc.end_date = end_date1
    clc.additional_statuses.append(models.CirculationLoanCycle.STATUS_OVERDUE)
    clc.save()

    start_date = datetime.date.today() + datetime.timedelta(weeks=2)
    end_date = start_date + datetime.timedelta(weeks=4)
    api.circulation.request_items(user, [item5], start_date, end_date)
