from django import template

register = template.Library()


def proposer_format(member):
    from stregsystem.models import Member
    if isinstance(member, Member):
        return f"{member.firstname}, fra {member.year}"
    else:
        return "N/A"


register.filter('proposer_format', proposer_format)


def movie_imdb_link(movie):
    return f'<a href="https://www.imdb.com/title/{movie.id}/">{movie.__str__()}</a>'


register.filter('movie_imdb_link', movie_imdb_link)
