from invenio.modules.circulation.models import (CirculationItem,
                                                CirculationLoanCycle)


class OnLoanPendingRequests(object):
    @classmethod
    def run(cls):
        res = [item for item in CirculationItem.search(current_status='on_loan') 
               if CirculationLoanCycle.search(current_status='requested',
                                              item=item)]
        return {'items': res}


# Display Name , link name, list 
lists= [('Books on loan with pending requests',
         'on_loan_pending_requests',
         OnLoanPendingRequests)]
