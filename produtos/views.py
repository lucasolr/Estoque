from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Count, Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
from .models import Produto, ProdutoImagem, Transacao, AlertaEstoqueBaixo, PrevisaoEstoque, Categoria
from .forms import ProdutoForm, TransacaoForm, ProdutoImagemForm, FiltroTransacaoForm

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
    
    # Alertas de estoque baixo
    alertas = AlertaEstoqueBaixo.objects.filter(resolvido=False).count()
    
    context = {
        'produtos': produtos,
        'total_itens': total_itens,
        'valor_total': valor_total,
        'query': query,
        'alertas': alertas
    }
    
    return render(request, 'produtos/dashboard.html', context)

def listar_produtos(request):
    query = request.GET.get('query', '')
    
    if query:
        produtos = Produto.objects.filter(
            Q(nome__icontains=query) | 
            Q(quantidade__icontains=query)
        )
    else:
        produtos = Produto.objects.all().order_by('nome')
    
    # Alertas de estoque baixo (para o contador na sidebar)
    alertas = AlertaEstoqueBaixo.objects.filter(resolvido=False).count()
    
    context = {
        'produtos': produtos,
        'query': query,
        'alertas': alertas,
        'titulo': 'Lista de Produtos'
    }
    
    return render(request, 'produtos/listar_produtos.html', context)

def produto_create(request):
    if request.method == 'POST':
        form = ProdutoForm(request.POST)
        if form.is_valid():
            produto = form.save()
            messages.success(request, 'Produto cadastrado com sucesso!')
            return redirect('dashboard')
        else:
            # Debugging for form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erro no campo {field}: {error}")
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
        motivo = request.POST.get('motivo', '')
        observacao = request.POST.get('observacao', '')
        
        if operacao == 'adicionar':
            produto.quantidade += quantidade
            tipo_transacao = 'entrada'
        elif operacao == 'remover':
            if produto.quantidade >= quantidade:
                produto.quantidade -= quantidade
                tipo_transacao = 'saida'
            else:
                messages.error(request, 'Quantidade insuficiente em estoque.')
                return redirect('dashboard')
        
        # Salvar a transação
        Transacao.objects.create(
            produto=produto,
            quantidade=quantidade,
            tipo=tipo_transacao,
            motivo=motivo,
            observacao=observacao,
            usuario=request.user if request.user.is_authenticated else None
        )
        
        produto.save()
        messages.success(request, f'Estoque de {produto.nome} atualizado com sucesso!')
        return redirect('dashboard')
    
    return render(request, 'produtos/atualizar_estoque.html', {'produto': produto})

def alertas_estoque(request):
    alertas = AlertaEstoqueBaixo.objects.filter(resolvido=False)
    
    context = {
        'alertas': alertas,
        'count': alertas.count()
    }
    
    return render(request, 'produtos/alertas_estoque.html', context)

def historico_transacoes(request):
    form = FiltroTransacaoForm(request.GET)
    transacoes = Transacao.objects.all().select_related('produto', 'usuario')
    
    if form.is_valid():
        if form.cleaned_data['data_inicio']:
            transacoes = transacoes.filter(data__gte=form.cleaned_data['data_inicio'])
        
        if form.cleaned_data['data_fim']:
            # Adicionar um dia para incluir todas as transações do último dia
            data_fim = form.cleaned_data['data_fim'] + timedelta(days=1)
            transacoes = transacoes.filter(data__lt=data_fim)
        
        if form.cleaned_data['produto']:
            transacoes = transacoes.filter(produto=form.cleaned_data['produto'])
        
        if form.cleaned_data['tipo']:
            transacoes = transacoes.filter(tipo=form.cleaned_data['tipo'])
    
    # Estatísticas
    entradas = transacoes.filter(tipo='entrada').aggregate(total=Sum('quantidade'))['total'] or 0
    saidas = transacoes.filter(tipo='saida').aggregate(total=Sum('quantidade'))['total'] or 0
    
    context = {
        'form': form,
        'transacoes': transacoes[:100],  # Limitar para os 100 mais recentes
        'entradas': entradas,
        'saidas': saidas,
        'saldo': entradas - saidas,
        'total_registros': transacoes.count()
    }
    
    return render(request, 'produtos/historico_transacoes.html', context)

def previsao_estoque(request):
    produtos = Produto.objects.all()
    previsoes = []
    
    for produto in produtos:
        dias = produto.dias_ate_acabar()
        previsao, created = PrevisaoEstoque.objects.get_or_create(produto=produto)
        
        if dias is not None:
            previsao.dias_estimados = dias
            previsao.save()
        
        # Identificar status para código de cores
        if dias is None:
            status = 'indefinido'  # Cinza
        elif dias <= 7:
            status = 'critico'     # Vermelho
        elif dias <= 15:
            status = 'alerta'      # Amarelo
        else:
            status = 'normal'      # Verde
        
        previsoes.append({
            'produto': produto,
            'dias': dias,
            'status': status
        })
    
    context = {
        'previsoes': previsoes
    }
    
    return render(request, 'produtos/previsao_estoque.html', context)

