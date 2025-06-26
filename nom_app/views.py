from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from .models import Transaction, Budget, Category
from datetime import date, timedelta
from django.db.models import Sum
from django.utils import timezone

def auth_view(request):
    if request.method == 'POST':
        if 'login' in request.POST:
            email = request.POST.get('loginEmail')
            password = request.POST.get('loginPassword')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, "Identifiants invalides")
        elif 'register' in request.POST:
            name = request.POST.get('registerName')
            email = request.POST.get('registerEmail')
            password = request.POST.get('registerPassword')
            confirm = request.POST.get('confirmPassword')
            if password != confirm:
                messages.error(request, "Les mots de passe ne correspondent pas")
            elif User.objects.filter(username=email).exists():
                messages.error(request, "Cet email existe déjà")
            else:
                user = User.objects.create_user(username=email, email=email, password=password, first_name=name)
                messages.success(request, "Compte créé avec succès ! Connectez-vous.")
                return redirect('auth')
    return render(request, 'auth.html')

@never_cache
@login_required
def dashboard_view(request):
    return render(request, 'dashboard.html', {'user': request.user})

def index_view(request):
    return render(request, 'index.html')

def register_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('firstName')
        last_name = request.POST.get('lastName')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm = request.POST.get('confirmPassword')
        accept_terms = request.POST.get('acceptTerms')

        if not all([first_name, last_name, email, password, confirm, accept_terms]):
            messages.error(request, "Veuillez remplir tous les champs obligatoires et accepter les conditions.")
        elif password != confirm:
            messages.error(request, "Les mots de passe ne correspondent pas.")
        elif User.objects.filter(username=email).exists():
            messages.error(request, "Cet email existe déjà.")
        else:
            User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            messages.success(request, "Compte créé avec succès ! Connectez-vous.")
            return redirect('auth')
    return render(request, 'register.html')

@never_cache
@login_required
def transaction_view(request):
    # Ajout rapide de catégorie
    if request.method == 'POST' and 'add_category' in request.POST:
        name = request.POST.get('categoryName')
        type = request.POST.get('categoryType')
        icon = request.POST.get('selectedIcon') or ""
        color = request.POST.get('selectedColor')
        if not name or not type or not color:
            messages.error(request, "Veuillez remplir tous les champs de la catégorie.")
        else:
            Category.objects.create(
                user=request.user,
                name=name,
                type=type,
                icon=icon,
                color=color
            )
            messages.success(request, "Catégorie ajoutée avec succès !")
        # Après ajout, tu peux rediriger pour éviter la double soumission :
        return redirect('transactions')  # ou le nom de ta route

    # Création (modifié selon la suggestion)
    if request.method == 'POST' and 'type' in request.POST and 'amount' in request.POST:
        type = request.POST.get('type')
        amount = request.POST.get('amount')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        transaction_date = request.POST.get('date')
        if type and amount and category_id and transaction_date:
            category = Category.objects.get(id=category_id, user=request.user)
            Transaction.objects.create(
                user=request.user,
                type=type,
                amount=amount,
                category=category,
                description=description,
                date=transaction_date
            )
            messages.success(request, "Transaction ajoutée avec succès !")
            return redirect('transactions')
        else:
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")

    # Modification
    if request.method == 'POST' and 'edit_transaction' in request.POST:
        transaction_id = request.POST.get('transaction_id')
        transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
        transaction.type = request.POST.get('type')
        transaction.amount = request.POST.get('amount')
        transaction.category = request.POST.get('category')
        transaction.description = request.POST.get('description')
        transaction.date = request.POST.get('date')
        transaction.save()
        messages.success(request, "Transaction modifiée avec succès !")

    # Suppression
    if request.method == 'POST' and 'delete_transaction' in request.POST:
        transaction_id = request.POST.get('transaction_id')
        transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
        transaction.delete()
        messages.success(request, "Transaction supprimée avec succès !")

    # Filtres (inchangé)
    transactions = Transaction.objects.filter(user=request.user)
    period = request.GET.get('period', 'all')
    category = request.GET.get('category', 'all')
    ttype = request.GET.get('type', 'all')
    min_amount = request.GET.get('min_amount')
    max_amount = request.GET.get('max_amount')

    today = date.today()
    if period == 'today':
        transactions = transactions.filter(date=today)
    elif period == 'week':
        start_week = today - timedelta(days=today.weekday())
        transactions = transactions.filter(date__gte=start_week)
    elif period == 'month':
        transactions = transactions.filter(date__year=today.year, date__month=today.month)
    elif period == 'year':
        transactions = transactions.filter(date__year=today.year)

    if category != 'all':
        transactions = transactions.filter(category=category)
    if ttype != 'all':
        transactions = transactions.filter(type=ttype)
    if min_amount:
        transactions = transactions.filter(amount__gte=min_amount)
    if max_amount:
        transactions = transactions.filter(amount__lte=max_amount)

    transactions = transactions.order_by('-date')
    categories = Category.objects.filter(user=request.user).order_by('name')
    return render(request, 'transactions.html', {
        'transactions': transactions,
        'categories': categories,
        'user': request.user,
    })

