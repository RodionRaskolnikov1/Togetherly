
import json
import secrets
import os
import smtplib

from fastapi import HTTPException
from dotenv import load_dotenv
from twilio.rest import Client
from .redis_client import r

from email.mime.text import MIMEText
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart

from utils.mail import (
    send_email_otp,
    _build_action_email,
    _send
)

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_FROM = os.getenv("TWILIO_PHONE_FROM")

OTP_TTL_SECONDS = 300
PENDING_TTL = 600

OTP_MAX_REQUESTS = 5
OTP_REQUEST_WINDOW = 600
OTP_COOLDOWN_SECONDS = 60

OTP_MAX_WRONG_ATTEMPTS = 3
OTP_BLOCK_DURATION = 900

FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://127.0.0.1:3000")


def check_rate_limit(target: str):
    key = f"otp:req-count:{target}"
    count = r.get(key)
    if count is None:
        r.setex(key, OTP_REQUEST_WINDOW, 1)
        return
    if int(count) >= OTP_MAX_REQUESTS:
        raise HTTPException(status_code=429, detail="Too many OTP requests")
    r.incr(key)


def check_cooldown(target: str):
    key = f"otp:cooldown:{target}"
    if r.exists(key):
        raise HTTPException(status_code=429, detail="Wait before requesting OTP")
    r.setex(key, OTP_COOLDOWN_SECONDS, 1)


def increment_wrong_attempt(target: str):
    key = f"otp:wrong:{target}"
    count = r.incr(key)
    if count == 1:
        r.expire(key, OTP_BLOCK_DURATION)
    if count >= OTP_MAX_WRONG_ATTEMPTS:
        r.setex(f"otp:blocked:{target}", OTP_BLOCK_DURATION, 1)
        raise HTTPException(status_code=403, detail="Blocked due to wrong attempts")


def is_user_blocked(target: str):
    if r.exists(f"otp:blocked:{target}"):
        raise HTTPException(status_code=403, detail="User blocked")


def is_email(target: str):
    return "@" in target


def _gen_otp():
    return str(secrets.randbelow(900000) + 100000)


def send_otp(target: str, via_email: bool):
    is_user_blocked(target)
    check_rate_limit(target)
    otp = _gen_otp()
    r.setex(f"otp:{target}", OTP_TTL_SECONDS, otp)
    if via_email:
        _send_email(target, otp)
    else:
        _send_phone(target, otp)
    return True



def _send_email(email: str, otp: str):
    send_email_otp(email, otp)
    
                    
def send_admin_invite_email(email: str, token: str):
    setup_link = f"{FRONTEND_BASE_URL}/setup-password?token={token}"
    plain, html = _build_action_email(
        heading="You've been invited!",
        subtext="You have been added as a <strong>Community Admin</strong> on Togetherly. "
                "Click below to activate your account and set your password.",
        role_badge="Community Admin",
        action_url=setup_link,
        btn_label="Set Up My Account",
        expiry_note="This link expires in 24 hours.",
        ignore_note="If you didn't expect this invite, you can safely ignore this email.",
    )
    _send(to=email, subject="You're invited — Set up your Community Admin account", plain=plain, html=html)
 
 
def send_coordinator_invite_email(email: str, token: str):
    setup_link = f"{FRONTEND_BASE_URL}/setup-password?token={token}"
    plain, html = _build_action_email(
        heading="You've been invited!",
        subtext="You have been added as a <strong>Coordinator</strong> on Togetherly. "
                "Click below to activate your account and set your password.",
        role_badge="Coordinator",
        action_url=setup_link,
        btn_label="Set Up My Account",
        expiry_note="This link expires in 24 hours.",
        ignore_note="If you didn't expect this invite, you can safely ignore this email.",
    )
    _send(to=email, subject="You're invited — Set up your Coordinator account", plain=plain, html=html)
 
 
def send_password_reset_email(email: str, token: str):
    reset_link = f"{FRONTEND_BASE_URL}/password-reset.html?token={token}"
    plain, html = _build_action_email(
        heading="Reset your password",
        subtext="We received a request to reset the password for your Togetherly account. "
                "Click below to choose a new password.",
        role_badge="Password Reset",
        action_url=reset_link,
        btn_label="Reset My Password",
        expiry_note="This link expires in 1 hour.",
        ignore_note="If you didn't request this, you can safely ignore this email.",
    )
    _send(to=email, subject="Reset your Togetherly password", plain=plain, html=html)
 
        
    
def send_member_invite(email: str, token: str):
    setup_link = f"{FRONTEND_BASE_URL}/setup-password?token={token}"
    plain, html = _build_action_email(
        heading="You've been invited!",
        subtext="You have been added as a <strong>Member</strong> on Togetherly. "
                "Click below to activate your account and set your password.",
        role_badge="Member",
        action_url=setup_link,
        btn_label="Set Up My Account",
        expiry_note="This link expires in 24 hours.",
        ignore_note="If you didn't expect this invite, you can safely ignore this email.",
    )
    _send(to=email, subject="You're invited — Set up your Togetherly Member account", plain=plain, html=html)
    


def _send_phone(phone: str, otp: str):
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_FROM:
        raise RuntimeError("Missing Twilio credentials")
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    client.messages.create(
        body=f"Your Togetherly verification code is: {otp}\nExpires in 10 minutes. Do not share this code.",
        from_=TWILIO_PHONE_FROM,
        to=phone
    )


def verify_otp(target: str, otp: str) -> bool:
    is_user_blocked(target)
    saved = r.get(f"otp:{target}")
    if not saved:
        return False
    if saved != otp:
        increment_wrong_attempt(target)
        return False
    r.delete(f"otp:wrong:{target}")
    r.delete(f"otp:req-count:{target}")
    return True


def save_pending_user(key: str, data: dict):
    r.setex(f"user:pending:{key}", PENDING_TTL, json.dumps(data))


def get_pending_user(key: str):
    raw = r.get(f"user:pending:{key}")
    return json.loads(raw) if raw else None


def delete_pending(key: str):
    r.delete(f"user:pending:{key}")
    r.delete(f"otp:{key}")



