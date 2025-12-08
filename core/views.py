from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import random
# Importação necessária para lidar com a hora atual
from datetime import date, time, datetime 

from .forms import RegisterForm, DepositForm, WithdrawalForm, BankDetailsForm
from .models import (
    PlatformSettings, CustomUser, Level, UserLevel, BankDetails, Deposit, 
    Withdrawal, Task, PlatformBankDetails, Roulette, RouletteSettings,
    DailyRewardCode, UserRewardClaim 
)

# --- FUNÇÕES DE NAVEGAÇÃO BÁSICAS ---

def home(request):
    """
    Redireciona o usuário autenticado para o menu e o não autenticado para o cadastro.
    """
    if request.user.is_authenticated:
        return redirect('menu')
    else:
        return redirect('cadastro')

def menu(request):
    """
    Página principal do menu após o login.
    """
    user_level = None
    levels = Level.objects.all().order_by('deposit_value')

    if request.user.is_authenticated:
        user_level = UserLevel.objects.filter(user=request.user, is_active=True).first()

    try:
        platform_settings = PlatformSettings.objects.first()
        whatsapp_link = platform_settings.whatsapp_link
        # >>> ADIÇÃO DO LINK DO TELEGRAM <<<
        telegram_link = platform_settings.telegram_link
    except (PlatformSettings.DoesNotExist, AttributeError):
        whatsapp_link = '#'
        telegram_link = '#'

    context = {
        'user_level': user_level,
        'levels': levels,
        'whatsapp_link': whatsapp_link,
        'telegram_link': telegram_link, # >>> ADICIONADO AO CONTEXTO <<<
    }
    return render(request, 'menu.html', context)

def cadastro(request):
    """
    Lida com o registro de novos usuários.
    """
    invite_code_from_url = request.GET.get('invite', None)
    
    # Constante para o bônus de boas-vindas
    WELCOME_BONUS = 750 

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            
            invited_by_code = form.cleaned_data.get('invited_by_code')
            
            if invited_by_code:
                try:
                    invited_by_user = CustomUser.objects.get(invite_code=invited_by_code)
                    user.invited_by = invited_by_user
                except CustomUser.DoesNotExist:
                    messages.error(request, 'Código de convite inválido.')
                    return render(request, 'cadastro.html', {'form': form})
            
            # Adiciona o bônus de boas-vindas ao saldo disponível
            user.available_balance = WELCOME_BONUS
            user.save()
            
            login(request, user)
            messages.success(request, f'Bem-vindo(a)! Você recebeu {WELCOME_BONUS} Kz de bônus de boas-vindas.')
            return redirect('menu')
        else:
            try:
                platform_settings = PlatformSettings.objects.first()
                whatsapp_link = platform_settings.whatsapp_link
                # >>> ADIÇÃO DO LINK DO TELEGRAM <<<
                telegram_link = platform_settings.telegram_link
            except (PlatformSettings.DoesNotExist, AttributeError):
                whatsapp_link = '#'
                telegram_link = '#'
            return render(request, 'cadastro.html', {'form': form, 'whatsapp_link': whatsapp_link, 'telegram_link': telegram_link})
    else:
        if invite_code_from_url:
            form = RegisterForm(initial={'invited_by_code': invite_code_from_url})
        else:
            form = RegisterForm()
    
    try:
        platform_settings = PlatformSettings.objects.first()
        whatsapp_link = platform_settings.whatsapp_link
        # >>> ADIÇÃO DO LINK DO TELEGRAM <<<
        telegram_link = platform_settings.telegram_link
    except (PlatformSettings.DoesNotExist, AttributeError):
        whatsapp_link = '#'
        telegram_link = '#'

    return render(request, 'cadastro.html', {'form': form, 'whatsapp_link': whatsapp_link, 'telegram_link': telegram_link}) # >>> ADICIONADO AO CONTEXTO <<<

