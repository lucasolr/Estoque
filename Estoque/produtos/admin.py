from django.contrib import admin
from .models import Produto

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'quantidade', 'preco', 'valor_total', 'data_cadastro', 'data_atualizacao')
    search_fields = ('nome', 'descricao')
    list_filter = ('data_cadastro', 'data_atualizacao')
    readonly_fields = ('data_cadastro', 'data_atualizacao')
