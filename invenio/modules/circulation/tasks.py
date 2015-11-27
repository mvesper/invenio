import celery
import datetime


def _change_to_overdue(overdue_loan):
    import invenio.modules.circulation.api.event.create as create_event
    import invenio.modules.circulation.models as models

    overdue_loan.current_status = models.CirculationLoanCycle.STATUS_OVERDUE
    overdue_loan.save()

    create_event(loan_cycle_id=overdue_loan.id,
                 event=models.CirculationEvent.EVENT_CLC_OVERDUE)

    # send overdue mail

    create_event(loan_cycle_id=overdue_loan.id,
                 event=models.CirculationEvent.EVENT_CLC_OVERDUE_LETTER)


@celery.task
def detect_overdue():
    import invenio.modules.circulation.models as models

    # Find items that are overdue
    today = datetime.date.today().isoformat()
    yesterday = today - datetime.timedelta(days=1)
    query = 'current_status:on_loan end_date:0000-01-01->{0}'.format(yesterday)
    overdue_loans = models.CirculationLoanCycle.search(query)

    for overdue_loan in overdue_loans:
        _change_to_overdue(overdue_loan)


@celery.task
def send_overdue_letters():
    import invenio.modules.circulation.models as m

    today = datetime.date.today()
    overdue_loans = m.CirculationLoanCycle.search('current_status:overdue')

    for overdue_loan in overdue_loans:
        # get all sent letter events for the loan cycle
        query = 'event:{0} loan_cycle_id:{1}'.format(
                m.CirculationEvent.EVENT_CLC_OVERDUE_LETTER,
                overdue_loan.id)
        overdue_event = sorted(m.CirculationEvent.search(query),
                               key=lambda x: x.creation_date)

        if overdue_event:
            time_delta = (today - overdue_event[-1].creation_date).days
        else:
            time_delta = 30

        if time_delta > 28:
            index = m.CirculationMailTemplate.__tablename__
            body = {'query': {'prefix': {'template_name': 'overdue_letter'}}}
            res = m.CirculationMailTemplate._es.search(index=index, body=body)
            letters = sorted(res, key=lambda x: x.template_name)

            # send another reminder
            pass
