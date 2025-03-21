from django import forms
from .models import Produto, Transacao, ProdutoImagem

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['nome', 'descricao', 'quantidade', 'preco', 'estoque_minimo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control'}),
            'preco': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'estoque_minimo': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class TransacaoForm(forms.ModelForm):
    class Meta:
        model = Transacao
        fields = ['quantidade', 'tipo', 'motivo', 'observacao']
        widgets = {
            'quantidade': forms.NumberInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'motivo': forms.TextInput(attrs={'class': 'form-control'}),
            'observacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ProdutoImagemForm(forms.ModelForm):
    class Meta:
        model = ProdutoImagem
        fields = ['imagem', 'principal']
        widgets = {
            'imagem': forms.FileInput(attrs={'class': 'form-control'}),
            'principal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class FiltroTransacaoForm(forms.Form):
    data_inicio = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    data_fim = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    produto = forms.ModelChoiceField(
        queryset=Produto.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    tipo = forms.ChoiceField(
        choices=(('', 'Todos'),) + Transacao.TIPO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    ) 