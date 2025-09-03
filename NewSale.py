import json
import requests
from datetime import datetime, timedelta
from test_config import *
import time
import random
import string
from datetime import datetime
import os
import csv

def generate_unique_name(prefix):
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    rand_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    if prefix == "Contact":
        return f"{rand_str}_{timestamp}_{prefix}_{rand_str}"
    else:
        return f"{prefix}_{ADDRESS["Country"]}_{timestamp}_{rand_str}"

ACCOUNT_NAME = generate_unique_name("Account")
LastName = generate_unique_name("Contact")

print(ACCOUNT_NAME)  # e.g., Account_20250812114835_X9K2
print(LastName)  # e.g., Contact_20250812114835_J8ZQ


HEADERS = {
    'Authorization': f'Bearer {SESSION_ID}',
    'Content-Type': 'application/json'
}

def create_account():
    url = f"{INSTANCE_URL}/services/data/{API_VERSION}/sobjects/Account"
    payload = {
        "Name": ACCOUNT_NAME,
        "TNV_Credit_Line_Less_Than_50k__c": "Yes",
        "TNV_Direct_Customer__c": "Yes",
        "TNV_Account_Upgrade_Status__c": "Sales Ops Review",
        "TNV_Sector__c": "CES_Construction_Enterprise_Solutions",
        "TNV_Account_Segment__c": "Commercial"
    }
    response = requests.post(url, headers=HEADERS, json=payload)
    return response.json().get("id") if response.status_code == 201 else print(f"❌ Account creation failed: {response.text}") or None

def assign_territory(account_id):
    query = f"SELECT Id, Name FROM Territory2 WHERE Name LIKE '%{TERRITORY_NAME}%' LIMIT 1"
    url = f"{INSTANCE_URL}/services/data/{API_VERSION}/query/?q={query}"
    response = requests.get(url, headers=HEADERS)
    records = response.json().get("records", [])
    if not records:
        return None
    territory_id = records[0]['Id']
    assign_payload = {
        "ObjectId": account_id,
        "Territory2Id": territory_id,
        "AssociationCause": "Territory2Manual"
    }
    assign_url = f"{INSTANCE_URL}/services/data/{API_VERSION}/sobjects/ObjectTerritory2Association"
    response = requests.post(assign_url, headers=HEADERS, json=assign_payload)
    if response.status_code != 201:
        print(f"❌ Territory assignment failed: {response.text}")
        return None
    return territory_id

def create_contact(account_id):
    payload = dict(CONTACT_INFO)
    payload["AccountId"] = account_id
    payload["LastName"] = LastName  # Use the generated unique LastName
    payload["TNV_Preferred_Language__c"] = Pref_Lan
    url = f"{INSTANCE_URL}/services/data/{API_VERSION}/sobjects/Contact"
    response = requests.post(url, headers=HEADERS, json=payload)
    return response.json().get("id") if response.status_code == 201 else print(f"❌ Contact creation failed: {response.text}") or None

def create_contact_point_address(account_id):
    for addr_type in ["Shipping", "Billing"]:
        payload = dict(ADDRESS)
        payload.update({
            "ParentId": account_id,
            "TNV_Ship_To__c": True,
            "TNV_Bill_To__c": True,
            "AddressType": addr_type,
            "IsDefault": True,
            "IsPrimary": True,
            "TNV_Active__c": True,
            "TNV_Master_Active__c": True
        })
        url = f"{INSTANCE_URL}/services/data/{API_VERSION}/sobjects/ContactPointAddress"
        response = requests.post(url, headers=HEADERS, json=payload)
        if response.status_code != 201:
            print(f"❌ Contact Point Address creation failed for {addr_type}: {response.text}")
            return False
    print("✅ Contact Point Addresses created successfully.")
    return True

def sync_account(account_id):
    url = f"{INSTANCE_URL}/services/data/{API_VERSION}/tooling/executeAnonymous"
    apex_code = f"AccountManagementServiceClass.createNewCdhCustomerAccountPlatformEvent('{account_id}');"
    response = requests.get(url, headers=HEADERS, params={"anonymousBody": apex_code})
    return response.status_code == 200 and response.json().get("success")

