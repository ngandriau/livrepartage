from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Livre, Transfert
from .models import UserProfile


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


class LivreAdmin(admin.ModelAdmin):
    # fields = ['pub_date', 'question_text']
    readonly_fields = ["creation_date"]
    list_display = ('titre_text', 'auteur_text', 'creation_date', 'transferable_status', 'possesseur', 'createur', 'livre_code')
    list_filter = ['creation_date', 'transferable_status', 'possesseur', 'createur']
    search_fields = ['titre_text', 'livre_code', 'auteur_text', 'createur__first_name', 'createur__last_name', 'possesseur__first_name', 'possesseur__last_name', 'possesseur__username', 'createur__username']


class TransfertAdmin(admin.ModelAdmin):
    # fields = ['pub_date', 'question_text']
    readonly_fields = ["creation_date"]
    list_display = (
    'demandeur', 'livre', 'creation_date', 'transfert_status')
    list_filter = ['creation_date', 'transfert_status', 'demandeur']
    search_fields = ['livre__titre_text', 'demandeur__first_name', 'demandeur__last_name', 'demandeur__username']


admin.site.register(Livre, LivreAdmin)
admin.site.register(Transfert, TransfertAdmin)
