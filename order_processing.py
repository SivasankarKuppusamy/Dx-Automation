# order_processing.py
# Order Processing - Runs each batch step as a separate anonymous Apex transaction

import requests
import time
from datetime import datetime

# Configurable batch steps for Order Processing
ORDER_PROCESSING_STEPS = [
    {
        "id": "step1_validation",
        "name": "TNV_BatchOrderValidation",
        "description": "Order Validation",
        "enabled": True
    },
    {
        "id": "step2_taxation",
        "name": "TNV_BatchOrderTaxation",
        "description": "Order Taxation",
        "enabled": True
    },
    {
        "id": "step3_credit",
        "name": "TNV_BatchOrderCreditService",
        "description": "Order Credit Service",
        "enabled": True
    },
    {
        "id": "step4_validation_status",
        "name": "TNV_BatchUpdateOrderValidationStatus",
        "description": "Update Order Validation Status",
        "enabled": True
    },
    {
        "id": "step5a_contract_association_1",
        "name": "TNV_ContractAssociationBatch (1st Run)",
        "description": "Contract Association - First Run",
        "enabled": True
    },
    {
        "id": "step5b_contract_association_2",
        "name": "TNV_ContractAssociationBatch (2nd Run)",
        "description": "Contract Association - Second Run",
        "enabled": True
    },
    {
        "id": "step6_queueing",
        "name": "TNV_BatchQueueingOrderItems",
        "description": "Queueing Order Items",
        "enabled": True
    },
    {
        "id": "step7_provisioning_staging",
        "name": "TNV_ProvisioningStagingBatch",
        "description": "Provisioning Staging",
        "enabled": True
    },
    {
        "id": "step8_provisioning_complete",
        "name": "TNV_ProvisioningCompleteORFailBatch",
        "description": "Provisioning Complete/Fail",
        "enabled": True
    },
    {
        "id": "step9_included_childs",
        "name": "TNV_BatchCompleteIncludedChilds",
        "description": "Complete Included Childs",
        "enabled": True
    }
]


def get_step_apex(step_id, order_id):
    """Return the anonymous Apex code for a given step."""
    apex_map = {
        "step1_validation": _get_validation_apex(order_id),
        "step2_taxation": _get_taxation_apex(order_id),
        "step3_credit": _get_credit_apex(order_id),
        "step4_validation_status": _get_validation_status_apex(order_id),
        "step5a_contract_association_1": _get_contract_association_apex(order_id),
        "step5b_contract_association_2": _get_contract_association_apex(order_id),
        "step6_queueing": _get_queueing_apex(order_id),
        "step7_provisioning_staging": _get_provisioning_staging_apex(order_id),
        "step8_provisioning_complete": _get_provisioning_complete_apex(order_id),
        "step9_included_childs": _get_included_childs_apex(order_id),
    }
    return apex_map.get(step_id, "")


def execute_anonymous_apex(instance_url, api_version, session_id, apex_code):
    """Execute anonymous Apex via Salesforce Tooling API."""
    url = f"{instance_url}/services/data/{api_version}/tooling/executeAnonymous"
    headers = {
        'Authorization': f'Bearer {session_id}',
        'Content-Type': 'application/json'
    }
    params = {"anonymousBody": apex_code}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        result = response.json()
        return {
            "success": result.get("success", False),
            "compiled": result.get("compiled", False),
            "compileProblem": result.get("compileProblem"),
            "exceptionMessage": result.get("exceptionMessage"),
            "exceptionStackTrace": result.get("exceptionStackTrace"),
            "line": result.get("line"),
            "column": result.get("column"),
        }
    else:
        return {
            "success": False,
            "compiled": False,
            "compileProblem": f"HTTP {response.status_code}: {response.text}",
            "exceptionMessage": None,
            "exceptionStackTrace": None,
        }


