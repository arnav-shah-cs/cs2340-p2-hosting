# tracker/forms.py
from decimal import Decimal

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Transaction, Budget, Goal

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['type', 'amount', 'date', 'category', 'description', 'is_recurring', 'recurring_due_date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'recurring_due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("Amount must be positive.")
        return amount


class BudgetForm(forms.ModelForm):
    CATEGORY_CHOICES = [
         ('Food', 'Food'),
         ('Transportation', 'Transportation'),
         ('Housing', 'Housing'),
         ('Utilities', 'Utilities'),
         ('Entertainment', 'Entertainment'),
         ('Clothing', 'Clothing'),
         ('Healthcare', 'Healthcare'),
         ('Personal Care', 'Personal Care'),
         ('Debt Payments', 'Debt Payments'),
         ('Savings/Investments', 'Savings/Investments'),
         ('Other', 'Other'),
    ]
    category = forms.ChoiceField(choices=CATEGORY_CHOICES)

    class Meta:
        model = Budget
        fields = ['category', 'amount', 'month']
        widgets = {
            'month': forms.DateInput(attrs={'type': 'date', 'placeholder': 'Select any day in month'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['amount'].widget.attrs['placeholder'] = 'e.g., 500.00'
        self.fields['month'].help_text = 'Select any day in the target month.'


    def clean_month(self):
        month_date = self.cleaned_data.get('month')
        if month_date:
            return month_date.replace(day=1)
        return month_date

class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['name', 'target_amount']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Vacation Fund'}),
            'target_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'})
        }
        labels = {
            'name': 'Goal Name',
            'target_amount': 'Target Amount ($)'
        }

    def clean_target_amount(self):
        target = self.cleaned_data.get('target_amount')
        if target is not None and target <= 0:
            raise forms.ValidationError("Target amount must be positive.")
        return target



class ContributionForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Amount to add'}),
        label="Contribution Amount ($)"
    )

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        return amount

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        help_text='Required. Please enter a valid email address.'
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

    def clean_email(self):
        # validation to make sure email address is unique
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

