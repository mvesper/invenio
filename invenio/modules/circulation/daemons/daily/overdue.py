import datetime

from invenio.modules.circulation.models import CirculationLoanCycle


def detect_overdue_items():
    # get active loan_cycles
    active_loan_cycles = CirculationLoanCycle.search(current_status='active')

    # get overdue loan_cycles
    overdue_loan_cycles = [x for x in active_loan_cycles
                           if x.end_date > datetime.date.today()]
