from invenio.modules.circulation.models import CirculationUser, CirculationItem


def search(val):
    return {'items': CirculationItem.search(isbn=val),
            'users': CirculationUser.search(id=val)}
