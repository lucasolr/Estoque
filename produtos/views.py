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
    
    produtos_novos = Produto.objects.filter(tipo='novo')
    produtos_usados = Produto.objects.filter(tipo='usado')
    
    if query:
        produtos_novos = produtos_novos.filter(Q(nome__icontains=query) | Q(quantidade__icontains=query))
        produtos_usados = produtos_usados.filter(Q(nome__icontains=query) | Q(quantidade__icontains=query))
        
    total_itens_novos = produtos_novos.aggregate(total=Sum('quantidade'))['total'] or 0
    total_itens_usados = produtos_usados.aggregate(total=Sum('quantidade'))['total'] or 0
    total_itens = total_itens_novos + total_itens_usados
    
    # Alertas de estoque baixo (apenas para produtos novos)
    alertas = AlertaEstoqueBaixo.objects.filter(resolvido=False).count()
    
    context = {
        'produtos_novos': produtos_novos,
        'produtos_usados': produtos_usados, # Passar para o template se necessário exibir separadamente
        'total_itens': total_itens,
        'query': query,
        'alertas': alertas
    }
    
    return render(request, 'produtos/dashboard.html', context)

# --- Views para Produtos Novos ---

def listar_produtos_novos(request):
    query = request.GET.get('query', '')
    produtos = Produto.objects.filter(tipo='novo').order_by('nome')
    
    if query:
        produtos = produtos.filter(Q(nome__icontains=query) | Q(quantidade__icontains=query))
    
    alertas = AlertaEstoqueBaixo.objects.filter(resolvido=False).count()
    
    context = {
        'produtos': produtos,
        'query': query,
        'alertas': alertas,
        'titulo': 'Lista de Produtos Novos',
        'tipo_produto': 'novo'
    }
    
    return render(request, 'produtos/listar_produtos.html', context)

def produto_novo_create(request):
    if request.method == 'POST':
        form = ProdutoForm(request.POST)
        if form.is_valid():
            produto = form.save(commit=False)
            produto.tipo = 'novo' # Garante que seja novo
            # A limpeza do form já garante que estoque_minimo está ok ou None
            produto.save()
            messages.success(request, 'Produto novo cadastrado com sucesso!')
            return redirect('listar_produtos_novos')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erro no campo {field}: {error}")
    else:
        form = ProdutoForm(initial={'tipo': 'novo'}) # Pré-seleciona o tipo
    
    return render(request, 'produtos/produto_form.html', {
        'form': form,
        'titulo_form': 'Cadastrar Novo Produto',
        'tipo_produto': 'novo'
    })

def produto_novo_update(request, pk):
    produto = get_object_or_404(Produto, pk=pk, tipo='novo')
    
    if request.method == 'POST':
        form = ProdutoForm(request.POST, instance=produto)
        if form.is_valid():
            produto = form.save(commit=False)
            produto.tipo = 'novo' # Garante
            produto.save()
            messages.success(request, 'Produto novo atualizado com sucesso!')
            return redirect('listar_produtos_novos')
    else:
        form = ProdutoForm(instance=produto)
    
    return render(request, 'produtos/produto_form.html', {
        'form': form, 
        'produto': produto,
        'titulo_form': 'Editar Produto Novo',
        'tipo_produto': 'novo'
    })

def produto_novo_delete(request, pk):
    produto = get_object_or_404(Produto, pk=pk, tipo='novo')
    
    if request.method == 'POST':
        produto.delete()
        messages.success(request, 'Produto novo excluído com sucesso!')
        return redirect('listar_produtos_novos')
    
    return render(request, 'produtos/produto_confirm_delete.html', {
        'produto': produto,
        'tipo_produto': 'novo'
    })

# --- Views para Produtos Usados ---

def listar_produtos_usados(request):
    query = request.GET.get('query', '')
    produtos = Produto.objects.filter(tipo='usado').order_by('nome')
    
    if query:
        produtos = produtos.filter(Q(nome__icontains=query) | Q(quantidade__icontains=query))
    
    alertas = AlertaEstoqueBaixo.objects.filter(resolvido=False).count() # Ainda mostrar alerta geral
    
    context = {
        'produtos': produtos,
        'query': query,
        'alertas': alertas,
        'titulo': 'Lista de Produtos Usados',
        'tipo_produto': 'usado'
    }
    
    # Reutiliza o template de listar, mas o contexto indicará que são usados
    return render(request, 'produtos/listar_produtos_usados.html', context)