def wait_for_oracle_account_number(account_id, max_wait_secs=120, poll_interval_secs=10):
    """Polls the Account record until TNV_Oracle_Account_Number__c is populated or timeout occurs."""
    waited = 0
    while waited < max_wait_secs:
        oracle_num = get_oracle_account_number(account_id)
        if oracle_num:
            print(f"✅ Oracle Account Number populated: {oracle_num}")
            return True
        print(f"⏳ Waiting for Oracle Account Number... ({waited}s)")
        time.sleep(poll_interval_secs)
        waited += poll_interval_secs
    print("❌ Timeout: Oracle Account Number was not populated in expected time.")
    return False

def get_oracle_account_number(account_id):
    """Returns TNV_Oracle_Account_Number__c value from the Account."""
    url = f"{INSTANCE_URL}/services/data/{API_VERSION}/query"
    soql = f"SELECT TNV_Oracle_Account_Number__c FROM Account WHERE Id = '{account_id}'"
    response = requests.get(url, headers=HEADERS, params={"q": soql})
    records = response.json().get("records", [])
    if records and records[0].get("TNV_Oracle_Account_Number__c"):
        return records[0]["TNV_Oracle_Account_Number__c"]
    return None


def create_opportunity(account_id):
    # Get Contact ID
    contact_query = f"SELECT Id FROM Contact WHERE AccountId = '{account_id}' LIMIT 1"
    contact_response = requests.get(f"{INSTANCE_URL}/services/data/{API_VERSION}/query", headers=HEADERS, params={'q': contact_query})
    print(contact_response.status_code, contact_response.text)
    contact_id = contact_response.json().get("records", [{}])[0].get("Id")

    # Get Territory ID
    territory_query = f"SELECT Id FROM Territory2 WHERE Name LIKE '%{TERRITORY_NAME}%' LIMIT 1"
    territory_response = requests.get(f"{INSTANCE_URL}/services/data/{API_VERSION}/query", headers=HEADERS, params={'q': territory_query})
    territory_id = territory_response.json().get("records", [{}])[0].get("Id")

    payload = {
        "AccountId": account_id,
        "Name": OPPORTUNITY_NAME,
        "StageName": "Prospecting / Pursue",
        "CloseDate": (datetime.today() + timedelta(days=30)).strftime('%Y-%m-%d'),
        "ForecastCategoryName": "Pipeline",
        "TNV_Deal_Order_Type__c": "Transformation",
        "TNV_Sector__c": "CES_Construction_Enterprise_Solutions",
        "TNV_Product_Category__c": "Design",
        "LeadSource": "Outbound Sales",
        "CurrencyIsoCode": DEFAULT_CURRENCY,
        "TNV_Billing_Contact__c": contact_id,
        "TNV_Shipping_Contact__c": contact_id,
        "TNV_Shipping_Account__c": account_id,
        "TNV_Billing_Account__c": account_id,
        "Territory2Id": territory_id,
        "TNV_Payment_term__c" : PAYMENT_TERMS
    }

    url = f"{INSTANCE_URL}/services/data/{API_VERSION}/sobjects/Opportunity"
    response = requests.post(url, headers=HEADERS, json=payload)
    return response.json().get("id") if response.status_code == 201 else print(f"❌ Opportunity creation failed: {response.text}") or None

def update_opportunity_currency(opportunity_id):
    print("Updating Opportunity currency...")
    payload = {"CurrencyIsoCode": DEFAULT_CURRENCY}
    url = f"{INSTANCE_URL}/services/data/{API_VERSION}/sobjects/Opportunity/{opportunity_id}"
    response =  requests.patch(url, headers=HEADERS, json=payload)
    if response:
        print(f"✅ Updated Opportunity {opportunity_id} with currency {DEFAULT_CURRENCY}")
        return True
    else:
        print(f"❌ Failed to update Opportunity {opportunity_id} with currency {DEFAULT_CURRENCY}")
        print(response.json())

