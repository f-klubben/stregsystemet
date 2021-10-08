from django import forms

from fkult.models import Movie
from treo.settings import cfg


class EventForm(forms.Form):
    theme = forms.CharField(label="The theme of your event suggestion")


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
            raise forms.ValidationError(f'{cleaned_id} is not a valid IMDB/TMDb id')

        return cleaned_id
