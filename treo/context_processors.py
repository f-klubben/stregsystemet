from django.utils import timezone

def september_context(request):
    month = timezone.now().month

    is_september = (month == 9)
    return {
        "is_september": is_september,
    }
