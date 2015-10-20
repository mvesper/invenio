import datetime

from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase
from invenio.modules.circulation.tests.utils import CirculationTestBase


class TestCirculationLoanApi(CirculationTestBase):
    def test_loan_items_success_no_waitlist(self):
        """
        Simplest case: The item is available for loan
        """
        import invenio.modules.circulation.api as api
        import invenio.modules.circulation.models as models

        self.create_test_data()
        start_date, end_date = self.create_dates()

        self.clcs = api.circulation.loan_items(self.cu, [self.ci],
                                               start_date, end_date,
                                               False)

        clc = self.clcs[0]
        self.assertTrue(len(self.clcs) == 1)
        self.assertTrue(clc.user == self.cu)
        self.assertTrue(clc.item == self.ci)
        self.assertTrue(clc.current_status == models.CirculationLoanCycle.STATUS_ON_LOAN)
        self.assertTrue(clc.start_date == start_date)
        self.assertTrue(clc.end_date == end_date)
        self.assertTrue(clc.desired_start_date == start_date)
        self.assertTrue(clc.desired_end_date == end_date)

        self.delete_test_data()

    def test_loan_items_failure_start_date(self):
        """
        The start date is not valid: the loan_items function only works for
        today.
        """
        import invenio.modules.circulation.api as api
        from invenio.modules.circulation.api.utils import ValidationExceptions

        self.create_test_data()
        # The start_date starts tomorrow, which is not allowed in a loan
        start_date, end_date = self.create_dates(start_days=1)

        with self.assertRaises(ValidationExceptions):
            self.clcs = api.circulation.loan_items(self.cu, [self.ci],
                                                   start_date, end_date,
                                                   False)

        start_date, end_date = self.create_dates(start_days=-1)

        # The start_date starts yesterday, which is not allowed in a loan
        with self.assertRaises(ValidationExceptions):
            self.clcs = api.circulation.loan_items(self.cu, [self.ci],
                                                   start_date, end_date,
                                                   False)
        self.assertTrue(len(self.clcs) == 0)

        self.delete_test_data()

    def test_loan_items_failure_loan_period(self):
        """
        The desired loan period exceeds the allowed period.
        """
        import invenio.modules.circulation.api as api
        from invenio.modules.circulation.api.utils import ValidationExceptions

        self.create_test_data()
        # Loan period of 5 weeks
        start_date, end_date = self.create_dates(end_weeks=8)

        with self.assertRaises(ValidationExceptions):
            self.clcs = api.circulation.loan_items(self.cu, [self.ci],
                                                   start_date, end_date,
                                                   False)
        self.assertTrue(len(self.clcs) == 0)

        self.delete_test_data()

    def test_loan_items_failure_active_request_no_waitlist(self):
        """
        Request an item in the future, the status should therefore stay as
        'on_shelf' and the item should be loan-able.
        Since the request is two weeks in advance, the usual loan period of 
        four weeks intersects, so the loan fails.
        """
        import invenio.modules.circulation.api as api
        import invenio.modules.circulation.models as models
        from invenio.modules.circulation.api.utils import ValidationExceptions

        self.create_test_data()
        start_date1, end_date1 = self.create_dates()
        start_date2, end_date2 = self.create_dates(start_weeks=2)

        self.clcs = api.circulation.request_items(self.cu, [self.ci],
                                                  start_date2, end_date2,
                                                  False)

        with self.assertRaises(ValidationExceptions):
            self.clcs.extend(api.circulation.loan_items(self.cu, [self.ci],
                                                        start_date1, end_date1,
                                                        False))

        self.assertTrue(len(self.clcs) == 1)
        self.assertTrue(self.ci.current_status == models.CirculationItem.STATUS_ON_SHELF)

        self.delete_test_data()

    def test_loan_items_success_active_request_waitlist(self):
        """
        Request an item in the future, the status should therefore stay as
        'on_shelf' and the item should be loan-able.
        Since the request is two weeks in advance, the usual loan period of 
        four weeks intersects, but with the waitlist flag, the loan comes
        through. The end_date will be adjusted.
        """
        import invenio.modules.circulation.api as api
        import invenio.modules.circulation.models as models

        self.create_test_data()
        start_date1, end_date1 = self.create_dates()
        start_date2, end_date2 = self.create_dates(start_weeks=2)

        self.clcs = api.circulation.request_items(self.cu, [self.ci],
                                                  start_date2, end_date2,
                                                  False)

        self.clcs.extend(api.circulation.loan_items(self.cu, [self.ci],
                                                    start_date1, end_date1,
                                                    True))
        clc = self.clcs[1]
        self.assertTrue(len(self.clcs) == 2)
        self.assertTrue(self.ci.current_status == models.CirculationItem.STATUS_ON_LOAN)
        self.assertTrue(clc.start_date == start_date1)
        self.assertTrue(clc.desired_start_date == start_date1)
        self.assertTrue(clc.end_date == start_date2 - datetime.timedelta(days=1))
        self.assertTrue(clc.desired_end_date == end_date1)

        self.delete_test_data()


