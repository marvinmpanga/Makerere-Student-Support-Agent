# Component Interfaces

This document specifies the exact JSON input/output contracts at the major component boundaries shown in the Component Architecture (Diagram 03).

## 1. REST API -> Authentication Service

**Purpose**: Validate the identity of the incoming request.
**Direction**: Incoming HTTP request reaches the API and is delegated to Auth.

### Input
- Extracted from HTTP headers.
```json
{
  "Authorization": "Bearer <jwt_token>",
  "X-Student-Id": "123456"
}
```

### Output
```json
{
  "is_authenticated": true,
  "student_id": "123456",
  "roles": ["undergrad_student"],
  "token_expires_at": "2024-05-20T14:00:00Z"
}
```

## 2. Authentication Service -> Session Context Manager

**Purpose**: Load or establish the conversation session for an authenticated user.

### Input
```json
{
  "student_id": "123456",
  "provided_session_id": "sess_987abc" // optional
}
```

### Output
```json
{
  "session_id": "sess_987abc",
  "is_new_session": false,
  "history_length": 4,
  "student_context": {
    "student_id": "123456"
  }
}
```

## 3. Agent Orchestrator -> Tool Request Validator

**Purpose**: The LLM proposed a tool call; the validator must check the schema and RBAC before execution.

### Input
```json
{
  "tool_name": "get_student_status",
  "proposed_arguments": {
    "student_id": "123456"
  },
  "session_context": {
    "student_id": "123456",
    "roles": ["undergrad_student"]
  }
}
```

### Output
```json
{
  "is_valid": true,
  "is_authorized": true,
  "validated_payload": {
    "student_id": "123456"
  },
  "error_message": null
}
```

## 4. Tool Validator -> Student Record Tool

**Purpose**: Execution of the deterministic read-only lookup.

### Input (Matches GetStudentStatusRequest)
```json
{
  "student_id": "123456"
}
```

### Output (Matches GetStudentStatusResponse)
```json
{
  "student_id": "123456",
  "status": "Enrolled",
  "financial_hold": false,
  "academic_warning": false
}
```

## 5. Tool Validator -> Ticket Management Tool

**Purpose**: Execution of the deterministic ticket drafting logic (no persistence yet).

### Input (Matches DraftSupportTicketRequest)
```json
{
  "student_id": "123456",
  "issue_category": "Financial",
  "issue_description": "I need help understanding my tuition balance.",
  "priority": "Normal"
}
```

### Output (Matches DraftSupportTicketResponse)
```json
{
  "ticket_id": "TKT-123456-7890",
  "status": "Drafted",
  "message": "Successfully drafted a Financial ticket for student 123456.",
  "student_confirmation_required": true
}
```
