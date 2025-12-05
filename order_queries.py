# order_queries.py

def get_contract_association_query():
    """Returns SOQL query for contract association batch"""
    return """
    SELECT Id, SalesStoreId, OpportunityId, TNV_Booked_Date__c, Opportunity.Id, Type, 
           Opportunity.IsClosed, Opportunity.CloseDate, Opportunity.TNV_SFB_Legal_Entity__r.TNV_Time_Zone__c, 
           TNV_Retry_Attempts_Count__c, TNV_Retry_Attempts__c, SBQQ__Quote__r.SBQQ__MasterContract__r.TNV_Renewal_Date__c, 
           SBQQ__Quote__c, TNV_Order_Processing_Status__c, Status, TNV_Order_Compliance_Status__c, 
           TNV_Order_Credit_Approval_Status__c, TNV_Order_Tax_Status__c, TNV_Order_Validation_Status__c, 
           SBQQ__Contracted__c 
    FROM Order 
    WHERE Id = :orderId
    """

def get_order_queueing_query():
    """Returns SOQL query for order items queueing batch"""
    return """
    SELECT SBQQ__BillingFrequency__c, TNV_ChangeBillingFreqIdentifier__c, 
           Order.SBQQ__Quote__r.TNV_Amendment_Reasons_Code__c, TNV_Is_Bundle_Date_Mismatch__c,
           SBQQ__RequiredBy__r.blng__HoldBilling__c, SBQQ__RequiredBy__r.blng__InvoiceRunProcessingStatus__c, 
           SBQQ__RequiredBy__r.blng__LastChargeToDate__c, SBQQ__RequiredBy__r.blng__NextChargeDate__c, 
           SBQQ__RequiredBy__r.blng__NextBillingDate__c, SBQQ__RequiredBy__r.blng__BillThroughDateOverride__c,
           SBQQ__RequiredBy__r.TNV_Billing_hold_reason__c, SBQQ__ChargeType__c, TNV_Provisioning_Date__c, 
           blng__HoldBilling__c, blng__InvoiceRunProcessingStatus__c, blng__LastChargeToDate__c,
           blng__NextChargeDate__c, blng__NextBillingDate__c, blng__BillThroughDateOverride__c,
           TNV_Billing_hold_reason__c, Id, ServiceDate, SBQQ__RequiredBy__r.ServiceDate, Quantity, 
           TNV_AmendIdentifierRef__c, TNV_External_Error_Message__c, TNV_Processed_Polling_Count__c, 
           TNV_Provisioning_Status__c, TNV_Provisioning_Method__c, TNV_Hold_Released__c, 
           SBQQ__ContractAction__c, SBQQ__RevisedOrderProduct__c, SBQQ__RevisedOrderProduct__r.TNV_Provisioning_Status__c, 
           SBQQ__RequiredBy__c, Product2.TNV_Tekla_Dependent_Product_Codes__c, OrderId, 
           SBQQ__RequiredBy__r.TNV_Provisioning_Method__c, Order.Type, TNV_Renewal_Sequence_OrderItem__c, 
           SBQQ__OrderedQuantity__c, SBQQ__RevisedOrderProduct__r.SBQQ__RequiredBy__c, 
           SBQQ__QuoteLine__r.SBQQ__Quote__r.TNV_Display_Message__c, TNV_PC_Original_Quantity__c, 
           SBQQ__QuoteLine__r.TNV_Amend_Order_Item__c, SBQQ__QuoteLine__r.SBQQ__Quote__r.TNV_Systematic_Update__c, 
           TNV_Previous_Order_Product__c, TNV_BeforeorAfterT__c, TNV_Previous_Order_Product__r.TNV_Provisioning_Status__c
    FROM OrderItem 
    WHERE OrderId = :orderId
    """