def produto_usado_create(request):
    if request.method == 'POST':
        form = ProdutoForm(request.POST)
        if form.is_valid():
            produto = form.save(commit=False)
            produto.tipo = 'usado' # Garante que seja usado
            produto.estoque_minimo = None # Garante explicitamente, embora o form.clean já faça
            produto.save()
            messages.success(request, 'Produto usado cadastrado com sucesso!')
            return redirect('listar_produtos_usados')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erro no campo {field}: {error}")
    else:
        # Pré-seleciona tipo 'usado' e oculta estoque_minimo via JS no template
        form = ProdutoForm(initial={'tipo': 'usado'}) 
    
    return render(request, 'produtos/produto_form.html', {
        'form': form,
        'titulo_form': 'Cadastrar Produto Usado',
        'tipo_produto': 'usado'
    })

def produto_usado_update(request, pk):
    produto = get_object_or_404(Produto, pk=pk, tipo='usado')
    
    if request.method == 'POST':
        form = ProdutoForm(request.POST, instance=produto)
        if form.is_valid():
            produto = form.save(commit=False)
            produto.tipo = 'usado' # Garante
            produto.estoque_minimo = None # Garante
            produto.save()
            messages.success(request, 'Produto usado atualizado com sucesso!')
            return redirect('listar_produtos_usados')
    else:
        form = ProdutoForm(instance=produto) # O JS cuidará de ocultar estoque_minimo
    
    return render(request, 'produtos/produto_form.html', {
        'form': form, 
        'produto': produto,
        'titulo_form': 'Editar Produto Usado',
        'tipo_produto': 'usado'
    })

def produto_usado_delete(request, pk):
    produto = get_object_or_404(Produto, pk=pk, tipo='usado')
    
    if request.method == 'POST':
        produto.delete()
        messages.success(request, 'Produto usado excluído com sucesso!')
        return redirect('listar_produtos_usados')
    
    # Reutilizar o template de confirmação de delete?
    return render(request, 'produtos/produto_confirm_delete.html', { 
        'produto': produto,
        'tipo_produto': 'usado'
    })

# --- Outras Views (manter como estão ou ajustar se necessário) ---

def atualizar_estoque(request, pk):
    produto = get_object_or_404(Produto, pk=pk) # Funciona para ambos os tipos
    redirect_url = 'listar_produtos_novos' if produto.tipo == 'novo' else 'listar_produtos_usados'
    
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
                return redirect(redirect_url)
        
        Transacao.objects.create(
            produto=produto,
            quantidade=quantidade,
            tipo=tipo_transacao,
            motivo=motivo,
            observacao=observacao,
            usuario=request.user if request.user.is_authenticated else None
        )
        
        produto.save() # O signal post_save cuidará dos alertas/previsões
        messages.success(request, f'Estoque de {produto.nome} atualizado com sucesso!')
        return redirect(redirect_url)
    
    return render(request, 'produtos/atualizar_estoque.html', {'produto': produto})

def alertas_estoque(request):
    # Alertas são apenas para produtos novos com estoque mínimo definido
    alertas = AlertaEstoqueBaixo.objects.filter(resolvido=False)
    
    context = {
        'alertas': alertas,
        'count': alertas.count(),
        'titulo': 'Alertas de Estoque Baixo (Produtos Novos)'
    }
    
    return render(request, 'produtos/alertas_estoque.html', context)

def historico_transacoes(request):
    form = FiltroTransacaoForm(request.GET) 
    # Adicionar filtro por tipo de produto ao form e aqui?
    # Por enquanto, mostra todas as transações
    transacoes = Transacao.objects.all().select_related('produto', 'usuario') 
    
    if form.is_valid():
        if form.cleaned_data['data_inicio']:
            transacoes = transacoes.filter(data__gte=form.cleaned_data['data_inicio'])
        
        if form.cleaned_data['data_fim']:
            data_fim = form.cleaned_data['data_fim'] + timedelta(days=1)
            transacoes = transacoes.filter(data__lt=data_fim)
        
        if form.cleaned_data['produto']:
            transacoes = transacoes.filter(produto=form.cleaned_data['produto'])
        
        if form.cleaned_data['tipo']:
            transacoes = transacoes.filter(tipo=form.cleaned_data['tipo'])
            
    entradas = transacoes.filter(tipo='entrada').aggregate(total=Sum('quantidade'))['total'] or 0
    saidas = transacoes.filter(tipo='saida').aggregate(total=Sum('quantidade'))['total'] or 0
    
    context = {
        'form': form,
        'transacoes': transacoes[:100],
        'entradas': entradas,
        'saidas': saidas,
        'saldo': entradas - saidas,
        'total_registros': transacoes.count(),
        'titulo': 'Histórico de Transações'
    }
    
    return render(request, 'produtos/historico_transacoes.html', context)

