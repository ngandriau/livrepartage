from django.urls import path

from . import views

app_name = 'livres'
urlpatterns = [
    path('', views.index_view, name='index'),
    # ex: /livres/5/
    path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    path('initnewlivre/', views.requete_nouveau_livre, name='reqnouvlivre'),
    path('initeditlivre/<int:pk>/', views.requete_edit_livre, name='reqeditlivre'),
    path('submitnewlivre/', views.submit_nouveau_livre, name='subnouvlivre'),
    path('submiteditlivre/', views.submit_edit_livre, name='subeditlivre'),
    path('demandetransfert/<int:pk>/', views.demande_transfert_livre, name='demandelivre'),
    path('transfertmeslivres/', views.list_demandes_transfert_mes_livres, name='listtransfertmeslivre'),
    path('listreceptionaconfirmer/', views.list_reception_livre_a_confirmer, name='listreceptionaconfirmer'),
    path('listmesdemandestransfert/', views.list_mes_demandes_transfert_de_livres, name='listmesdemandestransfert'),
    path('livretransmis/<int:pk>/', views.livre_a_ete_transfere, name='livretransmis'),
    path('livrerecu/<int:pk>/', views.livre_a_ete_recu, name='livrerecu'),
    path('annultransfert/<int:pk>/', views.annul_demande_transfert, name='annultransfert'),

]