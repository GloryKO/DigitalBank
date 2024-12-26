from rest_framework import serializers
from .models  import *
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate

class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'phone_number', 'password', 'confirm_password', 'role']

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "passwords do not match"})
        return attrs

    def create(self, validated_data):
        # Remove confirm_password before creating the user
        validated_data.pop('confirm_password')
        
        # Create the user with set_password to properly hash the password
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            phone_number=validated_data['phone_number'],
            password=validated_data['password'],
            role=validated_data.get('role', 'customer')
        )
        return user


from django.contrib.auth import authenticate

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        # Use Django's authenticate method
        user = authenticate(email=email, password=password)

        if not user:
            raise serializers.ValidationError({"error": "Invalid email or password."})

        if not user.is_active:
            raise serializers.ValidationError({"error": "Account is inactive."})

        attrs['user'] = user
        return attrs

    def get_user(self, validated_data):
        return validated_data['user']

class KYCSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYC
        fields = ['id','id_document', 'address_proof', 'profile_photo', 'status', 'submitted_at', 'reviewed_at']
        read_only_fields = ['status', 'submitted_at', 'reviewed_at']
    
    def create(self,validated_data):
        user=validated_data.get("user")
        if KYC.objects.filter(user=user).exists():
            raise serializers.ValidationError("KYC information already submitted")
        return super().create(validated_data)


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'account_number', 'account_type', 'balance', 'created_at']

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'transaction_type', 'amount', 'timestamp', 'description']

class TransferSerializer(serializers.Serializer):
    reciepient_account_number = serializers.CharField(max_length=10)
    amount = serializers.DecimalField(max_digits=15,decimal_places=2)

    #validate the amount,recipient account
    def validate(self,data):
        sender_account = self.context['request'].user.account
        amount = data['amount']
        if amount <=0:
            raise serializers.ValidationError("Transfer amount must be greater than zero.")
        
        if sender_account.balance < amount:
            raise serializers.ValidationError
        
        try:
            recipient_account = Account.objects.get(account_number=data["reciepient_account_number"])
            if recipient_account == sender_account:
                raise serializers.ValidationError("Cannot transfer to your own account.")
        except Account.DoesNotExist:
            raise serializers.ValidationError("Recipient account does not exist.")
        
        return data

class WithdrawSerializer(serializers.Serializer):
    bank_account_number = serializers.CharField(max_length=20)
    bank_name = serializers.CharField(max_length=20)
    amount = serializers.DecimalField(nax_digits=15,decimal_places=2)

    def validate(self,data):
        user_account = self.context['request'].user.account
        amount = data['amount']

        if amount <=0:
            raise serializers.ValidationError("Withdrawal amount must be greater than Zero")
        if user_account.balance < amount:
            raise serializers.VaidationError("Insufficient balance")
        
        return data
    

class SavingsPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavingsPlan
        fields = [
            'id', 'name', 'target_amount', 'current_balance', 
            'start_date', 'end_date', 'status'
        ]
        read_only_fields = ['current_balance', 'status']

class FundSavingPlanSerializer(serializers.Serializer):
    savings_plan_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=15,decimal_places =2)

    def validate(self,data):
        savings_plan = SavingsPlan.objects.get(id=data['savings_plan_id'])
        user_account = self.context['request'].user.account

        if savings_plan != 'active':
            raise serializers.ValidationError("You can only fund active savings plans.")
        if data['amount'] <= 0:
             raise serializers.ValidationError("Amount must be greater than zero.")
        if user_account.balance < data['amount']:
            raise serializers.ValidationError("Insufficient funds.")
        return data
        