# salesforce_automation.py
# Core business logic module - refactored from NewSale.py

import json
import requests
from datetime import datetime, timedelta
import time
import random
import string
import os
import csv

class SalesforceAutomation:
    """Core Salesforce automation logic"""
    
    def __init__(self, config, execution_id=None, execution_status=None, abort_flags=None):
        """Initialize with configuration dictionary"""
        self.config = config
        self.session_id = config['SESSION_ID']
        self.instance_url = config['INSTANCE_URL']
        self.api_version = config['API_VERSION']
        self.execution_id = execution_id
        self.execution_status = execution_status
        self.abort_flags = abort_flags
        self.headers = {
            'Authorization': f'Bearer {self.session_id}',
            'Content-Type': 'application/json'
        }
        self.results = {
            'account_id': None,
            'opportunity_id': None,
            'quote_id': None,
            'logs': [],
            'steps': []
        }
        self.current_step_start = None
    
    def should_abort(self):
        """Check if abort was requested"""
        if self.abort_flags and self.execution_id:
            return self.abort_flags.get(self.execution_id, False)
        return False
    
    def update_step(self, step_name, status, message=''):
        """Update step status in real-time"""
        step_info = {
            'name': step_name,
            'status': status,
            'message': message,
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
        
        if status == 'running':
            self.current_step_start = time.time()
        elif status in ['success', 'error', 'skipped'] and self.current_step_start:
            duration = time.time() - self.current_step_start
            step_info['duration'] = f"{duration:.1f}s"
            self.current_step_start = None
        
        self.results['steps'].append(step_info)
        
        # Update execution status if available
        if self.execution_status and self.execution_id:
            self.execution_status[self.execution_id]['steps'] = self.results['steps']
            self.execution_status[self.execution_id]['current_step'] = step_name if status == 'running' else ''
    
    def log(self, message, level='info'):
        """Add log message"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message
        }
        self.results['logs'].append(log_entry)
        
        # Update execution status if available
        if self.execution_status and self.execution_id:
            self.execution_status[self.execution_id]['logs'] = self.results['logs']
        
        print(f"[{timestamp}] [{level.upper()}] {message}")
    
    def generate_unique_name(self, prefix):
        """Generate unique name with timestamp"""
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        rand_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        if prefix == "Contact":
            return f"{rand_str}_{timestamp}_{prefix}_{rand_str}"
        else:
            country = self.config.get('ADDRESS', {}).get('Country', 'US')
            return f"{prefix}_{country}_{timestamp}_{rand_str}"
    
    def create_account(self):
        """Create Salesforce Account"""
        self.update_step('Create Account', 'running')
        self.log("Creating Account...", 'info')
        
        if self.should_abort():
            self.update_step('Create Account', 'skipped', 'Aborted by user')
            return None
            
        url = f"{self.instance_url}/services/data/{self.api_version}/sobjects/Account"
        
        account_name = self.config.get('ACCOUNT_NAME')
        if self.config.get('Random_Needed'):
            account_name = self.generate_unique_name(account_name)
        
        payload = {
            "Name": account_name,
            "TNV_Credit_Line_Less_Than_50k__c": "Yes",
            "TNV_Direct_Customer__c": "Yes",
            "TNV_Account_Upgrade_Status__c": "Sales Ops Review",
            "TNV_Sector__c": "CES_Construction_Enterprise_Solutions",
            "TNV_Account_Segment__c": "Commercial"
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code == 201:
            account_id = response.json().get("id")
            self.results['account_id'] = account_id
            self.log(f"Account created: {account_id}", 'success')
            self.update_step('Create Account', 'success', f'Account ID: {account_id}')
            return account_id
        else:
            error_msg = f"Account creation failed: {response.text}"
            self.log(error_msg, 'error')
            self.update_step('Create Account', 'error', response.text)
            return None
    
    def assign_territory(self, account_id):
        """Assign territory to account"""
        self.log("Assigning Territory...")
        territory_name = self.config.get('TERRITORY_NAME', 'Americas')
        query = f"SELECT Id, Name FROM Territory2 WHERE Name LIKE '%{territory_name}%' LIMIT 1"
        url = f"{self.instance_url}/services/data/{self.api_version}/query/?q={query}"
        
        response = requests.get(url, headers=self.headers)
        records = response.json().get("records", [])
        
        if not records:
            self.log("Territory not found", 'error')
            return None
        
        territory_id = records[0]['Id']
        assign_payload = {
            "ObjectId": account_id,
            "Territory2Id": territory_id,
            "AssociationCause": "Territory2Manual"
        }
        
        assign_url = f"{self.instance_url}/services/data/{self.api_version}/sobjects/ObjectTerritory2Association"
        response = requests.post(assign_url, headers=self.headers, json=assign_payload)
        
        if response.status_code == 201:
            self.log(f"Territory assigned: {territory_id}", 'success')
            return territory_id
        else:
            self.log(f"Territory assignment failed: {response.text}", 'error')
            return None
    
    def create_contact(self, account_id):
        """Create contact for account"""
        self.log("Creating Contact...")
        contact_info = self.config.get('CONTACT_INFO', {})
        last_name = self.generate_unique_name("Contact")
        
        payload = dict(contact_info)
        payload["AccountId"] = account_id
        payload["LastName"] = last_name
        payload["TNV_Preferred_Language__c"] = self.config.get('Pref_Lan', 'English')
        
        url = f"{self.instance_url}/services/data/{self.api_version}/sobjects/Contact"
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code == 201:
            contact_id = response.json().get("id")
            self.log(f"Contact created: {contact_id}", 'success')
            return contact_id
        else:
            self.log(f"Contact creation failed: {response.text}", 'error')
            return None
    
    def create_contact_point_address(self, account_id):
        """Create contact point addresses"""
        self.log("Creating Contact Point Addresses...")
        address = self.config.get('ADDRESS', {})
        
        for addr_type in ["Shipping", "Billing"]:
            payload = dict(address)
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
            
            url = f"{self.instance_url}/services/data/{self.api_version}/sobjects/ContactPointAddress"
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code != 201:
                self.log(f"Contact Point Address creation failed for {addr_type} : {response.text}", 'error')
                return False
        
        self.log("Contact Point Addresses created", 'success')
        return True
    
    def sync_account(self, account_id):
        """Sync account with Oracle"""
        self.log("Syncing Account with Oracle...")
        url = f"{self.instance_url}/services/data/{self.api_version}/tooling/executeAnonymous"
        apex_code = f"AccountManagementServiceClass.createNewCdhCustomerAccountPlatformEvent('{account_id}');"
        
        response = requests.get(url, headers=self.headers, params={"anonymousBody": apex_code})
        success = response.status_code == 200 and response.json().get("success")
        
        if success:
            self.log("Account synced with Oracle", 'success')
        else:
            self.log("Account sync failed", 'error')
        
        return success
    
    def wait_for_oracle_account_number(self, account_id, max_wait_secs=500, poll_interval_secs=10):
        """Wait for Oracle account number to be populated"""
        self.log("Waiting for Oracle Account Number...")
        waited = 0
        
        while waited < max_wait_secs:
            oracle_num = self.get_oracle_account_number(account_id)
            if oracle_num:
                self.log(f"Oracle Account Number populated: {oracle_num}", 'success')
                return True
            
            self.log(f"Waiting for Oracle Account Number... ({waited}s)")
            time.sleep(poll_interval_secs)
            waited += poll_interval_secs
        
        self.log("Timeout: Oracle Account Number not populated", 'error')
        return False
    
    def get_oracle_account_number(self, account_id):
        """Get Oracle account number"""
        url = f"{self.instance_url}/services/data/{self.api_version}/query"
        soql = f"SELECT TNV_Oracle_Account_Number__c FROM Account WHERE Id = '{account_id}'"
        
        response = requests.get(url, headers=self.headers, params={"q": soql})
        records = response.json().get("records", [])
        
        if records and records[0].get("TNV_Oracle_Account_Number__c"):
            return records[0]["TNV_Oracle_Account_Number__c"]
        return None
    
    def create_opportunity(self, account_id):
        """Create opportunity"""
        self.log("Creating Opportunity...")
        
        # Get Contact ID
        contact_query = f"SELECT Id FROM Contact WHERE AccountId = '{account_id}' LIMIT 1"
        contact_response = requests.get(
            f"{self.instance_url}/services/data/{self.api_version}/query",
            headers=self.headers,
            params={'q': contact_query}
        )
        print(contact_response.json())
        contact_id = contact_response.json().get("records", [{}])[0].get("Id")
        
        # Get Territory ID
        territory_name = self.config.get('TERRITORY_NAME', 'Americas')
        territory_query = f"SELECT Id FROM Territory2 WHERE Name LIKE '%{territory_name}%' LIMIT 1"
        territory_response = requests.get(
            f"{self.instance_url}/services/data/{self.api_version}/query",
            headers=self.headers,
            params={'q': territory_query}
        )
        territory_id = territory_response.json().get("records", [{}])[0].get("Id")
        
        payload = {
            "AccountId": account_id,
            "Name": self.config.get('OPPORTUNITY_NAME', 'Opportunity - Auto'),
            "StageName": "Prospecting / Pursue",
            "CloseDate": (datetime.today() + timedelta(days=30)).strftime('%Y-%m-%d'),
            "ForecastCategoryName": "Pipeline",
            "TNV_Deal_Order_Type__c": "Transformation",
            "TNV_Sector__c": "CES_Construction_Enterprise_Solutions",
            "TNV_Product_Category__c": "Design",
            "LeadSource": "Outbound Sales",
            "CurrencyIsoCode": self.config.get('DEFAULT_CURRENCY', 'USD'),
            "TNV_Billing_Contact__c": contact_id,
            "TNV_Shipping_Contact__c": contact_id,
            "TNV_Shipping_Account__c": account_id,
            "TNV_Billing_Account__c": account_id,
            "Territory2Id": territory_id,
            "TNV_Payment_term__c": self.config.get('PAYMENT_TERMS', '30 NET')
        }
        
        url = f"{self.instance_url}/services/data/{self.api_version}/sobjects/Opportunity"
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code == 201:
            opp_id = response.json().get("id")
            self.results['opportunity_id'] = opp_id
            self.log(f"Opportunity created: {opp_id}", 'success')
            return opp_id
        else:
            self.log(f"Opportunity creation failed: {response.text}", 'error')
            return None
    
    def update_opportunity_currency(self, opportunity_id):
        """Update opportunity currency"""
        self.log("Updating Opportunity currency...")
        payload = {"CurrencyIsoCode": self.config.get('DEFAULT_CURRENCY', 'USD')}
        url = f"{self.instance_url}/services/data/{self.api_version}/sobjects/Opportunity/{opportunity_id}"
        
        response = requests.patch(url, headers=self.headers, json=payload)
        if response.status_code == 204:
            self.log("Opportunity currency updated", 'success')
            return True
        else:
            self.log("Failed to update Opportunity currency", 'error')
            return False
    
    def update_opp_win_reason(self, opportunity_id, reason):
        """Update opportunity win reason"""
        payload = {"TNV_Win_Reason__c": reason}
        url = f"{self.instance_url}/services/data/{self.api_version}/sobjects/Opportunity/{opportunity_id}"
        
        response = requests.patch(url, headers=self.headers, json=payload)
        if response.status_code == 204:
            self.log(f"Win Reason updated: {reason}", 'success')
            return True
        else:
            self.log("Failed to update Win Reason", 'error')
            return False
    
    def create_quote(self, opportunity_id, account_id):
        """Create quote"""
        self.log("Creating Quote...")
        quote_config = self.config.get('QUOTE_CONFIG', {})
        quote_start_date = self.config.get('QUOTE_START_DATE', datetime.today() - timedelta(days=1))
        
        payload = {
            "SBQQ__StartDate__c": quote_start_date.strftime('%Y-%m-%d'),
            "TNV_Subscription_Term__c": quote_config.get('subscription_term', 24),
            "TNV_Billing_Frequency__c": quote_config.get('billing_frequency', 'Upfront'),
            "SBQQ__Opportunity2__c": opportunity_id,
            "SBQQ__Account__c": account_id,
            "TNV_Bypass_Quote_Creation_Validation__c": True,
            "SBQQ__Primary__c": True,
            "TNV_Sector__c": quote_config.get('sector', 'CES - Construction Enterprise Solutions'),
            "TNV_Payment_Terms__c": self.config.get('PAYMENT_TERMS', '30 NET'),
            "Multi_Year_Contract_with_Price_Ramps__c": self.config.get('RAMP', 'No'),
            "TNV_Multi_Year_Product_Uplift__c": self.config.get('ESC_Percent'),
            "TNV_Select_the_Business_Type__c": self.config.get('Business_type', ''),
        }
        
        url = f"{self.instance_url}/services/data/{self.api_version}/sobjects/SBQQ__Quote__c"
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code == 201:
            quote_id = response.json().get("id")
            self.results['quote_id'] = quote_id
            self.log(f"Quote created: {quote_id}", 'success')
            return quote_id
        else:
            self.log(f"Quote creation failed: {response.text}", 'error')
            return None
    
    def update_quote_sector(self, quote_id):
        """Update quote sector"""
        quote_config = self.config.get('QUOTE_CONFIG', {})
        payload = {"TNV_Sector__c": quote_config.get('sector', 'CES - Construction Enterprise Solutions')}
        url = f"{self.instance_url}/services/data/{self.api_version}/sobjects/SBQQ__Quote__c/{quote_id}"
        
        response = requests.patch(url, headers=self.headers, json=payload)
        return response.status_code == 204
    
    def add_products_to_quote_by_code(self, quote_id):
        """Add products to quote using Agentforce API with quantity support"""
        self.update_step('Add Products to Quote', 'running')
        self.log("Adding products to Quote...")
        
        product_input = self.config.get('PRODUCT_CODE_QUANTITY_MAP', {})

        # Support both legacy dict input and ordered list input from UI.
        if isinstance(product_input, dict):
            product_lines = [
                {'code': code, 'quantity': int(qty)}
                for code, qty in product_input.items()
            ]
        else:
            product_lines = []
            for entry in product_input or []:
                if not isinstance(entry, dict):
                    continue
                code = str(entry.get('code', '')).strip()
                if not code:
                    continue
                product_lines.append({
                    'code': code,
                    'quantity': int(entry.get('quantity', 1))
                })

        product_codes = [line['code'] for line in product_lines]
        unique_product_codes = list(dict.fromkeys(product_codes))
        self.log(f"Adding {len(unique_product_codes)} Product codes: {product_codes}")
        
        if not unique_product_codes:
            self.log("No products to add", 'warning')
            self.update_step('Add Products to Quote', 'skipped', 'No products specified')
            return True
        
        # Query all products by ProductCode
        product_codes_str = ",".join([f"'{code}'" for code in unique_product_codes])
        query = f"SELECT Id, ProductCode, Name FROM Product2 WHERE ProductCode IN ({product_codes_str})"
        
        try:
            response = requests.get(
                f"{self.instance_url}/services/data/{self.api_version}/query",
                headers=self.headers,
                params={"q": query}
            )
            
            if response.status_code != 200:
                error_msg = f"Failed to query products: {response.text}"
                self.log(error_msg, 'error')
                self.update_step('Add Products to Quote', 'error', 'Product query failed')
                return False
            
            records = response.json().get("records", [])
            
            if not records:
                self.log("No products found with the provided codes", 'error')
                self.update_step('Add Products to Quote', 'error', 'Products not found')
                return False
            
            product_lookup = {record.get('ProductCode'): record for record in records}

            # Add each product line using Agentforce API.
            success_count = 0
            failed_count = 0
            
            for line in product_lines:
                if self.should_abort():
                    self.log("Product addition aborted by user", 'warning')
                    self.update_step('Add Products to Quote', 'error', 'Aborted by user')
                    return False
                
                product_code = line['code']
                record = product_lookup.get(product_code)

                if not record:
                    self.log(f"Product {product_code} not found", 'error')
                    failed_count += 1
                    continue

                product_name = record.get('Name', product_code)
                product_id = record["Id"]
                product_quantity = int(line.get('quantity', 1))
                
                self.log(f"Adding product {product_code} (Qty: {product_quantity})...")
                
                # Get discount and ensure it's formatted as a Decimal for Apex
                discount = int(self.config.get('DEFAULT_DISCOUNT', 0))
                
                # Build Apex code to add product with quantity
                apex_code = f"""
                    TNV_Agentforce_AddProduct.Request request = new TNV_Agentforce_AddProduct.Request();  
                    request.QuoteId = '{quote_id}';
                    TNV_Agentforce_AddProduct.ProductDetail detail = new TNV_Agentforce_AddProduct.ProductDetail();  
                    detail.productId = '{product_id}';
                    detail.productQuantity = {product_quantity};
                    detail.productDiscount = {discount};
                    request.ProductDetails = new List<TNV_Agentforce_AddProduct.ProductDetail> {{ detail }};
                    List<TNV_Agentforce_AddProduct.Request> requestList = new List<TNV_Agentforce_AddProduct.Request> {{ request }};
                    TNV_Agentforce_AddProduct.addProduct(requestList);
                """
                
                exec_url = f"{self.instance_url}/services/data/{self.api_version}/tooling/executeAnonymous"
                exec_response = requests.get(exec_url, headers=self.headers, params={"anonymousBody": apex_code})
                
                if exec_response.status_code == 200 and exec_response.json().get("success"):
                    self.log(f"Product {product_code} added successfully (Qty: {product_quantity})", 'success')
                    success_count += 1
                    
                    # Wait for the specific job to complete
                    try:
                        self.wait_for_jobs_to_complete(["TNV_Agentforce_AddProduct", "TNV_CalculateQuote"], poll_interval=3, timeout=60)
                    except TimeoutError as e:
                        self.log(f"Warning: Job timeout for {product_code}: {str(e)}", 'warning')
                else:
                    error_details = exec_response.json() if exec_response.status_code == 200 else response.text
                    self.log(f"Failed to add product {product_code}: {error_details}", 'error')
                    failed_count += 1
            
            # Calculate quote after adding all products
            if success_count > 0:
                self.log(f"Successfully added {success_count}/{len(product_lines)} product line(s)", 'success')
                self.calculate_quote_via_apex(quote_id)
                
                if failed_count > 0:
                    self.update_step('Add Products to Quote', 'success', f'{success_count} added, {failed_count} failed')
                else:
                    self.update_step('Add Products to Quote', 'success', f'{success_count} products added')
                return True
            else:
                self.log("Failed to add any products", 'error')
                self.update_step('Add Products to Quote', 'error', 'No products added')
                return False
                
        except Exception as e:
            error_msg = f"Error adding products: {str(e)}"
            self.log(error_msg, 'error')
            self.update_step('Add Products to Quote', 'error', str(e))
            return False
    
    def wait_for_jobs_to_complete(self, class_names, poll_interval=3, timeout=300):
        """Wait for Apex jobs to complete - only checks recently submitted jobs"""
        start_time = time.time()
        names_str = ",".join([f"'{n}'" for n in class_names])
        logged_waiting = False
        
        # Get the timestamp to filter only recent jobs (submitted after this method was called)
        filter_time = datetime.now() - timedelta(seconds=5)  # Look for jobs created in last 5 seconds
        filter_time_str = filter_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        
        while True:
            # Query only recent jobs (created after we started waiting)
            q = (
                "SELECT ApexClass.Name, Status, ExtendedStatus, JobItemsProcessed, TotalJobItems, "
                "NumberOfErrors, CompletedDate, CreatedDate FROM AsyncApexJob "
                f"WHERE ApexClass.Name IN ({names_str}) "
                f"AND CreatedDate >= {filter_time_str} "
                "ORDER BY CreatedDate DESC"
            )
            url = f"{self.instance_url}/services/data/{self.api_version}/tooling/query"
            resp = requests.get(url, headers=self.headers, params={"q": q}).json()
            records = resp.get("records", [])
            
            if not records:
                # No jobs found yet - might still be queuing
                elapsed = int(time.time() - start_time)
                if elapsed < 10:  # Wait up to 10 seconds for jobs to appear
                    if not logged_waiting:
                        self.log(f"Waiting for background jobs to start...", 'info')
                        logged_waiting = True
                    time.sleep(poll_interval)
                    continue
                else:
                    # No jobs appeared, assume they completed instantly or weren't needed
                    self.log("No background jobs detected (may have completed instantly)", 'info')
                    break
            
            # Separate jobs by status
            pending_jobs = [r for r in records if r.get('Status') in ('Queued', 'Processing', 'Holding')]
            failed_jobs = [r for r in records if r.get('Status') == 'Failed']
            completed_jobs = [r for r in records if r.get('Status') == 'Completed']
            
            # Check for failed jobs
            if failed_jobs:
                for job in failed_jobs:
                    job_name = job.get('ApexClass', {}).get('Name', 'Unknown')
                    extended_status = job.get('ExtendedStatus', 'No details available')
                    num_errors = job.get('NumberOfErrors', 0)
                    self.log(f"❌ Job FAILED: {job_name}", 'error')
                    self.log(f"Error Details: {extended_status}", 'error')
                    self.log(f"Number of Errors: {num_errors}", 'error')
                
                # Return False to indicate failure
                raise Exception(f"Background job(s) failed: {', '.join([j.get('ApexClass', {}).get('Name', 'Unknown') for j in failed_jobs])}. Check logs for details.")
            
            # Check for completed jobs with errors
            for job in completed_jobs:
                num_errors = job.get('NumberOfErrors', 0)
                if num_errors > 0:
                    job_name = job.get('ApexClass', {}).get('Name', 'Unknown')
                    extended_status = job.get('ExtendedStatus', 'No details available')
                    self.log(f"⚠️ Job completed with errors: {job_name}", 'warning')
                    self.log(f"Error Details: {extended_status}", 'warning')
                    self.log(f"Number of Errors: {num_errors}", 'warning')
            
            # If no pending jobs, we're done
            if not pending_jobs:
                if logged_waiting:
                    self.log("Background jobs completed successfully", 'success')
                break
            
            # Log waiting message (only once or at intervals)
            elapsed = int(time.time() - start_time)
            if not logged_waiting or elapsed % 10 == 0:  # Log initially and every 10 seconds
                job_names = ", ".join([r.get('ApexClass', {}).get('Name', 'Unknown') for r in pending_jobs])
                job_progress = []
                for r in pending_jobs:
                    processed = r.get('JobItemsProcessed', 0)
                    total = r.get('TotalJobItems', 0)
                    if total > 0:
                        job_progress.append(f"{processed}/{total}")
                
                progress_str = f" [{', '.join(job_progress)}]" if job_progress else""
                self.log(f"Waiting for background jobs: {job_names}{progress_str} ({elapsed}s elapsed)", 'info')
                logged_waiting = True
            
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Jobs {class_names} did not complete within {timeout} seconds.")
            time.sleep(poll_interval)
    
    def calculate_quote_via_apex(self, quote_id):
        """Calculate quote"""
        self.log("Calculating Quote...")
        url = f"{self.instance_url}/services/apexrest/Quote/quoteCalculator/"
        payload = {"quoteId": quote_id}
        
        resp = requests.post(url, headers=self.headers, json=payload)
        if resp.status_code == 200:
            self.log("Quote calculation triggered", 'success')
            self.wait_for_jobs_to_complete(["QueueableCalculatorService"])
            self.log("Waiting 5 seconds for calculation to stabilize...", 'info')
            time.sleep(5)
        else:
            self.log(f"Failed to trigger calculation: {resp.text}", 'error')
    
    def submit_quote_for_approval(self, quote_id):
        """Submit quote for approval"""
        self.log("Submitting Quote for Approval...")
        url = f"{self.instance_url}/services/data/{self.api_version}/tooling/executeAnonymous"
        apex_code = f"TNV_SubmitForApproval.submitForApproval(new List<Id>{{'{quote_id}'}});"
        
        response = requests.get(url, headers=self.headers, params={"anonymousBody": apex_code})
        
        if response.status_code == 200 and response.json().get("success"):
            self.log("Quote submitted for approval", 'success')
        else:
            self.log("Quote submission failed", 'error')
    
    def validate_quote(self, quote_id):
        """Validate quote"""
        self.log("Validating Quote...")
        apex_code = f"TNV_Agentforce_QuoteGenerateDocument.validateQuote('{quote_id}');"
        url = f"{self.instance_url}/services/data/v58.0/tooling/executeAnonymous"
        
        resp = requests.get(url, headers=self.headers, params={'anonymousBody': apex_code})
        if resp.status_code == 200 and resp.json().get("success"):
            self.log("Quote validated", 'success')
        else:
            self.log("Quote validation failed", 'error')
    
    def update_quote_to_accepted(self, quote_id):
        """Update quote status to accepted"""
        
        self.log("Updating Quote to Presented...")
        # First update to Presented
        url = f"{self.instance_url}/services/data/{self.api_version}/sobjects/SBQQ__Quote__c/{quote_id}"
        response = requests.patch(url, headers=self.headers, json={"SBQQ__Status__c": "Presented"})
        
        if response.status_code != 204:
            self.log("Failed to update Quote to Presented", 'error')
            return False
        time.sleep(1)  # Small delay to ensure status change is processed
        self.log("Updating Quote to Accepted...")
        # Then update to Accepted
        response = requests.patch(url, headers=self.headers, json={"SBQQ__Status__c": "Accepted"})
        
        if response.status_code == 204:
            self.log("Quote updated to Accepted", 'success')
            return True
        else:
            self.log("Failed to update Quote to Accepted", 'error')
            return False
    
    def check_oara(self, quote_id):
        """Check OARA"""
        self.log("Checking OARA...")
        payload = {"TNV_Sale_Opps_Reviewed_and_Approved__c": True}
        url = f"{self.instance_url}/services/data/{self.api_version}/sobjects/SBQQ__Quote__c/{quote_id}"
        
        response = requests.patch(url, headers=self.headers, json=payload)
        if response.status_code == 204:
            self.log("OARA updated", 'success')
            return True
        else:
            self.log(f"Failed to update OARA : {response.text}", 'error')
            return False
    
    def send_email(self):
        """Send email notification"""
        self.log("Sending email notification...")
        email_url = f"{self.instance_url}/services/data/{self.api_version}/actions/standard/emailSimple"
        contact_info = self.config.get('CONTACT_INFO', {})
        
        account_id = self.results.get('account_id')
        opp_id = self.results.get('opportunity_id')
        quote_id = self.results.get('quote_id')
        
        account_url = f"{self.instance_url}/{account_id}" if account_id else "N/A"
        opp_url = f"{self.instance_url}/{opp_id}" if opp_id else "N/A"
        quote_url = f"{self.instance_url}/{quote_id}" if quote_id else "N/A"
        
        subject = f"Record Creation Summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        body = f"""Hello {contact_info.get('FirstName', 'User')},

The following records were created:

    Account: {account_url}
    Opportunity: {opp_url}
    Quote: {quote_url}

Regards,
Automation System"""
        
        payload = {
            "inputs": [{
                "emailBody": body,
                "emailBodyIsHtml": True,
                "emailAddresses": contact_info.get("Email", ""),
                "senderDisplayName": "Salesforce Automation",
                "emailSubject": subject
            }]
        }
        
        resp = requests.post(email_url, headers=self.headers, json=payload)
        if resp.status_code == 200:
            self.log("Email sent successfully", 'success')
        else:
            self.log("Email sending failed", 'error')
        
        # Save to CSV log
        self.save_to_csv_log(account_url, opp_url, quote_url)
    
    def save_to_csv_log(self, account_url, opp_url, quote_url):
        """Save results to CSV log"""
        log_file = "email_log.csv"
        file_exists = os.path.isfile(log_file)
        contact_info = self.config.get('CONTACT_INFO', {})
        
        with open(log_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Timestamp", "Contact Name", "Email", "Account URL", "Opportunity URL", "Quote URL", "Status"])
            writer.writerow([
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                contact_info.get("FirstName", ""),
                contact_info.get("Email", ""),
                account_url,
                opp_url,
                quote_url
            ])
    
    def run(self):
        """Main execution flow with step-by-step error handling and abort checks"""
        account_id = self.config.get('ACCOUNT_ID')
        opp_id = self.config.get('OPPORTUNITY_ID')
        quote_id = self.config.get('QUOTE_ID')
        
        # Account Creation
        if self.config.get('IS_ACCOUNT_CREATION_NEEDED'):
            if self.should_abort():
                return self.results
            
            account_id = self.create_account()
            if not account_id or self.should_abort():
                return self.results
            
            if self.should_abort():
                return self.results
            result = self.assign_territory(account_id)
            if not result or self.should_abort():
                return self.results
            
            if self.should_abort():
                return self.results
            result = self.create_contact(account_id)
            if not result or self.should_abort():
                return self.results
            
            if self.should_abort():
                return self.results
            result = self.create_contact_point_address(account_id)
            if not result or self.should_abort():
                return self.results
            
            if self.should_abort():
                return self.results
            result = self.sync_account(account_id)
            if not result or self.should_abort():
                return self.results
            
            if self.should_abort():
                return self.results
            oracle_number = self.wait_for_oracle_account_number(account_id)
            if not oracle_number or self.should_abort():
                return self.results
        
        # Opportunity Creation
        if self.config.get('IS_OPPORTUNITY_CREATION_NEEDED') and account_id:
            if self.should_abort():
                return self.results
            
            opp_id = self.create_opportunity(account_id)
            if not opp_id or self.should_abort():
                return self.results
            
            if self.should_abort():
                return self.results
            result = self.update_opportunity_currency(opp_id)
            if not result or self.should_abort():
                return self.results
        
        # Quote Creation
        if self.config.get('IS_QUOTE_CREATION_NEEDED') and opp_id:
            if self.should_abort():
                return self.results
            
            quote_id = self.create_quote(opp_id, account_id)
            if not quote_id or self.should_abort():
                return self.results
            
            if self.should_abort():
                return self.results
            result = self.update_quote_sector(quote_id)
            if not result or self.should_abort():
                return self.results
        
        # Add Products
        if self.config.get('IS_PRODUCT_ADDITION_NEEDED') and quote_id:
            if self.should_abort():
                return self.results
            
            result = self.add_products_to_quote_by_code(quote_id)
            if self.should_abort():
                return self.results
        
        # Submit for Approval
        if self.config.get('IS_SUBMIT_QUOTE_FOR_APPROVAL_NEEDED') and quote_id:
            if self.should_abort():
                return self.results
            
            result = self.submit_quote_for_approval(quote_id)
            if  self.should_abort():
                return self.results
        
        # Validate Quote
        if self.config.get('IS_VALIDATE_QUOTE_NEEDED') and quote_id:
            if self.should_abort():
                return self.results
            
            result = self.validate_quote(quote_id)
            print(result)
            if self.should_abort():
                return self.results
            
            time.sleep(10)
        
        # Update to Accepted
        if self.config.get('IS_QUOTE_TO_ACCEPTED_NEEDED') and quote_id:
            if self.should_abort():
                return self.results
            
            result = self.update_quote_to_accepted(quote_id)
            if self.should_abort():
                return self.results
        
        # OARA
        if self.config.get('IS_OARA_NEEDED') and quote_id and opp_id:
            if self.should_abort():
                return self.results
            
            result = self.update_opp_win_reason(opp_id, "Pricing")
            if self.should_abort():
                return self.results
            
            if self.should_abort():
                return self.results
            result = self.check_oara(quote_id)
            if self.should_abort():
                return self.results
            
            if self.should_abort():
                return self.results
            result = self.update_quote_to_accepted(quote_id)
            if self.should_abort():
                return self.results
        
        # Send Email
        if self.should_abort():
            return self.results
        self.send_email()
        
        return self.results