def update_opp_win_reason(opportunity_id,reason):
    payload = {"TNV_Win_Reason__c": reason}
    url = f"{INSTANCE_URL}/services/data/{API_VERSION}/sobjects/Opportunity/{opportunity_id}"
    resp = requests.patch(url, headers=HEADERS, json=payload).status_code == 204
    if resp:
        print(f"✅ Updated Opportunity {opportunity_id} with Win Reason: {reason}")
        return True
    else:
        print(f"❌ Failed to update Opportunity {opportunity_id} with Win Reason: {reason}")
    return False

def create_quote(opportunity_id, account_id):
    payload = {
        "SBQQ__StartDate__c": datetime.today().strftime('%Y-%m-%d'),
        "TNV_Subscription_Term__c": QUOTE_CONFIG["subscription_term"],
        "TNV_Billing_Frequency__c": QUOTE_CONFIG["billing_frequency"],
        "SBQQ__Opportunity2__c": opportunity_id,
        "SBQQ__Account__c": account_id,
        "TNV_Bypass_Quote_Creation_Validation__c": True,
        "SBQQ__Primary__c": True,
        "TNV_Sector__c": QUOTE_CONFIG["sector"],
        "TNV_Payment_Terms__c": PAYMENT_TERMS,
        "Multi_Year_Contract_with_Price_Ramps__c" : RAMP,
        "TNV_Multi_Year_Product_Uplift__c" : ESC_Percent,
        "TNV_Select_the_Business_Type__c"   : Business_type,
    }
    url = f"{INSTANCE_URL}/services/data/{API_VERSION}/sobjects/SBQQ__Quote__c"
    response = requests.post(url, headers=HEADERS, json=payload)
    return response.json().get("id") if response.status_code == 201 else print(f"❌ Quote creation failed: {response.text}") or None

def update_quote_sector(quote_id):
    payload = {"TNV_Sector__c": QUOTE_CONFIG["sector"]}
    url = f"{INSTANCE_URL}/services/data/{API_VERSION}/sobjects/SBQQ__Quote__c/{quote_id}"
    return requests.patch(url, headers=HEADERS, json=payload).status_code == 204

def add_products_to_quote_by_code(quote_id):
    product_codes_str = ",".join([f"'{code}'" for code in PRODUCT_CODES])
    query = f"SELECT Id, ProductCode FROM Product2 WHERE ProductCode IN ({product_codes_str})"
    response = requests.get(f"{INSTANCE_URL}/services/data/{API_VERSION}/query", headers=HEADERS, params={"q": query})
    records = response.json().get("records", [])

    for record in records:
        print(f"Adding product {record['ProductCode']} to Quote {quote_id}...")
        product_id = record["Id"]
        apex_code = f"""
            TNV_Agentforce_AddProduct.Request request = new TNV_Agentforce_AddProduct.Request();  
            request.QuoteId = '{quote_id}';
            TNV_Agentforce_AddProduct.ProductDetail detail = new TNV_Agentforce_AddProduct.ProductDetail();  
            detail.productId = '{product_id}';
            detail.productQuantity = {DEFAULT_QUANTITY};
            detail.productDiscount = {DEFAULT_DISCOUNT};
            request.ProductDetails = new List<TNV_Agentforce_AddProduct.ProductDetail> {{ detail }};
            List<TNV_Agentforce_AddProduct.Request> requestList = new List<TNV_Agentforce_AddProduct.Request> {{ request }};
            TNV_Agentforce_AddProduct.addProduct(requestList);
        """
        exec_url = f"{INSTANCE_URL}/services/data/{API_VERSION}/tooling/executeAnonymous"
        requests.get(exec_url, headers=HEADERS, params={"anonymousBody": apex_code})
        time.sleep(60)  # Brief pause to ensure processing
        # calculator_apex = f""" String quoteJSON = SBQQ.ServiceRouter.read('SBQQ.QuoteAPI.QuoteReader', {quote_id});
        # QuoteModel quote = (QuoteModel) JSON.deserialize(quoteJSON, QuoteModel.class);
        # QuoteCalculator calculator = new QuoteCalculator();
        # calculator.calculate(quote, 'TNV_Agentforce_QuoteCalculatorCallBack');"""
        # requests.get(exec_url, headers=HEADERS, params={"anonymousBody": calculator_apex})
        # time.sleep(30)  # Brief pause to ensure calculation


