from django.conf import settings
from django.apps import apps as proj_apps

def my_context(request):
    debug_flag = settings.DEBUG
    return{"debug_flag":debug_flag, "livres_app_version": proj_apps.get_app_config('livres').version, }