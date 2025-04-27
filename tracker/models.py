# tracker/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('Income', 'Income'),
        ('Expense', 'Expense'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=7, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    category = models.CharField(max_length=50)
    description = models.CharField(max_length=200, blank=True)

    is_recurring = models.BooleanField(default=False)
    recurring_due_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.type} - {self.amount} on {self.date}"

    class Meta:
        ordering = ['-date', '-created_at']

class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    category = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    month = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.amount <= Decimal('0.00'):
            raise ValidationError({'amount': "Budget amount must be positive."})
        if self.month and self.month.day != 1:
             raise ValidationError({'month': "Please select any day in the desired month; it will be saved as the 1st."})


    def save(self, *args, **kwargs):
        if self.month:
            self.month = self.month.replace(day=1)
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('user', 'category', 'month')
        ordering = ['-month', 'category']

    def __str__(self):
        month_str = self.month.strftime('%Y-%m')
        return f"{self.user.username} - {self.category} Budget ({month_str}): ${self.amount}"


class Goal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    name = models.CharField(max_length=100, help_text="Name of the financial goal (e.g., New Car Fund)")
    target_amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="The target amount for the goal")
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="The amount currently saved/contributed")
    created_at = models.DateTimeField(auto_now_add=True)
    # target_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    @property
    def progress_percent(self):
        if self.target_amount is None or self.target_amount <= 0:
            return 0
        progress = (self.current_amount / self.target_amount) * 100
        return min(progress, Decimal('100.00'))

    @property
    def remaining_amount(self):
        if self.target_amount is None:
            return None
        remaining = self.target_amount - self.current_amount
        return max(remaining, Decimal('0.00'))

