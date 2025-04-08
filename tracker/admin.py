# tracker/admin.py
from django.contrib import admin
from .models import Transaction
# No need to import User here unless you want to customize its admin view,
# as it's typically registered by default by django.contrib.auth.

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'type', 'category', 'amount')
    list_filter = ('user', 'type', 'category', 'date')
    search_fields = ('description', 'category')