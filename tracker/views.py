from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Transaction, Budget
from .forms import TransactionForm, BudgetForm
from django.utils import timezone
from django.db import IntegrityError
from collections import defaultdict
from decimal import Decimal
import datetime



def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('tracker:dashboard')
        else:
            messages.error(request, "Registration failed. Please correct the errors below.")
    else:
        form = UserCreationForm()
    return render(request, 'tracker/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"Welcome back, {username}!")
                next_url = request.POST.get('next', '/')
                return redirect(next_url or 'tracker:dashboard')
            else:
                 messages.error(request,"Invalid username or password.")
        else:
            messages.error(request,"Invalid username or password.")
    else:
         form = AuthenticationForm()
    return render(request, 'tracker/login.html', {'form': form, 'next': request.GET.get('next', '')})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('tracker:login')


@login_required
def dashboard_view(request):
    transactions = Transaction.objects.filter(user=request.user)
    context = {
        'transactions': transactions,
        'username': request.user.username,
    }
    return render(request, 'tracker/dashboard.html', context)

@login_required
def add_transaction_view(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            messages.success(request, "Transaction added successfully!")
            return redirect('tracker:dashboard')
        else:
             messages.error(request, "Please correct the errors below.")
    else:
        form = TransactionForm()
    return render(request, 'tracker/add_transaction.html', {'form': form})

@login_required
def edit_transaction_view(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)

    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            messages.success(request, "Transaction updated successfully!")
            return redirect('tracker:dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = TransactionForm(instance=transaction)

    return render(request, 'tracker/edit_transaction.html', {'form': form, 'transaction': transaction})

@login_required
def delete_transaction_view(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)

    if request.method == 'POST':
        transaction.delete()
        messages.success(request, "Transaction deleted successfully!")
        return redirect('tracker:dashboard')
    else:
        return render(request, 'tracker/delete_transaction_confirm.html', {'transaction': transaction})


@login_required
def financial_tips_view(request):
    tips = [
        "Create a budget and stick to it. Track your income and expenses.",
        "Build an emergency fund. Aim for 3-6 months of living expenses.",
        "Pay off high-interest debt as quickly as possible.",
        "Start saving for retirement early. Take advantage of employer matching if available.",
        "Review your subscriptions and memberships regularly. Cancel unused ones.",
        "Automate your savings. Set up automatic transfers to your savings account.",
        "Compare prices before making significant purchases.",
        "Understand the difference between needs and wants.",
        "Set specific, measurable, achievable, relevant, and time-bound (SMART) financial goals.",
        "Washing your money with soap and water can help it grow!",
        "Educate yourself about personal finance through books, blogs, or courses."
    ]
    context = {
        'financial_tips': tips
    }
    return render(request, 'tracker/financial_tips.html', context)

@login_required
def budget_list_view(request):
    budgets = Budget.objects.filter(user=request.user).order_by('-month', 'category')
    return render(request, 'tracker/budget_list.html', {'budgets': budgets})

@login_required
def budget_create_view(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            try:
                budget = form.save(commit=False)
                budget.user = request.user
                budget.save()
                messages.success(request, f"Budget for {budget.category} ({budget.month.strftime('%Y-%m')}) created!")
                return redirect('tracker:budget_list')
            except IntegrityError:
                messages.error(request, f"A budget for '{form.cleaned_data['category']}' in {form.cleaned_data['month'].strftime('%Y-%m')} already exists.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        initial_data = {'month': timezone.now().replace(day=1)}
        form = BudgetForm(initial=initial_data)

    return render(request, 'tracker/budget_form.html', {'form': form, 'action': 'Create'})


@login_required
def budget_edit_view(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f"Budget for {budget.category} ({budget.month.strftime('%Y-%m')}) updated!")
                return redirect('tracker:budget_list')
            except IntegrityError:
                 messages.error(request, f"A budget for '{form.cleaned_data['category']}' in {form.cleaned_data['month'].strftime('%Y-%m')} already exists (cannot update to conflict).")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = BudgetForm(instance=budget)

    return render(request, 'tracker/budget_form.html', {'form': form, 'action': 'Edit', 'budget': budget})

@login_required
def budget_delete_view(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    if request.method == 'POST':
        month_str = budget.month.strftime('%Y-%m')
        category = budget.category
        budget.delete()
        messages.success(request, f"Budget for {category} ({month_str}) deleted.")
        return redirect('tracker:budget_list')
    else:
        return render(request, 'tracker/budget_delete_confirm.html', {'budget': budget})


@login_required
def dashboard_view(request):
    transactions = Transaction.objects.filter(user=request.user)

    today = timezone.now().date()
    start_of_current_month = today.replace(day=1)
    if start_of_current_month.month == 12:
        start_of_next_month = start_of_current_month.replace(year=start_of_current_month.year + 1, month=1)
    else:
        start_of_next_month = start_of_current_month.replace(month=start_of_current_month.month + 1)

    current_budgets = Budget.objects.filter(user=request.user, month=start_of_current_month)
    budget_map = {b.category: b.amount for b in current_budgets}

    current_expenses = Transaction.objects.filter(
        user=request.user,
        type='Expense',
        date__gte=start_of_current_month,
        date__lt=start_of_next_month
    )

    spending_map = defaultdict(Decimal)
    for expense in current_expenses:
        spending_map[expense.category] += expense.amount

    budget_progress = []
    all_categories = set(budget_map.keys()) | set(spending_map.keys())

    for category in sorted(list(all_categories)):
        budget_amount = budget_map.get(category, Decimal('0.00'))
        spent_amount = spending_map.get(category, Decimal('0.00'))
        remaining = budget_amount - spent_amount if budget_amount > 0 else Decimal('0.00')
        percentage = int((spent_amount / budget_amount) * 100) if budget_amount > 0 else 0

        budget_progress.append({
            'category': category,
            'budget_amount': budget_amount,
            'spent_amount': spent_amount,
            'remaining': remaining,
            'percentage': min(percentage, 100),
            'over_budget': spent_amount > budget_amount if budget_amount > 0 else False,
            'has_budget': category in budget_map
        })


    context = {
        'transactions': transactions,
        'username': request.user.username,
        'budget_progress': budget_progress,
        'current_month_str': start_of_current_month.strftime('%B %Y')
    }
    return render(request, 'tracker/dashboard.html', context)

