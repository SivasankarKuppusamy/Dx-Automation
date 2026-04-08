# app.py
# Flask Web Application for Salesforce Automation UI

from flask import Flask, render_template, request, jsonify, session
from salesforce_automation import SalesforceAutomation
from datetime import datetime, timedelta
import json
import os
import threading

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Global variable to store execution status
execution_status = {}
abort_flags = {}

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

def expand_instance_url(instance_input, custom_instance_name=None):
    """Expand short instance codes to full URLs"""
    if not instance_input:
        return 'https://trimbledx--dxuat.sandbox.my.salesforce.com'
    
    # If it's already a full URL, return as is
    if instance_input.startswith('http'):
        return instance_input
    
    # Handle 'other' option with custom instance name
    if instance_input.lower() == 'other':
        if custom_instance_name:
            return f'https://trimbledx--{custom_instance_name}.sandbox.my.salesforce.com'
        else:
            return 'https://trimbledx--dxuat.sandbox.my.salesforce.com'  # Default fallback
    
    # Map of short codes to full URLs
    instance_map = {
        'tdwarriors': 'https://trimbledx--tdwarriors.sandbox.my.salesforce.com',
        'tecd': 'https://trimbledx--tecd.sandbox.my.salesforce.com',
        'tecq': 'https://trimbledx--tecq.sandbox.my.salesforce.com',
        'tecs': 'https://trimbledx--tecs.sandbox.my.salesforce.com',
        'tecu': 'https://trimbledx--tecu.sandbox.my.salesforce.com',
        'dxuat': 'https://trimbledx--dxuat.sandbox.my.salesforce.com',
        'prod': 'https://trimbledx.my.salesforce.com',
    }
    
    # Convert to lowercase for case-insensitive matching
    instance_lower = instance_input.lower().strip()
    
    # Return mapped URL or construct default pattern
    if instance_lower in instance_map:
        return instance_map[instance_lower]
    else:
        # If not in map, assume it's a sandbox name
        return f'https://trimbledx--{instance_input}.sandbox.my.salesforce.com'

