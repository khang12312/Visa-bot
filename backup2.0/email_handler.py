#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Email Handler Module

This module provides functions to fetch OTP from email inbox
and send notification emails.
"""

import os
import time
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from imap_tools import MailBox, AND
from loguru import logger


def fetch_otp(email, password, wait_time=60, check_interval=5, sender=None):
    """
    Fetch OTP from email inbox.
    
    Args:
        email: Email address to check
        password: Email password or app password
        wait_time: Maximum time to wait for OTP in seconds
        check_interval: Time between email checks in seconds
        sender: Expected sender email address (optional filter)
        
    Returns:
        str: OTP code if found, None otherwise
    """
    try:
        logger.info(f"Attempting to fetch OTP from {email}")
        
        # Determine the IMAP server based on email domain
        if "gmail" in email.lower():
            imap_server = "imap.gmail.com"
        elif "outlook" in email.lower() or "hotmail" in email.lower():
            imap_server = "outlook.office365.com"
        elif "yahoo" in email.lower():
            imap_server = "imap.mail.yahoo.com"
        else:
            logger.error(f"Unknown email provider for {email}")
            return None
            
        logger.info(f"Using IMAP server: {imap_server}")
        
        # Calculate end time for waiting
        end_time = time.time() + wait_time
        
        # Keep checking until timeout
        while time.time() < end_time:
            try:
                # Connect to the IMAP server
                with MailBox(imap_server).login(email, password) as mailbox:
                    # Search for recent emails with potential OTP
                    query = AND(date_gte=time.strftime("%d-%b-%Y", time.localtime(time.time() - 300)))
                    
                    if sender:
                        query = AND(query, from_=sender)
                        
                    # Get the most recent emails first
                    emails = list(mailbox.fetch(query, limit=5, reverse=True))
                    
                    logger.info(f"Found {len(emails)} recent emails")
                    
                    # Process each email
                    for msg in emails:
                        subject = msg.subject
                        body = msg.text or msg.html
                        
                        logger.info(f"Checking email: {subject}")
                        
                        # Look for common OTP patterns in subject and body
                        otp_patterns = [
                            r'\b([0-9]{4,8})\b',  # 4-8 digit numbers
                            r'verification code[^0-9]*([0-9]{4,8})',
                            r'OTP[^0-9]*([0-9]{4,8})',
                            r'one-time password[^0-9]*([0-9]{4,8})',
                            r'security code[^0-9]*([0-9]{4,8})',
                            r'verification code is ([0-9]{4,8})'
                        ]
                        
                        # Check subject first
                        for pattern in otp_patterns:
                            match = re.search(pattern, subject, re.IGNORECASE)
                            if match:
                                otp = match.group(1)
                                logger.info(f"Found OTP in subject: {otp}")
                                return otp
                                
                        # Then check body
                        for pattern in otp_patterns:
                            match = re.search(pattern, body, re.IGNORECASE)
                            if match:
                                otp = match.group(1)
                                logger.info(f"Found OTP in body: {otp}")
                                return otp
            except Exception as e:
                logger.error(f"Error checking emails: {str(e)}")
                
            # Wait before checking again
            logger.info(f"No OTP found, waiting {check_interval} seconds before checking again")
            time.sleep(check_interval)
            
        logger.warning(f"No OTP found after waiting {wait_time} seconds")
        return None
    except Exception as e:
        logger.error(f"Error in fetch_otp: {str(e)}")
        return None


def send_notification(sender_email, sender_password, recipient_email, subject, message, attachments=None):
    """
    Send notification email with optional attachments.
    
    Args:
        sender_email: Sender's email address
        sender_password: Sender's email password or app password
        recipient_email: Recipient's email address
        subject: Email subject
        message: Email message body (HTML format supported)
        attachments: List of file paths to attach (optional)
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        logger.info(f"Sending notification email to {recipient_email}")
        
        # Create message container
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Attach message body
        msg.attach(MIMEText(message, 'html'))
        
        # Attach files if provided
        if attachments:
            for file_path in attachments:
                if not os.path.exists(file_path):
                    logger.warning(f"Attachment not found: {file_path}")
                    continue
                    
                # Determine content type based on file extension
                file_name = os.path.basename(file_path)
                if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    # Handle image attachments
                    with open(file_path, 'rb') as img_file:
                        img = MIMEImage(img_file.read())
                        img.add_header('Content-Disposition', 'attachment', filename=file_name)
                        msg.attach(img)
                else:
                    # Handle other file types
                    with open(file_path, 'rb') as file:
                        attachment = MIMEText(file.read())
                        attachment.add_header('Content-Disposition', 'attachment', filename=file_name)
                        msg.attach(attachment)
        
        # Determine SMTP server based on sender email domain
        if "gmail" in sender_email.lower():
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
        elif "outlook" in sender_email.lower() or "hotmail" in sender_email.lower():
            smtp_server = "smtp.office365.com"
            smtp_port = 587
        elif "yahoo" in sender_email.lower():
            smtp_server = "smtp.mail.yahoo.com"
            smtp_port = 587
        else:
            logger.error(f"Unknown email provider for {sender_email}")
            return False
            
        logger.info(f"Using SMTP server: {smtp_server}:{smtp_port}")
        
        # Connect to SMTP server and send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            
        logger.info(f"Notification email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Error sending notification email: {str(e)}")
        return False