import os
from dotenv import load_dotenv


import smtplib
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

OTP_TTL_SECONDS = 300
PENDING_TTL = 600

OTP_MAX_REQUESTS = 5
OTP_REQUEST_WINDOW = 600
OTP_COOLDOWN_SECONDS = 60

OTP_MAX_WRONG_ATTEMPTS = 3
OTP_BLOCK_DURATION = 900



def send_support_emails(user_email: str, subject: str, message: str, ticket_id: str):
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        raise RuntimeError("Missing email credentials in environment variables.")

    admin_msg = _build_admin_notification(user_email, subject, message, ticket_id)
    user_msg = _build_user_confirmation(user_email, subject, message, ticket_id)

    # ✅ Single SMTP connection for both emails
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(admin_msg)
        server.send_message(user_msg)


def _build_admin_notification(user_email: str, subject: str, message: str, ticket_id: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = f"New Support Ticket #{ticket_id}"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_ADDRESS
    msg["Reply-To"] = user_email

    msg.set_content("New support ticket received.")
    msg.add_alternative(f"""
    <html><head><style>
        body {{ font-family: Arial, sans-serif; background: #f4f6f9; padding: 30px; }}
        .container {{ max-width: 600px; background: white; margin: auto; border-radius: 8px;
                      box-shadow: 0 3px 10px rgba(0,0,0,0.08); overflow: hidden; }}
        .header {{ background: #2d6cdf; color: white; padding: 20px; font-size: 20px; font-weight: bold; }}
        .content {{ padding: 25px; color: #333; }}
        .box {{ background: #f8f9fc; padding: 15px; border-radius: 6px;
                border: 1px solid #e3e6f0; margin-top: 10px; }}
        .label {{ font-weight: bold; color: #555; }}
    </style></head>
    <body>
        <div class="container">
            <div class="header">New Support Request</div>
            <div class="content">
                <p>A user submitted a support request.</p>
                <div class="box">
                    <p><span class="label">Ticket ID:</span> {ticket_id}</p>
                    <p><span class="label">User Email:</span> {user_email}</p>
                    <p><span class="label">Subject:</span> {subject}</p>
                </div>
                <div class="box">
                    <p class="label">User Message:</p>
                    <p>{message}</p>
                </div>
            </div>
        </div>
    </body></html>
    """, subtype="html")
    return msg


def _build_user_confirmation(user_email: str, subject: str, message: str, ticket_id: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = f"Support Request Received (Ticket #{ticket_id})"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = user_email

    msg.set_content("Your email client does not support HTML emails.")
    msg.add_alternative(f"""
    <html><head><style>
        body {{ font-family: Arial, sans-serif; background-color: #f5f7fb; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 40px auto; background: white; border-radius: 8px;
                      box-shadow: 0 2px 10px rgba(0,0,0,0.08); overflow: hidden; }}
        .header {{ background: #4CAF50; color: white; padding: 20px; text-align: center;
                   font-size: 22px; font-weight: bold; }}
        .content {{ padding: 30px; color: #333; line-height: 1.6; }}
        .ticket-box {{ background: #f8f9fc; padding: 15px; border-radius: 6px;
                       margin-top: 15px; border: 1px solid #e4e6ef; }}
        .footer {{ text-align: center; font-size: 13px; color: #888;
                   padding: 20px; border-top: 1px solid #eee; }}
    </style></head>
    <body>
        <div class="container">
            <div class="header">Support Request Received</div>
            <div class="content">
                <p>Hello,</p>
                <p>Thank you for contacting our support team. We have received your request
                and our team will review it shortly.</p>
                <div class="ticket-box">
                    <b>Ticket ID:</b> {ticket_id}<br><br>
                    <b>Subject:</b> {subject}<br><br>
                    <b>Your Message:</b><br>{message}
                </div>
                <p style="margin-top:20px;">Our team will get back to you as soon as possible.</p>
                <p>Regards,<br><b>Support Team</b></p>
            </div>
            <div class="footer">This is an automated message. Please do not reply directly to this email.</div>
        </div>
    </body></html>
    """, subtype="html")
    return msg




def send_email_otp(email: str, otp: str):
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        raise RuntimeError("Missing email credentials")
 
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Your Togetherly Verification Code"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = email
 
    digits = "".join(
        f'<span style="display:inline-block;width:44px;height:52px;line-height:52px;text-align:center;'
        f'background:#fff;border:1.5px solid #fde2cc;border-radius:10px;'
        f'font-family:Georgia,serif;font-size:26px;font-weight:700;color:#1a1a1a;'
        f'margin:0 4px;box-shadow:0 2px 8px rgba(232,82,26,0.10);">{ch}</span>'
        for ch in otp
    )
 
    html = f"""
    <div style="background:#f5ece4;padding:40px 16px;font-family:Arial,sans-serif;">
      <div style="max-width:480px;margin:0 auto;border-radius:16px;overflow:hidden;box-shadow:0 8px 32px rgba(0,0,0,0.08);">
 
        <!-- Header -->
        <div style="background:linear-gradient(135deg,#e8521a,#f97316);padding:24px 32px;">
          <div style="display:inline-block;width:40px;height:40px;background:#fff;border-radius:10px;text-align:center;line-height:40px;font-size:18px;vertical-align:middle;">🤝</div>
          <div style="display:inline-block;vertical-align:middle;margin-left:12px;">
            <div style="font-size:15px;font-weight:700;letter-spacing:2.5px;color:#fff;text-transform:uppercase;">Togetherly</div>
            <div style="font-size:10px;letter-spacing:1px;color:rgba(255,255,255,0.7);text-transform:uppercase;">Admin Portal</div>
          </div>
        </div>
 
        <!-- Body -->
        <div style="background:#fff;padding:36px 32px;text-align:center;">
          <div style="font-size:28px;margin-bottom:8px;">👋</div>
          <h2 style="font-family:Georgia,serif;font-size:22px;color:#1a1a1a;margin:0 0 6px;">Verify It's You</h2>
          <p style="font-size:13px;color:#999;margin:0 0 28px;">Use the code below to sign in to your admin dashboard.</p>
 
          <!-- OTP digits -->
          <div style="background:#fff8f4;border:1.5px solid #fde2cc;border-radius:12px;padding:24px 16px;margin-bottom:20px;">
            <div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#e8521a;font-weight:600;margin-bottom:14px;">One-Time Password</div>
            <div>{digits}</div>
            <div style="font-size:11px;color:#bbb;margin-top:14px;">Expires in <strong style="color:#e8521a;">10 minutes</strong></div>
          </div>
 
          <p style="font-size:12px;color:#aaa;line-height:1.7;margin:0;">
            If you didn't request this, you can safely ignore this email.<br/>
            Never share this code with anyone.
          </p>
        </div>
 
        <!-- Footer -->
        <div style="background:#1a1a1a;padding:18px 32px;text-align:center;">
          <span style="font-size:10px;letter-spacing:2px;color:#fb923c;text-transform:uppercase;font-weight:700;">Togetherly</span>
          <span style="color:#333;margin:0 10px;">·</span>
          <span style="font-size:10px;color:#555;">🔒 SSL Secured</span>
          <span style="color:#333;margin:0 10px;">·</span>
          <span style="font-size:10px;color:#555;">© 2026 Authorized Access Only</span>
        </div>
 
      </div>
    </div>
    """
 
    msg.attach(MIMEText(f"Your Togetherly OTP is: {otp}\nExpires in 10 minutes. Do not share this code.", "plain"))
    msg.attach(MIMEText(html, "html"))
 
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        
        
        
        
        
def _build_action_email(
    *,
    heading: str,
    subtext: str,
    role_badge: str,
    action_url: str,
    btn_label: str,
    expiry_note: str,
    ignore_note: str,
) -> tuple[str, str]:
    """Returns (plain_text, html) for a branded action/invite email."""
 
    plain = (
        f"{heading}\n\n"
        f"{subtext}\n\n"
        f"{btn_label}: {action_url}\n\n"
        f"{expiry_note}\n"
        f"{ignore_note}\n\n"
        f"Regards,\nTogetherly Support Team"
    )
 
    html = f"""
    <div style="background:#f5ece4;padding:40px 16px;font-family:Arial,sans-serif;">
      <div style="max-width:480px;margin:0 auto;border-radius:16px;overflow:hidden;box-shadow:0 8px 32px rgba(0,0,0,0.08);">
 
        <!-- Header -->
        <div style="background:linear-gradient(135deg,#e8521a,#f97316);padding:24px 32px;">
          <div style="display:inline-block;width:40px;height:40px;background:#fff;border-radius:10px;text-align:center;line-height:40px;font-size:18px;vertical-align:middle;">🤝</div>
          <div style="display:inline-block;vertical-align:middle;margin-left:12px;">
            <div style="font-size:15px;font-weight:700;letter-spacing:2.5px;color:#fff;text-transform:uppercase;">Togetherly</div>
            <div style="font-size:10px;letter-spacing:1px;color:rgba(255,255,255,0.7);text-transform:uppercase;">Admin Portal</div>
          </div>
        </div>
 
        <!-- Body -->
        <div style="background:#fff;padding:36px 32px;text-align:center;">
          <div style="font-size:28px;margin-bottom:12px;">✉️</div>
          <h2 style="font-family:Georgia,serif;font-size:22px;color:#1a1a1a;margin:0 0 8px;">{heading}</h2>
 
          <!-- Role badge -->
          <div style="display:inline-block;background:#fff8f4;border:1.5px solid #fde2cc;border-radius:20px;padding:5px 16px;margin-bottom:20px;">
            <span style="font-size:11px;letter-spacing:1.5px;text-transform:uppercase;color:#e8521a;font-weight:600;">{role_badge}</span>
          </div>
 
          <p style="font-size:13px;color:#666;line-height:1.7;margin:0 0 28px;">{subtext}</p>
 
          <!-- CTA button -->
          <a href="{action_url}"
             style="display:inline-block;background:linear-gradient(135deg,#e8521a,#f97316);color:#fff;
                    font-size:14px;font-weight:600;text-decoration:none;padding:14px 36px;
                    border-radius:50px;box-shadow:0 6px 20px rgba(232,82,26,0.30);letter-spacing:0.3px;">
            {btn_label} →
          </a>
 
          <!-- Expiry + ignore -->
          <div style="margin-top:24px;padding-top:20px;border-top:1px solid #f5f0eb;">
            <p style="font-size:11px;color:#e8521a;font-weight:600;margin:0 0 6px;">⏱ {expiry_note}</p>
            <p style="font-size:11px;color:#bbb;margin:0;">{ignore_note}</p>
          </div>
        </div>
 
        <!-- Footer -->
        <div style="background:#1a1a1a;padding:18px 32px;text-align:center;">
          <span style="font-size:10px;letter-spacing:2px;color:#fb923c;text-transform:uppercase;font-weight:700;">Togetherly</span>
          <span style="color:#333;margin:0 10px;">·</span>
          <span style="font-size:10px;color:#555;">🔒 SSL Secured</span>
          <span style="color:#333;margin:0 10px;">·</span>
          <span style="font-size:10px;color:#555;">© 2026 Authorized Access Only</span>
        </div>
 
      </div>
    </div>
    """
 
    return plain, html



def _send(*, to: str, subject: str, plain: str, html: str):
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        raise RuntimeError("Missing email credentials")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