class TestCirculationRequestApi(CirculationTestBase):
    def test_request_items_success(self):
        """
        Simplest case: The item is available for request and requested in the
        future.
        """
        import invenio.modules.circulation.api as api
        import invenio.modules.circulation.models as models

        self.create_test_data()
        start_date, end_date = self.create_dates(start_weeks=2)

        self.clcs = api.circulation.request_items(self.cu, [self.ci],
                                                  start_date, end_date,
                                                  False)

        clc = self.clcs[0]
        self.assertTrue(len(self.clcs) == 1)
        self.assertTrue(clc.user == self.cu)
        self.assertTrue(clc.item == self.ci)
        self.assertTrue(clc.current_status == models.CirculationLoanCycle.STATUS_REQUESTED)
        self.assertTrue(clc.start_date == start_date)
        self.assertTrue(clc.end_date == end_date)
        self.assertTrue(clc.desired_start_date == start_date)
        self.assertTrue(clc.desired_end_date == end_date)

        self.delete_test_data()

    def test_request_items_failure_start_date(self):
        """
        The start date is not valid: the request_items function only works for
        today and future dates.
        """
        import invenio.modules.circulation.api as api
        from invenio.modules.circulation.api.utils import ValidationExceptions

        self.create_test_data()
        start_date, end_date = self.create_dates(start_days=-1)
        # The start_date starts yesterday, which is not allowed
        with self.assertRaises(ValidationExceptions):
            self.clcs = api.circulation.request_items(self.cu, [self.ci],
                                                      start_date, end_date,
                                                      False)
        self.assertTrue(len(self.clcs) == 0)

        self.delete_test_data()

    def test_request_items_failure_loan_period(self):
        """
        The desired loan period exceeds the allowed period.
        """
        import invenio.modules.circulation.api as api
        from invenio.modules.circulation.api.utils import ValidationExceptions

        self.create_test_data()
        # Loan period of 5 weeks
        start_date, end_date = self.create_dates(end_weeks=8)

        with self.assertRaises(ValidationExceptions):
            self.clcs = api.circulation.request_items(self.cu, [self.ci],
                                                      start_date, end_date,
                                                      False)
        self.assertTrue(len(self.clcs) == 0)

        self.delete_test_data()

    def test_request_items_failure_active_request_no_waitlist(self):
        """
        Request an item in the future, the status should therefore stay as
        'on_shelf' and the item should be loan-able.
        Since the request is two weeks in advance, the usual loan period of 
        four weeks intersects, so the loan fails.
        """
        import invenio.modules.circulation.api as api
        import invenio.modules.circulation.models as models
        from invenio.modules.circulation.api.utils import ValidationExceptions

        self.create_test_data()
        start_date1, end_date1 = self.create_dates()
        start_date2, end_date2 = self.create_dates(start_weeks=2)

        self.clcs = api.circulation.request_items(self.cu, [self.ci],
                                                  start_date2, end_date2,
                                                  False)

        with self.assertRaises(ValidationExceptions):
            self.clcs.extend(api.circulation.request_items(self.cu, [self.ci],
                                                           start_date1, end_date1,
                                                           False))

        self.assertTrue(len(self.clcs) == 1)
        self.assertTrue(self.ci.current_status == models.CirculationItem.STATUS_ON_SHELF)

        self.delete_test_data()

    def test_request_items_success_active_request_waitlist(self):
        """
        Request an item in the future, the status should therefore stay as
        'on_shelf' and the item should be loan-able.
        Since the request is two weeks in advance, the usual loan period of 
        four weeks intersects, but with the waitlist flag, the loan comes
        through. The end_date will be adjusted.
        """
        import invenio.modules.circulation.api as api
        import invenio.modules.circulation.models as models

        self.create_test_data()
        start_date1, end_date1 = self.create_dates()
        start_date2, end_date2 = self.create_dates(start_weeks=2)

        self.clcs = api.circulation.request_items(self.cu, [self.ci],
                                                  start_date2, end_date2,
                                                  False)

        self.clcs.extend(api.circulation.request_items(self.cu, [self.ci],
                                                       start_date1, end_date1,
                                                       True))
        clc = self.clcs[1]
        self.assertTrue(len(self.clcs) == 2)
        self.assertTrue(self.ci.current_status == models.CirculationItem.STATUS_ON_SHELF)
        self.assertTrue(clc.start_date == start_date1)
        self.assertTrue(clc.desired_start_date == start_date1)
        self.assertTrue(clc.end_date == start_date2 - datetime.timedelta(days=1))
        self.assertTrue(clc.desired_end_date == end_date1)

        self.delete_test_data()


