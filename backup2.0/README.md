# VisaBot 2.0

An automated bot for handling visa appointment bookings on the Italy visa website with human-like behavior.

## Features

- Automated login with email and password
- CAPTCHA solving capabilities (image-based, reCAPTCHA, hCaptcha)
- Human-like behavior simulation (random delays, mouse movements)
- Post-login form handling
- Appointment availability checking
- Appointment selection and booking
- Payment processing
- OTP verification
- Email notifications
- Session management and recovery
- Error handling and recovery

## Project Structure

The project has been refactored into modular components for better maintainability. The codebase is organized in two ways:

### Root Directory
- `main.py` - Entry point for the application
- `visa_bot.py` - Main bot class integrating all components
- `config.py` - Centralized configuration
- `utils.py` - Common utility functions

### Original Files (Legacy Support)
These files are kept in the root directory for backward compatibility:
- `browser_manager.py` - Browser setup and management
- `login_handler.py` - Login process management
- `navigation_handler.py` - URL-based navigation and page detection
- `captcha_utils.py` - Captcha detection and solving
- `captcha_sove2.py` - Captcha solving implementation
- `coordinate_captcha_solver.py` - Coordinate-based captcha solver

### Backend Directory Structure
The backend directory contains modular components organized by functionality:

- `backend/`
  - `appointment/` - Appointment checking and selection
  - `browser/` - Browser setup and management
  - `captcha/` - Captcha detection and solving
  - `confirmation/` - Confirmation page handling
  - `email/` - Email OTP retrieval and notifications
  - `error/` - Error detection and recovery
  - `form/` - Form filling and submission
  - `login/` - Login process management
  - `navigation/` - URL-based navigation and page detection
  - `payment/` - Payment processing
  - `session/` - Session management and recovery

## Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Install Tesseract OCR (required for image-based captcha solving):
   - Windows: Download from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
   - Linux: `sudo apt install tesseract-ocr`
   - macOS: `brew install tesseract`
   - For detailed instructions, see [Tesseract Setup Guide](docs/tesseract_setup.md)
   - To verify your installation, run: `python test_tesseract.py`
4. Update Selenium (if using Chrome 138+):
   - Run: `python update_selenium.py`
   - For more information, see [Chrome Selenium Compatibility Guide](docs/chrome_selenium_compatibility.md)
5. Create a `.env` file based on the `.env.example` template
6. Fill in your credentials and preferences in the `.env` file

## Environment Variables

Copy the `.env.example` file to a new file named `.env` and fill in your details:

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

# Post-login form details
LOCATION=ISLAMABAD
VISA_TYPE=TOURISM
VISA_SUBTYPE=TOURISM
ISSUE_PLACE=ISLAMABAD
```

## Captcha Handling Flow

The bot follows a six-step strategy to solve the image-based coordinate captcha displayed on the login page:

1. **Detection** – Scans the page for elements that match common captcha patterns (image `src`/`alt` contains *captcha*, or container classes/IDs that reference *captcha*).
2. **Screenshot & 2Captcha Submission** – Captures a cropped screenshot of the captcha (falls back to full-page if cropping fails) and submits it to 2Captcha with `coordinatescaptcha=1`.
3. **Polling** – Repeatedly polls 2Captcha until a set of click coordinates is returned or the max wait time (default 120 s) elapses.
4. **Simulated Clicks** – Converts the returned coordinates to viewport space and dispatches JavaScript click events with small randomised delays to mimic human actions.
5. **Verify/Submit Click** – After all coordinates are clicked, the bot automatically presses the green **Submit / Verify** button (`#btnVerify`) if it is visible and enabled.
6. **Alert Handling & Retry** – If an alert such as “Please select correct number boxes” appears, the bot accepts it, retypes the password, and restarts the captcha-solving loop—up to the configured attempt limits.

These enhancements work in concert with increased retry limits and additional random delays to improve login robustness while remaining within human-like interaction thresholds.

## Post-Login Form Handling

After successful login, the bot will:

1. Navigate to the "Manage Applicants" page
2. Click on the "Edit/Complete Applicant Details" button
3. Fill out the form with the following details from your `.env` file:
   - Location
   - Visa Type
   - Visa Subtype
4. Click the "Proceed" button
5. Verify and update the Issue Place field if needed
6. Submit the form

## Usage

Run the bot with:

```
python bot.py
```

The bot will:
1. Log in to the visa appointment website
2. Handle the post-login form process
3. Check for appointment availability
4. Select an available appointment if found
5. Process payment
6. Handle OTP verification if required
7. Complete the application
8. Send a confirmation email with details

## Troubleshooting

- Check the logs in the `logs` directory for detailed information
- Debug information is saved in the `data/debug` directory
- Screenshots are saved in the `data/screenshots` directory

## License

This project is for educational purposes only. Use responsibly and in accordance with the terms of service of the target website.