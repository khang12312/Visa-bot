# Post-Login Handler Documentation

## Overview

The `PostLoginHandler` class in `post_login.py` is responsible for handling all post-login processes in the VisaBot application. After a successful login, this handler navigates through the application, fills out forms, and completes the necessary steps to prepare for appointment booking.

## Class Structure

### Initialization

```python
PostLoginHandler(driver, bot_instance)
```

- `driver`: Selenium WebDriver instance
- `bot_instance`: The main bot instance for accessing shared methods

### Main Methods

#### `handle_post_login_process(location, visa_type, visa_subtype, issue_place)`

The main entry point that orchestrates the entire post-login workflow:

1. Navigate to the "Manage Applicants" page
2. Click on the "Edit/Complete Applicant Details" button
3. Fill out the applicant form with location, visa type, and visa subtype
4. Click the "Proceed" button
5. Verify and update the Issue Place field if needed
6. Submit the form

#### `navigate_to_manage_applicants()`

Navigates to the "Manage Applicants" page after successful login by:

1. Finding the appropriate link using multiple selector patterns
2. Moving to the element with randomized mouse movements
3. Clicking the link with human-like timing

#### `click_edit_applicant_details()`

Locates and clicks the "Edit/Complete Applicant Details" button by:

1. Finding the button using multiple selector patterns
2. Moving to the element with randomized mouse movements
3. Clicking the button with human-like timing
4. Waiting for the modal dialog to appear

#### `fill_applicant_form(location, visa_type, visa_subtype)`

Fills out the applicant form with the provided values by:

1. Selecting the location from the dropdown
2. Selecting the visa type from the dropdown
3. Selecting the visa subtype from the dropdown

#### `verify_and_update_issue_place(expected_issue_place)`

Verifies if the Issue Place field contains the expected value and updates it if needed by:

1. Finding the Issue Place input field
2. Checking if the current value matches the expected value
3. Updating the field with human-like typing if needed

#### `click_proceed_button()` and `click_submit_button()`

Locate and click the respective buttons with human-like behavior.

### Helper Methods

#### `_select_dropdown_option(dropdown_id, option_text)`

A helper method to select an option from a dropdown by:

1. Finding the dropdown element
2. Clicking to open the dropdown
3. Finding and clicking the desired option

## Integration with VisaBot

The `PostLoginHandler` is integrated into the main `VisaBot` class in the `run()` method. After a successful login, the bot:

1. Imports the `PostLoginHandler` class
2. Retrieves form field values from environment variables
3. Initializes the handler with the current WebDriver instance
4. Calls the `handle_post_login_process()` method with the form field values

## Environment Variables

The following environment variables are used by the `PostLoginHandler`:

- `LOCATION`: The location value to select in the form (e.g., "ISLAMABAD")
- `VISA_TYPE`: The visa type value to select (e.g., "TOURISM")
- `VISA_SUBTYPE`: The visa subtype value to select (e.g., "TOURISM")
- `ISSUE_PLACE`: The expected value for the Issue Place field (e.g., "ISLAMABAD")

## Error Handling

The `PostLoginHandler` implements comprehensive error handling:

1. Each method returns a boolean indicating success or failure
2. Detailed logging is provided at each step
3. Multiple selector patterns are used with fallback mechanisms
4. Exceptions are caught and logged appropriately

## Human-like Behavior

To simulate human-like behavior and avoid detection as a bot, the `PostLoginHandler` implements:

1. Random delays between actions (0.3-3.0 seconds)
2. Randomized mouse movements when navigating to elements
3. Human-like typing with random delays between keystrokes (0.05-0.15 seconds)
4. Progressive fallback mechanisms for element selection