def gerenciar_imagens(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    imagens = ProdutoImagem.objects.filter(produto=produto)
    
    if request.method == 'POST':
        form = ProdutoImagemForm(request.POST, request.FILES)
        if form.is_valid():
            nova_imagem = form.save(commit=False)
            nova_imagem.produto = produto
            
            # Se for definida como principal, remover status principal das outras
            if nova_imagem.principal:
                ProdutoImagem.objects.filter(produto=produto, principal=True).update(principal=False)
            
            nova_imagem.save()
            messages.success(request, 'Imagem adicionada com sucesso!')
            return redirect('gerenciar_imagens', pk=pk)
    else:
        form = ProdutoImagemForm()
    
    context = {
        'produto': produto,
        'imagens': imagens,
        'form': form
    }
    
    return render(request, 'produtos/gerenciar_imagens.html', context)

def deletar_imagem(request, pk):
    imagem = get_object_or_404(ProdutoImagem, pk=pk)
    produto_id = imagem.produto.id
    
    if request.method == 'POST':
        imagem.delete()
        messages.success(request, 'Imagem excluída com sucesso!')
        return redirect('gerenciar_imagens', pk=produto_id)
    
    return render(request, 'produtos/deletar_imagem.html', {'imagem': imagem})

def definir_imagem_principal(request, pk):
    imagem = get_object_or_404(ProdutoImagem, pk=pk)
    produto = imagem.produto
    
    # Remover status principal de todas as imagens deste produto
    ProdutoImagem.objects.filter(produto=produto, principal=True).update(principal=False)
    
    # Definir esta imagem como principal
    imagem.principal = True
    imagem.save()
    
    messages.success(request, 'Imagem definida como principal com sucesso!')
    return redirect('gerenciar_imagens', pk=produto.id)

# Novas funções de visualização 
def configuracoes(request):
    # Alertas de estoque baixo (para o contador na sidebar)
    alertas = AlertaEstoqueBaixo.objects.filter(resolvido=False).count()
    
    context = {
        'titulo': 'Configurações do Sistema',
        'alertas': alertas
    }
    return render(request, 'produtos/configuracoes.html', context)

def perfil_usuario(request):
    # Alertas de estoque baixo (para o contador na sidebar)
    alertas = AlertaEstoqueBaixo.objects.filter(resolvido=False).count()
    
    context = {
        'titulo': 'Perfil do Usuário',
        'alertas': alertas
    }
    return render(request, 'produtos/perfil_usuario.html', context)

def relatorios(request):
    # Calcula estatísticas gerais
    total_produtos = Produto.objects.count()
    total_itens = Produto.objects.aggregate(total=Sum('quantidade'))['total'] or 0
    
    # Valor total do estoque
    valor_total = Produto.objects.aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantidade') * F('preco'), 
                output_field=DecimalField()
            )
        )
    )['total'] or 0
    
    # Produtos com estoque baixo
    produtos_estoque_baixo = Produto.objects.filter(
        quantidade__lte=F('estoque_minimo')
    ).count()
    
    # Total de transações nos últimos 30 dias
    data_inicio = timezone.now() - timedelta(days=30)
    total_transacoes = Transacao.objects.filter(data__gte=data_inicio).count()
    
    # Alertas de estoque baixo (para o contador na sidebar)
    alertas = AlertaEstoqueBaixo.objects.filter(resolvido=False).count()
    
    context = {
        'titulo': 'Relatórios',
        'total_produtos': total_produtos,
        'total_itens': total_itens,
        'valor_total': valor_total,
        'produtos_estoque_baixo': produtos_estoque_baixo,
        'total_transacoes': total_transacoes,
        'alertas': alertas
    }
    return render(request, 'produtos/relatorios.html', context)

def backup_sistema(request):
    # Alertas de estoque baixo (para o contador na sidebar)
    alertas = AlertaEstoqueBaixo.objects.filter(resolvido=False).count()
    
    if request.method == 'POST':
        # Aqui implementaríamos a lógica de backup, mas por enquanto vamos apenas simular
        messages.success(request, 'Backup realizado com sucesso!')
        return redirect('backup_sistema')
    
    context = {
        'titulo': 'Backup do Sistema',
        'alertas': alertas,
        'ultimo_backup': timezone.now() - timedelta(days=3)  # Simulação de data do último backup
    }
    return render(request, 'produtos/backup_sistema.html', context)

def categoria_list(request):
    categorias = Categoria.objects.all()
    
    # Alertas de estoque baixo (para o contador na sidebar)
    alertas = AlertaEstoqueBaixo.objects.filter(resolvido=False).count()
    
    context = {
        'categorias': categorias,
        'titulo': 'Categorias de Produtos',
        'alertas': alertas
    }
    
    return render(request, 'produtos/categoria_list.html', context)

def categoria_create(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao')
        
        categoria = Categoria.objects.create(
            nome=nome,
            descricao=descricao
        )
        
        messages.success(request, 'Categoria criada com sucesso!')
        return redirect('categoria_list')
    
    return redirect('categoria_list')

def categoria_update(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    
    if request.method == 'POST':
        categoria.nome = request.POST.get('nome')
        categoria.descricao = request.POST.get('descricao')
        categoria.save()
        
        messages.success(request, 'Categoria atualizada com sucesso!')
        return redirect('categoria_list')
    
    return redirect('categoria_list')

def categoria_delete(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    
    if request.method == 'POST':
        categoria.delete()
        messages.success(request, 'Categoria excluída com sucesso!')
        return redirect('categoria_list')
    
    return redirect('categoria_list')
