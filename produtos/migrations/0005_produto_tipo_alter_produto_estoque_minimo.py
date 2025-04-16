# Generated by Django 5.1.7 on 2025-04-16 15:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produtos', '0004_remove_produto_preco'),
    ]

    operations = [
        migrations.AddField(
            model_name='produto',
            name='tipo',
            field=models.CharField(choices=[('novo', 'Novo'), ('usado', 'Usado')], default='novo', max_length=10),
        ),
        migrations.AlterField(
            model_name='produto',
            name='estoque_minimo',
            field=models.IntegerField(blank=True, help_text='Quantidade mínima para produtos novos antes de gerar alerta', null=True),
        ),
    ]
