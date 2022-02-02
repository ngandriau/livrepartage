from django.contrib import admin
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import UserProfile
from .models import Livre, Transfert

admin.site.register(Livre)
admin.site.register(Transfert)

# Extension du model d'User pour avoir au moins une 'ville' en plus
# cf https://docs.djangoproject.com/en/4.0/topics/auth/customizing/
# which acts a bit like a singleton
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile utilisateurs'

# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
