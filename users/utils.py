import random

def generate_account_number():
    """Generate random 10-digit account number"""
    return str(random.randint(1000000000, 9999999999))