def run_order_processing(instance_url, api_version, session_id, order_id, selected_steps, execution_id, execution_status, abort_flags):
    """Run selected order processing steps sequentially as separate transactions."""
    results = []
    total_steps = len(selected_steps)

    for idx, step_id in enumerate(selected_steps):
        # Check abort
        if abort_flags and abort_flags.get(execution_id, False):
            execution_status[execution_id]['status'] = 'aborted'
            execution_status[execution_id]['logs'].append('[ABORT] User requested to abort order processing')
            break

        # Find step config
        step_config = next((s for s in ORDER_PROCESSING_STEPS if s['id'] == step_id), None)
        if not step_config:
            continue

        step_name = step_config['name']
        step_desc = step_config['description']

        # Update status
        execution_status[execution_id]['current_step'] = f"({idx+1}/{total_steps}) {step_desc}"
        execution_status[execution_id]['logs'].append(f'[INFO] Starting Step {idx+1}/{total_steps}: {step_name}')

        # Update step status to running
        step_entry = {
            'name': f"{step_desc}",
            'status': 'running',
            'message': '',
            'timestamp': datetime.now().strftime('%H:%M:%S')
        }
        execution_status[execution_id]['steps'].append(step_entry)

        start_time = time.time()

        # Get apex code and execute
        apex_code = get_step_apex(step_id, order_id)
        result = execute_anonymous_apex(instance_url, api_version, session_id, apex_code)

        duration = time.time() - start_time

        # Update step result
        step_entry['duration'] = f"{duration:.1f}"
        if result['success']:
            step_entry['status'] = 'success'
            step_entry['message'] = 'Completed successfully'
            execution_status[execution_id]['logs'].append(
                f'[SUCCESS] {step_name} completed in {duration:.1f}s'
            )
        else:
            step_entry['status'] = 'error'
            error_msg = result.get('compileProblem') or result.get('exceptionMessage') or 'Unknown error'
            step_entry['message'] = error_msg
            execution_status[execution_id]['logs'].append(
                f'[ERROR] {step_name} failed: {error_msg}'
            )
            if result.get('exceptionStackTrace'):
                execution_status[execution_id]['logs'].append(
                    f'[ERROR] Stack trace: {result["exceptionStackTrace"]}'
                )

        # Re-assign to trigger update
        execution_status[execution_id]['steps'] = list(execution_status[execution_id]['steps'])
        results.append({'step_id': step_id, 'step_name': step_name, **result, 'duration': f"{duration:.1f}s"})

    return results


# ============ Apex Code Generators ============

def _get_validation_apex(order_id):
    return f"""
Id orderId = '{order_id}';
TNV_BatchOrderValidation orderValBatch = new TNV_BatchOrderValidation();
List<Order> ordersForValidation = [
    SELECT Id, Type, EffectiveDate, AccountId, Account.TNV_Hard_Credit_Hold__c,
           blng__BillingAccount__c, blng__BillingAccount__r.TNV_Hard_Credit_Hold__c,
           TNV_Shipping_Account__c, TNV_Shipping_Account__r.TNV_Hard_Credit_Hold__c,
           TNV_Quote_and_Order_Amounts_Mismatch__c, TNV_Order_Tax_Status__c,
           Account.TNV_Full_Account_Suspension_Hold__c, TNV_D_Country_Hold__c,
           TNV_Validated_EEUC_Form__c, TNV_Signed_EEUC_Form_Confirmation__c,
           TNV_Order_Validation_Status__c, TNV_License_Compliance__c,
           blng__BillingAccount__r.TNV_Full_Account_Suspension_Hold__c, SBQQ__OrderBookings__c,
           SBQQ__Quote__c, TNV_Order_Compliance_Status__c,
           TNV_Shipping_Account__r.TNV_Full_Account_Suspension_Hold__c,
           Account.TNV_Embargo_Entity__c, SBQQ__Quote__r.SBQQ__NetAmount__c,
           TNV_CPBilling_Address__c, TNV_CPBilling_Address__r.Country,
           TNV_CPShipping_Address__c, TNV_CPShipping_Address__r.Country,
           TNV_Shipping_Address__r.Compliance_Status__c,
           TNV_CPBilling_Address__r.TNV_Compliance_Status__c,
           blng__BillingAccount__r.TNV_Embargo_Entity__c,
           TNV_Shipping_Account__r.TNV_Embargo_Entity__c,
           TNV_Order_Credit_Approval_Status__c,
           Account.TNV_CPDefault_ShipAddress__r.TNV_Compliance_Status__c,
           Account.TNV_CPDefault_ShipAddress__c,
           Account.TNV_CPDefault_Address__c,
           Account.TNV_CPDefault_Address__r.Country,
           Account.TNV_CPDefault_ShipAddress__r.Country,
           Account.TNV_CPDefault_Address__r.TNV_Compliance_Status__c,
           SBQQ__Quote__r.TNV_Is_Bad_Debt_From_Account__c
    FROM Order
    WHERE Id = :orderId
];
if (!ordersForValidation.isEmpty()) {{
    orderValBatch.execute(null, (List<sObject>) ordersForValidation);
}}
"""


