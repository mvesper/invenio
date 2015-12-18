import datetime

from collections import namedtuple

from invenio.testsuite import InvenioTestCase, make_test_suite, run_test_suite


class IllTest(InvenioTestCase):
    def setUp(self):
        import invenio.modules.circulation.models as circ_models
        import invenio.modules.circulation.api as circ_api

        self.user = circ_api.user.create(
                1, 'ccid', 'name', 'address', 'mailbox', 'email', 'phone', '',
                circ_models.CirculationUser.GROUP_DEFAULT)

        self.start_date = datetime.date.today()
        self.end_date = self.start_date + datetime.timedelta(weeks=4)


    def test_request_ill(self):
        import invenio.modules.circulation_ill.models as models
        import invenio.modules.circulation_ill.api.ill as api

        record = namedtuple('Record', ['id'])(1)
        ill_lc = api.request_ill(self.user, record,
                                 self.start_date, self.end_date)

        status = models.IllLoanCycle.STATUS_REQUESTED
        delivery = models.IllLoanCycle.DELIVERY_DEFAULT

        self.assertTrue(ill_lc.current_status == status)
        self.assertTrue(ill_lc.user == self.user)
        self.assertTrue(ill_lc.start_date == self.start_date)
        self.assertTrue(ill_lc.end_date == self.end_date)
        self.assertTrue(ill_lc.delivery == delivery)

        self.assertTrue(ill_lc.item.record_id == record.id)
        self.assertTrue('ill_temporary' in ill_lc.item.additional_statuses)

    def test_confirm_ill_request(self):
        import invenio.modules.circulation_ill.models as models
        import invenio.modules.circulation_ill.api.ill as api

        record = namedtuple('Record', ['id'])(1)
        ill_lc = api.request_ill(self.user, record,
                                 self.start_date, self.end_date)

        api.confirm_ill_request(ill_lc)

        status = models.IllLoanCycle.STATUS_ORDERED
        self.assertTrue(ill_lc.current_status == status)

    def test_cancel_ill_request(self):
        import invenio.modules.circulation_ill.models as models
        import invenio.modules.circulation_ill.api.ill as api

        record = namedtuple('Record', ['id'])(1)
        ill_lc = api.request_ill(self.user, record,
                                 self.start_date, self.end_date)

        api.cancel_ill_request(ill_lc)

        status = models.IllLoanCycle.STATUS_CANCELED
        self.assertTrue(ill_lc.current_status == status)

    def test_decline_ill_request(self):
        import invenio.modules.circulation_ill.models as models
        import invenio.modules.circulation_ill.api.ill as api

        record = namedtuple('Record', ['id'])(1)
        ill_lc = api.request_ill(self.user, record,
                                 self.start_date, self.end_date)

        api.decline_ill_request(ill_lc)

        status = models.IllLoanCycle.STATUS_DECLINED
        self.assertTrue(ill_lc.current_status == status)

    def test_deliver_ill(self):
        import invenio.modules.circulation_ill.models as models
        import invenio.modules.circulation_ill.api.ill as api

        record = namedtuple('Record', ['id'])(1)
        ill_lc = api.request_ill(self.user, record,
                                 self.start_date, self.end_date)

        api.confirm_ill_request(ill_lc)
        ill = api.deliver_ill(ill_lc)

        status = models.IllLoanCycle.STATUS_ON_LOAN
        self.assertTrue(ill_lc.current_status == status)

        self.assertTrue('ill_loan_cycle' in ill.additional_statuses)

    def test_request_ill_extension(self):
        import invenio.modules.circulation_ill.api.ill as api

        record = namedtuple('Record', ['id'])(1)
        ill_lc = api.request_ill(self.user, record,
                                 self.start_date, self.end_date)

        api.confirm_ill_request(ill_lc)
        ill = api.deliver_ill(ill_lc)
        api.request_ill_extension(ill, self.end_date)

        self.assertTrue(ill.desired_end_date == self.end_date)

    def test_extend_ill(self):
        # This basically doesn't need to be tested
        pass

    def test_return_ill(self):
        import invenio.modules.circulation_ill.models as models
        import invenio.modules.circulation_ill.api.ill as api

        record = namedtuple('Record', ['id'])(1)
        ill_lc = api.request_ill(self.user, record,
                                 self.start_date, self.end_date)

        api.confirm_ill_request(ill_lc)
        api.deliver_ill(ill_lc)
        api.return_ill(ill_lc)

        status = models.IllLoanCycle.STATUS_FINISHED
        self.assertTrue(ill_lc.current_status == status)

    def test_send_back_ill(self):
        import invenio.modules.circulation_ill.models as models
        import invenio.modules.circulation_ill.api.ill as api

        record = namedtuple('Record', ['id'])(1)
        ill_lc = api.request_ill(self.user, record,
                                 self.start_date, self.end_date)

        api.confirm_ill_request(ill_lc)
        api.deliver_ill(ill_lc)
        api.return_ill(ill_lc)
        api.send_back_ill(ill_lc)

        status = models.IllLoanCycle.STATUS_SEND_BACK
        self.assertTrue(ill_lc.current_status == status)


TEST_SUITE = make_test_suite(IllTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