def submit_Quote_For_Approval(quote_id):
    url = f"{INSTANCE_URL}/services/data/{API_VERSION}/tooling/executeAnonymous"
    
    apex_code = f"TNV_SubmitForApproval.submitForApproval(new List<Id>{{'{quote_id}'}});"
    params = {
        "anonymousBody": apex_code
    }

    response = requests.get(url, headers=HEADERS, params=params)

    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print("✅ Quote Submitted for Approval successfully.")
        else:
            print("❌ Anonymous Apex execution failed:", result.get("compileProblem", "Unknown error"))
    else:
        print("❌ Quote Submit for Approval Failed", response.status_code, response.text)

def validate_quote(quote_id):

    apex_code = f"TNV_Agentforce_QuoteGenerateDocument.validateQuote('{quote_id}');"
    url = f"{INSTANCE_URL}/services/data/v58.0/tooling/executeAnonymous"
    resp = requests.get(url, headers=HEADERS, params={'anonymousBody': apex_code})
    print(resp.status_code, resp.text)
    if resp.status_code == 200:
        result = resp.json()
        if result.get("success"):
            print("✅ Quote validation Submitted.")
        else:
            print("❌ Quote validation failed:", result.get("compileProblem", "Unknown error"))


def update_quote_to_accepted(quote_id):
    field_values = {"SBQQ__Status__c": "Presented"}
    url = f"{INSTANCE_URL}/services/data/{API_VERSION}/sobjects/SBQQ__Quote__c/{quote_id}"
    response = requests.patch(url, headers=HEADERS, data=json.dumps(field_values))
    if response.status_code == 204:
        print(f"✅ Updated Quote Status to Presented {quote_id}")
    else:
        print(f"❌ Failed to update Quote {quote_id}: {response.text}")
        return False
    field_values = {"SBQQ__Status__c": "Accepted"}
    url = f"{INSTANCE_URL}/services/data/{API_VERSION}/sobjects/SBQQ__Quote__c/{quote_id}"
    response = requests.patch(url, headers=HEADERS, data=json.dumps(field_values))
    if response.status_code == 204:
        print(f"✅ Updated Quote Status to Accepted {quote_id}")
        return True
    else:
        print(f"❌ Failed to update Quote {quote_id}: {response.text}")
        return False
    
def check_OARA(quote_id):
    field_values = {"TNV_Sale_Opps_Reviewed_and_Approved__c": True}
    url = f"{INSTANCE_URL}/services/data/{API_VERSION}/sobjects/SBQQ__Quote__c/{quote_id}"
    response = requests.patch(url, headers=HEADERS, data=json.dumps(field_values))
    if response.status_code == 204:
        print(f"✅ Updated Quote OARA {quote_id}")
        return True
    else:
        print(f"❌ Failed to update Quote {quote_id}: {response.text}")
        return False

