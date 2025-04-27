from email.mime.image import MIMEImage

from django.contrib.sites import requests
from django.core.mail import send_mail, EmailMultiAlternatives, EmailMessage
from django.db.models import Sum
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
import matplotlib.pyplot as plt
import io
import base64



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
    important_dates = [
        ("April 15", "Individual income tax returns due (Form 1040)"),
        ("April 15", "First quarter estimated tax payments due"),
        ("June 15", "Second quarter estimated tax payments due"),
        ("September 15", "Third quarter estimated tax payments due"),
        ("October 15", "Extended individual tax returns due"),
        ("January 15", "Fourth quarter estimated tax payments due"),
        ("April 15", "IRA contribution deadline for previous tax year"),
        ("December 31", "401(k) contribution deadline"),
        ("December 31", "Required Minimum Distributions (RMDs) due"),
    ]
    upcoming_expenses = Transaction.objects.filter(
        user=user,
        is_recurring=True,
        recurring_due_date__gte=date.today()
    )

    if upcoming_expenses.exists():
        text_lines = [
            f"Hi {user.username},",
            "",
            "Here are your upcoming recurring expenses:"
        ]
        html_expense_rows = ""

        for expense in upcoming_expenses:
            text_lines.append(f"- {expense.category}: ${expense.amount:.2f} due on {expense.recurring_due_date}")
            html_expense_rows += f"""
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;">{expense.category}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;">${expense.amount:.2f}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;">{expense.recurring_due_date}</td>
                </tr>
            """
        text_lines.append("\nAdditionally, here are some upcoming important financial dates:")

        for date_str, description in important_dates:
            text_lines.append(f"- {date_str}: {description}")

        text_lines.append("\nStay on top of your finances! 💸\n- Your Finance Tracker Team")

        # Build the full HTML email
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f6f9fc; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                <h2 style="color: #333;">Hello, {user.username}!</h2>
                <p style="color: #555;">Here’s a quick reminder of your upcoming recurring expenses:</p>

                <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                    <thead>
                        <tr style="background-color: #007bff; color: white;">
                            <th style="padding: 10px;">Category</th>
                            <th style="padding: 10px;">Amount</th>
                            <th style="padding: 10px;">Due Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {html_expense_rows}
                    </tbody>
                </table>
                
                <p style="margin-top: 30px; color: #555;">Additionally, here are some important financial dates to keep in mind:</p>
                <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                    <thead>
                        <tr style="background-color: #28a745; color: white;">
                            <th style="padding: 10px;">Date</th>
                            <th style="padding: 10px;">Description</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(f"""
                            <tr>
                                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{date_str}</td>
                                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{description}</td>
                            </tr>
                        """ for date_str, description in important_dates)}
                    </tbody>
                </table>

                <p style="margin-top: 20px; color: #333;">Stay on top of your finances! 💸</p>
                <p style="font-size: 0.9em; color: #888;">- Your Finance Tracker Team</p>
            </div>
        </body>
        </html>
        """

        text_body = "\n".join(text_lines)

        email = EmailMultiAlternatives(
            subject='Upcoming Financial Due Dates and Recurring Payments!',
            body=text_body,
            from_email='aravshahphotos@gmail.com',
            to=[user.email],
        )
        email.attach_alternative(html_body, "text/html")
        email.send()

        messages.success(request, 'Upcoming expenses email sent successfully! ✅')
    else:
        messages.info(request, 'No upcoming expenses found to email. ℹ️')

    return redirect('tracker:dashboard')


def send_spending_summary_email(request):
    user = request.user
    transactions = Transaction.objects.filter(user=user)

    total_income = transactions.filter(type='Income').aggregate(Sum('amount'))['amount__sum'] or 0
    expenses = transactions.filter(type='Expense')

    category_spending = expenses.values('category').annotate(total_spent=Sum('amount'))

    text_lines = []
    text_lines.append(f"Hello {user.username},")
    text_lines.append("")
    text_lines.append("Here’s your spending summary:")
    text_lines.append(f"- Total Income: ${total_income:.2f}")
    text_lines.append("")

    for item in category_spending:
        category = item['category']
        spent = item['total_spent']
        percent_of_income = (spent / total_income) * 100 if total_income > 0 else 0
        text_lines.append(f"- {category}: Spent ${spent:.2f} ({percent_of_income:.1f}% of your income)")

    text_content = "\n".join(text_lines)

    categories = [item['category'] for item in category_spending]
    amounts = [item['total_spent'] for item in category_spending]

    chart_image = None
    if categories and amounts:
        plt.figure(figsize=(6, 6))
        plt.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=140)
        plt.title('Spending by Category')
        plt.tight_layout()

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()
        buffer.seek(0)
        chart_image = buffer.read()

    subject = 'Your Spending Summary'
    from_email = 'your_email@example.com'
    to = [user.email]

    email = EmailMultiAlternatives(subject, text_content, from_email, to)

    if chart_image:
        img = MIMEImage(chart_image)
        img.add_header('Content-ID', '<spending_chart>')
        img.add_header('Content-Disposition', 'inline', filename='spending_chart.png')
        email.attach(img)

        html_content = f"""
        <p>{text_content.replace('\n', '<br>')}</p>
        <p><strong>Spending Breakdown:</strong></p>
        <img src="cid:spending_chart" alt="Spending by Category">
        """
        email.attach_alternative(html_content, "text/html")
    email.send()


def send_spending_summary_email_view(request):
    if request.method == 'POST':
        send_spending_summary_email(request)
        messages.success(request, "Spending summary email sent successfully!")
    return redirect('tracker:dashboard')


def check_and_send_budget_alerts(user):
    today = datetime.date.today()
    budgets = Budget.objects.filter(user=user)

    for budget in budgets:
        category = budget.category
        budget_limit = budget.amount
        budget_month = budget.month

        if budget_month.year == today.year and budget_month.month == today.month:
            total_spent = Transaction.objects.filter(
                user=user,
                type='Expense',
                category=category,
                date__year=today.year,
                date__month=today.month
            ).aggregate(Sum('amount'))['amount__sum'] or 0

            if budget_limit > 0:
                percent_used = (total_spent / budget_limit) * 100
            else:
                percent_used = 0

            if percent_used >= 80:
                send_mail(
                    subject='Budget Alert: Approaching Limit!',
                    message=(
                        f"Hi {user.username},\n\n"
                        f"You've spent ${total_spent:.2f} of your ${budget_limit:.2f} budget for {category} "
                        f"({percent_used:.1f}% used).\n\n"
                        "Keep an eye on your spending!"
                    ),
                    from_email='aravshahphotos@gmail.com',
                    recipient_list=[user.email],
                    fail_silently=False,
                )


# @login_required
# def dashboard_view(request):
#     print("dashboard hello")
#     transactions = Transaction.objects.filter(user=request.user)
#     goals_queryset = Goal.objects.filter(user=request.user).order_by('created_at')
#
#     today = timezone.now().date()
#     upcoming_recurring_expenses = Transaction.objects.filter(
#         user=request.user,
#         #type='Expense',
#         is_recurring=True,
#         recurring_due_date__gte=today
#     ).order_by('recurring_due_date')
#
#     context = {
#         'transactions': transactions,
#         'username': request.user.username,
#         'goals': goals_queryset,
#         'upcoming_recurring_expenses': upcoming_recurring_expenses,
#     }
#     return render(request, 'tracker/dashboard.html', context)



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
            return redirect('tracker:dashboard')
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
    check_and_send_budget_alerts(request.user)
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
    goals_queryset = Goal.objects.filter(user=request.user).order_by('created_at')

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
    upcoming_recurring_expenses = Transaction.objects.filter(
        user=request.user,
        # type='Expense',
        is_recurring=True,
        recurring_due_date__gte=today
    ).order_by('recurring_due_date')

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
        'goals': goals_queryset,
        'upcoming_recurring_expenses': upcoming_recurring_expenses,
        'current_month_str': start_of_current_month.strftime('%B %Y')
    }
    return render(request, 'tracker/dashboard.html', context)


# def stock_market_overview(request):
#     indices = ["SPY", "QQQ", "DIA"]
#     overview_data = []
#     api_key = settings.POLYGON_API_KEY
#     base_url = "https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers/"
#
#     for ticker in indices:
#         url = f"{base_url}{ticker}?apiKey={api_key}"
#         print(f"--- Requesting Snapshot URL: {url}")
#         try:
#             response = requests.get(url, timeout=10)
#             print(f"--- Snapshot Response Status ({ticker}): {response.status_code}")
#
#             if response.status_code == 200:
#                 data = response.json()
#                 if data.get('ticker'):
#                     overview_data.append(data['ticker'])
#                 else:
#                     print(f"--- Warning: Unexpected snapshot structure for {ticker}")
#             else:
#                 print(f"--- Error fetching snapshot for {ticker}: Status {response.status_code}")
#
#         except requests.exceptions.RequestException as e:
#             print(f"--- Network error fetching snapshot for {ticker}: {e}")
#
#     return render(request, 'tracker/stock_market.html', {'overview_data': overview_data})

import requests
from django.conf import settings
from django.shortcuts import render

def stock_market_overview(request):
    indices = ["SPY", "QQQ", "DIA", "IWM", "VTI", "ACWI", "VOO", "IVV", "AAPL", "GOOGL", "MSFT",]
    overview_data = []
    api_key = settings.ALPHA_VANTAGE_API_KEY
    base_url = "https://www.alphavantage.co/query"

    for ticker in indices:
        url = f"{base_url}?function=TIME_SERIES_DAILY&symbol={ticker}&apikey={api_key}"
        #print(f"--- Requesting Alpha Vantage URL: {url}")
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'Time Series (Daily)' in data:
                    last_date = list(data['Time Series (Daily)'].keys())[0]
                    daily_data = data['Time Series (Daily)'][last_date]
                    overview_data.append({
                        'ticker': ticker,
                        'date': last_date,
                        'open': daily_data['1. open'],
                        'high': daily_data['2. high'],
                        'low': daily_data['3. low'],
                        'close': daily_data['4. close'],
                    })
                else:
                    return
                    #print(f"--- Warning: No time series data available for {ticker}")
            else:
                return
                #print(f"--- Error fetching data for {ticker}: Status {response.status_code}")

        except requests.exceptions.RequestException as e:
            return
            # print(f"--- Network error fetching data for {ticker}: {e}")

    return render(request, 'tracker/stock_market.html', {'overview_data': overview_data})

