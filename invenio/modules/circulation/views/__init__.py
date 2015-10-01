"""View blueprints for circulation."""

from .circulation import blueprint as circulation_blueprint
from .lists import blueprint as lists_blueprint 
from .entity import blueprint as entity_blueprint

blueprints = [
    circulation_blueprint,
    lists_blueprint,
    entity_blueprint
]
