import datetime

from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


class TestDateManager(InvenioTestCase):
    def create_dates(self, start_days=0, start_weeks=0,
                     end_days=0, end_weeks=4):
        start_date = (datetime.date.today() +
                      datetime.timedelta(days=start_days, weeks=start_weeks))
        end_date = (start_date +
                    datetime.timedelta(days=end_days, weeks=end_weeks))
        return start_date, end_date

    def test_contained_date1(self):
        """
        requested:  |-----|
        present:            |-----|
        """
        from invenio.modules.circulation.api.utils import DateManager

        start_date1 = datetime.date(2000, 1, 1)
        end_date1 = datetime.date(2000, 2, 1)
        start_date2 = datetime.date(2000, 3, 1)
        end_date2 = datetime.date(2000, 4, 1)
        
        contained = DateManager.get_contained_date(start_date1, end_date1,
                                                   [(start_date2, end_date2)])
        self.assertTrue(contained[0] == start_date1)
        self.assertTrue(contained[1] == end_date1)

    def test_contained_date2(self):
        """
        requested:  |-----|
        present:       |-----|
        """
        from invenio.modules.circulation.api.utils import DateManager

        start_date1 = datetime.date(2000, 1, 1)
        end_date1 = datetime.date(2000, 2, 1)
        start_date2 = datetime.date(2000, 1, 15)
        end_date2 = datetime.date(2000, 2, 15)
        
        contained = DateManager.get_contained_date(start_date1, end_date1,
                                                   [(start_date2, end_date2)])
        self.assertTrue(contained[0] == start_date1)
        self.assertTrue(contained[1] == start_date2 - datetime.timedelta(days=1))

    def test_contained_date3(self):
        """
        requested:      |-----|
        present:       |-------|
        """
        from invenio.modules.circulation.api.utils import (DateManager,
                                                           DateException)

        start_date1 = datetime.date(2000, 1, 15)
        end_date1 = datetime.date(2000, 2, 15)
        start_date2 = datetime.date(2000, 1, 1)
        end_date2 = datetime.date(2000, 3, 1)
        
        with self.assertRaises(DateException):
            contained = DateManager.get_contained_date(start_date1, end_date1,
                                                       [(start_date2, end_date2)])

    def test_contained_date4(self):
        """
        requested:      |-----|
        present:         |---|
        """
        from invenio.modules.circulation.api.utils import (DateManager,
                                                           DateException)

        start_date1 = datetime.date(2000, 1, 1)
        end_date1 = datetime.date(2000, 3, 1)
        start_date2 = datetime.date(2000, 1, 15)
        end_date2 = datetime.date(2000, 2, 15)
        
        contained = DateManager.get_contained_date(start_date1, end_date1,
                                                   [(start_date2, end_date2)])

        self.assertTrue(contained[0] == start_date1)
        self.assertTrue(contained[1] == start_date2 - datetime.timedelta(days=1))

    def test_contained_date5(self):
        """
        requested:      |-----|
        present:    |-----|
        """
        from invenio.modules.circulation.api.utils import DateManager

        start_date1 = datetime.date(2000, 1, 15)
        end_date1 = datetime.date(2000, 2, 15)
        start_date2 = datetime.date(2000, 1, 1)
        end_date2 = datetime.date(2000, 2, 1)
        
        contained = DateManager.get_contained_date(start_date1, end_date1,
                                                   [(start_date2, end_date2)])
        self.assertTrue(contained[0] == end_date2 + datetime.timedelta(days=1))
        self.assertTrue(contained[1] == end_date1)

    def test_contained_date6(self):
        """
        requested:          |-----|
        present:    |-----|
        """
        from invenio.modules.circulation.api.utils import DateManager

        start_date1 = datetime.date(2000, 3, 1)
        end_date1 = datetime.date(2000, 4, 1)
        start_date2 = datetime.date(2000, 1, 1)
        end_date2 = datetime.date(2000, 2, 1)
        
        contained = DateManager.get_contained_date(start_date1, end_date1,
                                                   [(start_date2, end_date2)])
        self.assertTrue(contained[0] == start_date1)
        self.assertTrue(contained[1] == end_date1)

    def test_date_suggestions1(self):
        """
        No periods
        """
        from invenio.modules.circulation.api.utils import DateManager

        suggested = DateManager.get_date_suggestions([])
        self.assertTrue(suggested == [datetime.date.today()])

    def test_date_suggestions2(self):
        """
        On period from today.
        """
        from invenio.modules.circulation.api.utils import DateManager

        start_date1 = datetime.date.today()
        end_date1 = start_date1 + datetime.timedelta(weeks=4)

        suggested = DateManager.get_date_suggestions([(start_date1,
                                                          end_date1)])
        self.assertTrue(suggested == [end_date1 + datetime.timedelta(days=1)])

    def test_date_suggestions3(self):
        """
        On period from today another later.
        """
        from invenio.modules.circulation.api.utils import DateManager

        start_date1 = datetime.date.today()
        end_date1 = start_date1 + datetime.timedelta(weeks=4)
        start_date2 = datetime.date.today() + datetime.timedelta(weeks=6)
        end_date2 = start_date2 + datetime.timedelta(weeks=4)

        suggested = DateManager.get_date_suggestions([(start_date1,
                                                          end_date1),
                                                         (start_date2,
                                                          end_date2)])
        self.assertTrue(len(suggested) == 2)
        self.assertTrue(suggested[0] == (end_date1 + datetime.timedelta(days=1), start_date2 - datetime.timedelta(days=1)))
        self.assertTrue(suggested[1] == end_date2 + datetime.timedelta(days=1))

    def test_date_suggestions4(self):
        """
        On period in the future.
        """
        from invenio.modules.circulation.api.utils import DateManager

        start_date1 = datetime.date.today() + datetime.timedelta(weeks=2)
        end_date1 = start_date1 + datetime.timedelta(weeks=4)

        suggested = DateManager.get_date_suggestions([(start_date1,
                                                          end_date1)])
        self.assertTrue(len(suggested) == 2)
        self.assertTrue(suggested[0] == (datetime.date.today(), start_date1 - datetime.timedelta(days=1)))
        self.assertTrue(suggested[1] == end_date1 + datetime.timedelta(days=1))

    def test_date_suggestions5(self):
        """
        On period in the future another later.
        """
        from invenio.modules.circulation.api.utils import DateManager

        start_date1 = datetime.date.today() + datetime.timedelta(weeks=2)
        end_date1 = start_date1 + datetime.timedelta(weeks=4)
        start_date2 = datetime.date.today() + datetime.timedelta(weeks=8)
        end_date2 = start_date2 + datetime.timedelta(weeks=4)

        suggested = DateManager.get_date_suggestions([(start_date1,
                                                          end_date1),
                                                         (start_date2,
                                                          end_date2)])
        self.assertTrue(len(suggested) == 3)
        self.assertTrue(suggested[0] == (datetime.date.today(), start_date1 - datetime.timedelta(days=1)))
        self.assertTrue(suggested[1] == (end_date1 + datetime.timedelta(days=1), start_date2 - datetime.timedelta(days=1)))
        self.assertTrue(suggested[2] == end_date2 + datetime.timedelta(days=1))


TEST_SUITE = make_test_suite(TestDateManager,)

if __name__ == "__main__":
       run_test_suite(TEST_SUITE)
