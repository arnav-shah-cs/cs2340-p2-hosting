# tracker/urls.py
from django.urls import path
from . import views

app_name = 'tracker'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('add/', views.add_transaction_view, name='add_transaction'),
    path('tips/', views.financial_tips_view, name='financial_tips'),
    path('edit/<int:pk>/', views.edit_transaction_view, name='edit_transaction'),
    path('delete/<int:pk>/', views.delete_transaction_view, name='delete_transaction'),
    path('goals/add/', views.add_goal, name='add_goal'),
    path('goals/<int:goal_id>/contribute/', views.add_contribution, name='add_contribution'),
    path('stock-market/', views.stock_market_overview, name='stock_market_overview'),
    path('budgets/', views.budget_list_view, name='budget_list'),
    path('budgets/add/', views.budget_create_view, name='budget_create'),
    path('budgets/edit/<int:pk>/', views.budget_edit_view, name='budget_edit'),
    path('budgets/delete/<int:pk>/', views.budget_delete_view, name='budget_delete'),
    path('send-upcoming-expenses-email/', views.send_upcoming_due_date_emails, name='send_upcoming_due_date_emails'),
    path('send-spending-summary/', views.send_spending_summary_email_view, name='send_spending_summary_email'),
    path('plaid-link/', views.plaid_link_view, name='plaid_link'),
    path('plaid-exchange/', views.exchange_public_token, name='plaid_exchange_public_token'),

    path('plaid-transactions/', views.plaid_transactions_view, name='plaid_transactions'),

]