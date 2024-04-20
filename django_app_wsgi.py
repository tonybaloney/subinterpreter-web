from django import conf, http, urls
from django.core.handlers.wsgi import WSGIHandler

conf.settings.configure(ALLOWED_HOSTS="*", ROOT_URLCONF=__name__)

app = WSGIHandler()


def root(request):
    return http.JsonResponse({"message": "Hello World"})


urlpatterns = [urls.path("", root)]
