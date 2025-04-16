from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import os
from django.utils import timezone
from datetime import timedelta
import uuid
from django.db.models import Sum

# Create your models here.

class Produto(models.Model):
    TIPO_CHOICES = (
        ('novo', 'Novo'),
        ('usado', 'Usado'),
    )
    
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    quantidade = models.IntegerField(default=0)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    estoque_minimo = models.IntegerField(null=True, blank=True, help_text="Quantidade mínima para produtos novos antes de gerar alerta")
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='novo')
    
    def __str__(self):
        return self.nome
    
    def esta_abaixo_do_minimo(self):
        if self.tipo == 'novo' and self.estoque_minimo is not None:
            return self.quantidade <= self.estoque_minimo
        return False
    
    def dias_ate_acabar(self):
        # Verificar transações dos últimos 30 dias
        ultimos_30_dias = timezone.now() - timedelta(days=30)
        transacoes = Transacao.objects.filter(
            produto=self, 
            data__gte=ultimos_30_dias,
            tipo='saida'
        ).aggregate(total_saidas=Sum('quantidade'))
        
        total_saidas = transacoes['total_saidas'] or 0
        
        if total_saidas == 0:
            return None  # Sem dados suficientes ou sem consumo
            
        # Calcular média diária de saídas (considerando apenas dias com saída? Não, média em 30 dias)
        media_diaria = total_saidas / 30
        
        if media_diaria <= 0:
            return None  # Evita divisão por zero
            
        # Dias até acabar o estoque
        return round(self.quantidade / media_diaria)

def produto_imagem_upload_path(instance, filename):
    # Gera um nome único para o arquivo
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('produtos', 'imagens', filename)

class ProdutoImagem(models.Model):
    produto = models.ForeignKey(Produto, related_name='imagens', on_delete=models.CASCADE)
    imagem = models.ImageField(upload_to=produto_imagem_upload_path)
    principal = models.BooleanField(default=False)
    data_upload = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Imagem de {self.produto.nome}"
    
    class Meta:
        verbose_name = "Imagem de Produto"
        verbose_name_plural = "Imagens de Produtos"

class Transacao(models.Model):
    TIPO_CHOICES = (
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
    )
    
    produto = models.ForeignKey(Produto, related_name='transacoes', on_delete=models.CASCADE)
    quantidade = models.IntegerField()
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    motivo = models.CharField(max_length=100, blank=True, null=True)
    observacao = models.TextField(blank=True, null=True)
    data = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.tipo.capitalize()} de {self.quantidade} unidades de {self.produto.nome}"
    
    class Meta:
        verbose_name = "Transação"
        verbose_name_plural = "Transações"
        ordering = ['-data']

class AlertaEstoqueBaixo(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    data_alerta = models.DateTimeField(auto_now_add=True)
    quantidade_atual = models.IntegerField()
    resolvido = models.BooleanField(default=False)
    data_resolucao = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Alerta: {self.produto.nome} - {self.data_alerta.strftime('%d/%m/%Y')}"
    
    class Meta:
        verbose_name = "Alerta de Estoque Baixo"
        verbose_name_plural = "Alertas de Estoque Baixo"
        ordering = ['-data_alerta']

class PrevisaoEstoque(models.Model):
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    dias_estimados = models.IntegerField(null=True, blank=True)
    consumo_medio_diario = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    data_calculo = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.dias_estimados:
            return f"Previsão para {self.produto.nome}: {self.dias_estimados} dias"
        return f"Previsão para {self.produto.nome}: Indeterminado"
    
    class Meta:
        verbose_name = "Previsão de Estoque"
        verbose_name_plural = "Previsões de Estoque"

class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'

# Signals para manter o sistema automatizado

@receiver(post_save, sender=Produto)
def verificar_estoque_minimo(sender, instance, **kwargs):
    """Verifica se o produto está abaixo do mínimo e cria um alerta se necessário (apenas para produtos novos)"""
    if instance.tipo == 'novo' and instance.estoque_minimo is not None: # Apenas para produtos novos
        if instance.quantidade <= instance.estoque_minimo:
            # Verificar se já existe um alerta não resolvido
            alerta_existente = AlertaEstoqueBaixo.objects.filter(
                produto=instance,
                resolvido=False
            ).first()
            
            if not alerta_existente:
                AlertaEstoqueBaixo.objects.create(
                    produto=instance,
                    quantidade_atual=instance.quantidade
                )
        else:
            # Resolver alertas existentes se o estoque foi reabastecido
            alertas_abertos = AlertaEstoqueBaixo.objects.filter(
                produto=instance,
                resolvido=False
            )
            
            for alerta in alertas_abertos:
                alerta.resolvido = True
                alerta.data_resolucao = timezone.now()
                alerta.save()
    else:
        # Se o produto virou 'usado' ou não tem estoque mínimo, resolve alertas pendentes
        alertas_abertos = AlertaEstoqueBaixo.objects.filter(
            produto=instance,
            resolvido=False
        )
        for alerta in alertas_abertos:
            alerta.resolvido = True
            alerta.data_resolucao = timezone.now()
            alerta.save()

@receiver(post_save, sender=Transacao)
def atualizar_estoque_e_previsao(sender, instance, created, **kwargs):
    """Atualiza o estoque do produto após uma transação e recalcula previsões"""
    if created:  # Apenas se for uma nova transação
        produto = instance.produto
        
        # Atualizar previsão
        ultimos_30_dias = timezone.now() - timedelta(days=30)
        transacoes = Transacao.objects.filter(
            produto=produto, 
            data__gte=ultimos_30_dias,
            tipo='saida'
        )
        
        if transacoes.count() > 0:
            total_saidas = sum([t.quantidade for t in transacoes])
            consumo_medio = total_saidas / 30
            dias_estimados = round(produto.quantidade / consumo_medio) if consumo_medio > 0 else None
            
            # Atualizar ou criar previsão
            previsao, created = PrevisaoEstoque.objects.get_or_create(produto=produto)
            previsao.dias_estimados = dias_estimados
            previsao.consumo_medio_diario = consumo_medio
            previsao.save()
