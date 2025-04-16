from django.contrib import admin
from .models import Produto, ProdutoImagem, Transacao, AlertaEstoqueBaixo, PrevisaoEstoque, Categoria

class ProdutoImagemInline(admin.TabularInline):
    model = ProdutoImagem
    extra = 1

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'quantidade', 'estoque_minimo', 'esta_abaixo_do_minimo', 'data_cadastro', 'data_atualizacao')
    search_fields = ('nome', 'descricao')
    list_filter = ('tipo', 'data_cadastro', 'data_atualizacao')
    readonly_fields = ('data_cadastro', 'data_atualizacao')
    inlines = [ProdutoImagemInline]

@admin.register(ProdutoImagem)
class ProdutoImagemAdmin(admin.ModelAdmin):
    list_display = ('produto', 'principal', 'data_upload')
    list_filter = ('principal', 'data_upload')
    search_fields = ('produto__nome',)

@admin.register(Transacao)
class TransacaoAdmin(admin.ModelAdmin):
    list_display = ('produto', 'quantidade', 'tipo', 'motivo', 'data', 'usuario')
    list_filter = ('tipo', 'data', 'usuario')
    search_fields = ('produto__nome', 'motivo', 'observacao')
    readonly_fields = ('data',)

@admin.register(AlertaEstoqueBaixo)
class AlertaEstoqueBaixoAdmin(admin.ModelAdmin):
    list_display = ('produto', 'quantidade_atual', 'data_alerta', 'resolvido', 'data_resolucao')
    list_filter = ('resolvido', 'data_alerta', 'data_resolucao')
    search_fields = ('produto__nome',)
    readonly_fields = ('data_alerta',)

@admin.register(PrevisaoEstoque)
class PrevisaoEstoqueAdmin(admin.ModelAdmin):
    list_display = ('produto', 'dias_estimados', 'consumo_medio_diario', 'data_calculo')
    list_filter = ('data_calculo',)
    search_fields = ('produto__nome',)
    readonly_fields = ('data_calculo',)

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome',)
