from django.contrib import admin
from django.urls import path, include 
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('/', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('bulk-import/', views.bulk_import, name='bulk_import'),
    path('edit-user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('add-user/', views.add_user, name='add_user'),
]