def user_login(request):
    """
    Lida com o login do usuário.
    """
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('menu')
    else:
        form = AuthenticationForm()

    try:
        platform_settings = PlatformSettings.objects.first()
        whatsapp_link = platform_settings.whatsapp_link
        # >>> ADIÇÃO DO LINK DO TELEGRAM <<<
        telegram_link = platform_settings.telegram_link
    except (PlatformSettings.DoesNotExist, AttributeError):
        whatsapp_link = '#'
        telegram_link = '#'

    return render(request, 'login.html', {'form': form, 'whatsapp_link': whatsapp_link, 'telegram_link': telegram_link}) # >>> ADICIONADO AO CONTEXTO <<<

@login_required
def user_logout(request):
    """
    Lida com o logout do usuário.
    """
    logout(request)
    return redirect('menu')

# --- FUNÇÕES DE TRANSAÇÃO E FINANÇAS ---

@login_required
def deposito(request):
    """
    Lida com o envio de comprovativo de depósito pelo usuário.
    Implementa um fluxo de múltiplas etapas simulado no frontend.
    """
    platform_bank_details = PlatformBankDetails.objects.all()
    platform_settings = PlatformSettings.objects.first()
    deposit_instruction = platform_settings.deposit_instruction if platform_settings else 'Instruções de depósito não disponíveis.'
    
    # Busca todos os valores de depósito dos Níveis para a Etapa 2
    level_deposits = Level.objects.all().values_list('deposit_value', flat=True).distinct().order_by('deposit_value')
    # Converte os Decimais para strings formatadas para JS
    level_deposits_list = [str(d) for d in level_deposits] 

    if request.method == 'POST':
        # O formulário é submetido na Etapa 3
        form = DepositForm(request.POST, request.FILES)
        if form.is_valid():
            deposit = form.save(commit=False)
            deposit.user = request.user
            deposit.save()
            
            # Retorna a tela de sucesso
            return render(request, 'deposito.html', {
                'platform_bank_details': platform_bank_details,
                'deposit_instruction': deposit_instruction,
                'level_deposits_list': level_deposits_list,
                'deposit_success': True # Variável de contexto para a tela de sucesso
            })
        else:
            messages.error(request, 'Erro ao enviar o depósito. Verifique o valor e o comprovativo.')
    
    # Se não for POST ou se for a primeira vez acessando a página
    form = DepositForm()
    
    context = {
        'platform_bank_details': platform_bank_details,
        'deposit_instruction': deposit_instruction,
        'form': form,
        'level_deposits_list': level_deposits_list,
        'deposit_success': False, # Estado inicial
    }
    return render(request, 'deposito.html', context)

@login_required
def approve_deposit(request, deposit_id):
    """
    (Apenas para staff) Aprova um depósito pendente.
    """
    if not request.user.is_staff:
        messages.error(request, 'Você não tem permissão para realizar esta ação.')
        return redirect('menu')

    deposit = get_object_or_404(Deposit, id=deposit_id)
    if not deposit.is_approved:
        deposit.is_approved = True
        deposit.save()
        deposit.user.available_balance += deposit.amount
        deposit.user.save()
        messages.success(request, f'Depósito de {deposit.amount} Kz aprovado para {deposit.user.phone_number}. Saldo atualizado.')
    
    return redirect('renda')

