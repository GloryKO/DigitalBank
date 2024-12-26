from django.shortcuts import render
from .utils import *
# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import *
from .serializers import *
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Add any custom validation if needed
        data = super().validate(attrs)
        # You can add more data to the response if required
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class RegisterView(APIView):
    def post(self,request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message":"Registration successful"})
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.get_user(serializer.validated_data)
            tokens = RefreshToken.for_user(user)
            return Response({
                "access": str(tokens.access_token),
                "refresh": str(tokens)
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class KYCView(APIView):
    """
        retrieve and post customer kyc
    """
    permission_classes = [IsAuthenticated]

    def get(self,request):
        """ retrieve kyc for a logged in user"""
        try:
            kyc = KYC.objects.get(user=request.user)
            serializer = KYCSerializer(kyc)
            return Response(serializer.data,status=status.HTTP_200_OK)
        except KYC.DoesNotExist:
            return Response({"detail":"kyc not submitted"})
    
    def post(self,request):
        """ submit user kyc for a logged in user"""
        serializer = KYCSerializer(data=request.data)
        if serializer.is_valid:
            serializer.save(user=request.user)
            return Response({"detail":"kyc submitted "},status=status.HTTP_201_CREATED)
        return Response(serializer.erros,status=status.HTTP_400_BAD_REQUEST)

    
class CreateAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request):
        """
        allow a user create a bank account
        """
        if hasattr(request.user,'account'):
            return Response({"detail":"User has an account already"},status=status.HTTP_400_BAD_REQUEST)
        account_number = generate_account_number()
        account = Account.objects.create(
            user = request.user,
            account_number=account_number,
            account_type=request.data.get('account_type','savings')

        )
        serializer = AccountSerializer(account)
        if serializer.is_valid:
            serializer.save()
        return Response(serializer.data,status=status.HTTP_201_CREATED)

class AccountDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request):
        """
        Retrieve the user's account details.
        """
        try:
            #account = Account.objects.get(user=request.user)
           account= request.user.account
           serializer = AccountSerializer(account)
           return Response (serializer.data,status=status.HTTP_200_OK)
        
        except Account.DoesNotExist:
            return Response({"detail":"Account not found"},status=status.HTTP_400_NOT_FOUND)
    

class FundAccountView(APIView):
    permission_classes= [IsAuthenticated]
    def post(self,request):
        """
        Mock depositing money into the user's account.
        """
        try:
            account = request.user.account
            amount =request.data.get('amount',0)
            if amount <=0:
                return Response({"detail":"Invalid amount"},status=status.HTTP_404_BAD_REQUEST)
            account.balance += float(amount)
            account.save()
            Transaction.objects.create(
                account=account,amount=amount,transaction_type='deposit',description=request.data.get("description","Deposit")
            )
            serializer = AccountSerializer(account)
            return Response(serializer.data,status=status.HTTP_200_OK)
        except Account.DoesNotExist:
            return Response({"detail":"account does not exist"},status=status.HTTP_404_NOT_FOUND)
        

class TransactionHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request):
        """
        Retrieve all transactions for the user's account.
        """
        try:
            account = request.user.account
            transactions = account.transactions.all()
            serializer = TransactionSerializer(transactions,many=True)
            return Response(serializer.data,status=status.HTTP_200_OK)
        except Account.DoesNotExist:
            return Response({"detail":"account does not exist"},status=status.HTTP_404_NOT_FOUND)

class TransferFundsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request):
        serializer = TransferSerializer(request.data,context={'request':request})
        if serializer.is_valid():
            sender_account = request.user.account
            recipient_account = Account.objects.get(account_number=serializer.validated_data['reciepient_account_number'])
            amount = serializer.validated_data['amount']

            #deduct balance from sender account
            sender_account.balance -= amount
            sender_account.save()

            #add to recipient account
            recipient_account += amount
            recipient_account.save()

            #record both transactions
            reference = uuid.uuuid4()
            Transaction.objects.create(
                account=sender_account,
                transaction_type='transfer',
                amount=-amount,
                description=f"Transfer to {recipient_account.account_number}",
                reference=reference,
            )
            Transaction.objects.create(
                account=recipient_account,
                transaction_type='transfer',
                amount=amount,
                description=f"Transfer from {sender_account.account_number}",
                reference=reference,
            )
            return Response({"detail":"Transfer successful"},status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

class WithdrawFundsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request):
        serializer = WithdrawSerializer(request.data,context={'request':request})
        if serializer.is_valid():
            bank_name = serializer.validated_data['bank_name']
            user_account = request.user.account
            bank_account_number = serializer.validated_data['bank_account_number']
            amount = serializer.validated_data['amount']

            user_account.balance -= amount
            user_account.save()

            transaction = Transaction.objects.create(
                account=user_account,
                transaction_type='withdrawal',
                amount=-amount,
                description=f"Withdrawal to {bank_name} ({bank_account_number})",
                status='pending'
            )

            transaction.status ="successful"
            transaction.save()

            return Response(
                {"detail": "Withdrawal successful.", "transaction_id": transaction.id},
                status=status.HTTP_200_OK
            )

class SavingsPlanView(APIView):
       permission_classes = [IsAuthenticated]
       def get(self, request):
        """
        Retrieve all savings plans for the authenticated user.
        """
        plans = request.user.savings_plans.all()
        serializer = SavingsPlanSerializer(plans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
       
       def post(self,request):
           """
           create a savings plan for the authenticated user.
           """
           serializer = SavingsPlanSerializer(data=request.data)
           if serializer.is_valid():
               serializer.save(user=request.user)
               return Response(serializer.data,status=status.HTTP_201_CREATED)
           return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
       

class FundSavingsPlanView(APIView):
     permission_classes = [IsAuthenticated]

     def post(self,request):
         serializer = FundSavingPlanSerializer(data=request.data,context={'request':request})
         if serializer.is_valid():
             savings_plan = SavingsPlan.objects.get(id=serializer.validated_data['savings_plan_id'])
             amount = serializer.validated_data['amount']
             user_account = request.user.account

             #Deduct from user account to savings plan
             user_account -=amount
             user_account.save()
             savings_plan.current_balance += amount
             if savings_plan.current_balance >= savings_plan.target_amount:
                 savings_plan.status = 'completed'
             savings_plan.save()

             return Response({"detail":"Savings plan funded successfully."}, status=status.HTTP_200_OK)
         
         return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)




        