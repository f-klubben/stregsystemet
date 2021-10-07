from django.contrib import admin

# Register your models here.
from fkult.models import Movie, Event

admin.site.register(Movie)
admin.site.register(Event)