from django.db import models

# Create your models here.

class Produto(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    quantidade = models.IntegerField(default=0)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.nome
    
    def valor_total(self):
        return self.quantidade * self.preco
