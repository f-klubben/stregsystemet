from django.db import models

from oauth2_provider.models import AbstractCustomUser

class MemberSSO(AbstractCustomUser):
    username = models.CharField(max_length=40, unique=True)