class TestCirculationReturnApi(CirculationTestBase):
    def test_return_items_successful(self):
        import invenio.modules.circulation.api as api
        import invenio.modules.circulation.models as models

        self.create_test_data()
        start_date, end_date = self.create_dates()
        # Loan the item first
        self.clcs = api.circulation.loan_items(self.cu, [self.ci],
                                               start_date, end_date,
                                               False)
        
        api.circulation.return_items([self.ci])

        clc = self.clcs[0]
        self.assertTrue(len(self.clcs) == 1)
        self.assertTrue(self.ci.current_status == models.CirculationItem.STATUS_ON_SHELF)
        self.assertTrue(clc.current_status == models.CirculationLoanCycle.STATUS_FINISHED)

        self.delete_test_data()

    def test_return_items_failure(self):
        import invenio.modules.circulation.api as api
        from invenio.modules.circulation.api.utils import ValidationExceptions

        self.create_test_data()
        
        with self.assertRaises(ValidationExceptions):
            api.circulation.return_items([self.ci])

        self.delete_test_data()

    def test_return_items_successful_update_waitlist1(self):
        import invenio.modules.circulation.api as api
        import invenio.modules.circulation.models as models

        self.create_test_data()
        start_date1, end_date1 = self.create_dates()
        start_date2, end_date2 = self.create_dates(start_weeks=2)
        # Loan the item first
        self.clcs = api.circulation.loan_items(self.cu, [self.ci],
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

        # Return the item
        api.circulation.return_items([self.ci])

        # Check the start dates of clc2
        self.assertTrue(clc2.desired_start_date == start_date2)
        self.assertTrue(clc2.start_date == start_date2)

        self.delete_test_data()

TEST_SUITE = make_test_suite(TestCirculationLoanApi,
                             TestCirculationRequestApi,
                             TestCirculationReturnApi)
if __name__ == "__main__":
       run_test_suite(TEST_SUITE)
