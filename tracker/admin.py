# tracker/admin.py
from django.contrib import admin
from .models import Transaction, Goal
# No need to import User here unless you want to customize its admin view,
# as it's typically registered by default by django.contrib.auth.

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'type', 'category', 'amount')
    list_filter = ('user', 'type', 'category', 'date')
    search_fields = ('description', 'category')

admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Goal)