def _get_taxation_apex(order_id):
    return f"""
Id orderId = '{order_id}';
TNV_BatchOrderTaxation taxBatch = new TNV_BatchOrderTaxation();
List<OrderItem> orderItemsForTax = [
    SELECT Id, OrderId, Order.Account.TNV_CPDefault_Address__r.Country, Order.TNV_Order_Tax_Status__c
    FROM OrderItem
    WHERE OrderId = :orderId
];
if (!orderItemsForTax.isEmpty()) {{
    taxBatch.execute(null, (List<sObject>) orderItemsForTax);
}}
"""


def _get_credit_apex(order_id):
    return f"""
Id orderId = '{order_id}';
TNV_BatchOrderCreditService creditBatch = new TNV_BatchOrderCreditService();
List<Order> creditOrders = [
    SELECT Id, TNV_Order_Compliance_Status__c, SBQQ__Quote__c, Status, TNV_License_Compliance__c,
           TNV_Payment_Terms__c, TNV_Order_Validation_Status__c, TNV_Order_Credit_Approval_Status__c,
           TNV_Credit_Release_Attempts__c, CreatedDate, TNV_Payment_Authorization_Status__c,
           Account.Id, Account.TNV_External_Exposure__c, Account.TNV_Credit_Limit__c,
           Account.TNV_Order_Credit_Limit__c, Account.TNV_Credit_Status__c,
           TNV_Payment_Method__c, SBQQ__Quote__r.TNV_Payment_Method__c,
           TNV_7_Month_Billings_Total_USD__c, TNV_Order_Credit_Approval_Timestamp__c,
           SBQQ__Quote__r.TNV_Payment_Terms__c, Type, TNV_Amendment_Reasons_Code__c,
           TotalAmount, TNV_First_Billing_Gross_Amount__c, CurrencyIsoCode,
           IsCIAChangedtoEpayment__c
    FROM Order
    WHERE Id = :orderId
];
if (!creditOrders.isEmpty()) {{
    creditBatch.execute(null, (List<sObject>) creditOrders);
}}
"""


def _get_validation_status_apex(order_id):
    return f"""
Id orderId = '{order_id}';
TNV_BatchUpdateOrderValidationStatus valStatusBatch = new TNV_BatchUpdateOrderValidationStatus();
List<Order> ordersForStatusUpdate = [
    SELECT Id, CreatedDate, TNV_Customer_PO_Required__c, TNV_Quote_and_Order_Amounts_Mismatch__c,
           TNV_Order_Validation_Status__c, TNV_Order_Compliance_Status__c,
           TNV_Order_Compliance_Status_TimeStamp__c, TNV_Order_Tax_Status__c,
           TNV_Order_Credit_Approval_Status__c
    FROM Order
    WHERE Id = :orderId
];
if (!ordersForStatusUpdate.isEmpty()) {{
    valStatusBatch.execute(null, (List<sObject>) ordersForStatusUpdate);
}}
"""


def _get_contract_association_apex(order_id):
    return f"""
Id orderId = '{order_id}';
TNV_ContractAssociationBatch contractBatch = new TNV_ContractAssociationBatch();
List<Order> contractOrders = [
    SELECT Id, SalesStoreId, OpportunityId, TNV_Booked_Date__c, Opportunity.Id, Type,
           Opportunity.IsClosed, Opportunity.CloseDate,
           Opportunity.TNV_SFB_Legal_Entity__r.TNV_Time_Zone__c,
           TNV_Retry_Attempts_Count__c, TNV_Retry_Attempts__c,
           SBQQ__Quote__r.SBQQ__MasterContract__r.TNV_Renewal_Date__c,
           SBQQ__Quote__c, TNV_Order_Processing_Status__c, Status,
           TNV_Order_Compliance_Status__c, TNV_Order_Credit_Approval_Status__c,
           TNV_Order_Tax_Status__c, TNV_Order_Validation_Status__c, SBQQ__Contracted__c
    FROM Order
    WHERE Id = :orderId
];
if (!contractOrders.isEmpty()) {{
    contractBatch.execute(null, contractOrders);
}}
"""


