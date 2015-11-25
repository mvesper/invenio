import celery
import datetime

import invenio.modules.circulation.api.event.create as create_event

from invenio.modules.circulation.models import (CirculationLoanCycle,
                                                CirculationEvent,
                                                CirculationMailTemplate)


def _change_to_overdue(overdue_loan)
    overdue_loan.current_status = CirculationLoanCycle.STATUS_OVERDUE
    overdue_loan.save()

    create_event(loan_cycle_id=overdue_loan.id,
                 event=CirculationEvent.EVENT_CLC_OVERDUE)

    #send overdue mail
    
    create_event(loan_cycle_id=overdue_loan.id,
                 event=CirculationEvent.EVENT_CLC_OVERDUE_LETTER)

@celery.task
def detect_overdue():
    # Find items that are overdue
    today = datetime.date.today().isoformat()
    yesterday = today - datetime.timedelta(days=1)
    query = 'current_status:on_loan end_date:0000-01-01->{0}'.format(yesterday)
    overdue_loans = CirculationLoanCycle.search(query)

    for overdue_loan in overdue_loans:
        _change_to_overdue(overdue_loan)


@celery.task
def send_overdue_letters():
    today = datetime.date.today()
    overdue_loans = CirculationLoanCycle.search('current_status:overdue')

    for overdue_loan in overdue_loans:
        # get all sent letter events for the loan cycle
        query = 'event:{0} loan_cycle_id:{1}'.format(
                CirculationEvent.EVENT_CLC_OVERDUE_LETTER,
                overdue_loan.id)
        overdue_event = sorted(CirculationEvent.search(query),
                               key=lambda x: x.creation_date)

        if overdue_event:
            time_delta = (today - overdue_event[-1].creation_date).days
        else:
            time_delta = 30

        if time_delta > 28:
            index = CirculationMailTemplate.__tablename__
            body = {'query': {'prefix': {'template_name': 'overdue_letter'}}}
            res = CirculationMailTemplate._es.search(index=index, body=body)
            letters = sorted(res, key=lambda x: x.template_name)

            # send another reminder
            pass
