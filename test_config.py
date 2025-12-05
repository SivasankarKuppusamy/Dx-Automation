# test_config.py

# Session & Environment
from datetime import datetime, timedelta

SESSION_ID = ''  # Set dynamically or use environment variable
INSTANCE_URL = 'https://trimbledx--dxuat.sandbox.my.salesforce.com'
API_VERSION = 'v58.0'

IS_ACCOUNT_CREATION_NEEDED = False  

ACCOUNT_ID = '001cc00000ET0r0AAD'

Random_Needed = False

ACCOUNT_NAME_CONFIG = "Account by Automation"

IS_SEPERATE_ACCOUNT_CREATION_NEEDED = True

IS_OPPORTUNITY_CREATION_NEEDED = True
OPPORTUNITY_ID = ''

IS_QUOTE_CREATION_NEEDED = True
QUOTE_ID = 'a0zcc000005r9VJAAY'

QUOTE_START_DATE = datetime.today() - timedelta(days=1)

IS_PRODUCT_ADDITION_NEEDED = False

IS_VALIDATE_QUOTE_NEEDED = True

IS_SUBMIT_QUOTE_FOR_APPROVAL_NEEDED = True

IS_QUOTE_TO_ACCEPTED_NEEDED = True

IS_OARA_NEEDED = True
# Test Data
TERRITORY_NAME = "Americas"

CONTACT_INFO = {
    "FirstName": "Siva",
    "Email": "sivasankar_k+randomstring@trimble.com",
    "Phone": "+11033567890",
    "Contact_Role__c": "Invoice Recipient"
}
Pref_Lan = "English"

ADDRESS = {
    "Street": "4803 Worthington Drive",
    "City": "Westville",
    "State": "Ohio",
    "Country": "United States",
    "CountryCode": "US",
    "PostalCode": "43083",
    "Name": "Test Address"
}

OPPORTUNITY_NAME = "Opportunity by Automation"
QUOTE_CONFIG = {
    "subscription_term": 24,
    "billing_frequency": "Upfront",
    "sector": "CES - Construction Enterprise Solutions"
    }
RAMP = "No"
ESC_Percent = 5 if RAMP == "Yes" else None
Business_type = "Other Businesses with Price Ramps" if RAMP == "Yes" else ""

PAYMENT_TERMS = "30 NET"

PRODUCT_CODES = ["BN-SB-TC1EST-ACE"]

DEFAULT_CURRENCY = "USD"
DEFAULT_QUANTITY = 5
DEFAULT_DISCOUNT = 0
NO_OF_RECORDS_TO_CREATE = 1
