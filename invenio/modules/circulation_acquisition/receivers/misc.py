from invenio.base import signals
from invenio.base.scripts.database import create, drop, recreate


def create_circulation_acquisition_indices(sender, **kwargs):
    from invenio.modules.circulation_acquisition.models import entities
    from invenio.modules.circulation_acquisition.mappings import mappings
    for name, __, cls in filter(lambda x: x[0] != 'Record', entities):
        mapping = mappings.get(name, {})
        index = cls.__tablename__
        cls._es.indices.delete(index=index, ignore=404)
        cls._es.indices.create(index=index, body=mapping)


def delete_circulation_acquisition_indices(sender, **kwargs):
    from invenio.modules.circulation_acquisition.models import entities
    for _, __, cls in filter(lambda x: x[0] != 'Record', entities):
        cls._es.indices.delete(index=cls.__tablename__, ignore=404)


signals.pre_command.connect(delete_circulation_acquisition_indices, sender=drop)
signals.pre_command.connect(create_circulation_acquisition_indices, sender=create)
signals.pre_command.connect(delete_circulation_acquisition_indices, sender=recreate)
signals.pre_command.connect(create_circulation_acquisition_indices, sender=recreate)