@login_required
def saque(request):
    """
    Lida com a solicitação de saque pelo usuário.
    """
    platform_settings = PlatformSettings.objects.first()
    withdrawal_instruction = platform_settings.withdrawal_instruction if platform_settings else 'Instruções de saque não disponíveis.'
    
    withdrawal_records = Withdrawal.objects.filter(user=request.user).order_by('-created_at')
    
    has_bank_details = BankDetails.objects.filter(user=request.user).exists()
    
    # Regras de Saque
    MIN_WITHDRAWAL = 3000
    START_TIME = time(9, 0) # 09:00 horas
    END_TIME = time(17, 0) # 17:00 horas
    
    current_time = datetime.now().time()
    today = date.today()
    
    # 1. Verifica se já realizou saque hoje
    has_withdrawn_today = Withdrawal.objects.filter(user=request.user, created_at__date=today).exists()
    
    if request.method == 'POST':
        form = WithdrawalForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            
            if not has_bank_details:
                messages.error(request, 'Por favor, adicione suas coordenadas bancárias no seu perfil antes de solicitar um saque.')
                return redirect('perfil')
            
            # 2. Verifica a hora
            if not (START_TIME <= current_time <= END_TIME):
                messages.error(request, f'O saque só é permitido entre {START_TIME.strftime("%H:%M")} e {END_TIME.strftime("%H:%M")}.')
                return redirect('saque')

            # 3. Verifica se já sacou hoje
            if has_withdrawn_today:
                messages.error(request, 'Você só pode realizar 1 saque por dia.')
                return redirect('saque')
            
            # 4. Verifica o valor mínimo
            if amount < MIN_WITHDRAWAL:
                messages.error(request, f'O valor mínimo para saque é {MIN_WITHDRAWAL} Kz.')
            elif request.user.available_balance < amount:
                messages.error(request, 'Saldo insuficiente.')
            else:
                # Cria o registro de saque
                Withdrawal.objects.create(user=request.user, amount=amount)
                
                # Deduz o valor (será estornado se não for aprovado pelo staff)
                request.user.available_balance -= amount
                request.user.save()
                
                messages.success(request, 'Saque solicitado com sucesso. Aguarde a aprovação.')
                return redirect('saque')
    else:
        form = WithdrawalForm()

    context = {
        'withdrawal_instruction': withdrawal_instruction,
        'withdrawal_records': withdrawal_records,
        'form': form,
        'has_bank_details': has_bank_details,
        'has_withdrawn_today': has_withdrawn_today, # Adicionado para exibir info na tela, se necessário
    }
    return render(request, 'saque.html', context)

# --- FUNÇÕES DE TAREFA E NÍVEL ---

@login_required
def tarefa(request):
    """
    Exibe a página de tarefas e verifica o status diário.
    """
    user = request.user
    
    # Encontra o nível ativo do usuário
    active_level = UserLevel.objects.filter(user=user, is_active=True).first()
    has_active_level = active_level is not None
    
    # Define o número de tarefas (pode ser ajustado por settings, mas 1 é o padrão)
    max_tasks = 1
    tasks_completed_today = 0
    
    if has_active_level:
        today = date.today()
        tasks_completed_today = Task.objects.filter(user=user, completed_at__date=today).count()
    
    context = {
        'has_active_level': has_active_level,
        'active_level': active_level,
        'tasks_completed_today': tasks_completed_today,
        'max_tasks': max_tasks,
    }
    return render(request, 'tarefa.html', context)

@login_required
@require_POST
def process_task(request):
    """
    Processa a conclusão de uma tarefa diária.
    """
    user = request.user
    active_level = UserLevel.objects.filter(user=user, is_active=True).first()

    if not active_level:
        return JsonResponse({'success': False, 'message': 'Você não tem um nível ativo para realizar tarefas.'})

    today = date.today()
    tasks_completed_today = Task.objects.filter(user=user, completed_at__date=today).count()
    max_tasks = 1

    if tasks_completed_today >= max_tasks:
        return JsonResponse({'success': False, 'message': 'Você já concluiu todas as tarefas diárias.'})

    earnings = active_level.level.daily_gain
    Task.objects.create(user=user, earnings=earnings)
    user.available_balance += earnings
    user.save()

    return JsonResponse({'success': True, 'daily_gain': earnings})

