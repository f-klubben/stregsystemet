



from typing import Protocol

from django.db.models import Field


class _HasModelField(Protocol):
    @property
    def field(self) -> Field: ...


def name_of(field_descriptor: _HasModelField) -> str:
    return field_descriptor.field.name