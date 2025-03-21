from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('produtos/', views.listar_produtos, name='listar_produtos'),
    path('produto/new/', views.produto_create, name='produto_create'),
    path('produto/<int:pk>/edit/', views.produto_update, name='produto_update'),
    path('produto/<int:pk>/delete/', views.produto_delete, name='produto_delete'),
    path('produto/<int:pk>/estoque/', views.atualizar_estoque, name='atualizar_estoque'),
    
    # Novas URLs
    path('alertas/', views.alertas_estoque, name='alertas_estoque'),
    path('historico/', views.historico_transacoes, name='historico_transacoes'),
    path('previsao/', views.previsao_estoque, name='previsao_estoque'),
    
    # Gerenciamento de imagens
    path('produto/<int:pk>/imagens/', views.gerenciar_imagens, name='gerenciar_imagens'),
    path('imagem/<int:pk>/delete/', views.deletar_imagem, name='deletar_imagem'),
    path('imagem/<int:pk>/principal/', views.definir_imagem_principal, name='definir_imagem_principal'),
    
    # URLs para configurações e perfil
    path('configuracoes/', views.configuracoes, name='configuracoes'),
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
    path('relatorios/', views.relatorios, name='relatorios'),
    path('backup/', views.backup_sistema, name='backup_sistema'),
    
    # Categorias
    path('categorias/', views.categoria_list, name='categoria_list'),
    path('categoria/new/', views.categoria_create, name='categoria_create'),
    path('categoria/<int:pk>/edit/', views.categoria_update, name='categoria_update'),
    path('categoria/<int:pk>/delete/', views.categoria_delete, name='categoria_delete'),
    
    # Autenticação
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
] 