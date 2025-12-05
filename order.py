import requests
from test_config import SESSION_ID, INSTANCE_URL, API_VERSION
from order_queries import get_contract_association_apex, get_order_queueing_apex, get_provisioning_staging_apex, get_provisioning_completion_apex

# Headers for Salesforce API calls
HEADERS = {
    'Authorization': f'Bearer {SESSION_ID}',
    'Content-Type': 'application/json'
}

def update_order_fields(order_id, order_data):
    """Update order fields using Salesforce REST API"""
    print("Updating order approval statuses")
    url = f"{INSTANCE_URL}/services/data/{API_VERSION}/sobjects/Order/{order_id}"
    response = requests.patch(url, json=order_data, headers=HEADERS)
    
    if response.status_code == 204:
        print("✅ Order approval statuses updated")
    else:
        print(f"❌ Order update failed: {response.status_code}")
    
    return response

def execute_contract_association_batch(apex_code):
    """Execute contract association batch"""
    print("Processing contract association")
    url = f"{INSTANCE_URL}/services/data/{API_VERSION}/tooling/executeAnonymous"
    params = {"anonymousBody": apex_code}
    response = requests.get(url, headers=HEADERS, params=params)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("✅ Contract association completed")
        else:
            print(f"❌ Contract association failed")
    else:
        print(f"❌ Contract association HTTP error: {response.status_code}")
    
    return response

def execute_order_queueing(apex_code):
    """Execute order queueing process"""
    print("Processing order items queueing")
    url = f"{INSTANCE_URL}/services/data/{API_VERSION}/tooling/executeAnonymous"
    params = {"anonymousBody": apex_code}
    response = requests.get(url, headers=HEADERS, params=params)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("✅ Order queueing completed")
        else:
            print(f"❌ Order queueing failed")
    else:
        print(f"❌ Order queueing HTTP error: {response.status_code}")
    
    return response

def execute_provisioning_staging(apex_code):
    """Execute provisioning staging"""
    print("Processing provisioning staging")
    url = f"{INSTANCE_URL}/services/data/{API_VERSION}/tooling/executeAnonymous"
    params = {"anonymousBody": apex_code}
    response = requests.get(url, headers=HEADERS, params=params)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("✅ Provisioning staging completed")
        else:
            print(f"❌ Provisioning staging failed")
    else:
        print(f"❌ Provisioning staging HTTP error: {response.status_code}")
    
    return response

def execute_provisioning_completion(apex_code):
    """Execute provisioning completion batch"""
    print("Starting provisioning completion")
    url = f"{INSTANCE_URL}/services/data/{API_VERSION}/tooling/executeAnonymous"
    params = {"anonymousBody": apex_code}
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code == 200:
        result = response.json()
        if not result.get('success'):
            print(f"ERROR: Provisioning completion batch failed: {result.get('compileProblem', 'Unknown error')}")
    else:
        print(f"ERROR: Provisioning completion HTTP error: {response.status_code}")
    return response

if __name__ == "__main__":
    print("Starting order processing")
    
    # Sample order processing workflow
    sample_order_id = "801cc00000Eb5c3AAB"
    
    # Order approval status updates
    order_data = {
        "TNV_Order_Credit_Approval_Status__c": "Approved",
        "TNV_Order_Validation_Status__c": "Completed",
        "TNV_Order_Tax_Status__c": "Queued",
        "TNV_Order_Compliance_Status__c": "Approved"
    }
    
    # Execute the order processing steps
    try:
        print("=== Order Processing Workflow ===")
        
        # Step 1: Update order fields
        update_order_fields(sample_order_id, order_data)
        
        # Step 2: Contract association
        execute_contract_association_batch(get_contract_association_apex(sample_order_id))
        
        # Step 3: Order queueing
        execute_order_queueing(get_order_queueing_apex(sample_order_id))
        
        # Step 4: Provisioning staging
        execute_provisioning_staging(get_provisioning_staging_apex(sample_order_id))
        
        # Step 5: Provisioning completion
        execute_provisioning_completion(get_provisioning_completion_apex(sample_order_id))

        print("Order processing completed")
        
    except Exception as e:
        print(f"ERROR: Order processing failed: {str(e)}")