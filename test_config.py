# test_config.py

# Session & Environment
SESSION_ID = ''  # Set dynamically or use environment variable
INSTANCE_URL = 'https://trimbledx--dxces.sandbox.my.salesforce.com'
API_VERSION = 'v58.0'

IS_ACCOUNT_CREATION_NEEDED = False  

ACCOUNT_ID = ''

IS_OPPORTUNITY_CREATION_NEEDED = True
OPPORTUNITY_ID = ''

IS_QUOTE_CREATION_NEEDED = True
QUOTE_ID = ''

IS_PRODUCT_ADDITION_NEEDED = True

IS_VALIDATE_QUOTE_NEEDED = True

IS_SUBMIT_QUOTE_FOR_APPROVAL_NEEDED = True

IS_QUOTE_TO_ACCEPTED_NEEDED = True

IS_OARA_NEEDED = True
# Test Data
# ACCOUNT_NAME = "IN LE – Trimble DX"
# TERRITORY_NAME = "APAC Korea"
TERRITORY_NAME = "Americas"
# TERRITORY_NAME = "APAC India"
# TERRITORY_NAME = "APAC-JAP-1"
CONTACT_INFO = {
    "FirstName": "Siva",
    "Email": "sivasankar_k+randomstring@trimble.com",
    "Phone": "+11033567890",
    "Contact_Role__c": "Invoice Recipient"
}
Pref_Lan = ""
# ADDRESS = {
#     "Street": "３５６-１００７, Ｋａｗａｈｉｇａｓｈｉｍａｃｈｉ Ｈｉｒｏｔａ, Ａｉｚｕｗａｋａｍａｔｓｕ-Ｓｈｉ, Ｆｕｋｕｓｈｉｍａ",
#     "City": "会津若松市",
#     "Country": "Japan",
#     "CountryCode": "JP",
#     "PostalCode": "〒969-3471",
#     "Name": "356-1007, Kawahigashimachi Hirota, Aizuwakamatsu-shi, Fukushima Location"
# }
# ADDRESS = {
#     "Street": "Ito Building 2F, 2-26-5 Nishigotanda",
#     "City": "Tokyo",
#     "Country": "Japan",
#     "CountryCode": "JP",
#     "PostalCode": "141-0031",
#     "Name": "Ito Building 2F, 2-26-5 Nishigotanda, Tokyo 141-0031, Japan"
# }

ADDRESS = {
    "Street": "4803 Worthington Drive",
    "City": "Westville",
    "State": "Ohio",
    "Country": "United States",
    "CountryCode": "US",
    "PostalCode": "43083",
    "Name": "Test Address"
}

# ADDRESS = {
#     "Street": "237-5, Sameunri, Jiksan-eup",
#     "City": "Seobuk-gu Cheonan-si",
#     "State": "",
#     "Country": "Korea, Republic of",
#     "CountryCode": "KR",
#     "PostalCode": "50052",
#     "Name": "Test Address Korea"
# }

# ADDRESS = {
#     "Street": "123, Gandhi Nagar",
#     "City": "Ahmedabad",
#     "State": "Gujarat",
#     "PostalCode": "380001",
#     "Country": "India",
#     "CountryCode": "IN",
#     "Name": "123, Gandhi Nagar, Ahmedabad, Gujarat 380001, India"
# }

# ADDRESS = {
#     "Street": "Barkur, Udupi, Mysore",
#     "City": "Barkur",
#     "State": "Karnataka",
#     "PostalCode": "576210",
#     "Country": "India",
#     "CountryCode": "IN",
#     "Name": "Barkur, Udupi, Mysore, Karnataka 576210, India"
# }
# ADDRESS = {
#     "Street": "Karakavagu, Paloncha, Khammam",
#     "City": "Karakavagu",
#     "State": "Andhra Pradesh",
#     "PostalCode": "507115",
#     "Country": "India",
#     "CountryCode": "IN",
#     "Name": "Karakavagu, Paloncha, Khammam, Andhra Pradesh 507115, India"
# }



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

# PRODUCT_CODES = ["BN-TRM-TKL-CARBON", "DIA-B-R12-W-BDL", "BS-TRN-CR-TEKLA-SD"]
# PRODUCT_CODES = ["BN-SB-TC1PM-PS-VISTA", "BN-TRM-TC1COP"]
# PRODUCT_CODES = ["DS-MEP06000"]
# PRODUCT_CODES = ["BN-SB-QB-7414","SKP-GO","BN-SB-SKP-EDU"]
PRODUCT_CODES = ["111191","111184","111188"]
DEFAULT_CURRENCY = "USD"
DEFAULT_QUANTITY = 5
DEFAULT_DISCOUNT = 0
NO_OF_RECORDS_TO_CREATE = 1
