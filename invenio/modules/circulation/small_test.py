import datetime

from invenio.modules.circulation.models import (CirculationItem,
                                                CirculationLoanCycle,
                                                CirculationUser,
                                                CirculationLibrary,
                                                CirculationTask,
                                                CirculationEvent,
                                                CirculationMailTemplate)


def create_all():
    CirculationItem.new(barcode='i1', record=101, title='Atlantis',
                        current_status='on_shelf', isbn='i1',
                        allowed_loan_period=28)
    CirculationItem.new(barcode='i2', record=101, title='Atlantis',
                        current_status='on_shelf', isbn='i2',
                        allowed_loan_period=28)
    CirculationItem.new(barcode='i3', record=100, title='Atlantis',
                        current_status='on_loan', isbn='i3',
                        allowed_loan_period=28)
    CirculationItem.new(barcode='i4', record=100, title='Atlantis',
                        current_status='on_loan', isbn='i4',
                        allowed_loan_period=28)

    CirculationUser.new(current_status='active', ccid='u1',
                        name='John Doe',
                        email='john.doe@cern.ch', phone='+41227671483',
                        address='3 1-014', mailbox='C27800')

    CirculationLibrary.new(name='Central')
    CirculationMailTemplate.new(template_name='item_loan',
                                subject='Loan confirmation',
                                header='Dear Mr/Mrs/Ms {{ user.last_name }}',
                                content=('\nYou successfully loaned the '
                                         'following item(s)\n'
                                         '{% for item in items %}'
                                         '\t{{ item.title }}\n'
                                         '{% endfor %}'))


def delete_all():
    CirculationItem.delete_all()
    CirculationUser.delete_all()
    CirculationLibrary.delete_all()
    CirculationLoanCycle.delete_all()
    CirculationEvent.delete_all()
    CirculationTask.delete_all()
    CirculationMailTemplate.delete_all()


def set_all():
    return (CirculationItem.get_all()[0], CirculationItem.get_all()[1],
            CirculationItem.get_all()[2], CirculationItem.get_all()[3],
            CirculationUser.get_all()[0], CirculationLibrary.get_all()[0])


delete_all()
create_all()
item1, item2, item3, item4, user, library = set_all()

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
