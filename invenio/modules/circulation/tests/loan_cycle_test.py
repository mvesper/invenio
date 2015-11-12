import datetime

from invenio.testsuite import make_test_suite, run_test_suite
from invenio.modules.circulation.tests.utils import CirculationTestBase

class TestLoanCycleApi(CirculationTestBase):
    def test_cancel_clc_successful(self):
        import invenio.modules.circulation.api as api
        import invenio.modules.circulation.models as models

        self.create_test_data()

        start_date1, end_date1 = self.create_dates()
        self.clcs = api.circulation.request_items(self.cu, [self.ci],
                                                  start_date1, end_date1,
                                                  False)
        api.loan_cycle.cancel_clcs(self.clcs)

        clc = self.clcs[0]
        self.assertTrue(len(self.clcs) == 1)
        self.assertTrue(clc.current_status == models.CirculationLoanCycle.STATUS_CANCELED)

        self.delete_test_data()

    """
    This turns out to be possible, since a clc can be canceled du to a lost
    item for example
    def test_cancel_clc_failure(self):
        import invenio.modules.circulation.api as api
        import invenio.modules.circulation.models as models
        from invenio.modules.circulation.api.utils import ValidationExceptions

        self.create_test_data()

        start_date1, end_date1 = self.create_dates()
        self.clcs = api.circulation.loan_items(self.cu, [self.ci],
                                               start_date1, end_date1,
                                               False)
        with self.assertRaises(ValidationExceptions):
            api.loan_cycle.cancel_clcs(self.clcs)

        self.delete_test_data()
    """

    def test_cancel_clc_successful_update_waitlist(self):
        import invenio.modules.circulation.api as api
        import invenio.modules.circulation.models as models

        self.create_test_data()
        start_date1, end_date1 = self.create_dates()
        start_date2, end_date2 = self.create_dates(start_weeks=2)
        # Loan the item first
        self.clcs = api.circulation.request_items(self.cu, [self.ci],
                                                  start_date1, end_date1,
                                                  False)

        # Request the item another time, adding it to a waitlist
        self.clcs.extend(api.circulation.request_items(self.cu, [self.ci],
                                                       start_date2, end_date2,
                                                       True))

        clc1 = self.clcs[0]
        clc2 = self.clcs[1]

        # Check the start dates of clc2
        self.assertTrue(clc2.desired_start_date == start_date2)
        self.assertTrue(clc2.start_date == end_date1 + datetime.timedelta(days=1))

        # Cancel the request
        api.loan_cycle.cancel_clcs([clc1])

        # Check the start dates of clc2
        self.assertTrue(clc2.desired_start_date == start_date2)
        self.assertTrue(clc2.start_date == start_date2)

        self.delete_test_data()


    def test_overdue_clc(self):
        import invenio.modules.circulation.api as api
        import invenio.modules.circulation.models as models

        self.create_test_data()

        start_date1, end_date1 = self.create_dates()
        self.clcs = api.circulation.loan_items(self.cu, [self.ci],
                                               start_date1, end_date1,
                                               False)
        clc = self.clcs[0]
        clc.end_date = datetime.date.today() - datetime.timedelta(days=1)
        clc.save()
        api.loan_cycle.overdue_clcs(self.clcs)

        clc = self.clcs[0]
        self.assertTrue(len(self.clcs) == 1)
        self.assertTrue(models.CirculationLoanCycle.STATUS_OVERDUE in clc.additional_statuses)

        self.delete_test_data()

    def test_loan_extension_success(self):
        import invenio.modules.circulation.api as api
        import invenio.modules.circulation.models as models

        self.create_test_data()

        start_date1, end_date1 = self.create_dates(end_weeks=2)
        requested_end_date, _ = self.create_dates(start_weeks=4)
        self.clcs = api.circulation.loan_items(self.cu, [self.ci],
                                               start_date1, end_date1,
                                               False)
        api.loan_cycle.loan_extension(self.clcs, requested_end_date)

        clc = self.clcs[0]
        self.assertTrue(len(self.clcs) == 1)
        self.assertTrue(clc.current_status == models.CirculationLoanCycle.STATUS_ON_LOAN)
        self.assertTrue(clc.end_date == requested_end_date)
        self.assertTrue(clc.desired_end_date == requested_end_date)

        self.delete_test_data()

    def test_loan_extension_failure(self):
        import invenio.modules.circulation.api as api
        import invenio.modules.circulation.models as models
        from invenio.modules.circulation.api.utils import ValidationExceptions

        self.create_test_data()

        start_date1, end_date1 = self.create_dates(end_weeks=2)
        start_date2, end_date2 = self.create_dates(start_weeks=3)
        requested_end_date, _ = self.create_dates(start_weeks=4)
        self.clcs = api.circulation.loan_items(self.cu, [self.ci],
                                               start_date1, end_date1,
                                               False)
        self.clcs.extend(api.circulation.request_items(self.cu, [self.ci],
                                                       start_date2,
                                                       end_date2, False))
        clc = self.clcs[0]
        with self.assertRaises(ValidationExceptions):
            api.loan_cycle.loan_extension([clc], requested_end_date)

        self.delete_test_data()

    def test_loan_extension_waitlist(self):
        import invenio.modules.circulation.api as api
        import invenio.modules.circulation.models as models

        self.create_test_data()

        start_date1, end_date1 = self.create_dates(end_weeks=2)
        start_date2, end_date2 = self.create_dates(start_weeks=3)
        requested_end_date, _ = self.create_dates(start_weeks=4)
        self.clcs = api.circulation.loan_items(self.cu, [self.ci],
                                               start_date1, end_date1,
                                               False)
        self.clcs.extend(api.circulation.request_items(self.cu, [self.ci],
                                                       start_date2,
                                                       end_date2, False))
        clc = self.clcs[0]
        api.loan_cycle.loan_extension([clc], requested_end_date, True)
        self.assertTrue(clc.end_date == start_date2 - datetime.timedelta(days=1))
        self.assertTrue(clc.desired_end_date == requested_end_date)

        self.delete_test_data()

    def test_loan_extension_waitlist_update(self):
        import invenio.modules.circulation.api as api
        import invenio.modules.circulation.models as models

        self.create_test_data()

        start_date1, end_date1 = self.create_dates(end_weeks=2)
        start_date2, end_date2 = self.create_dates(start_weeks=3)
        requested_end_date, _ = self.create_dates(start_weeks=4)
        self.clcs = api.circulation.loan_items(self.cu, [self.ci],
                                               start_date1, end_date1,
                                               False)
        self.clcs.extend(api.circulation.request_items(self.cu, [self.ci],
                                                       start_date2,
                                                       end_date2, False))
        clc = self.clcs[0]
        api.loan_cycle.loan_extension([clc], requested_end_date, True)
        self.assertTrue(clc.end_date == start_date2 - datetime.timedelta(days=1))
        self.assertTrue(clc.desired_end_date == requested_end_date)

        api.loan_cycle.cancel_clcs([self.clcs[1]])
        self.assertTrue(clc.end_date == requested_end_date)
        self.assertTrue(clc.desired_end_date == requested_end_date)

        self.delete_test_data()

    def test_update_waitlist(self):
        # TODO
        pass

TEST_SUITE = make_test_suite(TestLoanCycleApi)
if __name__ == "__main__":
       run_test_suite(TEST_SUITE)
