# Troubleshooting Post-Login Navigation

This document provides guidance on troubleshooting navigation issues that may occur after successful login in the VisaBot 2.0 system.

## Common Issues

### Post-Login Processing Not Starting

If the bot successfully logs in but the post-login processing doesn't start, it may be due to one of the following issues:

1. **URL Redirection**: The website might redirect to an unexpected URL after login.
2. **Navigation Selectors**: The selectors used to find navigation elements might not match the current page structure.
3. **Session Issues**: The login session might not be properly established or might expire quickly.

## Diagnostic Steps

### 1. Check the Logs

Examine the log files for the following information:

- Current URL after login
- Navigation attempts and failures
- Error messages related to element selection
- Screenshots saved during the process

### 2. Run the Navigation Test

Use the `test_navigation.py` script to specifically test the navigation flow:

```bash
python test_navigation.py
```

This script will:
- Log in to the website
- Verify the post-login URL
- Test direct navigation to the target URL if needed
- Test the PostLoginHandler navigation methods
- Save screenshots at each step for visual verification

### 3. Check Environment Variables

Ensure the following environment variables are correctly set in your `.env` file:

```
# Login URL (where the login form is located)
LOGIN_URL=https://appointment.theitalyvisa.com/Global/account/login

# Target URL (where the bot should navigate after login)
TARGET_URL=https://appointment.theitalyvisa.com/Global/appointmentdata/MyAppointments

# Post-login form details
LOCATION=ISLAMABAD
VISA_TYPE=TOURISM
VISA_SUBTYPE=TOURISM
ISSUE_PLACE=ISLAMABAD
```

### 4. Examine Screenshots

The bot now saves screenshots at critical points in the navigation process. Check the `data/screenshots` directory for:

- `post_login_start_*.png`: The page state at the beginning of post-login processing
- `navigation_issue_*.png`: Screenshots taken when navigation issues are detected
- `navigation_error_*.png`: Screenshots taken when navigation errors occur
- `post_login_success_*.png`: The page state after successful post-login processing

## Advanced Troubleshooting

### Manual URL Navigation

If automatic navigation fails, the bot will attempt direct navigation to the URL specified in the `TARGET_URL` environment variable. You can modify this URL if the website structure has changed.

### Selector Updates

If the website's HTML structure has changed, you may need to update the selectors in the `navigate_to_manage_applicants` method in `post_login.py`. The current implementation tries multiple selector variants, but you can add more if needed.

### Session Debugging

To debug session issues:

1. Set the browser to not close after execution by modifying the bot initialization
2. Examine the cookies and local storage in the browser's developer tools
3. Check for any CSRF tokens or other security measures that might be preventing navigation

## Reporting Issues

When reporting navigation issues, please include:

1. The complete log file
2. Screenshots from the `data/screenshots` directory
3. The current values of your environment variables (excluding sensitive information)
4. Any changes you've made to the codebase