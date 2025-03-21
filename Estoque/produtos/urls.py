from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('produto/new/', views.produto_create, name='produto_create'),
    path('produto/<int:pk>/edit/', views.produto_update, name='produto_update'),
    path('produto/<int:pk>/delete/', views.produto_delete, name='produto_delete'),
    path('produto/<int:pk>/estoque/', views.atualizar_estoque, name='atualizar_estoque'),
] 