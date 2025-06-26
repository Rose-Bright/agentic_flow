# Telecom Email Support Flow - Phone Number Management

```mermaid
flowchart TD
    Email[Email Request<br/>Phone Disconnect/Add] --> EmailValidator[Email Validation Agent]
    
    EmailValidator --> ValidEmail{Email Valid &<br/>Customer Match?}
    
    ValidEmail -->|No| EmailReply[Send Email Reply<br/>Request Clarification]
    ValidEmail -->|Yes| TelecomAgent[Telecom Service Agent]
    
    TelecomAgent --> ExtractInfo[Extract Phone Numbers<br/>& Service Request]
    
    ExtractInfo --> ValidateNumbers{Phone Numbers<br/>Valid & In Profile?}
    
    ValidateNumbers -->|Invalid/Missing| EmailReply2[Send Email Reply<br/>Invalid Number Info]
    
    ValidateNumbers -->|Valid| ProcessRequest[Process Service Request]
    
    ProcessRequest --> CheckAction{Request Type}
    
    CheckAction -->|Disconnect| DisconnectFlow[Validate Disconnect<br/>Permissions]
    CheckAction -->|Add| AddFlow[Validate Add<br/>Capacity & Eligibility]
    
    DisconnectFlow --> CreateTicket[Create SmartPath Ticket<br/>Disconnect Request]
    AddFlow --> CreateTicket2[Create SmartPath Ticket<br/>Add Line Request]
    
    CreateTicket --> EmailConfirmation[Send Email Confirmation<br/>Ticket Created]
    CreateTicket2 --> EmailConfirmation
    
    EmailConfirmation --> HumanAgent[Human Agent<br/>Service Center]
    
    style TelecomAgent fill:#e1f5fe
    style EmailValidator fill:#f3e5f5
    style HumanAgent fill:#e8f5e8
```

## Agent Assignment

**Primary Agent**: `TelecomServiceAgent` (specialized customer service agent)

## Required Tools

1. **Email Validation Tools**
   - `validate_email_format`
   - `lookup_customer_by_email` 
   - `send_email_reply`

2. **Phone Number Management Tools**
   - `validate_phone_number`
   - `get_customer_phone_services`
   - `check_disconnect_eligibility`
   - `check_add_line_capacity`

3. **Ticketing System Tools**
   - `create_smartpath_ticket`
   - `add_ticket_notes`
   - `set_ticket_priority`

4. **Customer Profile Tools**
   - `get_customer_profile`
   - `update_customer_notes`
   - `log_customer_interaction`

## Workflow Steps

1. **Email Validation** - Verify sender email and match to customer profile
2. **Information Extraction** - Parse phone numbers and service request details
3. **Validation** - Confirm phone numbers exist in customer profile
4. **Service Processing** - Handle disconnect/add requests with business rules
5. **Ticket Creation** - Generate SmartPath tickets with detailed notes
6. **Email Response** - Send confirmation or clarification requests
7. **Human Handoff** - Queue for service center with complete context