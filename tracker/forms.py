# tracker/forms.py
from django import forms
from .models import Transaction, Budget

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['type', 'amount', 'date', 'category', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
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