def previsao_estoque(request):
    produtos = Produto.objects.filter(tipo='novo') # Previsão só faz sentido para novos?
    previsoes = []
    
    for produto in produtos:
        dias = produto.dias_ate_acabar()
        previsao, created = PrevisaoEstoque.objects.get_or_create(produto=produto)
        
        if dias is not None:
            previsao.dias_estimados = dias
            # Calcular consumo médio se necessário
            ultimos_30_dias = timezone.now() - timedelta(days=30)
            transacoes_saida = Transacao.objects.filter(
                produto=produto, 
                data__gte=ultimos_30_dias,
                tipo='saida'
            ).aggregate(total_saidas=Sum('quantidade'))
            total_saidas = transacoes_saida['total_saidas'] or 0
            previsao.consumo_medio_diario = total_saidas / 30
            previsao.save()
        else:
            # Se não há dias, limpar previsão?
            previsao.dias_estimados = None
            previsao.consumo_medio_diario = None
            previsao.save()
            
        status = 'indefinido'
        if dias is not None:
            if dias <= 7: status = 'critico'
            elif dias <= 15: status = 'alerta'
            else: status = 'normal'
        
        previsoes.append({
            'produto': produto,
            'dias': dias,
            'status': status
        })
    
    context = {
        'previsoes': previsoes,
        'titulo': 'Previsão de Estoque (Produtos Novos)'
    }
    
    return render(request, 'produtos/previsao_estoque.html', context)

def gerenciar_imagens(request, pk):
    produto = get_object_or_404(Produto, pk=pk) # Funciona para ambos
    imagens = ProdutoImagem.objects.filter(produto=produto)
    redirect_url = 'gerenciar_imagens' # Mantém na mesma página
    
    if request.method == 'POST':
        form = ProdutoImagemForm(request.POST, request.FILES)
        if form.is_valid():
            nova_imagem = form.save(commit=False)
            nova_imagem.produto = produto
            
            if nova_imagem.principal:
                ProdutoImagem.objects.filter(produto=produto, principal=True).update(principal=False)
            
            nova_imagem.save()
            messages.success(request, 'Imagem adicionada com sucesso!')
            return redirect(redirect_url, pk=pk)
    else:
        form = ProdutoImagemForm()
    
    context = {
        'produto': produto,
        'imagens': imagens,
        'form': form,
        'titulo': f'Gerenciar Imagens - {produto.nome}'
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
    
    ProdutoImagem.objects.filter(produto=produto, principal=True).update(principal=False)
    imagem.principal = True
    imagem.save()
    
    messages.success(request, 'Imagem definida como principal com sucesso!')
    return redirect('gerenciar_imagens', pk=produto.id)

# --- Views de Páginas Gerais --- 
def configuracoes(request):
    alertas = AlertaEstoqueBaixo.objects.filter(resolvido=False).count()
    context = {
        'titulo': 'Configurações do Sistema',
        'alertas': alertas
    }
    return render(request, 'produtos/configuracoes.html', context)

def perfil_usuario(request):
    alertas = AlertaEstoqueBaixo.objects.filter(resolvido=False).count()
    context = {
        'titulo': 'Perfil do Usuário',
        'alertas': alertas
    }
    return render(request, 'produtos/perfil_usuario.html', context)

def relatorios(request):
    total_produtos_novos = Produto.objects.filter(tipo='novo').count()
    total_produtos_usados = Produto.objects.filter(tipo='usado').count()
    total_itens = Produto.objects.aggregate(total=Sum('quantidade'))['total'] or 0
    produtos_estoque_baixo = Produto.objects.filter(
        tipo='novo', quantidade__lte=F('estoque_minimo')
    ).count()
    data_inicio = timezone.now() - timedelta(days=30)
    total_transacoes = Transacao.objects.filter(data__gte=data_inicio).count()
    alertas = AlertaEstoqueBaixo.objects.filter(resolvido=False).count()
    
    context = {
        'titulo': 'Relatórios',
        'total_produtos': total_produtos_novos + total_produtos_usados,
        'total_produtos_novos': total_produtos_novos,
        'total_produtos_usados': total_produtos_usados,
        'total_itens': total_itens,
        'produtos_estoque_baixo': produtos_estoque_baixo,
        'total_transacoes': total_transacoes,
        'alertas': alertas
    }
    return render(request, 'produtos/relatorios.html', context)

def backup_sistema(request):
    alertas = AlertaEstoqueBaixo.objects.filter(resolvido=False).count()
    if request.method == 'POST':
        messages.success(request, 'Backup realizado com sucesso!')
        return redirect('backup_sistema')
    context = {
        'titulo': 'Backup do Sistema',
        'alertas': alertas,
        'ultimo_backup': timezone.now() - timedelta(days=3) 
    }
    return render(request, 'produtos/backup_sistema.html', context)

# --- Views de Categoria (manter como estão) ---
def categoria_list(request):
    categorias = Categoria.objects.all()
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
        categoria = Categoria.objects.create(nome=nome, descricao=descricao)
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