@login_required
def nivel(request):
    """
    Página de níveis, lida com a compra de novos níveis.
    """
    levels = Level.objects.all().order_by('deposit_value')
    # Obtém apenas os IDs dos níveis ATIVOS do usuário
    user_levels_ids = UserLevel.objects.filter(user=request.user, is_active=True).values_list('level__id', flat=True)
    
    if request.method == 'POST':
        level_id = request.POST.get('level_id')
        level_to_buy = get_object_or_404(Level, id=level_id)

        # 1. Verifica se o usuário já possui este nível ativo
        if level_to_buy.id in user_levels_ids:
            messages.error(request, f'Você já possui o nível {level_to_buy.name} ativo.')
            return redirect('nivel')
        
        # 2. Verifica se tem saldo suficiente
        if request.user.available_balance >= level_to_buy.deposit_value:
            # 2.1. Deduz o valor
            request.user.available_balance -= level_to_buy.deposit_value
            
            # 2.2. Cria o novo nível ativo
            UserLevel.objects.create(user=request.user, level=level_to_buy, is_active=True)
            request.user.level_active = True
            
            # 2.3. Lógica de subsídio de convite (para o convidante)
            invited_by_user = request.user.invited_by
            
            if invited_by_user:
                # Nota: A lógica abaixo depende da existência do campo
                # 'first_level_invested_paid_to_inviter' no seu modelo CustomUser.
                
                # Lógica de subsídio de 15% (APENAS UMA VEZ)
                if not getattr(request.user, 'first_level_invested_paid_to_inviter', False):
                    # Calcula o subsídio
                    subsidy_percentage = 0.15 # 15%
                    subsidy_amount = level_to_buy.deposit_value * subsidy_percentage
                    
                    # Adiciona ao saldo do convidante
                    invited_by_user.subsidy_balance += subsidy_amount
                    invited_by_user.available_balance += subsidy_amount
                    invited_by_user.save()
                    
                    # Marca que o subsídio de primeiro investimento foi pago
                    # USANDO SETATTR CASO O CAMPO NÃO EXISTA, mas o ideal é adicioná-lo ao modelo.
                    setattr(request.user, 'first_level_invested_paid_to_inviter', True)
                    
                    messages.success(request, f'Parabéns! Seu convidado investiu e você recebeu {subsidy_amount:.2f} Kz de subsídio (15%).')
                else:
                    # Se for um investimento subsequente do mesmo convidado
                    messages.info(request, 'Subsídio de primeiro investimento já foi pago.')
            
            request.user.save()
            messages.success(request, f'Você comprou o nível {level_to_buy.name} com sucesso!')
        else:
            messages.error(request, 'Saldo insuficiente. Por favor, faça um depósito.')
        
        return redirect('nivel')
        
    context = {
        'levels': levels,
        'user_levels': user_levels_ids,
    }
    return render(request, 'nivel.html', context)

# --- FUNÇÕES DE EQUIPA E CONVITE ---

@login_required
def equipa(request):
    """
    Exibe informações sobre a equipe e o link de convite.
    Cria uma lista única de todos os membros diretos com seus status de investimento.
    """
    user = request.user

    # 1. Encontra todos os membros da equipe (convidados diretos)
    team_members = CustomUser.objects.filter(invited_by=user).order_by('-date_joined')
    team_count = team_members.count()

    # 2. Processa cada membro para criar a lista unificada com os detalhes necessários
    all_team_members = []
    
    for member in team_members:
        # Busca o nível ativo atual do membro
        active_level = UserLevel.objects.filter(user=member, is_active=True).first()
        
        # Define o status de investimento
        if active_level:
            investment_status = active_level.level.name # Nome do Nível
        else:
            investment_status = "Não Investiu"
            
        all_team_members.append({
            'phone_number': member.phone_number,
            'registration_date': member.date_joined,
            'investment_level': investment_status,
        })

    # 3. Cálculo do saldo de subsídios
    subsidy_balance = user.subsidy_balance

    # 4. Contexto para o template
    context = {
        'team_count': team_count, # Contagem total de membros
        'invite_link': request.build_absolute_uri(reverse('cadastro')) + f'?invite={user.invite_code}',
        'subsidy_balance': subsidy_balance, # Saldo de Subsídios
        'all_team_members': all_team_members, # Nova lista unificada
    }
    return render(request, 'equipa.html', context)

# --- FUNÇÕES DE ROLETAS ---

@login_required
def roleta(request):
    """
    Página da roleta.
    """
    user = request.user
    
    context = {
        'roulette_spins': user.roulette_spins,
    }
    
    return render(request, 'roleta.html', context)

