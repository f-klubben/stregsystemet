from django.contrib import admin

# Register your models here.
from fkult.models import Movie, Event, Season

admin.site.register(Movie)
admin.site.register(Event)
admin.site.register(Season)