def _get_queueing_apex(order_id):
    return f"""
Id orderId = '{order_id}';
TNV_BatchQueueingOrderItems queueBatch = new TNV_BatchQueueingOrderItems();
List<OrderItem> orderItemsToQueue = [
    SELECT Product2.TNV_AutoRenewal__c, TNV_AutoRenewal__c, SBQQ__BillingFrequency__c,
           TNV_ChangeBillingFreqIdentifier__c, Order.SBQQ__Quote__r.TNV_Amendment_Reasons_Code__c,
           TNV_Is_Bundle_Date_Mismatch__c, SBQQ__RequiredBy__r.blng__HoldBilling__c,
           SBQQ__RequiredBy__r.blng__InvoiceRunProcessingStatus__c,
           SBQQ__RequiredBy__r.blng__LastChargeToDate__c, SBQQ__RequiredBy__r.blng__NextChargeDate__c,
           SBQQ__RequiredBy__r.blng__NextBillingDate__c, SBQQ__RequiredBy__r.blng__BillThroughDateOverride__c,
           SBQQ__RequiredBy__r.TNV_Billing_hold_reason__c, SBQQ__ChargeType__c,
           TNV_Provisioning_Date__c, blng__HoldBilling__c, blng__InvoiceRunProcessingStatus__c,
           blng__LastChargeToDate__c, blng__NextChargeDate__c, blng__NextBillingDate__c,
           blng__BillThroughDateOverride__c, TNV_Billing_hold_reason__c,
           Id, ServiceDate, SBQQ__RequiredBy__r.ServiceDate, Quantity, TNV_AmendIdentifierRef__c,
           TNV_External_Error_Message__c, TNV_Processed_Polling_Count__c, TNV_Provisioning_Status__c,
           TNV_Provisioning_Method__c, TNV_Hold_Released__c, SBQQ__ContractAction__c,
           SBQQ__RevisedOrderProduct__c, SBQQ__RevisedOrderProduct__r.TNV_Provisioning_Status__c,
           SBQQ__RequiredBy__c, Product2.TNV_Tekla_Dependent_Product_Codes__c, OrderId,
           SBQQ__RequiredBy__r.TNV_Provisioning_Method__c, SBQQ__RequiredBy__r.TNV_Provisioning_Status__c,
           Order.Type, TNV_Renewal_Sequence_OrderItem__c, SBQQ__OrderedQuantity__c,
           SBQQ__RevisedOrderProduct__r.SBQQ__RequiredBy__c,
           SBQQ__QuoteLine__r.SBQQ__Quote__r.TNV_Display_Message__c,
           TNV_PC_Original_Quantity__c, SBQQ__QuoteLine__r.TNV_Amend_Order_Item__c,
           SBQQ__QuoteLine__r.SBQQ__Quote__r.TNV_Systematic_Update__c,
           TNV_Previous_Order_Product__c, TNV_BeforeorAfterT__c,
           TNV_Previous_Order_Product__r.TNV_Provisioning_Status__c
    FROM OrderItem
    WHERE OrderId = :orderId
];
if (!orderItemsToQueue.isEmpty()) {{
    queueBatch.execute(null, (List<sObject>) orderItemsToQueue);
}}
"""


def _get_provisioning_staging_apex(order_id):
    return f"""
Id orderId = '{order_id}';
TNV_ProvisioningStagingBatch stagingBatch = new TNV_ProvisioningStagingBatch();
List<OrderItem> orderItemsForStaging = [
    SELECT Id, OrderId, TNV_Provisioning_Status__c, TNV_Mulesoft_Contract_Action__c,
           TNV_Quantity_for_Provisioning__c, SBQQ__ContractAction__c, TNV_Provisioning_Method__c,
           TNV_Amendment_Reasons_Code__c, Order.Type,
           SBQQ__QuoteLine__r.TNV_Upgraded_Downgraded_Subscription__r.Total_Quantity__c,
           SBQQ__OrderedQuantity__c,
           SBQQ__QuoteLine__r.TNV_Upgraded_Downgraded_Subscription__r.SBQQ__Quantity__c,
           (SELECT Id FROM Provisioning_Details1__r),
           Order.AccountId, TNV_Technical_Admin__c, Product2.ProductCode,
           TNV_Renewal_Sequence_OrderItem__c
    FROM OrderItem
    WHERE OrderId = :orderId
      AND TNV_Provisioning_Method__c != NULL
      AND TNV_Hold_Released__c = True
];
if (!orderItemsForStaging.isEmpty()) {{
    stagingBatch.execute(null, orderItemsForStaging);
}}
"""