@login_required
@require_POST
def spin_roulette(request):
    """
    Processa um giro na roleta, deduzindo um giro e concedendo um prêmio.
    """
    user = request.user

    if not user.roulette_spins or user.roulette_spins <= 0:
        return JsonResponse({'success': False, 'message': 'Você não tem giros disponíveis para a roleta.'})

    user.roulette_spins -= 1
    user.save()
    
    try:
        roulette_settings = RouletteSettings.objects.first()
        
        if roulette_settings and roulette_settings.prizes:
            # Garante que os prêmios são tratados como inteiros
            # Corrigido o erro de digitação de 'prrizes' para 'prizes'
            prizes_from_admin = [int(p.strip()) for p in roulette_settings.prizes.split(',') if p.strip().isdigit()]
            
            prizes_weighted = []
            # Se não houver prêmios válidos, usa o padrão
            if not prizes_from_admin:
                prizes = [100, 200, 300, 500, 1000, 2000]
                prize = random.choice(prizes)
            else:
                for prize_value in prizes_from_admin:
                    # Lógica de ponderação (exemplo: prêmios menores têm mais chance)
                    if prize_value <= 1000:
                        prizes_weighted.extend([prize_value] * 3) # Peso 3
                    else:
                        prizes_weighted.append(prize_value) # Peso 1
                
                # Se a lista ponderada ainda estiver vazia (só prêmios inválidos), usa o padrão
                if not prizes_weighted:
                    prizes = [100, 200, 300, 500, 1000, 2000]
                    prize = random.choice(prizes)
                else:
                    prize = random.choice(prizes_weighted)

    except RouletteSettings.DoesNotExist:
        prizes = [100, 200, 300, 500, 1000, 2000]
        prize = random.choice(prizes)
    except Exception as e:
        # Caso de erro na conversão ou lógica, usa o prêmio padrão
        print(f"Erro ao processar prêmios da roleta: {e}")
        prizes = [100, 200, 300, 500, 1000, 2000]
        prize = random.choice(prizes)


    # Cria o registro do prêmio da roleta
    Roulette.objects.create(user=user, prize=prize, is_approved=True)

    # Adiciona o prêmio ao saldo do usuário (subsídio e disponível)
    user.subsidy_balance += prize
    user.available_balance += prize
    user.save()

    return JsonResponse({'success': True, 'prize': prize, 'roulette_spins': user.roulette_spins, 'message': f'Parabéns! Você ganhou {prize} Kz.'})

# --- FUNÇÕES DE PERFIL E INFORMAÇÕES GERAIS ---

@login_required
def sobre(request):
    """
    Exibe a página 'Sobre' com o histórico da plataforma.
    """
    try:
        platform_settings = PlatformSettings.objects.first()
        history_text = platform_settings.history_text if platform_settings else 'Histórico da plataforma não disponível.'
    except PlatformSettings.DoesNotExist:
        history_text = 'Histórico da plataforma não disponível.'

    return render(request, 'sobre.html', {'history_text': history_text})

@login_required
def perfil(request):
    """
    Página de perfil, lida com detalhes bancários e mudança de senha.
    """
    bank_details, created = BankDetails.objects.get_or_create(user=request.user)
    user_levels = UserLevel.objects.filter(user=request.user, is_active=True)

    if request.method == 'POST':
        form = BankDetailsForm(request.POST, instance=bank_details)
        password_form = PasswordChangeForm(request.user, request.POST)

        if 'update_bank' in request.POST:
            if form.is_valid():
                form.save()
                messages.success(request, 'Detalhes bancários atualizados com sucesso!')
                return redirect('perfil')
            else:
                messages.error(request, 'Ocorreu um erro ao atualizar os detalhes bancários.')

        if 'change_password' in request.POST:
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Sua senha foi alterada com sucesso!')
                return redirect('perfil')
            else:
                messages.error(request, 'Ocorreu um erro ao alterar a senha. Verifique se a senha antiga está correta e a nova senha é válida.')
    else:
        form = BankDetailsForm(instance=bank_details)
        password_form = PasswordChangeForm(request.user)

    context = {
        'form': form,
        'password_form': password_form,
        'user_levels': user_levels,
    }
    return render(request, 'perfil.html', context)

