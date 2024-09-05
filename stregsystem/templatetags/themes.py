from logging import getLogger
from urllib.parse import quote, urljoin
from datetime import timedelta
from django import template
from django.utils import timezone
from django.utils.html import conditional_escape
from django.utils.encoding import iri_to_uri
from django.contrib.staticfiles.storage import staticfiles_storage
from django.db.models import Q, F
from stregsystem.models import Theme

logger = getLogger(__name__)
register = template.Library()


# Paths to the theme files
THEMES_URL = "stregsystem/themes/"
THEMES_STATIC_URL = staticfiles_storage.url(THEMES_URL)
THEMES_TEMPLATE_URL = THEMES_URL

# The database query is cached for this long
cache_ttl = timedelta(seconds=30)


class PrefixNode(template.Node):
    def __init__(self, base, name):
        self.base = base
        self.name = name

    def __repr__(self):
        return "<PrefixNode for %r>" % self.name

    @classmethod
    def handle_token(cls, base, name, parser, token):
        return cls(base, name)

    @classmethod
    def handle_simple(cls, base):
        return iri_to_uri(base)

    def render(self, context):
        return self.handle_simple(self.base)


@register.tag
def get_themes_static_prefix(parser, token):
    return PrefixNode.handle_token(THEMES_STATIC_URL, "themes static prefix", parser, token)


class ThemesNode(template.Node):
    def __init__(self, base, path):
        self.base = base
        self.path = path

    def __repr__(self):
        return f"{self.__class__.__name__}(base={self.base!r}, path={self.path!r})"

    def url(self, context, base):
        path = self.path.resolve(context)
        return self.handle_simple(base, path)

    def render(self, context):
        url = self.url(context, self.base)
        if context.autoescape:
            url = conditional_escape(url)
        return url

    @classmethod
    def handle_simple(cls, base, path):
        return urljoin(PrefixNode.handle_simple(base), quote(path))

    @classmethod
    def handle_token(cls, base, parser, token):
        bits = token.split_contents()

        if len(bits) < 2:
            raise template.TemplateSyntaxError("'%s' must be given a path to a file" % bits[0])

        path = parser.compile_filter(bits[1])

        return cls(base, path)


@register.tag("themes_static")
def do_themes_static(parser, token):
    return ThemesNode.handle_token(THEMES_STATIC_URL, parser, token)


def themes_static(path):
    return ThemesNode.handle_simple(THEMES_STATIC_URL, path)


@register.tag("themes_template")
def do_themes_template(parser, token):
    return ThemesNode.handle_token(THEMES_TEMPLATE_URL, parser, token)


def themes_template(path):
    return ThemesNode.handle_simple(THEMES_TEMPLATE_URL, path)


cache_timestamp = None
style_paths = []
script_paths = []
content_paths = []


def get_paths():
    global cache_ttl, cache_timestamp, style_paths, script_paths, content_paths

    # You can change these values manually to debug the theming system
    now = timezone.now()
    month = now.month  # 1-12
    day = now.day  # 1-31

    # Exit early if the cache is fresh
    if cache_timestamp and now - cache_timestamp < cache_ttl:
        return

    try:
        # Get themes that are active for this month and day
        themes = Theme.objects.filter(
            # Always include force shown themes
            Q(override=Theme.SHOW)
            |
            # Never include force hidden themes
            ~Q(override=Theme.HIDE)
            & (
                (  # Month range check
                    # Support normal ranges, e.g. 20/4 - 20/8
                    (Q(begin_month__lte=month) & Q(end_month__gte=month))
                    |
                    # Support ranges across year boundaries, e.g. 20/11 - 20/2
                    (Q(begin_month__gt=F('end_month')) & (Q(begin_month__lte=month) | Q(end_month__gte=month)))
                )
                & (  # Day range check
                    ((~Q(begin_month=month) | Q(begin_day__lte=day)) & (~Q(end_month=month) | Q(end_day__gte=day)))
                )
            )
        )
        # We dont support ranges across year boundaries if they start and end in the same month
        # because we like our sanity and we respect the poor server that needs to process this query

        del style_paths[:]
        del script_paths[:]
        del content_paths[:]

        for theme in themes:
            if theme.css:
                style_paths.append(f"{theme.name}/{theme.css}")
            if theme.js:
                script_paths.append(f"{theme.name}/{theme.js}")
            if theme.html:
                content_paths.append(themes_template(f"{theme.name}/{theme.html}"))

        cache_timestamp = now

    except Exception as e:
        logger.error(f'Error loading themes: {str(e)}')


@register.inclusion_tag(themes_template('theme_styles.html'))
def theme_styles():
    get_paths()
    return {'paths': style_paths}


@register.inclusion_tag(themes_template('theme_scripts.html'))
def theme_scripts():
    get_paths()
    return {'paths': script_paths}


@register.inclusion_tag(themes_template('theme_content.html'))
def theme_content():
    get_paths()
    return {'paths': content_paths}
