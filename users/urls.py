from django.urls import path
from .views import *

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('kyc/', KYCView.as_view(), name='kyc'),
    path('account/create/', CreateAccountView.as_view(), name='create_account'),
    path('account/', AccountDetailsView.as_view(), name='account_details'),
    path('account/fund/', FundAccountView.as_view(), name='fund_account'),
    path('account/transactions/', TransactionHistoryView.as_view(), name='transaction_history'),
    path('account/transfer/', TransferFundsView.as_view(), name='transfer_funds'),
    path('account/withdraw/', WithdrawFundsView.as_view(), name='withdraw_funds'),
    path('savings-plans/', SavingsPlanView.as_view(), name='savings_plans'),
    path('savings-plans/fund/',FundSavingsPlanView.as_view(), name='fund_savings_plan'),
]