def _get_provisioning_complete_apex(order_id):
    return f"""
Id orderId = '{order_id}';
TNV_ProvisioningCompleteORFailBatch provCompBatch = new TNV_ProvisioningCompleteORFailBatch();
List<TNV_DX_Staging__c> dxStagings = [
    SELECT Id, TNV_Action__c, TNV_Order_Product_ID__c, TNV_Order_Product_ID__r.OrderId,
           TNV_Provisioning_Status__c, TNV_Quantity__c, TNV_EMS_Job_Id__c, MYT_EMS_PK_ID__c,
           TNV_Order_Product_ID__r.Order.Type,
           TNV_Order_Product_ID__r.TNV_Partial_Renewal_Rev_Lic_Notification__c,
           TNV_Error_Type__c, TNV_Provisioning_Backup_End_Date__c, TNV_Provisioned_Date__c,
           TNV_Provisioning_Backup_Start_Date__c, TNV_Provisioning_Method__c,
           TNV_Entitlement_ID__c, TNV_Entitlement_Line_ID__c, TNV_PS_SKU__c,
           TNV_Is_PD_Processed__c, TNV_Provisioning_Error_Message__c,
           TNV_Contract_Action__c, TNV_Revoked_Licensed_Ids__c,
           TNV_Order_Product_ID__r.SBQQ__RequiredBy__c
    FROM TNV_DX_Staging__c
    WHERE TNV_Is_Processed__c = FALSE
      AND TNV_Order_Product_ID__c != null
      AND TNV_Provisioning_Status__c IN ('Completed', 'Failed', 'Error', 'Delayed Provisioning', 'Draft Entitlement Created')
      AND TNV_Order_Product_ID__r.OrderId = :orderId
    ORDER BY TNV_Order_Product_ID__r.OrderId DESC
];
if (!dxStagings.isEmpty()) {{
    provCompBatch.execute(null, dxStagings);
}}
"""


def _get_included_childs_apex(order_id):
    return f"""
Id orderId = '{order_id}';
TNV_BatchCompleteIncludedChilds childsBatch = new TNV_BatchCompleteIncludedChilds();
List<String> setOfProvMethod = System.Label.TNV_BundleHeader_ProvisioningMethod.split(';');
List<OrderItem> includedChildItems = [
    SELECT Id, TNV_Provisioning_Status__c, Product2.ProductCode,
           Product2.TNV_Tekla_Dependent_Product_Codes__c, SBQQ__RequiredBy__c,
           TNV_Provisioning_Method__c, SBQQ__RequiredBy__r.TNV_Provisioned_Date__c,
           SBQQ__RequiredBy__r.TNV_Provisioning_Method__c, TNV_Provisioned_Date__c,
           Delivery_Date__c, TNV_Partial_Cancellation_Source__c, TNV_AmendIdentifierRef__c,
           TNV_Partial_Cancellation_Source__r.TNV_Provisioning_Status__c
    FROM OrderItem
    WHERE OrderId = :orderId
      AND ((SBQQ__RequiredBy__c != NULL
            AND SBQQ__RequiredBy__r.TNV_Provisioning_Status__c = 'Completed'
            AND SBQQ__RequiredBy__r.TNV_Provisioned_Date__c != NULL
            AND TNV_Provisioning_Status__c = 'Included'
            AND SBQQ__RequiredBy__r.TNV_Provisioning_Method__c IN :setOfProvMethod)
          OR (TNV_Provisioning_Method__c = 'ATC (Tekla)'
              AND SBQQ__RequiredBy__c != NULL
              AND SBQQ__RequiredBy__r.TNV_Provisioning_Method__c = NULL
              AND TNV_Provisioning_Status__c = 'Completed'
              AND SBQQ__RequiredBy__r.SBQQ__Activated__c != TRUE)
          OR (TNV_Provisioning_Status__c = 'Completed'
              AND TNV_AmendIdentifierRef__c != NULL
              AND TNV_Partial_Cancellation_Source__c != NULL
              AND TNV_Partial_Cancellation_Source__r.TNV_Provisioning_Status__c = 'Hold'))
];
if (!includedChildItems.isEmpty()) {{
    childsBatch.execute(null, (List<sObject>) includedChildItems);
}}
"""
