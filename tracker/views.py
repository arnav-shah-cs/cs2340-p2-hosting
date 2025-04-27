from django.contrib.sites import requests
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Transaction, Budget, Goal
from .forms import TransactionForm, BudgetForm
from django.utils import timezone
from django.db import IntegrityError
from collections import defaultdict
from decimal import Decimal
from django.conf import settings
from django.shortcuts import render
from datetime import date
import datetime
import requests
from .forms import GoalForm, ContributionForm
from django.utils import timezone




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


def send_upcoming_due_date_emails(request):
    user = request.user
    upcoming_expenses = Transaction.objects.filter(
        user=user,
        is_recurring=True,
        recurring_due_date__gte=date.today()
    )
    if upcoming_expenses.exists():
        message_lines = [
            f"Hi {user.username},",
            "",
            "Here are your upcoming recurring expenses:"
        ]
        for expense in upcoming_expenses:
            message_lines.append(f"- {expense.category}: ${expense.amount:.2f} due on {expense.recurring_due_date}")
        message_lines.append("")

        message_lines.append("Additionally, here are some upcoming financial due dates:")
        message_lines.append("April 15: Individual income tax returns due (Form 1040)")
        message_lines.append("April 15: First quarter estimated tax payments due")
        message_lines.append("June 15: Second quarter estimated tax payments due")
        message_lines.append("September 15: Third quarter estimated tax payments due")
        message_lines.append("October 15: Extended individual tax returns due")
        message_lines.append("January 15: Fourth quarter estimated tax payments due")
        message_lines.append("April 15: IRA contribution deadline for previous tax year")
        message_lines.append("December 31: 401(k) contribution deadline")
        message_lines.append("December 31: Required Minimum Distributions (RMDs) due")
        message_lines.append(" Remember to stay on top of your finances!")
        message_lines.append("- Your Finance Tracker Team")

        message_body = "\n".join(message_lines)

        # Send the email
        send_mail(
            'Upcoming Financial Due Dates 📅',
            message_body,
            'aravshahphotos@gmail.com',
            [user.email],
            fail_silently=False,
        )
        messages.success(request, 'Upcoming expenses email sent successfully! ✅')
    else:
        messages.info(request, 'No upcoming expenses found to email. ℹ️')

    return redirect('tracker:dashboard')

@login_required
def dashboard_view(request):
    print("dashboard hello")
    transactions = Transaction.objects.filter(user=request.user)
    goals_queryset = Goal.objects.filter(user=request.user).order_by('created_at')

    today = timezone.now().date()
    upcoming_recurring_expenses = Transaction.objects.filter(
        user=request.user,
        #type='Expense',
        is_recurring=True,
        recurring_due_date__gte=today
    ).order_by('recurring_due_date')

    context = {
        'transactions': transactions,
        'username': request.user.username,
        'goals': goals_queryset,
        'upcoming_recurring_expenses': upcoming_recurring_expenses,
    }
    print(f"Upcoming recurring expenses: {upcoming_recurring_expenses.count()}")
    for exp in upcoming_recurring_expenses:
        print(f"{exp.description} due on {exp.recurring_due_date}")
    return render(request, 'tracker/dashboard.html', context)



@login_required
def add_goal(request):
    if request.method == 'POST':
        form = GoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.current_amount = Decimal('0.00')
            goal.save()
            messages.success(request, f"Goal '{goal.name}' created successfully!")
            return redirect('tracker:dashboard')
        else:
             messages.error(request, "Please correct the errors below.")
    else:
        form = GoalForm()
    return render(request, 'tracker/add_goal.html', {'form': form})

@login_required
def add_contribution(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)
    if request.method == 'POST':
        form = ContributionForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            if not isinstance(goal.current_amount, Decimal):
                 goal.current_amount = Decimal(goal.current_amount)
            goal.current_amount += amount
            goal.save()
            messages.success(request, f"Successfully added ${amount} to '{goal.name}'!")
             # --- Redirect to YOUR dashboard view ---
            return redirect('tracker:dashboard') # Make sure 'dashboard' URL name points to dashboard_view
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ContributionForm()
    context = {
        'form': form,
        'goal': goal
    }
    return render(request, 'tracker/add_contribution.html', context)

@login_required
def add_transaction_view(request):
    print("hello")
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


def stock_market_overview(request):
    indices = ["SPY", "QQQ", "DIA"] # Key ETFs for overview
    overview_data = []
    api_key = settings.POLYGON_API_KEY
    base_url = "https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers/"

    for ticker in indices:
        url = f"{base_url}{ticker}?apiKey={api_key}"
        print(f"--- Requesting Snapshot URL: {url}")
        try:
            response = requests.get(url, timeout=10)
            print(f"--- Snapshot Response Status ({ticker}): {response.status_code}")
            # Add response text printing for debugging if needed
            # print(f"--- Snapshot Response Text ({ticker}): {response.text[:200]}")

            if response.status_code == 200:
                data = response.json()
                if data.get('ticker'): # Basic check for valid response structure
                    overview_data.append(data['ticker']) # Add the 'ticker' part of the snapshot
                else:
                    print(f"--- Warning: Unexpected snapshot structure for {ticker}")
            else:
                print(f"--- Error fetching snapshot for {ticker}: Status {response.status_code}")
                # Optionally add placeholder error data for the template

        except requests.exceptions.RequestException as e:
            print(f"--- Network error fetching snapshot for {ticker}: {e}")
            # Optionally add placeholder error data

    return render(request, 'tracker/stock_market.html', {'overview_data': overview_data})
    # Adjust your template 'stock_market.html' to display snapshot data