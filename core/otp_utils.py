import random
from datetime import datetime, timedelta

def generate_otp():
    return str(random.randint(100000, 999999))  # 6-digit OTP

def otp_expiry():
    return datetime.utcnow() + timedelta(minutes=10)
