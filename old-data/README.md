# Italy Visa Checker Bot

A Python-based automation bot designed to check visa appointment availability on the Italy visa appointment website (https://appointment.theitalyvisa.com). This bot can log in with user credentials, bypass captchas, check for visa appointment slot availability, automatically make payments when slots are available, fetch OTPs from email inbox, complete the full application process, and send email notifications to the user.

## Features

✅ **Headless browser automation** using Selenium

✅ **Advanced Captcha solving integration**:
   - 2Captcha API for reCAPTCHA and image captchas
   - OCR-based solving for number box captchas
   - Fallback mechanisms for reliable operation

✅ **OTP extraction from email** (IMAP)

✅ **Secure login automation** with dynamic field detection:
   - Handles randomized password field IDs
   - Identifies password fields by label text
   - Multiple fallback mechanisms for reliable login

✅ **Notification system** (Email)

✅ **Auto-payment handling** via card/UPI

✅ **Logging and error tracking**

✅ **Screenshot capture** of appointment and confirmation pages

✅ **Data scraping** of appointment details and confirmation information

## Requirements


- Python 3.8+
- Selenium
- Requests
- IMAP Tools
- Python-dotenv
- Loguru
- 2Captcha API key (recommended but optional)
- Tesseract OCR (for OCR-based captcha solving)
- OpenCV and NumPy (installed via requirements.txt)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/visa-checker-bot.git
cd visa-checker-bot
```

2. Install the required packages:

```bash
pip install -r requirements.txt
```

3. Install Tesseract OCR (for OCR-based captcha solving):

   - **Windows**: Download and install from [Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
     - During installation, note the installation path (default is usually `C:\Program Files\Tesseract-OCR`)
     - Add the Tesseract installation directory to your system PATH or update the path in `captcha_solver.py`
   - **Linux**: `sudo apt install tesseract-ocr`
   - **macOS**: `brew install tesseract`

   Make sure the Tesseract executable is in your system PATH or properly configured in the code.
   
   To verify your Tesseract OCR installation, run the test script:
   
   ```bash
   python test_ocr.py
   ```
   
   This script will check if Tesseract is properly installed and configured, and test OCR functionality with a sample image.

4. Set up environment variables:

Create a `.env` file in the project root directory based on the provided `.env.example` file:

```
# Copy the .env.example file to .env
cp .env.example .env

# Edit the .env file with your actual values
```

## Configuration

Edit the `.env` file with your actual values:

```
# Target website URL
TARGET_URL=https://appointment.theitalyvisa.com/Global/appointmentdata/MyAppointments

# User credentials for visa website
USER_ID=your_username_or_email
USER_PASSWORD=your_secure_password

# Email settings for OTP retrieval and notifications
EMAIL=your_email@gmail.com
EMAIL_PASSWORD=your_app_password_or_email_password
NOTIFY_EMAIL=email_to_receive_notifications@example.com

# Captcha solving service API key (2Captcha or Anti-Captcha)
CAPTCHA_API_KEY=your_captcha_api_key

# Payment details (for card payment)
CARD_NUMBER=1234567890123456
CARD_HOLDER=YOUR NAME
CARD_EXPIRY_MONTH=12
CARD_EXPIRY_YEAR=25
CARD_CVV=123

# UPI payment (for Indian users)
UPI_ID=your_upi_id@upi
```

### Important Notes on Email Password

If you're using Gmail, you'll need to use an App Password instead of your regular password. To generate an App Password:

1. Enable 2-Step Verification on your Google Account
2. Go to your Google Account > Security > App passwords
3. Select "Mail" and "Other (Custom name)"
4. Enter a name like "Visa Bot" and click "Generate"
5. Use the generated 16-character password in your `.env` file

## Troubleshooting

### Login Issues

- **Dynamic Password Fields**: The website uses randomized IDs for password fields. The bot is designed to handle this by looking for password fields by label text first, then by type attribute.

- **Debug Information**: If login fails, check the `data/debug` directory for screenshots and HTML source of the login page. This can help identify changes in the website structure.

### Captcha Solving Issues

- **OCR-based Solving**: For number box captchas, ensure Tesseract OCR is properly installed and in your system PATH.

- **2Captcha Service**: If using 2Captcha, verify your API key is correct and has sufficient balance.

- **Fallback Mechanisms**: The bot will attempt multiple strategies to solve captchas, including random selection as a last resort.

### Browser Automation Issues

- **Chrome Driver**: Make sure you have the correct ChromeDriver version for your Chrome browser.

- **Anti-Bot Detection**: The bot uses various techniques to avoid detection. If you're still experiencing issues, try adjusting the random delay settings in the code.

### Payment Processing Issues

- **Card Details**: Ensure your card details in the `.env` file are correct.

- **UPI Payments**: For UPI payments, make sure your UPI ID is valid and active.

## Usage

Run the bot with the following command:

```bash
python bot.py
```

### How It Works

1. The bot launches the browser and navigates to the target URL.
2. It performs login and handles captcha (if required).
3. It periodically checks for visa slot availability.
4. If a slot is found, it proceeds to make a payment.
5. During the payment process, it navigates to the appointment data page, takes a screenshot, and scrapes appointment details.
6. It saves the screenshot and scraped data to the data directory for future reference.
7. It fetches OTP from the registered email if required.
8. It completes the application process, taking a screenshot of the confirmation page and scraping confirmation details.
9. It sends a confirmation email with details and screenshots.

## Customization

### Headless Mode

By default, the bot runs in visible browser mode. To run in headless mode (no visible browser window), uncomment the following line in `bot.py`:

```python
# chrome_options.add_argument("--headless")
```

### Check Interval

You can modify the check interval (how often the bot checks for available slots) by changing the `check_interval` value in the `VisaCheckerBot` class:

```python
self.check_interval = 300  # 5 minutes by default
```

### Data Storage

The bot automatically creates and uses the following directory structure for storing screenshots and scraped data:

```
data/
├── screenshots/     # Contains screenshots of appointment and confirmation pages
└── scraped_data/    # Contains JSON files with scraped appointment and confirmation data
```

Screenshots and data files are named with timestamps for easy tracking and reference.

## Troubleshooting

### Logs

The bot logs all activities to the `visa_bot.log` file. Check this file if you encounter any issues.

### Common Issues

1. **Captcha Solving Fails**: Ensure your 2Captcha API key is valid and has sufficient balance.

2. **Email OTP Retrieval Fails**: Check your email credentials and ensure IMAP is enabled for your email account.

3. **Payment Processing Fails**: Verify your payment details in the `.env` file.

4. **Browser Driver Issues**: Make sure you have the correct version of Chrome and ChromeDriver installed.

## Legal Disclaimer

This project is intended for educational and ethical use only. Do not use on websites where automation is prohibited. The user is responsible for ensuring compliance with the terms of service of the target website and all applicable laws and regulations.

## License

MIT License

## Contributors

Developed by [Khan G Developers]

Feel free to raise issues or contribute improvements!