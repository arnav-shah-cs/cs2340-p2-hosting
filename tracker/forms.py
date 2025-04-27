# tracker/forms.py
from decimal import Decimal

from django import forms
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
        fields = ['name', 'target_amount']  # User and current_amount set in view
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Vacation Fund'}),
            'target_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'})
        }
        labels = {
            'name': 'Goal Name',
            'target_amount': 'Target Amount ($)'
        }

    def clean_target_amount(self):
        # Ensure target amount is positive
        target = self.cleaned_data.get('target_amount')
        if target is not None and target <= 0:
            raise forms.ValidationError("Target amount must be positive.")
        return target



class ContributionForm(forms.Form):
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),  # Minimum contribution
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Amount to add'}),
        label="Contribution Amount ($)"
    )

    def clean_amount(self):
        # Additional validation if needed
        amount = self.cleaned_data.get('amount')
        # Example: Check against available funds if you track that elsewhere
        return amount

