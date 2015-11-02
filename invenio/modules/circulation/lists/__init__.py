def get_circulation_lists():
    from invenio.modules.circulation.lists.on_loan_pending_requests import OnLoanPendingRequests
    from invenio.modules.circulation.lists.on_shelf_pending_requests import OnShelfPendingRequests
    from invenio.modules.circulation.lists.overdue_pending_requests import OverduePendingRequests
    from invenio.modules.circulation.lists.overdue_items import OverdueItems
    from invenio.modules.circulation.lists.latest_loans import LatestLoans
    return [('latest_loans', LatestLoans),
            ('overdue_items', OverdueItems),
            ('on_shelf_pending_requests', OnShelfPendingRequests),
            ('on_loan_pending_requests', OnLoanPendingRequests),
            ('overdue_pending_requests', OverduePendingRequests)]
