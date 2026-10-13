



from django.db.models import BooleanField, CharField, ImageField, ManyToManyField, DateTimeField, DurationField
from django.db.models.fields import _FieldDescriptor
    

def name_of(field_descriptor: _FieldDescriptor[BooleanField | CharField | ImageField | ManyToManyField | DateTimeField | DurationField]) -> str:
    return field_descriptor.field.name 