def get_provisioning_staging_query():
    """Returns SOQL query for provisioning staging batch"""
    return """
    SELECT Id, OrderId, TNV_Provisioning_Status__c, TNV_Mulesoft_Contract_Action__c, 
           TNV_Quantity_for_Provisioning__c, SBQQ__ContractAction__c, TNV_Provisioning_Method__c, 
           TNV_Amendment_Reasons_Code__c, Order.Type, 
           SBQQ__QuoteLine__r.TNV_Upgraded_Downgraded_Subscription__r.Total_Quantity__c, 
           SBQQ__OrderedQuantity__c, 
           SBQQ__QuoteLine__r.TNV_Upgraded_Downgraded_Subscription__r.SBQQ__Quantity__c,
           (SELECT Id FROM Provisioning_Details1__r), 
           Order.AccountId, TNV_Technical_Admin__c, Product2.ProductCode, TNV_Renewal_Sequence_OrderItem__c
    FROM OrderItem 
    WHERE OrderId = :orderId
    """

def get_contract_association_apex(order_id):
    """Returns Apex code for contract association batch"""
    return f"""
    String orderId = '{order_id}';
    List<Order> orderList = [{get_contract_association_query()}];
    if (!orderList.isEmpty()) {{
        TNV_ContractAssociationBatch contractBatch = new TNV_ContractAssociationBatch();
        contractBatch.execute(null, orderList);
    }}
    """

def get_order_queueing_apex(order_id):
    """Returns Apex code for order queueing batch"""
    return f"""
    String orderId = '{order_id}';
    List<OrderItem> queueingOrderItems = [{get_order_queueing_query()}];
    if (!queueingOrderItems.isEmpty()) {{
        TNV_BatchQueueingOrderItems queueingBatch = new TNV_BatchQueueingOrderItems();
        queueingBatch.execute(null, queueingOrderItems);
    }}
    """

def get_provisioning_staging_apex(order_id):
    """Returns Apex code for provisioning staging batch"""
    return f"""
    String orderId = '{order_id}';
    List<OrderItem> stagingOrderItems = [{get_provisioning_staging_query()}];
    if (!stagingOrderItems.isEmpty()) {{
        TNV_ProvisioningStagingBatch stagingBatch = new TNV_ProvisioningStagingBatch();
        stagingBatch.execute(null, stagingOrderItems);
    }}
    """

def get_provisioning_completion_apex(order_id):
    """Returns Apex code for provisioning completion batch"""
    return f"""
    String orderId = '{order_id}';
    List<TNV_DX_Staging__c> stagingRecords = [
        SELECT Id, TNV_Action__c, TNV_Order_Product_ID__c, TNV_Order_Product_ID__r.OrderId, 
               TNV_Provisioning_Status__c, TNV_Quantity__c, TNV_EMS_Job_Id__c, MYT_EMS_PK_ID__c, 
               TNV_Order_Product_ID__r.Order.Type, TNV_Order_Product_ID__r.TNV_Partial_Renewal_Rev_Lic_Notification__c, 
               TNV_Error_Type__c, TNV_Provisioning_Backup_End_Date__c, TNV_Provisioned_Date__c, 
               TNV_Provisioning_Backup_Start_Date__c, TNV_Provisioning_Method__c, TNV_Entitlement_ID__c, 
               TNV_Entitlement_Line_ID__c, TNV_PS_SKU__c, TNV_Is_PD_Processed__c, TNV_Provisioning_Error_Message__c, 
               TNV_Contract_Action__c, TNV_Revoked_Licensed_Ids__c, TNV_Order_Product_ID__r.SBQQ__RequiredBy__c, 
               TNV_Order_ID__r.TNV_Legal_Entity__r.TNV_Time_Zone__c, TNV_Order_Product_ID__r.TNV_LEStartDateTime__c, 
               TNV_Order_Product_ID__r.TNV_LEEndDateTime__c
        FROM TNV_DX_Staging__c 
        WHERE TNV_Order_Product_ID__r.OrderId = :orderId
    ];
    
    if (!stagingRecords.isEmpty()) {{
        TNV_ProvisioningCompleteORFailBatch completeOrFailBatch = new TNV_ProvisioningCompleteORFailBatch();
        completeOrFailBatch.processedOrderIds = new Set<Id>();
        completeOrFailBatch.execute(null, stagingRecords);
    }}
    """