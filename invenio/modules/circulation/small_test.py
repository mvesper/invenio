import datetime

from invenio.modules.circulation.models import (CirculationItem,
                                                CirculationLoanCycle,
                                                CirculationUser,
                                                CirculationLocation,
                                                CirculationEvent,
                                                CirculationMailTemplate,
                                                CirculationLoanRule)


def create_all():
    clo = CirculationLocation.new(code='ccl', name='CERN central library')

    cl1 = CirculationItem.new(record_id=100,
                              location = clo,
                              barcode='i1', isbn='i1', collection='books',
                              current_status='on_shelf',
                              item_group=CirculationItem.GROUP_BOOK)
    cl2 = CirculationItem.new(record_id=31,
                              location = clo,
                              barcode='i2', isbn='i2', collection='books',
                              current_status='on_shelf',
                              item_group=CirculationItem.GROUP_BOOK)

    cu = CirculationUser.new(current_status='active', ccid='u1',
                             invenio_user_id=1,
                             name='John Doe',
                             email='john.doe@cern.ch', phone='+41227671483',
                             address='3 1-014', mailbox='C27800',
                             user_group=CirculationUser.GROUP_DEFAULT)

    CirculationMailTemplate.new(template_name='item_loan',
                                subject='Loan confirmation',
                                header='Dear Mr/Mrs/Ms {{name}}',
                                content=('\nYou successfully {{action}} the '
                                         'following item(s)\n'
                                         '{% for item in items %}'
                                         '\t{{item}}\n'
                                         '{% endfor %}'))

    CirculationLoanRule.new(item_group=CirculationItem.GROUP_BOOK,
                            user_group=CirculationUser.GROUP_DEFAULT,
                            location_code='ccl',
                            loan_period=28)


def delete_all():
    CirculationItem.delete_all()
    CirculationUser.delete_all()
    CirculationLocation.delete_all()
    CirculationLoanCycle.delete_all()
    CirculationEvent.delete_all()
    CirculationMailTemplate.delete_all()
    CirculationLoanRule.delete_all()


"""
def set_all():
    return (CirculationItem.get_all()[0], CirculationItem.get_all()[1],
            CirculationItem.get_all()[2], CirculationItem.get_all()[3],
            CirculationUser.get_all()[0], CirculationLocation.get_all()[0])
"""


delete_all()
create_all()
#item1, item2, item3, item4, user, library = set_all()

start_date = datetime.date.today()
end_date = datetime.date.today() + datetime.timedelta(weeks=4)

start_date1 = datetime.date.today() + datetime.timedelta(weeks=1)
end_date1 = datetime.date.today() + datetime.timedelta(weeks=5)

start_date2 = datetime.date.today() + datetime.timedelta(weeks=2)
end_date2 = datetime.date.today() + datetime.timedelta(weeks=6)

# This will loan an item for 4 weeks
#item1.run('loan', item=item1, user=user, library=library, start_date=start_date, end_date=end_date)

# This will request the item in 2 weeks
#item1.run('request', item=item1, user=user, library=library, start_date=start_date1, end_date=end_date1)

# This will loan two items at once for 4 weeks, starting from the user
#user.run('loan', items=[item1, item2], user=user, library=library, start_date=start_date, end_date=end_date)

# This will return the previously loaned items, starting from the user
#user.run('return', items=[item1, item2])

# Let's try canceling a request
#user.run('request', items=[item1], user=user, library=library, start_date=start_date1, end_date=end_date1)
#user.run('loan', items=[item1], user=user, library=library, start_date=start_date, end_date=end_date, waitlist=True)

# Let's cancel a request with multiple items 
#user.run('request', items=[item1], user=user, library=library, start_date=start_date1, end_date=end_date1)
#user.run('loan', items=[item1, item2], user=user, library=library, start_date=start_date, end_date=end_date, waitlist=True)

# Let's cancel a request with multiple items on the waitlist
#user.run('request', items=[item1], user=user, library=library, start_date=start_date2, end_date=end_date2, waitlist=True)
#user.run('request', items=[item1], user=user, library=library, start_date=start_date1, end_date=end_date1, waitlist=True)
#user.run('request', items=[item1], user=user, library=library, start_date=start_date, end_date=end_date, waitlist=True)