@login_required
def renda(request):
    """
    Exibe a página de renda e estatísticas financeiras do usuário.
    """
    user = request.user
    
    active_level = UserLevel.objects.filter(user=user, is_active=True).first()

    approved_deposit_total = Deposit.objects.filter(user=user, is_approved=True).aggregate(Sum('amount'))['amount__sum'] or 0
    
    today = date.today()
    daily_income = Task.objects.filter(user=user, completed_at__date=today).aggregate(Sum('earnings'))['earnings__sum'] or 0

    # Saques aprovados
    total_withdrawals = Withdrawal.objects.filter(user=user, status='Aprovado').aggregate(Sum('amount'))['amount__sum'] or 0

    # Renda total = Tarefas (ganho de tarefas) + Subsídios (roleta + convites + prêmios diários)
    total_income = (Task.objects.filter(user=user).aggregate(Sum('earnings'))['earnings__sum'] or 0) + user.subsidy_balance
    
    context = {
        'user': user,
        'active_level': active_level,
        'approved_deposit_total': approved_deposit_total,
        'daily_income': daily_income,
        'total_withdrawals': total_withdrawals,
        'total_income': total_income,
    }
    return render(request, 'renda.html', context)

# --- FUNÇÕES DE PRÊMIOS E SUBSÍDIOS ---

@login_required
def premios_subsidios(request):
    """
    Lida com a página de Prêmios e Subsídios, 
    verificando o status de resgate diário do usuário.
    """
    user = request.user
    today = date.today()
    
    # 1. Tenta encontrar o código ativo para o dia
    # Procura um código ativo criado HOJE (assumindo que o código diário é criado diariamente)
    active_code = DailyRewardCode.objects.filter(is_active=True, created_date=today).first()
    
    # 2. Verifica se o usuário já resgatou hoje (independente do código, se a regra é um resgate por dia)
    has_claimed_today = UserRewardClaim.objects.filter(user=user, claim_date=today).exists()
    
    # 3. Obtém o histórico dos 10 resgates mais recentes do usuário
    claim_history = UserRewardClaim.objects.filter(user=user).order_by('-claimed_at')[:10]
    
    context = {
        'user': user,
        'subsidy_balance': user.subsidy_balance,
        'active_code': active_code,
        'has_claimed_today': has_claimed_today,
        'claim_history': claim_history,
    }
    return render(request, 'premios_subsidios.html', context)

@login_required
@require_POST
def claim_daily_reward(request):
    """
    Processa o resgate do código de subsídio diário enviado pelo usuário.
    Esta é a lógica do prêmio diário.
    """
    user = request.user
    today = date.today()
    
    submitted_code = request.POST.get('reward_code', '').strip()
    
    # 1. Verifica se já resgatou hoje 
    if UserRewardClaim.objects.filter(user=user, claim_date=today).exists():
        messages.error(request, 'Você já resgatou seu prêmio diário hoje.')
        return redirect('premios_subsidios')
    
    # 2. Tenta encontrar o código ativo correspondente ao código enviado
    try:
        active_code = DailyRewardCode.objects.get(
            code=submitted_code, 
            is_active=True,
        )
    except DailyRewardCode.DoesNotExist:
        messages.error(request, 'Código de subsídio inválido, expirado ou inativo. Verifique o código do dia.')
        return redirect('premios_subsidios')

    # 3. Processa o resgate
    reward_amount = active_code.reward_amount
    
    # Cria o registro de resgate
    UserRewardClaim.objects.create(
        user=user, 
        reward_code=active_code, 
        claim_date=today
    )
    
    # Atualiza o saldo do usuário (subsídio e disponível)
    user.subsidy_balance += reward_amount
    user.available_balance += reward_amount # Adicionando também ao saldo disponível
    user.save()
    
    messages.success(request, f'Parabéns! Você resgatou {reward_amount} Kz no seu Saldo de Subsídios.')
    return redirect('premios_subsidios')
    