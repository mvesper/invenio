import datetime

from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


class CirculationTestBase(InvenioTestCase):
    def create_test_data(self):
        import invenio.modules.circulation.api as api
        import invenio.modules.circulation.models as models
        self.cl = api.location.create('CCL', 'CERN CENTRAL LIBRARY', '')
        self.clr = api.loan_rule.create(models.CirculationItem.GROUP_BOOK,
                                        models.CirculationUser.GROUP_DEFAULT,
                                        self.cl.code, 28)
        self.cu = api.user.create(1, 934657, 'John Doe', '3 1-014', 'C27800',
                                  'john.doe@cern.ch', '+41227141337', '', 
                                  models.CirculationUser.GROUP_DEFAULT)
        self.ci = api.item.create(30, self.cl.id, '978-1934356982', 'CM-B00001338',
                                  'books', '13.37', 'Vol 1', 'no desc',
                                  models.CirculationItem.STATUS_ON_SHELF,
                                  models.CirculationItem.GROUP_BOOK)
        self.clcs = []

    def delete_test_data(self):
        for clc in self.clcs:
            clc.delete()
        self.cu.delete()
        self.ci.delete()
        self.cl.delete()
        self.clr.delete()

    def create_dates(self, start_days=0, start_weeks=0,
                     end_days=0, end_weeks=4):
        start_date = (datetime.date.today() +
                      datetime.timedelta(days=start_days, weeks=start_weeks))
        end_date = (start_date +
                    datetime.timedelta(days=end_days, weeks=end_weeks))
        return start_date, end_date
