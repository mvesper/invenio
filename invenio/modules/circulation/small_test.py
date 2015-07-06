import datetime

from invenio.modules.circulation.models import (CirculationItem,
                                                CirculationLoanCycle,
                                                CirculationUser,
                                                CirculationLibrary,
                                                CirculationTask,
                                                CirculationEvent,
                                                CirculationMailTemplate)


def create_all():
    CirculationItem.new(id='i1',
                        current_status='on_shelf', title='Higgs', isbn='i1')
    CirculationItem.new(id='i2',
                        current_status='on_shelf', title='Higgs', isbn='i2')

    CirculationUser.new(current_status='active', id='u1',
                        first_name='John', last_name='Doe',
                        email='martin.vesper@cern.ch')

    CirculationLibrary.new(id='l1', name='Central')
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
            CirculationUser.get_all()[0], CirculationLibrary.get_all()[0])


delete_all()
create_all()
item1, item2, user, library = set_all()

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