def send_email(account_id, opp_id, quote_id):
    email_url = f"{INSTANCE_URL}/services/data/{API_VERSION}/actions/standard/emailSimple"

    account_url = f"{INSTANCE_URL}/{account_id}"
    opp_url = f"{INSTANCE_URL}/{opp_id}"
    quote_url = f"{INSTANCE_URL}/{quote_id}"

    subject = f"Record Creation Summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    body = f"""Hello {CONTACT_INFO["FirstName"] },

    The following records were created:

        Account: {account_url}

        Opportunity: {opp_url}

        Quote: {quote_url}

    Regards,
    Siva
    """

    payload = {
        "inputs": [{
            "emailBody": body,
            "emailBodyIsHtml": True,
            "emailAddresses": CONTACT_INFO["Email"],
            "senderDisplayName": "Automation Bot",
            "emailSubject": subject
        }]
    }

    resp = requests.post(email_url, headers=HEADERS, json=payload)
    if resp.status_code == 200:
        print("✅ Email sent successfully.")
    else:
        print(f"❌ Email sending failed: {resp.status_code} {resp.text}")
  # Save to CSV log
    log_file = "email_log.csv"
    file_exists = os.path.isfile(log_file)

    with open(log_file, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Write header only if file doesn't exist
        if not file_exists:
            writer.writerow(["Timestamp", "Contact Name", "Email", "Account URL", "Opportunity URL", "Quote URL", "Status"])
        writer.writerow([
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            CONTACT_INFO["FirstName"],
            CONTACT_INFO["Email"],
            account_url,
            opp_url,
            quote_url
        ])
def main():
    account_id = ACCOUNT_ID
    opp_id = OPPORTUNITY_ID
    quote_id = QUOTE_ID
    

    if IS_ACCOUNT_CREATION_NEEDED:
        print("Creating Account...")
        account_id = create_account()
        if not account_id:
            print("❌ Account creation failed.")
            return
        print(f"✅ Account created with ID: {account_id}")
        print("Assigning Territory...")
        assigned_territory_id = assign_territory(account_id)
        if not assigned_territory_id:
            print("❌ Territory assignment failed.")
            return
        print('Creating Contact...')
        contact = create_contact(account_id)
        if not contact:
            print("❌ Contact creation failed.")
            return
        print('Creating Contact Point Addresses...')
        cpa = create_contact_point_address(account_id)
        if not cpa:
            print("❌ Contact Point Address creation failed.")
            return
        print('Syncing Account with Oracle...')
        sync = sync_account(account_id)
        if not sync:
            print("❌ Account sync failed.")
            return
        if not wait_for_oracle_account_number(account_id):
            return 
        print(f"✅ Oracle Account Number synced for Account ID: {account_id}")
    
    if IS_OPPORTUNITY_CREATION_NEEDED:
        print("Creating Opportunity...")
        opp_id = create_opportunity(account_id)
        update_opportunity_currency(opp_id)
        print(f"✅ Opportunity ID: {opp_id}")

    if not opp_id and IS_OPPORTUNITY_CREATION_NEEDED:
        print("❌ Opportunity creation failed.")
        return

    if IS_QUOTE_CREATION_NEEDED:
        print("Creating Quote...")
        quote_id = create_quote(opp_id, account_id)
        update_quote_sector(quote_id)
    if not quote_id:
        print("❌ Quote creation failed.")
        return
    print(f"✅ Quote ID: {quote_id}")
    if IS_PRODUCT_ADDITION_NEEDED:
        print("Adding products to Quote...")
        add_products_to_quote_by_code(quote_id)
        print("Waiting for Some time to ensure products are added...")
        time.sleep(120)
        print(f"✅ Products added to Quote ID: {quote_id}")
       

    if IS_SUBMIT_QUOTE_FOR_APPROVAL_NEEDED:
        print("Submitting Quote for Approval...")
        submit_Quote_For_Approval(quote_id)

    if IS_VALIDATE_QUOTE_NEEDED:
        print("Validating Quote...")
        validate_quote(quote_id)
        time.sleep(10)
    if IS_QUOTE_TO_ACCEPTED_NEEDED:
        print("Updating Quote to Accepted...")
        update_quote_to_accepted(quote_id)
        time.sleep(30)

    if IS_OARA_NEEDED:
        print("Checking OARA...")
        if update_opp_win_reason(opp_id, "Pricing"):
            check_OARA(quote_id)
            update_quote_to_accepted(quote_id)
        else:
            print("❌ Failed to update Opportunity with Win Reason.")
    send_email(account_id, opp_id, quote_id)

if __name__ == "__main__":
    for i in range(NO_OF_RECORDS_TO_CREATE):
        print(f"Running iteration {i+1} of {NO_OF_RECORDS_TO_CREATE}")
        main()
    # send_email('001cc00000BENXyAAP','006cc00000BEXXyAAP','a0Kcc00000BENXyAAP')
