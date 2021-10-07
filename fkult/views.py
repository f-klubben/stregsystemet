from django.http import HttpResponse
from django.shortcuts import render

from fkult.models import Movie, Event


def index(request):
    # todo show calendar view of accepted events in current season
    data = dict()

    # todo; get (calculate) current season
    #           get all events
    #           for each event, check for any None fields and try populate+save by API, on failure, put human-readablle unknown value
    #       put Object([Event{Movie}]) into data for template
    #   *fuck* this should actually be done post-save of movie objectl

    return render(request, "fkult/index.html", data)


def suggest_event(request):
    data = dict()

    # todo check that suggestions have not been accepted within the previous 7 years
    #   (correct for startup of fkult, assuming 1st feb/1st sep yearly)
    #   (check for at least fember status, maybespecial permission?)

    # todo create movies (check for exists), add to event and save

    return render(request, "fkult/suggest_event.html", data)


def get_movie_info_api(imdb_id: str):
    # try lookup given id

    # except failure, put human-readable

    # else fail
    pass
