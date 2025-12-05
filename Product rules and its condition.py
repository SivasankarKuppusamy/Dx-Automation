"""
Product rules and its condition.py
Product rules and condition handling for Salesforce automation
"""

import requests
from test_config import SESSION_ID, INSTANCE_URL, API_VERSION

# Headers for Salesforce API calls
HEADERS = {
    'Authorization': f'Bearer {SESSION_ID}',
    'Content-Type': 'application/json'
}

# Product rule definitions
PRODUCT_RULES = {
    "BN-SB-QB-7414": {
        "name": "QB 7414 Bundle",
        "min_quantity": 1,
        "max_quantity": 100,
        "requires_approval": False,
        "compatible_products": ["SKP-GO", "BN-SB-SKP-EDU"],
        "restricted_territories": [],
        "business_type_required": False
    },
    "SKP-GO": {
        "name": "SketchUp Go",
        "min_quantity": 1,
        "max_quantity": 1000,
        "requires_approval": False,
        "compatible_products": ["BN-SB-QB-7414", "BN-SB-SKP-EDU"],
        "restricted_territories": [],
        "business_type_required": False
    },
    "BN-SB-SKP-EDU": {
        "name": "SketchUp Education",
        "min_quantity": 1,
        "max_quantity": 500,
        "requires_approval": True,
        "compatible_products": ["BN-SB-QB-7414", "SKP-GO"],
        "restricted_territories": ["North Korea", "Iran"],
        "business_type_required": True,
        "allowed_business_types": ["Educational Institution", "Non-profit"]
    },
    "BN-TRM-TC1DSG": {
        "name": "Trimble Connect Design",
        "min_quantity": 1,
        "max_quantity": 50,
        "requires_approval": False,
        "compatible_products": ["BN-SB-TC1PM", "BS-SB-SKP-PRO"],
        "restricted_territories": [],
        "business_type_required": False
    }
}

def validate_product_quantity(product_code, quantity):
    """Validate if the quantity is within allowed limits for the product"""
    if product_code not in PRODUCT_RULES:
        return True, "Product not found in rules - allowing"
    
    rule = PRODUCT_RULES[product_code]
    min_qty = rule.get("min_quantity", 1)
    max_qty = rule.get("max_quantity", 999999)
    
    if quantity < min_qty:
        return False, f"Quantity {quantity} is below minimum {min_qty} for {product_code}"
    
    if quantity > max_qty:
        return False, f"Quantity {quantity} exceeds maximum {max_qty} for {product_code}"
    
    return True, "Quantity valid"

def validate_product_compatibility(primary_product, other_products):
    """Check if products are compatible with each other"""
    if primary_product not in PRODUCT_RULES:
        return True, "Primary product not in rules - allowing"
    
    rule = PRODUCT_RULES[primary_product]
    compatible = rule.get("compatible_products", [])
    
    incompatible_products = []
    for product in other_products:
        if product != primary_product and product not in compatible:
            incompatible_products.append(product)
    
    if incompatible_products:
        return False, f"{primary_product} is not compatible with: {', '.join(incompatible_products)}"
    
    return True, "Products are compatible"

def validate_territory_restriction(product_code, territory):
    """Check if product can be sold in the specified territory"""
    if product_code not in PRODUCT_RULES:
        return True, "Product not in rules - allowing"
    
    rule = PRODUCT_RULES[product_code]
    restricted = rule.get("restricted_territories", [])
    
    if territory in restricted:
        return False, f"{product_code} cannot be sold in {territory}"
    
    return True, "Territory is allowed"

def validate_business_type(product_code, business_type):
    """Check if business type is allowed for the product"""
    if product_code not in PRODUCT_RULES:
        return True, "Product not in rules - allowing"
    
    rule = PRODUCT_RULES[product_code]
    
    if not rule.get("business_type_required", False):
        return True, "Business type not required"
    
    allowed_types = rule.get("allowed_business_types", [])
    if business_type not in allowed_types:
        return False, f"{product_code} requires business type to be one of: {', '.join(allowed_types)}"
    
    return True, "Business type is valid"

def requires_approval(product_code):
    """Check if product requires approval"""
    if product_code not in PRODUCT_RULES:
        return False
    
    return PRODUCT_RULES[product_code].get("requires_approval", False)

def validate_quote_products(product_list, territory="", business_type=""):
    """Validate all products in a quote against rules"""
    validation_results = []
    
    # Extract product codes and quantities
    products = []
    for item in product_list:
        if isinstance(item, dict):
            products.append((item.get('product_code'), item.get('quantity', 1)))
        else:
            products.append((item, 1))  # Assume quantity 1 if just product code
    
    for product_code, quantity in products:
        result = {
            'product_code': product_code,
            'valid': True,
            'messages': [],
            'requires_approval': requires_approval(product_code)
        }
        
        # Validate quantity
        valid, message = validate_product_quantity(product_code, quantity)
        if not valid:
            result['valid'] = False
        result['messages'].append(f"Quantity: {message}")
        
        # Validate territory
        if territory:
            valid, message = validate_territory_restriction(product_code, territory)
            if not valid:
                result['valid'] = False
            result['messages'].append(f"Territory: {message}")
        
        # Validate business type
        if business_type:
            valid, message = validate_business_type(product_code, business_type)
            if not valid:
                result['valid'] = False
            result['messages'].append(f"Business Type: {message}")
        
        # Validate compatibility with other products
        other_products = [p[0] for p in products if p[0] != product_code]
        valid, message = validate_product_compatibility(product_code, other_products)
        if not valid:
            result['valid'] = False
        result['messages'].append(f"Compatibility: {message}")
        
        validation_results.append(result)
    
    return validation_results

if __name__ == "__main__":
    # Example validation
    from test_config import PRODUCT_CODES, TERRITORY_NAME
    
    print("=== Product Rule Validation ===")
    
    # Create test product list with quantities
    test_products = [
        {'product_code': 'BN-SB-QB-7414', 'quantity': 2},
        {'product_code': 'SKP-GO', 'quantity': 5},
        {'product_code': 'BN-SB-SKP-EDU', 'quantity': 10}
    ]
    
    results = validate_quote_products(
        test_products, 
        territory=TERRITORY_NAME, 
        business_type="Educational Institution"
    )
    
    for result in results:
        print(f"\nProduct: {result['product_code']}")
        print(f"Valid: {result['valid']}")
        print(f"Requires Approval: {result['requires_approval']}")
        for message in result['messages']:
            print(f"  - {message}")
    
    print("\n=== Summary ===")
    all_valid = all(r['valid'] for r in results)
    needs_approval = any(r['requires_approval'] for r in results)
    
    print(f"All products valid: {all_valid}")
    print(f"Requires approval: {needs_approval}")