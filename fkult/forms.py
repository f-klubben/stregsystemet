from django import forms

from fkult.models import Movie, Event
from stregsystem.models import Member
from treo.settings import cfg
from django_select2 import forms as s2forms


class Select2MemberWidget(s2forms.ModelSelect2Widget):
    search_fields = ['username__icontains', 'firstname__icontains', 'lastname__icontains', 'email__icontains']
    model = Member


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        exclude = []
        widgets = {"proposer": Select2MemberWidget}


class MovieForm(forms.ModelForm):
    # movie_id = forms.CharField(label='The TMDB ID of movie', max_length=20)
    class Meta:
        model = Movie
        fields = ['id']

    def clean_id(self):
        cleaned_id = self.cleaned_data['id']
        from tmdbv3api import TMDb, exceptions, Movie as TMDbMovie

        tmdb = TMDb()
        tmdb.api_key = cfg.get("tmdb", "API_KEY")
        tmdb.language = 'en'
        tmdb_movie = TMDbMovie()

        # make TMDB lookup on id, if fail - get mad, otherwise just return same
        try:
            _ = tmdb_movie.details(movie_id=cleaned_id)
        except exceptions.TMDbException:
            raise forms.ValidationError(
                f'"{cleaned_id}" IMDB/TMDb id could not be found. Check your given ID on imdb.com or themoviedb.org'
            )

        return cleaned_id
