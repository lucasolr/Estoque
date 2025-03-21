from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.contrib import messages
from .models import Produto
from .forms import ProdutoForm
from django.db.models import Q

def dashboard(request):
    query = request.GET.get('query', '')
    
    if query:
        produtos = Produto.objects.filter(
            Q(nome__icontains=query) | 
            Q(quantidade__icontains=query)
        )
    else:
        produtos = Produto.objects.all()
    
    total_itens = produtos.aggregate(total=Sum('quantidade'))['total'] or 0
    
    # Cálculo do valor total do estoque
    valor_total = produtos.aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantidade') * F('preco'), 
                output_field=DecimalField()
            )
        )
    )['total'] or 0
    
    context = {
        'produtos': produtos,
        'total_itens': total_itens,
        'valor_total': valor_total,
        'query': query
    }
    
    return render(request, 'produtos/dashboard.html', context)

def produto_create(request):
    if request.method == 'POST':
        form = ProdutoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Produto cadastrado com sucesso!')
            return redirect('dashboard')
    else:
        form = ProdutoForm()
    
    return render(request, 'produtos/produto_form.html', {'form': form})

def produto_update(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    
    if request.method == 'POST':
        form = ProdutoForm(request.POST, instance=produto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Produto atualizado com sucesso!')
            return redirect('dashboard')
    else:
        form = ProdutoForm(instance=produto)
    
    return render(request, 'produtos/produto_form.html', {'form': form, 'produto': produto})

def produto_delete(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    
    if request.method == 'POST':
        produto.delete()
        messages.success(request, 'Produto excluído com sucesso!')
        return redirect('dashboard')
    
    return render(request, 'produtos/produto_confirm_delete.html', {'produto': produto})

def atualizar_estoque(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    
    if request.method == 'POST':
        quantidade = int(request.POST.get('quantidade', 0))
        operacao = request.POST.get('operacao')
        
        if operacao == 'adicionar':
            produto.quantidade += quantidade
        elif operacao == 'remover':
            if produto.quantidade >= quantidade:
                produto.quantidade -= quantidade
            else:
                messages.error(request, 'Quantidade insuficiente em estoque.')
                return redirect('dashboard')
        
        produto.save()
        messages.success(request, f'Estoque de {produto.nome} atualizado com sucesso!')
        return redirect('dashboard')
    
    return render(request, 'produtos/atualizar_estoque.html', {'produto': produto})