@app.route('/api/run', methods=['POST'])
def run_automation():
    """Run the automation with provided configuration"""
    try:
        data = request.json
        
        # Expand instance URL from short code if needed
        instance_url = expand_instance_url(
            data.get('instance_url', ''),
            data.get('custom_instance_name', '')
        )
        
        # Build configuration from form data
        config = {
            'SESSION_ID': data.get('session_id', ''),
            'INSTANCE_URL': instance_url,
            'API_VERSION': data.get('api_version', 'v58.0'),
            
            # Account settings
            'IS_ACCOUNT_CREATION_NEEDED': data.get('create_account', False),
            'ACCOUNT_ID': data.get('account_id', ''),
            'ACCOUNT_NAME': data.get('account_name', 'Account by Automation'),
            'Random_Needed': data.get('random_name', False),
            'TERRITORY_NAME': data.get('territory_name', 'Americas'),
            
            # Opportunity settings
            'IS_OPPORTUNITY_CREATION_NEEDED': data.get('create_opportunity', False),
            'OPPORTUNITY_ID': data.get('opportunity_id', ''),
            'OPPORTUNITY_NAME': data.get('opportunity_name', 'Opportunity - Auto'),
            
            # Quote settings
            'IS_QUOTE_CREATION_NEEDED': data.get('create_quote', False),
            'QUOTE_ID': data.get('quote_id', ''),
            'QUOTE_START_DATE': datetime.strptime(data.get('quote_start_date', ''), '%Y-%m-%d') if data.get('quote_start_date') else datetime.today() - timedelta(days=1),
            
            # Quote Config
            'QUOTE_CONFIG': {
                'subscription_term': int(data.get('subscription_term', 24)),
                'billing_frequency': data.get('billing_frequency', 'Upfront'),
                'sector': data.get('sector', 'CES - Construction Enterprise Solutions')
            },
            
            # Ramp settings
            'RAMP': data.get('ramp', 'No'),
            'ESC_Percent': int(data.get('esc_percent', 5)) if data.get('ramp') == 'Yes' else None,
            'Business_type': data.get('business_type', '') if data.get('ramp') == 'Yes' else None,
            
            # Product settings
            'IS_PRODUCT_ADDITION_NEEDED': data.get('add_products', False),
            'PRODUCT_CODE_QUANTITY_MAP': parse_products(data.get('products', '')),
            
            # Approval & Validation
            'IS_SUBMIT_QUOTE_FOR_APPROVAL_NEEDED': data.get('submit_approval', False),
            'IS_VALIDATE_QUOTE_NEEDED': data.get('validate_quote', False),
            'IS_QUOTE_TO_ACCEPTED_NEEDED': data.get('quote_to_accepted', False),
            'IS_OARA_NEEDED': data.get('oara_needed', False),
            
            # Contact Info
            'CONTACT_INFO': {
                'FirstName': data.get('contact_firstname', 'User'),
                'Email': data.get('contact_email', ''),
                'Phone': data.get('contact_phone', '+11033567890'),
                'Contact_Role__c': data.get('contact_role', 'Invoice Recipient')
            },
            
            'Pref_Lan': data.get('preferred_language', 'English'),
            
            # Address
            'ADDRESS': {
                'Street': data.get('address_street', '4803 Worthington Drive'),
                'City': data.get('address_city', 'Westville'),
                'State': data.get('address_state', 'Ohio'),
                'Country': data.get('address_country', 'United States'),
                'CountryCode': data.get('address_country_code', 'US'),
                'PostalCode': data.get('address_postal', '43083'),
                'Name': data.get('address_name', 'Test Address')
            },
            
            # Other settings
            'PAYMENT_TERMS': data.get('payment_terms', '30 NET'),
            'DEFAULT_CURRENCY': data.get('custom_currency') if data.get('currency') == 'Other' else data.get('currency', 'USD'),
            'DEFAULT_DISCOUNT': float(data.get('discount', 0)),
        }
        
        # Validate session ID
        if not config['SESSION_ID']:
            return jsonify({
                'success': False,
                'error': 'Session ID is required'
            }), 400
        
        # Run automation in a separate thread
        execution_id = str(datetime.now().timestamp())
        abort_flags[execution_id] = False
        execution_status[execution_id] = {
            'status': 'running',
            'current_step': 'Initializing',
            'steps': [],
            'logs': [],
            'results': {}
        }
        
        def run_in_background():
            try:
                automation = SalesforceAutomation(config, execution_id, execution_status, abort_flags)
                results = automation.run()
                
                if abort_flags.get(execution_id):
                    execution_status[execution_id]['status'] = 'aborted'
                else:
                    execution_status[execution_id]['status'] = 'completed'
                    
                execution_status[execution_id]['logs'] = results.get('logs', [])
                execution_status[execution_id]['results'] = {
                    'account_id': results.get('account_id'),
                    'opportunity_id': results.get('opportunity_id'),
                    'quote_id': results.get('quote_id')
                }
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                execution_status[execution_id]['status'] = 'error'
                execution_status[execution_id]['error'] = str(e)
                execution_status[execution_id]['error_details'] = error_details
                execution_status[execution_id]['logs'].append(f'[ERROR] {str(e)}')
                execution_status[execution_id]['logs'].append(f'[ERROR DETAILS] {error_details}')
                execution_status[execution_id]['current_step'] = 'Failed'
        
        thread = threading.Thread(target=run_in_background)
        thread.start()
        
        return jsonify({
            'success': True,
            'execution_id': execution_id
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'error_details': traceback.format_exc()
        }), 500

@app.route('/api/status/<execution_id>', methods=['GET'])
def get_status(execution_id):
    """Get execution status"""
    if execution_id not in execution_status:
        return jsonify({
            'success': False,
            'error': 'Execution ID not found'
        }), 404
    
    return jsonify({
        'success': True,
        'data': execution_status[execution_id]
    })

@app.route('/api/abort/<execution_id>', methods=['POST'])
def abort_execution(execution_id):
    """Abort execution"""
    if execution_id not in abort_flags:
        return jsonify({
            'success': False,
            'error': 'Execution ID not found'
        }), 404
    
    abort_flags[execution_id] = True
    if execution_id in execution_status:
        execution_status[execution_id]['logs'].append('[ABORT] User requested to abort execution')
        execution_status[execution_id]['current_step'] = 'Aborting...'
    
    return jsonify({
        'success': True,
        'message': 'Abort signal sent'
    })

def parse_products(products_str):
    """Parse products string into an ordered list of product lines.
    Format: PRODUCT-CODE-1:5, PRODUCT-CODE-2:10
    Duplicate product codes are preserved as separate lines.
    """
    if not products_str:
        return []
    
    product_lines = []
    for item in products_str.split(','):
        item = item.strip()
        if not item:
            continue

        if ':' in item:
            code, qty = item.split(':', 1)
            code = code.strip()
            qty_value = int(qty.strip())
        else:
            code = item
            qty_value = 1

        product_lines.append({
            'code': code,
            'quantity': qty_value
        })
    
    return product_lines

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
