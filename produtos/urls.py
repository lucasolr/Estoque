from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    # URLs Produtos Novos
    path('produtos/novos/', views.listar_produtos_novos, name='listar_produtos_novos'),
    path('produtos/novos/novo/', views.produto_novo_create, name='produto_novo_create'),
    path('produtos/novos/<int:pk>/editar/', views.produto_novo_update, name='produto_novo_update'),
    path('produtos/novos/<int:pk>/excluir/', views.produto_novo_delete, name='produto_novo_delete'),
    
    # URLs Produtos Usados
    path('produtos/usados/', views.listar_produtos_usados, name='listar_produtos_usados'),
    path('produtos/usados/novo/', views.produto_usado_create, name='produto_usado_create'),
    path('produtos/usados/<int:pk>/editar/', views.produto_usado_update, name='produto_usado_update'),
    path('produtos/usados/<int:pk>/excluir/', views.produto_usado_delete, name='produto_usado_delete'),
    
    # URLs Comuns a ambos os tipos
    path('produto/<int:pk>/estoque/', views.atualizar_estoque, name='atualizar_estoque'),
    path('produto/<int:pk>/imagens/', views.gerenciar_imagens, name='gerenciar_imagens'),
    path('imagem/<int:pk>/delete/', views.deletar_imagem, name='deletar_imagem'),
    path('imagem/<int:pk>/principal/', views.definir_imagem_principal, name='definir_imagem_principal'),
    
    # Outras funcionalidades
    path('alertas/', views.alertas_estoque, name='alertas_estoque'),
    path('historico/', views.historico_transacoes, name='historico_transacoes'),
    path('previsao/', views.previsao_estoque, name='previsao_estoque'),
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