@never_cache
@login_required
def categories_view(request):
    # Ajout
    if request.method == 'POST' and 'add_category' in request.POST:
        name = request.POST.get('categoryName')
        type = request.POST.get('categoryType')
        icon = request.POST.get('selectedIcon')
        color = request.POST.get('selectedColor')
        if not name or not type or not icon or not color:
            messages.error(request, "Veuillez remplir tous les champs.")
        else:
            Category.objects.create(
                user=request.user,
                name=name,
                type=type,
                icon=icon,
                color=color
            )
            messages.success(request, "Catégorie ajoutée avec succès !")
    # Suppression
    if request.method == 'POST' and 'delete_category' in request.POST:
        cat_id = request.POST.get('category_id')
        cat = Category.objects.filter(id=cat_id, user=request.user).first()
        if cat:
            cat.delete()
            messages.success(request, "Catégorie supprimée.")
    # Modification
    if request.method == 'POST' and 'edit_category' in request.POST:
        cat_id = request.POST.get('category_id')
        cat = Category.objects.filter(id=cat_id, user=request.user).first()
        if cat:
            cat.name = request.POST.get('categoryName')
            cat.type = request.POST.get('categoryType')
            cat.icon = request.POST.get('selectedIcon')
            cat.color = request.POST.get('selectedColor')
            cat.save()
            messages.success(request, "Catégorie modifiée.")
    # Filtrage
    filter_type = request.GET.get('type', 'all')
    categories = Category.objects.filter(user=request.user)
    if filter_type in ['expense', 'income']:
        categories = categories.filter(type=filter_type)
    categories = categories.order_by('name')
    return render(request, 'categories.html', {'categories': categories, 'filter_type': filter_type})

@never_cache
@login_required
def budgets_view(request):
    # Ajout d'un budget
    if request.method == 'POST' and 'add_budget' in request.POST:
        category_id = request.POST.get('budgetCategory')
        amount = request.POST.get('budgetAmount')
        start_date = request.POST.get('budgetStartDate')
        end_date = request.POST.get('budgetEndDate') or None
        alerts = bool(request.POST.get('budgetAlerts'))
        if not category_id or not amount or not start_date:
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
        else:
            category = Category.objects.get(id=category_id, user=request.user)
            Budget.objects.create(
                user=request.user,
                category=category,
                amount=amount,
                start_date=start_date,
                end_date=end_date,
                alerts=alerts
            )
            messages.success(request, "Budget créé avec succès !")
            return redirect('budgets')

    # Récupérer les catégories et budgets de l'utilisateur
    categories = Category.objects.filter(user=request.user).order_by('name')
    budgets = Budget.objects.filter(user=request.user).select_related('category').order_by('-start_date')

    # Calcul des totaux pour l'aperçu
    total_budget = budgets.aggregate(total=Sum('amount'))['total'] or 0
    spent_budget = 0
    for budget in budgets:
        spent = Transaction.objects.filter(
            user=request.user,
            type='expense',
            category=budget.category,
            date__gte=budget.start_date,
            date__lte=budget.end_date if budget.end_date else timezone.now().date()
        ).aggregate(total=Sum('amount'))['total'] or 0
        spent_budget += spent

    remaining_budget = total_budget - spent_budget
    budget_usage = int((spent_budget / total_budget) * 100) if total_budget else 0

    # Calcul progression par budget
    budgets_progress = []
    for budget in budgets:
        spent = Transaction.objects.filter(
            user=request.user,
            type='expense',
            category=budget.category,
            date__gte=budget.start_date,
            date__lte=budget.end_date if budget.end_date else timezone.now().date()
        ).aggregate(total=Sum('amount'))['total'] or 0
        percent = min(100, int((spent / budget.amount) * 100)) if budget.amount else 0
        restant = float(budget.amount) - float(spent)
        budgets_progress.append({
            'budget': budget,
            'spent': spent,
            'percent': percent,
            'restant': restant,
        })

    return render(request, 'budgets.html', {
        'categories': categories,
        'budgets_progress': budgets_progress,
        'total_budget': total_budget,
        'spent_budget': spent_budget,
        'remaining_budget': remaining_budget,
        'budget_usage': budget_usage,
    })

@never_cache
@login_required
def export_view(request):
    return render(request, 'export.html', )

@never_cache
@login_required
def profile_view(request):
    return render(request, 'profile.html', )

def logout_view(request):
    logout(request)
    return redirect('auth')