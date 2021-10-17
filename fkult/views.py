from pprint import pprint

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.db import transaction
from django.forms import modelformset_factory
from django.shortcuts import render

from fkult.forms import MovieForm, EventForm, EventVoteForm
from fkult.models import Movie, Event, Season

CURR_SEASON = Season.objects.order_by('-id').first()


def index(request):
    curr_season = CURR_SEASON
    # todo show calendar view of accepted events in current season
    # events = Event.objects.filter(season=curr_season)
    events = Event.objects.all()

    return render(request, "fkult/index.html", locals())


def suggest_event(request):
    movie_formset_factory = modelformset_factory(Movie, form=MovieForm, extra=2, max_num=2)
    movie_formset = movie_formset_factory(queryset=Movie.objects.none())  # this is probably bad form
    event_form = EventForm()

    if request.method == 'POST':
        movie_formset = movie_formset_factory(request.POST)
        event_form = EventForm(request.POST)
        if movie_formset.is_valid():
            # todo check that suggestions have not been accepted within the previous 7 years
            if event_form.is_valid():
                # get but don't save modelforms
                event = event_form.save(commit=False)
                movies = movie_formset.save(commit=False)
                movies = [Movie.create_from_id(movie.id) for movie in movies]

                # create event
                e = Event.objects.create(theme=event.theme, proposer=event.proposer)
                [e.movies.add(m) for m in movies]
                e.save()

    return render(request, "fkult/suggest.html", locals())


@staff_member_required()
@permission_required("fkult.admin") # todo, make fkult permission
def vote_event(request):
    curr_season = CURR_SEASON

    vote_formset_factory = modelformset_factory(Event, form=EventVoteForm, extra=0)
    vote_formset = vote_formset_factory(queryset=Event.objects.filter(season__isnull=True))  # this is probably bad form

    if request.method == 'POST':
        vote_formset = vote_formset_factory(request.POST or None)
        if vote_formset.is_valid():
            print('yar')
            vote_formset.save()
        else:
            print('nar')
        pprint(vote_formset)


    return render(request, "fkult/vote.html", locals())
