from django.urls import path
from .views import dashboard_view, index_view, auth_view, register_view, transaction_view, categories_view, budgets_view, export_view, profile_view, logout_view
from . import views

urlpatterns = [
    path('', index_view, name='index'),  # page d'accueil
    path('dashboard/', dashboard_view, name='dashboard'),  # si tu as aussi dashboard_view
    path('auth/', auth_view, name='auth'),  # Ajoute cette ligne
    path('register/', register_view, name='register'),
    path('transactions/', transaction_view, name='transactions'),
    path('categories/', categories_view, name='categories'),
    path('budgets/', budgets_view, name='budgets'),
    path('export/', export_view, name='export'),
    path('profile/', profile_view, name='profile'),
    path('logout/', logout_view, name='logout'),
]