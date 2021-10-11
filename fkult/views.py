from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render

from fkult.forms import MovieForm, EventForm
from fkult.models import Movie, Event, Season


def index(request):
    # todo show calendar view of accepted events in current season
    curr_season = Season.objects.order_by('-id').first()
    events = Event.objects.filter(season=curr_season)
    # todo; get (calculate) current season
    #           get all events
    #           for each event, check for any None fields and try populate+save by API, on failure, put human-readablle unknown value
    #       put Object([Event{Movie}]) into data for template
    #   *fuck* this should actually be done post-save of movie objectl

    return render(request, "fkult/index.html", locals())


def suggest_event(request):
    movie_form = MovieForm()
    event_form = EventForm()

    # todo check that suggestions have not been accepted within the previous 7 years
    #   (correct for startup of fkult, assuming 1st feb/1st sep yearly)
    #   (check for at least fember status, maybespecial permission?)

    # todo create movies (check for exists), add to event and save

    # handle submitted form
    if request.method == 'POST':
        movie_form = MovieForm(request.POST)
        if movie_form.is_valid():
            # if movie is valid, create Movie object from input id
            Movie.create_from_id(movie_form.cleaned_data['id'])

    return render(request, "fkult/suggest_event.html", locals())
