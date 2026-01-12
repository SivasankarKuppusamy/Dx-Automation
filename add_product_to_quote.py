"""
Add Product to Quote using Salesforce Custom API
Uses the TNV_ProductAPIForBot REST API to add products to CPQ quotes
"""

import json
import sys
import time
from test_config import SESSION_ID, INSTANCE_URL, API_VERSION, QUOTE_ID, PRODUCT_CODES
import requests

HEADERS = {
    'Authorization': f'Bearer {SESSION_ID}',
    'Content-Type': 'application/json'
}


def query_salesforce(soql):
    """Execute a SOQL query"""
    query_url = f"{INSTANCE_URL}/services/data/{API_VERSION}/query"
    params = {'q': soql}
    
    try:
        response = requests.get(query_url, headers=HEADERS, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Query error: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return None

def get_product_by_code(product_code):
    """Query product by ProductCode"""
    print(f"\n🔍 Searching for product with code: {product_code}")
    
    soql = f"SELECT Id, Name, ProductCode FROM Product2 WHERE ProductCode = '{product_code}' LIMIT 1"
    result = query_salesforce(soql)
    
    if result and result.get('records'):
        product = result['records'][0]
        print(f"✅ Found product: {product['Name']} (ID: {product['Id']})")
        return product['Id']
    else:
        print(f"❌ Product with code '{product_code}' not found")
        return None

def get_quote_details(quote_id):
    """Query quote for pricebook and currency information"""
    print(f"\n🔍 Fetching quote details for: {quote_id}")
    
    soql = f"SELECT Id, Name, SBQQ__PricebookId__c, CurrencyIsoCode FROM SBQQ__Quote__c WHERE Id = '{quote_id}' LIMIT 1"
    result = query_salesforce(soql)
    
    if result and result.get('records'):
        quote = result['records'][0]
        print(f"✅ Found quote: {quote['Name']}")
        print(f"   - Pricebook ID: {quote.get('SBQQ__PricebookId__c', 'N/A')}")
        print(f"   - Currency: {quote.get('CurrencyIsoCode', 'USD')}")
        
        return {
            'pricebookId': quote.get('SBQQ__PricebookId__c'),
            'currencyCode': quote.get('CurrencyIsoCode', 'USD')
        }
    else:
        print(f"❌ Quote with ID '{quote_id}' not found")
        return None

def add_product_to_quote(quote_id, product_id, pricebook_id, currency_code):
    """Call the custom API to add product to quote"""
    print(f"\nAdding product to quote via API...")
    
    api_url = f"{INSTANCE_URL}/services/apexrest/Quote/QuoteProductAdder/"
    
    payload = {
        'quoteId': quote_id,
        'productId': product_id,
        'pricebookId': pricebook_id,
        'currencyCode': currency_code
    }
    
    print(f"📤 Request payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.patch(api_url, headers=HEADERS, json=payload)
        response.raise_for_status()
        
        result = response.json()
        print(f"\nProduct added successfully!")
        print(f"📋 Job ID: {result.get('jobId', 'N/A')}")
        print(f"\nℹ The product is being added asynchronously. The job ID can be used to track the status.")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"\nAPI call failed: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return None

def process_add_product(quote_id, product_code):
    """Main process to add product to quote"""
    print("\n" + "=" * 60)
    print("🎯 Starting Quote Product Addition Process")
    print("=" * 60)
    
    product_id = get_product_by_code(product_code)
    if not product_id:
        return False
    
    quote_details = get_quote_details(quote_id)
    if not quote_details:
        return False
    
    if not quote_details['pricebookId']:
        print("❌ Quote does not have a pricebook assigned")
        return False
    
    result = add_product_to_quote(
        quote_id,
        product_id,
        quote_details['pricebookId'],
        quote_details['currencyCode']
    )
    
    return result is not None


def main():
    """Main function"""
    print("📦 Add Product to Quote Tool")
    print("=" * 60)
    
    quote_id = QUOTE_ID
    product_code = PRODUCT_CODES[0] if PRODUCT_CODES else None
    
    print(f"\n Quote ID: {quote_id}")
    print(f" Product Code: {product_code}")
    
    if not quote_id or not product_code:
        print("❌ Both Quote ID and Product Code are required in test_config.py!")
        sys.exit(1)
    
    print(f"\n" + "=" * 60)
    print(f" Fetching product and quote details...")
    print(f"=" * 60)
    
    product_id = get_product_by_code(product_code)
    if not product_id:
        sys.exit(1)
    
    quote_details = get_quote_details(quote_id)
    if not quote_details:
        sys.exit(1)
    
    if not quote_details['pricebookId']:
        print("❌ Quote does not have a pricebook assigned")
        sys.exit(1)
    
    success_count = 0
    failure_count = 0
    
    for iteration in range(1, 101):
        print(f"\n{'='*60}")
        print(f"Iteration {iteration}/100")
        print(f"{'='*60}")
        
        result = add_product_to_quote(
            quote_id,
            product_id,
            quote_details['pricebookId'],
            quote_details['currencyCode']
        )
        
        if result:
            success_count += 1
            print(f"✅ [Iteration {iteration}] SUCCESS")
        else:
            failure_count += 1
            print(f"❌ [Iteration {iteration}] FAILED")
    
    print(f"\n\n{'='*60}")
    print(f"✅ Successful: {success_count}/100")
    print(f"❌ Failed: {failure_count}/100")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
