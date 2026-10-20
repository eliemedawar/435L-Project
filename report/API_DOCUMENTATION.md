# 8. Merged API Documentation (Marc Bteich)

The following endpoint inventory is extracted from the actual route source. Request examples and negative tests are in the merged Postman collection. Roles shown are the route-level checks; object-level checks in Elie’s services still apply.

Public authentication uses Authorization: Bearer <JWT>. Internal endpoints require X-Service-Key. JSON writes use Content-Type: application/json. Success: {status: success, message, data}; errors: {status: error, message}. Typical errors: 400 invalid input, 401 absent/invalid credentials, 403 insufficient permission, 404 missing record, 409 database conflict, 503 unavailable dependency. A 409 is only expected when an applicable constraint exists.

## Users (Marc Bteich)

### POST /users/register (Marc Bteich)

Purpose: register user. Access: public. Authentication: Public.

Postman example: `POST {{base_users}}/users/register`.

Request body example (template; credentials remain private):

```json

{
  "full_name": "Rami Haddad",
  "username": "rami",
  "email": "rami@corp.com",
  "password": "{{user_password}}",
  "department": "Finance",
  "role": "user"
}

```

Executed response example: HTTP 201; Newman request "Register - regular user (self-registration)". Credentials are redacted.

```json

{
  "status": "success",
  "message": "User registered successfully",
  "data": {
    "id": 2,
    "full_name": "Rami Haddad",
    "username": "rami",
    "email": "rami@corp.com",
    "department": "Finance",
    "role": "user",
    "account_status": "Active",
    "created_at": "2026-10-20T12:08:48Z",
    "last_login": null
  }
}

```

### POST /users/login (Marc Bteich)

Purpose: login. Access: public. Authentication: Public.

Postman example: `POST {{base_users}}/users/login`.

Request body example (template; credentials remain private):

```json

{
  "username": "{{admin_username}}",
  "password": "{{admin_password}}"
}

```

Executed response example: HTTP 200; Newman request "Login - admin (success)". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Login successful",
  "data": {
    "token": "[REDACTED]",
    "token_type": "[REDACTED]",
    "user": {
      "id": 1,
      "full_name": "Local test admin",
      "username": "admin",
      "email": "admin@example.test",
      "department": "Lab",
      "role": "admin",
      "account_status": "Active",
      "created_at": "2026-10-20T12:08:43Z",
      "last_login": "2026-10-20T12:08:48Z"
    }
  }
}

```

### PUT /users/{user_id} (Marc Bteich)

Purpose: update user. Access: admin,user. Authentication: Bearer JWT.

Path parameters: user_id. IDs must identify existing records.

Postman example: `PUT {{base_users}}/users/{{user_id}}`.

Request body example (template; credentials remain private):

```json

{
  "department": "Accounting",
  "full_name": "Rami Haddad"
}

```

Executed response example: HTTP 200; Newman request "Update own info - regular user". Credentials are redacted.

```json

{
  "status": "success",
  "message": "User updated successfully",
  "data": {
    "id": 2,
    "full_name": "Rami Haddad",
    "username": "rami",
    "email": "rami@corp.com",
    "department": "Accounting",
    "role": "user",
    "account_status": "Active",
    "created_at": "2026-10-20T12:08:48Z",
    "last_login": "2026-10-20T12:08:50Z"
  }
}

```

### DELETE /users/{user_id} (Marc Bteich)

Purpose: delete user. Access: admin. Authentication: Bearer JWT.

Path parameters: user_id. IDs must identify existing records.

Postman example: `DELETE {{base_users}}/users/{{temp_user_id}}`.

Executed response example: HTTP 200; Newman request "Delete user - admin (success)". Credentials are redacted.

```json

{
  "status": "success",
  "message": "User 5 deleted successfully",
  "data": null
}

```

### GET /users (Marc Bteich)

Purpose: get all users. Access: admin,auditor. Authentication: Bearer JWT.

Postman example: `GET {{base_users}}/users`.

Executed response example: HTTP 200; Newman request "Get all users - admin". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Users retrieved successfully",
  "data": {
    "count": 5,
    "users": [
      {
        "id": 1,
        "full_name": "Local test admin",
        "username": "admin",
        "email": "admin@example.test",
        "department": "Lab",
        "role": "admin",
        "account_status": "Active",
        "created_at": "2026-10-20T12:08:43Z",
        "last_login": "2026-10-20T12:08:48Z"
      },
      {
        "id": 2,
        "full_name": "Rami Haddad",
        "username": "rami",
        "email": "rami@corp.com",
        "department": "Finance",
        "role": "user",
        "account_status": "Active",
        "created_at": "2026-10-20T12:08:48Z",
        "last_login": "2026-10-20T12:08:50Z"
      },
      {
        "id": 3,
        "full_name": "Lara Khoury",
        "username": "lara",
        "email": "lara@corp.com",
        "department": "SOC",
        "role": "analyst",
        "account_status": "Active",
        "created_at": "2026-10-20T12:08:49Z",
        "last_login": "2026-10-20T12:08:50Z"
      },
      {
        "id": 4,
        "full_name": "Nadia Saab",
        "username": "nadia",
        "email": "nadia@corp.com",
        "department": "Compliance",
        "role": "auditor",
        "account_status": "Active",
        "created_at": "2026-10-20T12:08:49Z",
        "last_login": "2026-10-20T12:08:51Z"
      },
      {
        "id": 5,
        "full_name": "Temp Employee",
        "username": "temp.employee",
        "email": "temp@corp.com",
        "department": "HR",
        "role": "user",
        "account_status": "Active",
        "created_at": "2026-10-20T12:08:49Z",
        "last_login": null
      }
    ]
  }
}

```

### GET /users/{username} (Marc Bteich)

Purpose: get user by username. Access: admin,auditor,user. Authentication: Bearer JWT.

Path parameters: username. IDs must identify existing records.

Postman example: `GET {{base_users}}/users/lara`.

Executed response example: HTTP 200; Newman request "Get user by username - existing". Credentials are redacted.

```json

{
  "status": "success",
  "message": "User retrieved successfully",
  "data": {
    "id": 3,
    "full_name": "Lara Khoury",
    "username": "lara",
    "email": "lara@corp.com",
    "department": "SOC",
    "role": "analyst",
    "account_status": "Active",
    "created_at": "2026-10-20T12:08:49Z",
    "last_login": "2026-10-20T12:08:50Z"
  }
}

```

### GET /internal/users/{user_id} (Marc Bteich)

Purpose: internal get user. Access: internal service only. Authentication: Service key.

Path parameters: user_id. IDs must identify existing records.

### GET /internal/users (Marc Bteich)

Purpose: internal list users. Access: internal service only. Authentication: Service key.

### GET /internal/stats (Marc Bteich)

Purpose: internal stats. Access: internal service only. Authentication: Service key.

Postman example: `GET {{base_assets}}/internal/stats`.

Executed response example: HTTP 200; Newman request "Internal statistics". Credentials are redacted.

```json

{
  "status": "success",
  "message": "OK",
  "data": {
    "total_assets": 6,
    "critical_assets": 1,
    "by_type": {
      "Server": 1,
      "Workstation": 1,
      "Database": 1,
      "Application": 1,
      "Network Device": 1,
      "Cloud Resource": 1
    }
  }
}

```

## Assets (Marc Bteich)

### POST /assets (Marc Bteich)

Purpose: create asset. Access: admin. Authentication: Bearer JWT.

Postman example: `POST {{base_assets}}/assets`.

Request body example (template; credentials remain private):

```json

{
  "asset_name": "Postman Lab Server",
  "asset_type": "Server",
  "ip_address": "192.0.2.10",
  "operating_system": "Linux",
  "department": "Security",
  "owner_id": {{owner_id}},
  "location": "Lab",
  "criticality": "Critical",
  "status": "Active"
}

```

Executed response example: HTTP 201; Newman request "Create asset". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Asset created successfully",
  "data": {
    "id": 1,
    "asset_name": "Postman Lab Server",
    "asset_type": "Server",
    "ip_address": "192.0.2.10",
    "operating_system": "Linux",
    "owner_id": 1,
    "department": "Security",
    "location": "Lab",
    "criticality": "Critical",
    "status": "Active"
  }
}

```

### PUT /assets/{asset_id} (Marc Bteich)

Purpose: update asset. Access: admin. Authentication: Bearer JWT.

Path parameters: asset_id. IDs must identify existing records.

Postman example: `PUT {{base_assets}}/assets/{{asset_id}}`.

Request body example (template; credentials remain private):

```json

{
  "asset_name": "Updated Postman Server",
  "department": "IT",
  "criticality": "High",
  "status": "Under Maintenance"
}

```

Executed response example: HTTP 200; Newman request "Update asset (admin)". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Asset updated successfully",
  "data": {
    "id": 1,
    "asset_name": "Updated Postman Server",
    "asset_type": "Server",
    "ip_address": "192.0.2.10",
    "operating_system": "Linux",
    "owner_id": 1,
    "department": "IT",
    "location": "Lab",
    "criticality": "High",
    "status": "Under Maintenance"
  }
}

```

### DELETE /assets/{asset_id} (Marc Bteich)

Purpose: delete asset. Access: admin. Authentication: Bearer JWT.

Path parameters: asset_id. IDs must identify existing records.

Postman example: `DELETE {{base_assets}}/assets/{{asset_id}}`.

Executed response example: HTTP 200; Newman request "Delete asset (admin)". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Asset 1 deleted successfully",
  "data": null
}

```

### GET /assets (Marc Bteich)

Purpose: list assets. Access: admin,auditor. Authentication: Bearer JWT.

Postman example: `GET {{base_assets}}/assets`.

Executed response example: HTTP 200; Newman request "List assets (auditor)". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Assets retrieved successfully",
  "data": {
    "count": 6,
    "assets": [
      {
        "id": 1,
        "asset_name": "Postman Lab Server",
        "asset_type": "Server",
        "ip_address": "192.0.2.10",
        "operating_system": "Linux",
        "owner_id": 1,
        "department": "Security",
        "location": "Lab",
        "criticality": "Critical",
        "status": "Active"
      },
      {
        "id": 2,
        "asset_name": "Postman Workstation",
        "asset_type": "Workstation",
        "ip_address": "192.0.2.10",
        "operating_system": "Linux",
        "owner_id": 1,
        "department": "Security",
        "location": "Lab",
        "criticality": "Low",
        "status": "Active"
      },
      {
        "id": 3,
        "asset_name": "Postman Database",
        "asset_type": "Database",
        "ip_address": "192.0.2.10",
        "operating_system": "Linux",
        "owner_id": 1,
        "department": "Security",
        "location": "Lab",
        "criticality": "Medium",
        "status": "Inactive"
      },
      {
        "id": 4,
        "asset_name": "Postman Application",
        "asset_type": "Application",
        "ip_address": "192.0.2.10",
        "operating_system": "Linux",
        "owner_id": 1,
        "department": "Security",
        "location": "Lab",
        "criticality": "High",
        "status": "Under Maintenance"
      },
      {
        "id": 5,
        "asset_name": "Postman Network Device",
        "asset_type": "Network Device",
        "ip_address": "192.0.2.10",
        "operating_system": "Linux",
        "owner_id": 1,
        "department": "Security",
        "location": "Lab",
        "criticality": "High",
        "status": "Active"
      },
      {
        "id": 6,
        "asset_name": "Postman Cloud Resource",
        "asset_type": "Cloud Resource",
        "ip_address": "192.0.2.10",
        "operating_system": "Linux",
        "owner_id": 1,
        "department": "Security",
        "location": "Lab",
        "criticality": "Critical",
        "status": "Active"
      }
    ]
  }
}

```

### GET /assets/{asset_id} (Marc Bteich)

Purpose: get asset. Access: admin,analyst,auditor. Authentication: Bearer JWT.

Path parameters: asset_id. IDs must identify existing records.

Postman example: `GET {{base_assets}}/assets/{{asset_id}}`.

Executed response example: HTTP 200; Newman request "Get asset before update (analyst)". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Asset retrieved successfully",
  "data": {
    "id": 1,
    "asset_name": "Postman Lab Server",
    "asset_type": "Server",
    "ip_address": "192.0.2.10",
    "operating_system": "Linux",
    "owner_id": 1,
    "department": "Security",
    "location": "Lab",
    "criticality": "Critical",
    "status": "Active"
  }
}

```

### GET /assets/search (Marc Bteich)

Purpose: search assets. Access: admin,analyst,auditor. Authentication: Bearer JWT.

Postman example: `GET {{base_assets}}/assets/search?name=Postman`.

Search parameters demonstrated: criticality, department, ip, name, type; consult field rules below for allowed keys.

Executed response example: HTTP 200; Newman request "Search by name". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Asset search completed",
  "data": {
    "count": 6,
    "assets": [
      {
        "id": 1,
        "asset_name": "Updated Postman Server",
        "asset_type": "Server",
        "ip_address": "192.0.2.10",
        "operating_system": "Linux",
        "owner_id": 1,
        "department": "IT",
        "location": "Lab",
        "criticality": "High",
        "status": "Under Maintenance"
      },
      {
        "id": 2,
        "asset_name": "Postman Workstation",
        "asset_type": "Workstation",
        "ip_address": "192.0.2.10",
        "operating_system": "Linux",
        "owner_id": 1,
        "department": "Security",
        "location": "Lab",
        "criticality": "Low",
        "status": "Active"
      },
      {
        "id": 3,
        "asset_name": "Postman Database",
        "asset_type": "Database",
        "ip_address": "192.0.2.10",
        "operating_system": "Linux",
        "owner_id": 1,
        "department": "Security",
        "location": "Lab",
        "criticality": "Medium",
        "status": "Inactive"
      },
      {
        "id": 4,
        "asset_name": "Postman Application",
        "asset_type": "Application",
        "ip_address": "192.0.2.10",
        "operating_system": "Linux",
        "owner_id": 1,
        "department": "Security",
        "location": "Lab",
        "criticality": "High",
        "status": "Under Maintenance"
      },
      {
        "id": 5,
        "asset_name": "Postman Network Device",
        "asset_type": "Network Device",
        "ip_address": "192.0.2.10",
        "operating_system": "Linux",
        "owner_id": 1,
        "department": "Security",
        "location": "Lab",
        "criticality": "High",
        "status": "Active"
      },
      {
        "id": 6,
        "asset_name": "Postman Cloud Resource",
        "asset_type": "Cloud Resource",
        "ip_address": "192.0.2.10",
        "operating_system": "Linux",
        "owner_id": 1,
        "department": "Security",
        "location": "Lab",
        "criticality": "Critical",
        "status": "Active"
      }
    ]
  }
}

```

### GET /internal/stats (Marc Bteich)

Purpose: internal stats. Access: internal service only. Authentication: Service key.

Postman example: `GET {{base_assets}}/internal/stats`.

Executed response example: HTTP 200; Newman request "Internal statistics". Credentials are redacted.

```json

{
  "status": "success",
  "message": "OK",
  "data": {
    "total_assets": 6,
    "critical_assets": 1,
    "by_type": {
      "Server": 1,
      "Workstation": 1,
      "Database": 1,
      "Application": 1,
      "Network Device": 1,
      "Cloud Resource": 1
    }
  }
}

```

### GET /internal/assets/{asset_id} (Marc Bteich)

Purpose: internal get asset. Access: internal service only. Authentication: Service key.

Path parameters: asset_id. IDs must identify existing records.

Postman example: `GET {{base_assets}}/internal/assets/{{asset_id}}`.

Executed response example: HTTP 200; Newman request "Internal asset lookup". Credentials are redacted.

```json

{
  "status": "success",
  "message": "OK",
  "data": {
    "id": 1,
    "asset_name": "Updated Postman Server",
    "asset_type": "Server",
    "ip_address": "192.0.2.10",
    "operating_system": "Linux",
    "owner_id": 1,
    "department": "IT",
    "location": "Lab",
    "criticality": "High",
    "status": "Under Maintenance"
  }
}

```

## Incidents (Marc Bteich)

### POST /incidents (Marc Bteich)

Purpose: create incident. Access: admin,user. Authentication: Bearer JWT.

Postman example: `POST {{base_incidents}}/incidents`.

Request body example (template; credentials remain private):

```json

{
  "title": "Phishing email received",
  "description": "Employee clicked a link in a fake invoice email",
  "category": "Phishing",
  "severity": "Medium",
  "asset_id": {{asset_id}}
}

```

Executed response example: HTTP 201; Newman request "Create - regular user (Medium)". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Incident created successfully",
  "data": {
    "id": 1,
    "title": "Phishing email received",
    "description": "Employee clicked a link in a fake invoice email",
    "category": "Phishing",
    "severity": "Medium",
    "reporter_id": 2,
    "asset_id": 7,
    "assigned_analyst_id": null,
    "status": "Open",
    "created_at": "2026-10-20T12:08:59Z",
    "resolved_at": null
  }
}

```

### GET /incidents (Marc Bteich)

Purpose: get all incidents. Access: admin,auditor. Authentication: Bearer JWT.

Postman example: `GET {{base_incidents}}/incidents`.

Executed response example: HTTP 200; Newman request "Get all - admin". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Incidents retrieved successfully",
  "data": {
    "count": 4,
    "incidents": [
      {
        "id": 4,
        "title": "Port scan detected",
        "description": "Firewall blocked a port scan",
        "category": "Other",
        "severity": "Low",
        "reporter_id": 2,
        "asset_id": 7,
        "assigned_analyst_id": null,
        "status": "Open",
        "created_at": "2026-10-20T12:08:59Z",
        "resolved_at": null
      },
      {
        "id": 3,
        "title": "Brute force on HR database",
        "description": "Thousands of failed logins from one IP",
        "category": "Unauthorized Access",
        "severity": "High",
        "reporter_id": 1,
        "asset_id": 7,
        "assigned_analyst_id": null,
        "status": "Open",
        "created_at": "2026-10-20T12:08:59Z",
        "resolved_at": null
      },
      {
        "id": 2,
        "title": "Ransomware on web server",
        "description": "Files encrypted, ransom note found",
        "category": "Malware",
        "severity": "Critical",
        "reporter_id": 1,
        "asset_id": 7,
        "assigned_analyst_id": null,
        "status": "Open",
        "created_at": "2026-10-20T12:08:59Z",
        "resolved_at": null
      },
      {
        "id": 1,
        "title": "Phishing email received",
        "description": "Employee clicked a link in a fake invoice email",
        "category": "Phishing",
        "severity": "Medium",
        "reporter_id": 2,
        "asset_id": 7,
        "assigned_analyst_id": null,
        "status": "Open",
        "created_at": "2026-10-20T12:08:59Z",
        "resolved_at": null
      }
    ]
  }
}

```

### GET /incidents/{incident_id} (Marc Bteich)

Purpose: get incident. Access: admin,auditor,analyst,user. Authentication: Bearer JWT.

Path parameters: incident_id. IDs must identify existing records.

Postman example: `GET {{base_incidents}}/incidents/{{incident_id}}`.

Executed response example: HTTP 200; Newman request "Get - reporter views own incident". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Incident retrieved successfully",
  "data": {
    "id": 1,
    "title": "Phishing email received",
    "description": "Employee clicked a link in a fake invoice email",
    "category": "Phishing",
    "severity": "Medium",
    "reporter_id": 2,
    "asset_id": 7,
    "assigned_analyst_id": null,
    "status": "Open",
    "created_at": "2026-10-20T12:08:59Z",
    "resolved_at": null,
    "investigation_notes": []
  }
}

```

### PUT /incidents/{incident_id}/assign (Marc Bteich)

Purpose: assign incident. Access: admin. Authentication: Bearer JWT.

Path parameters: incident_id. IDs must identify existing records.

Postman example: `PUT {{base_incidents}}/incidents/{{incident_id}}/assign`.

Request body example (template; credentials remain private):

```json

{
  "analyst_id": {{analyst_id}}
}

```

Executed response example: HTTP 200; Newman request "Assign - admin to analyst". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Incident assigned successfully",
  "data": {
    "id": 1,
    "title": "Phishing email received",
    "description": "Employee clicked a link in a fake invoice email",
    "category": "Phishing",
    "severity": "Medium",
    "reporter_id": 2,
    "asset_id": 7,
    "assigned_analyst_id": 3,
    "status": "Open",
    "created_at": "2026-10-20T12:08:59Z",
    "resolved_at": null
  }
}

```

### PUT /incidents/{incident_id}/status (Marc Bteich)

Purpose: update incident status. Access: admin,analyst. Authentication: Bearer JWT.

Path parameters: incident_id. IDs must identify existing records.

Postman example: `PUT {{base_incidents}}/incidents/{{incident_id}}/status`.

Request body example (template; credentials remain private):

```json

{
  "status": "Under Investigation"
}

```

Executed response example: HTTP 200; Newman request "Open -> Under Investigation". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Incident status updated to 'Under Investigation'",
  "data": {
    "id": 1,
    "title": "Phishing email received",
    "description": "Employee clicked a link in a fake invoice email",
    "category": "Phishing",
    "severity": "Medium",
    "reporter_id": 2,
    "asset_id": 7,
    "assigned_analyst_id": 3,
    "status": "Under Investigation",
    "created_at": "2026-10-20T12:08:59Z",
    "resolved_at": null
  }
}

```

### POST /incidents/{incident_id}/notes (Marc Bteich)

Purpose: add investigation note. Access: admin,analyst. Authentication: Bearer JWT.

Path parameters: incident_id. IDs must identify existing records.

Postman example: `POST {{base_incidents}}/incidents/{{incident2_id}}/notes`.

Request body example (template; credentials remain private):

```json

{
  "content": "Analysis: ransomware strain identified as LockBit"
}

```

Executed response example: HTTP 201; Newman request "Add note - assigned analyst". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Investigation note added successfully",
  "data": {
    "id": 2,
    "title": "Ransomware on web server",
    "description": "Files encrypted, ransom note found",
    "category": "Malware",
    "severity": "Critical",
    "reporter_id": 1,
    "asset_id": 7,
    "assigned_analyst_id": 3,
    "status": "Open",
    "created_at": "2026-10-20T12:08:59Z",
    "resolved_at": null,
    "investigation_notes": [
      {
        "id": 1,
        "incident_id": 2,
        "analyst_id": 3,
        "content": "Analysis: ransomware strain identified as LockBit",
        "created_at": "2026-10-20T12:09:01Z"
      }
    ]
  }
}

```

### GET /internal/stats (Marc Bteich)

Purpose: internal stats. Access: internal service only. Authentication: Service key.

Postman example: `GET {{base_assets}}/internal/stats`.

Executed response example: HTTP 200; Newman request "Internal statistics". Credentials are redacted.

```json

{
  "status": "success",
  "message": "OK",
  "data": {
    "total_assets": 6,
    "critical_assets": 1,
    "by_type": {
      "Server": 1,
      "Workstation": 1,
      "Database": 1,
      "Application": 1,
      "Network Device": 1,
      "Cloud Resource": 1
    }
  }
}

```

## Threats (Marc Bteich)

### POST /threats (Marc Bteich)

Purpose: create. Access: admin. Authentication: Bearer JWT.

Postman example: `POST {{base_threats}}/threats`.

Request body example (template; credentials remain private):

```json

{
  "threat_type": "Domain",
  "threat_value": "{{indicator_domain}}",
  "description": "Synthetic Postman lab indicator",
  "severity": "Critical",
  "source": "Postman lab"
}

```

Executed response example: HTTP 201; Newman request "Create Critical threat". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Threat created",
  "data": {
    "id": 1,
    "threat_type": "Domain",
    "threat_value": "postman.example.test",
    "description": "Synthetic Postman lab indicator",
    "severity": "Critical",
    "source": "Postman lab",
    "date_added": "2026-10-20T12:09:03Z"
  }
}

```

### GET /threats (Marc Bteich)

Purpose: list all. Access: admin,analyst,auditor. Authentication: Bearer JWT.

Postman example: `GET {{base_threats}}/threats`.

Executed response example: HTTP 200; Newman request "List threats". Credentials are redacted.

```json

{
  "status": "success",
  "message": "OK",
  "data": {
    "count": 1,
    "threats": [
      {
        "id": 1,
        "threat_type": "Domain",
        "threat_value": "postman.example.test",
        "description": "Synthetic Postman lab indicator",
        "severity": "Critical",
        "source": "Postman lab",
        "date_added": "2026-10-20T12:09:03Z"
      }
    ]
  }
}

```

### GET /threats/{record_id} (Marc Bteich)

Purpose: get. Access: admin,analyst,auditor. Authentication: Bearer JWT.

Path parameters: record_id. IDs must identify existing records.

Postman example: `GET {{base_threats}}/threats/{{threat_id}}`.

Executed response example: HTTP 200; Newman request "Get threat". Credentials are redacted.

```json

{
  "status": "success",
  "message": "OK",
  "data": {
    "id": 1,
    "threat_type": "Domain",
    "threat_value": "postman.example.test",
    "description": "Synthetic Postman lab indicator",
    "severity": "Critical",
    "source": "Postman lab",
    "date_added": "2026-10-20T12:09:03Z"
  }
}

```

### GET /threats/search (Marc Bteich)

Purpose: search. Access: admin,analyst. Authentication: Bearer JWT.

Postman example: `GET {{base_threats}}/threats/search?type=Domain`.

Search parameters demonstrated: severity, source, type, value; consult field rules below for allowed keys.

Executed response example: HTTP 200; Newman request "Search type=Domain". Credentials are redacted.

```json

{
  "status": "success",
  "message": "OK",
  "data": {
    "count": 1,
    "threats": [
      {
        "id": 1,
        "threat_type": "Domain",
        "threat_value": "postman.example.test",
        "description": "Synthetic Postman lab indicator",
        "severity": "Critical",
        "source": "Postman lab",
        "date_added": "2026-10-20T12:09:03Z"
      }
    ]
  }
}

```

### PUT /threats/{record_id} (Marc Bteich)

Purpose: update. Access: admin. Authentication: Bearer JWT.

Path parameters: record_id. IDs must identify existing records.

Postman example: `PUT {{base_threats}}/threats/{{threat_id}}`.

Request body example (template; credentials remain private):

```json

{
  "description": "Reviewed",
  "severity": "High",
  "source": "Reviewed lab"
}

```

Executed response example: HTTP 200; Newman request "Update threat". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Threat updated",
  "data": {
    "id": 1,
    "threat_type": "Domain",
    "threat_value": "postman.example.test",
    "description": "Reviewed",
    "severity": "High",
    "source": "Reviewed lab",
    "date_added": "2026-10-20T12:09:03Z"
  }
}

```

### DELETE /threats/{record_id} (Marc Bteich)

Purpose: delete. Access: admin. Authentication: Bearer JWT.

Path parameters: record_id. IDs must identify existing records.

Postman example: `DELETE {{base_threats}}/threats/{{threat_id}}`.

Executed response example: HTTP 200; Newman request "Delete threat". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Threat deleted",
  "data": null
}

```

### GET /internal/stats (Marc Bteich)

Purpose: stats. Access: internal service only. Authentication: Service key.

Postman example: `GET {{base_assets}}/internal/stats`.

Executed response example: HTTP 200; Newman request "Internal statistics". Credentials are redacted.

```json

{
  "status": "success",
  "message": "OK",
  "data": {
    "total_assets": 6,
    "critical_assets": 1,
    "by_type": {
      "Server": 1,
      "Workstation": 1,
      "Database": 1,
      "Application": 1,
      "Network Device": 1,
      "Cloud Resource": 1
    }
  }
}

```

## Logs (Marc Bteich)

### POST /logs (Marc Bteich)

Purpose: create log. Access: admin. Authentication: Bearer JWT.

Postman example: `POST {{base_logs}}/logs`.

Request body example (template; credentials remain private):

```json

{
  "user_id": {{user_id}},
  "action": "ACCOUNT_REVIEW",
  "description": "Quarterly review of account activity",
  "severity": "Information",
  "related_service": "users"
}

```

Executed response example: HTTP 201; Newman request "Create log - admin (Information)". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Log record created successfully",
  "data": {
    "id": 79,
    "user_id": 2,
    "username": "rami",
    "action": "ACCOUNT_REVIEW",
    "description": "Quarterly review of account activity",
    "severity": "Information",
    "related_service": "users",
    "timestamp": "2026-10-20T12:09:07Z"
  }
}

```

### GET /logs (Marc Bteich)

Purpose: get all logs. Access: admin,auditor. Authentication: Bearer JWT.

Postman example: `GET {{base_logs}}/logs`.

Executed response example: HTTP 200; Newman request "Get all logs - admin". Credentials are redacted.

Full response is retained without truncation in evidence/newman-combined.json for that request; large list output is omitted here for readability.

### GET /logs/search (Marc Bteich)

Purpose: search logs. Access: admin,auditor,analyst. Authentication: Bearer JWT.

Postman example: `GET {{base_logs}}/logs/search?service=assets`.

Search parameters demonstrated: action, date, date_from, date_to, service, severity, user; consult field rules below for allowed keys.

Executed response example: HTTP 200; Newman request "Inspect Assets audit records". Credentials are redacted.

```json

{
  "status": "success",
  "message": "7 log(s) match the search criteria",
  "data": {
    "count": 7,
    "logs": [
      {
        "id": 30,
        "user_id": 1,
        "username": "admin",
        "action": "ASSET_UPDATED",
        "description": "Updated asset 1: asset_name, criticality, department, status",
        "severity": "Information",
        "related_service": "assets",
        "timestamp": "2026-10-20T12:08:54Z"
      },
      {
        "id": 29,
        "user_id": 1,
        "username": "admin",
        "action": "ASSET_CREATED",
        "description": "Created asset 6",
        "severity": "Information",
        "related_service": "assets",
        "timestamp": "2026-10-20T12:08:54Z"
      },
      {
        "id": 28,
        "user_id": 1,
        "username": "admin",
        "action": "ASSET_CREATED",
        "description": "Created asset 5",
        "severity": "Information",
        "related_service": "assets",
        "timestamp": "2026-10-20T12:08:54Z"
      },
      {
        "id": 27,
        "user_id": 1,
        "username": "admin",
        "action": "ASSET_CREATED",
        "description": "Created asset 4",
        "severity": "Information",
        "related_service": "assets",
        "timestamp": "2026-10-20T12:08:54Z"
      },
      {
        "id": 26,
        "user_id": 1,
        "username": "admin",
        "action": "ASSET_CREATED",
        "description": "Created asset 3",
        "severity": "Information",
        "related_service": "assets",
        "timestamp": "2026-10-20T12:08:54Z"
      },
      {
        "id": 25,
        "user_id": 1,
        "username": "admin",
        "action": "ASSET_CREATED",
        "description": "Created asset 2",
        "severity": "Information",
        "related_service": "assets",
        "timestamp": "2026-10-20T12:08:54Z"
      },
      {
        "id": 24,
        "user_id": 1,
        "username": "admin",
        "action": "ASSET_CREATED",
        "description": "Created asset 1",
        "severity": "Information",
        "related_service": "assets",
        "timestamp": "2026-10-20T12:08:53Z"
      }
    ]
  }
}

```

### GET /logs/user/{user_id} (Marc Bteich)

Purpose: get logs by user. Access: admin,auditor. Authentication: Bearer JWT.

Path parameters: user_id. IDs must identify existing records.

Postman example: `GET {{base_logs}}/logs/user/{{user_id}}`.

Executed response example: HTTP 200; Newman request "Logs by user - user with logs". Credentials are redacted.

Full response is retained without truncation in evidence/newman-combined.json for that request; large list output is omitted here for readability.

### GET /logs/{log_id} (Marc Bteich)

Purpose: get log. Access: admin,auditor,analyst. Authentication: Bearer JWT.

Path parameters: log_id. IDs must identify existing records.

Postman example: `GET {{base_logs}}/logs/search?service=assets`.

Executed response example: HTTP 200; Newman request "Get log by id - admin". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Log retrieved successfully",
  "data": {
    "id": 79,
    "user_id": 2,
    "username": "rami",
    "action": "ACCOUNT_REVIEW",
    "description": "Quarterly review of account activity",
    "severity": "Information",
    "related_service": "users",
    "timestamp": "2026-10-20T12:09:07Z"
  }
}

```

### DELETE /logs/{log_id} (Marc Bteich)

Purpose: delete log. Access: admin. Authentication: Bearer JWT.

Path parameters: log_id. IDs must identify existing records.

Postman example: `DELETE {{base_logs}}/logs/{{log_id}}`.

Executed response example: HTTP 200; Newman request "Delete log - admin (success)". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Log 79 deleted successfully",
  "data": null
}

```

### GET /internal/stats (Marc Bteich)

Purpose: internal stats. Access: internal service only. Authentication: Service key.

Postman example: `GET {{base_assets}}/internal/stats`.

Executed response example: HTTP 200; Newman request "Internal statistics". Credentials are redacted.

```json

{
  "status": "success",
  "message": "OK",
  "data": {
    "total_assets": 6,
    "critical_assets": 1,
    "by_type": {
      "Server": 1,
      "Workstation": 1,
      "Database": 1,
      "Application": 1,
      "Network Device": 1,
      "Cloud Resource": 1
    }
  }
}

```

## Reports (Marc Bteich)

### GET /reports/summary (Marc Bteich)

Purpose: security summary report. Access: admin,auditor. Authentication: Bearer JWT.

Postman example: `GET {{base_reports}}/reports/summary`.

Executed response example: HTTP 200; Newman request "Summary - admin". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Security summary report generated",
  "data": {
    "report_type": "security summary",
    "generated_at": "2026-10-20T12:09:21Z",
    "generated_by": "admin",
    "users": 4,
    "assets": 6,
    "incidents": 4,
    "open_incidents": 3,
    "critical_incidents": 1,
    "threats": 0,
    "critical_threats": 0
  }
}

```

### GET /reports/incidents (Marc Bteich)

Purpose: incident report. Access: admin,auditor. Authentication: Bearer JWT.

Postman example: `GET {{base_reports}}/reports/incidents`.

Executed response example: HTTP 200; Newman request "Incident report - admin". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Incident report generated",
  "data": {
    "report_type": "incident",
    "generated_at": "2026-10-20T12:09:22Z",
    "generated_by": "admin",
    "total_incidents": 4,
    "open_incidents": 3,
    "unassigned_open_incidents": 2,
    "incidents_by_severity": {
      "Low": 1,
      "Medium": 1,
      "High": 1,
      "Critical": 1
    },
    "incidents_by_status": {
      "Open": 3,
      "Under Investigation": 0,
      "Mitigated": 0,
      "Resolved": 0,
      "Closed": 1
    },
    "incidents_by_category": {
      "Malware": 1,
      "Unauthorized Access": 1,
      "Phishing": 1,
      "Data Leakage": 0,
      "Account Compromise": 0,
      "Denial of Service": 0,
      "Other": 1
    }
  }
}

```

### GET /reports/activity (Marc Bteich)

Purpose: activity report. Access: admin,auditor. Authentication: Bearer JWT.

Postman example: `GET {{base_reports}}/reports/activity`.

Executed response example: HTTP 200; Newman request "Activity report - admin". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Activity report generated",
  "data": {
    "report_type": "activity",
    "generated_at": "2026-10-20T12:09:22Z",
    "generated_by": "admin",
    "total_user_activities": 144,
    "login_attempts": 38,
    "successful_logins": 36,
    "failed_login_attempts": 2,
    "failed_login_rate_percent": 5.3,
    "unauthorized_access_attempts": 44,
    "activities_by_severity": {
      "Information": 92,
      "Warning": 50,
      "Error": 0,
      "Critical": 2
    },
    "activities_by_service": {
      "assets": 18,
      "incidents": 20,
      "logs": 9,
      "notifications": 12,
      "playbooks": 13,
      "reports": 3,
      "threats": 6,
      "users": 52,
      "vulnerabilities": 11
    },
    "most_performed_actions": [
      {
        "action": "UNAUTHORIZED_ACCESS",
        "count": 44
      },
      {
        "action": "LOGIN_SUCCESS",
        "count": 36
      },
      {
        "action": "ASSET_CREATED",
        "count": 9
      },
      {
        "action": "ACTION_HISTORY_ARCHIVED",
        "count": 4
      },
      {
        "action": "INCIDENT_CREATED",
        "count": 4
      }
    ]
  }
}

```

### GET /reports/assets (Marc Bteich)

Purpose: assets. Access: admin,auditor. Authentication: Bearer JWT.

Postman example: `GET {{base_reports}}/reports/assets`.

Executed response example: HTTP 200; Newman request "Generate assets report (admin)". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Asset report generated",
  "data": {
    "report_type": "asset",
    "generated_at": "2026-10-20T12:09:24Z",
    "generated_by": "admin",
    "total_assets": 6,
    "critical_assets": 1,
    "assets_by_type": {
      "Server": 1,
      "Workstation": 1,
      "Database": 1,
      "Application": 1,
      "Network Device": 1,
      "Cloud Resource": 1
    }
  }
}

```

### GET /reports/threats (Marc Bteich)

Purpose: threats. Access: admin,auditor. Authentication: Bearer JWT.

Postman example: `GET {{base_reports}}/reports/threats`.

Executed response example: HTTP 200; Newman request "Generate threats report (admin)". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Threat report generated",
  "data": {
    "report_type": "threat",
    "generated_at": "2026-10-20T12:09:24Z",
    "generated_by": "admin",
    "total_threats": 0,
    "threats_by_severity": {
      "Low": 0,
      "Medium": 0,
      "High": 0,
      "Critical": 0
    },
    "threats_by_type": {
      "IP Address": 0,
      "Domain": 0,
      "File Hash": 0,
      "Malware Signature": 0,
      "Other": 0
    },
    "recently_added": []
  }
}

```

### GET /reports/vulnerabilities (Marc Bteich)

Purpose: vulnerabilities. Access: admin,auditor. Authentication: Bearer JWT.

Postman example: `GET {{base_reports}}/reports/vulnerabilities`.

Executed response example: HTTP 200; Newman request "Generate vulnerabilities report (admin)". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Vulnerability report generated",
  "data": {
    "report_type": "vulnerability",
    "generated_at": "2026-10-20T12:09:25Z",
    "generated_by": "admin",
    "total_vulnerabilities": 0,
    "critical_vulnerabilities": 0,
    "vulnerabilities_by_severity": {
      "Low": 0,
      "Medium": 0,
      "High": 0,
      "Critical": 0
    },
    "vulnerabilities_by_status": {
      "Open": 0,
      "Under Investigation": 0,
      "In Progress": 0,
      "Resolved": 0,
      "Closed": 0
    }
  }
}

```

## Vulnerabilities (Marc Bteich)

### POST /vulnerabilities (Marc Bteich)

Purpose: create. Access: admin. Authentication: Bearer JWT.

Postman example: `POST {{base_vulnerabilities}}/vulnerabilities`.

Request body example (template; credentials remain private):

```json

{
  "title": "Synthetic Postman vulnerability",
  "description": "Lab scenario only",
  "cve_id": "CVE-2026-12345",
  "cvss_score": 9.8,
  "severity": "Low",
  "asset_id": {{linked_asset_id}},
  "discovery_source": "Postman lab"
}

```

Executed response example: HTTP 201; Newman request "Link vulnerability". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Vulnerability created",
  "data": {
    "id": 1,
    "title": "Synthetic Postman vulnerability",
    "description": "Lab scenario only",
    "cve_id": "CVE-2026-12345",
    "cvss_score": 9.8,
    "severity": "Low",
    "asset_id": 7,
    "discovery_source": "Postman lab",
    "status": "Open",
    "created_at": "2026-10-20T12:08:57Z",
    "resolution_date": null
  }
}

```

### GET /vulnerabilities (Marc Bteich)

Purpose: list all. Access: admin,analyst,auditor. Authentication: Bearer JWT.

Postman example: `GET {{base_vulnerabilities}}/vulnerabilities`.

Executed response example: HTTP 200; Newman request "List vulnerabilities". Credentials are redacted.

```json

{
  "status": "success",
  "message": "OK",
  "data": {
    "count": 1,
    "vulnerabilities": [
      {
        "id": 1,
        "title": "Synthetic Postman vulnerability",
        "description": "Lab scenario only",
        "cve_id": "CVE-2026-12345",
        "cvss_score": 9.8,
        "severity": "Critical",
        "asset_id": 8,
        "discovery_source": "Postman lab",
        "status": "Open",
        "created_at": "2026-10-20T12:09:11Z",
        "resolution_date": null
      }
    ]
  }
}

```

### GET /vulnerabilities/{record_id} (Marc Bteich)

Purpose: get. Access: admin,analyst,auditor. Authentication: Bearer JWT.

Path parameters: record_id. IDs must identify existing records.

Postman example: `GET {{base_vulnerabilities}}/vulnerabilities/{{vulnerability_id}}`.

Executed response example: HTTP 200; Newman request "Get vulnerability". Credentials are redacted.

```json

{
  "status": "success",
  "message": "OK",
  "data": {
    "id": 1,
    "title": "Synthetic Postman vulnerability",
    "description": "Lab scenario only",
    "cve_id": "CVE-2026-12345",
    "cvss_score": 9.8,
    "severity": "Critical",
    "asset_id": 8,
    "discovery_source": "Postman lab",
    "status": "Open",
    "created_at": "2026-10-20T12:09:11Z",
    "resolution_date": null
  }
}

```

### PUT /vulnerabilities/{record_id} (Marc Bteich)

Purpose: update. Access: admin,analyst. Authentication: Bearer JWT.

Path parameters: record_id. IDs must identify existing records.

Postman example: `PUT {{base_vulnerabilities}}/vulnerabilities/{{vulnerability_id}}`.

Request body example (template; credentials remain private):

```json

{
  "status": "Closed"
}

```

Executed response example: HTTP 200; Newman request "Transition Under Investigation". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Vulnerability updated",
  "data": {
    "id": 1,
    "title": "Synthetic Postman vulnerability",
    "description": "Lab scenario only",
    "cve_id": "CVE-2026-12345",
    "cvss_score": 9.8,
    "severity": "Critical",
    "asset_id": 8,
    "discovery_source": "Postman lab",
    "status": "Under Investigation",
    "created_at": "2026-10-20T12:09:11Z",
    "resolution_date": null
  }
}

```

### GET /vulnerabilities/search (Marc Bteich)

Purpose: search. Access: admin,analyst,auditor. Authentication: Bearer JWT.

Postman example: `GET {{base_vulnerabilities}}/vulnerabilities/search?cve=CVE-2026-12345`.

Search parameters demonstrated: asset, cve, severity, status; consult field rules below for allowed keys.

Executed response example: HTTP 200; Newman request "Search cve=CVE-2026-12345". Credentials are redacted.

```json

{
  "status": "success",
  "message": "OK",
  "data": {
    "count": 1,
    "vulnerabilities": [
      {
        "id": 1,
        "title": "Synthetic Postman vulnerability",
        "description": "Lab scenario only",
        "cve_id": "CVE-2026-12345",
        "cvss_score": 9.8,
        "severity": "Critical",
        "asset_id": 8,
        "discovery_source": "Postman lab",
        "status": "Open",
        "created_at": "2026-10-20T12:09:11Z",
        "resolution_date": null
      }
    ]
  }
}

```

### DELETE /vulnerabilities/{record_id} (Marc Bteich)

Purpose: delete. Access: admin. Authentication: Bearer JWT.

Path parameters: record_id. IDs must identify existing records.

Postman example: `DELETE {{base_vulnerabilities}}/vulnerabilities/{{linked_vulnerability_id}}`.

Executed response example: HTTP 200; Newman request "Remove fixture vulnerability". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Vulnerability deleted",
  "data": null
}

```

### GET /internal/stats (Marc Bteich)

Purpose: stats. Access: internal service only. Authentication: Service key.

Postman example: `GET {{base_assets}}/internal/stats`.

Executed response example: HTTP 200; Newman request "Internal statistics". Credentials are redacted.

```json

{
  "status": "success",
  "message": "OK",
  "data": {
    "total_assets": 6,
    "critical_assets": 1,
    "by_type": {
      "Server": 1,
      "Workstation": 1,
      "Database": 1,
      "Application": 1,
      "Network Device": 1,
      "Cloud Resource": 1
    }
  }
}

```

## Notifications (Marc Bteich)

### POST /notifications (Marc Bteich)

Purpose: create notification. Access: admin. Authentication: Bearer JWT.

Postman example: `POST {{base_notifications}}/notifications`.

Request body example (template; credentials remain private):

```json

{
  "user_id": {{user_id}},
  "title": "Security awareness training",
  "message": "Mandatory training on Friday",
  "notification_type": "System Notification",
  "severity": "Low"
}

```

Executed response example: HTTP 201; Newman request "Create - system notification". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Notification created successfully",
  "data": {
    "id": 9,
    "user_id": 2,
    "title": "Security awareness training",
    "message": "Mandatory training on Friday",
    "notification_type": "System Notification",
    "severity": "Low",
    "status": "Unread",
    "created_at": "2026-10-20T12:09:15Z",
    "read_at": null
  }
}

```

### GET /notifications/user/{user_id} (Marc Bteich)

Purpose: get user notifications. Access: admin,analyst,user,auditor. Authentication: Bearer JWT.

Path parameters: user_id. IDs must identify existing records.

Postman example: `GET {{base_notifications}}/notifications/user/{{user_id}}`.

Executed response example: HTTP 200; Newman request "User's own notifications". Credentials are redacted.

```json

{
  "status": "success",
  "message": "6 notification(s) found for user 2",
  "data": {
    "count": 6,
    "notifications": [
      {
        "id": 10,
        "user_id": 2,
        "title": "Malicious IP blocked",
        "message": "185.220.101.4 tried to reach your laptop",
        "notification_type": "Threat Alert",
        "severity": "High",
        "status": "Unread",
        "created_at": "2026-10-20T12:09:15Z",
        "read_at": null
      },
      {
        "id": 9,
        "user_id": 2,
        "title": "Security awareness training",
        "message": "Mandatory training on Friday",
        "notification_type": "System Notification",
        "severity": "Low",
        "status": "Unread",
        "created_at": "2026-10-20T12:09:15Z",
        "read_at": null
      },
      {
        "id": 6,
        "user_id": 2,
        "title": "Incident #1 is now Closed",
        "message": "The status of your reported incident 'Phishing email received' changed from Resolved to Closed.",
        "notification_type": "System Notification",
        "severity": "Medium",
        "status": "Unread",
        "created_at": "2026-10-20T12:09:01Z",
        "read_at": null
      },
      {
        "id": 5,
        "user_id": 2,
        "title": "Incident #1 is now Resolved",
        "message": "The status of your reported incident 'Phishing email received' changed from Mitigated to Resolved.",
        "notification_type": "System Notification",
        "severity": "Medium",
        "status": "Unread",
        "created_at": "2026-10-20T12:09:01Z",
        "read_at": null
      },
      {
        "id": 4,
        "user_id": 2,
        "title": "Incident #1 is now Mitigated",
        "message": "The status of your reported incident 'Phishing email received' changed from Under Investigation to Mitigated.",
        "notification_type": "System Notification",
        "severity": "Medium",
        "status": "Unread",
        "created_at": "2026-10-20T12:09:01Z",
        "read_at": null
      },
      {
        "id": 3,
        "user_id": 2,
        "title": "Incident #1 is now Under Investigation",
        "message": "The status of your reported incident 'Phishing email received' changed from Open to Under Investigation.",
        "notification_type": "System Notification",
        "severity": "Medium",
        "status": "Unread",
        "created_at": "2026-10-20T12:09:01Z",
        "read_at": null
      }
    ]
  }
}

```

### GET /notifications/search (Marc Bteich)

Purpose: search notifications. Access: admin,analyst,auditor. Authentication: Bearer JWT.

Postman example: `GET {{base_notifications}}/notifications/search?type=Threat%20Alert`.

Search parameters demonstrated: severity, status, type, user; consult field rules below for allowed keys.

Executed response example: HTTP 200; Newman request "Critical threat notification". Credentials are redacted.

```json

{
  "status": "success",
  "message": "1 notification(s) match the search criteria",
  "data": {
    "count": 1,
    "notifications": [
      {
        "id": 7,
        "user_id": 1,
        "title": "Critical threat #1",
        "message": "postman.example.test",
        "notification_type": "Threat Alert",
        "severity": "Critical",
        "status": "Unread",
        "created_at": "2026-10-20T12:09:03Z",
        "read_at": null
      }
    ]
  }
}

```

### GET /notifications/{notification_id} (Marc Bteich)

Purpose: get notification. Access: admin,analyst,user,auditor. Authentication: Bearer JWT.

Path parameters: notification_id. IDs must identify existing records.

Postman example: `GET {{base_notifications}}/notifications/search?type=Threat%20Alert`.

Executed response example: HTTP 200; Newman request "Get - owner". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Notification retrieved successfully",
  "data": {
    "id": 9,
    "user_id": 2,
    "title": "Security awareness training",
    "message": "Mandatory training on Friday",
    "notification_type": "System Notification",
    "severity": "Low",
    "status": "Unread",
    "created_at": "2026-10-20T12:09:15Z",
    "read_at": null
  }
}

```

### PUT /notifications/{notification_id}/read (Marc Bteich)

Purpose: mark notification read. Access: admin,analyst,user. Authentication: Bearer JWT.

Path parameters: notification_id. IDs must identify existing records.

Postman example: `PUT {{base_notifications}}/notifications/{{notification_id}}/read`.

Executed response example: HTTP 200; Newman request "Mark read - owner". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Notification marked as read",
  "data": {
    "id": 9,
    "user_id": 2,
    "title": "Security awareness training",
    "message": "Mandatory training on Friday",
    "notification_type": "System Notification",
    "severity": "Low",
    "status": "Read",
    "created_at": "2026-10-20T12:09:15Z",
    "read_at": "2026-10-20T12:09:16Z"
  }
}

```

### DELETE /notifications/{notification_id} (Marc Bteich)

Purpose: delete notification. Access: admin. Authentication: Bearer JWT.

Path parameters: notification_id. IDs must identify existing records.

Postman example: `DELETE {{base_notifications}}/notifications/{{notification_id}}`.

Executed response example: HTTP 200; Newman request "Delete - admin". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Notification 9 deleted successfully",
  "data": null
}

```

## Playbooks (Marc Bteich)

### POST /playbooks (Marc Bteich)

Purpose: create. Access: admin. Authentication: Bearer JWT.

Postman example: `POST {{base_playbooks}}/playbooks`.

Request body example (template; credentials remain private):

```json

{
  "name": "Postman laboratory response",
  "description": "Lab procedure",
  "incident_category": "Malware",
  "severity": "High"
}

```

Executed response example: HTTP 201; Newman request "Create playbook". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Playbook created",
  "data": {
    "id": 1,
    "name": "Postman laboratory response",
    "description": "Lab procedure",
    "incident_category": "Malware",
    "severity": "High",
    "created_by": 1,
    "created_at": "2026-10-20T12:09:18Z"
  }
}

```

### GET /playbooks (Marc Bteich)

Purpose: list all. Access: admin,analyst,auditor. Authentication: Bearer JWT.

Postman example: `GET {{base_playbooks}}/playbooks`.

Executed response example: HTTP 200; Newman request "List playbooks". Credentials are redacted.

```json

{
  "status": "success",
  "message": "OK",
  "data": {
    "count": 1,
    "playbooks": [
      {
        "id": 1,
        "name": "Postman laboratory response",
        "description": "Lab procedure",
        "incident_category": "Malware",
        "severity": "High",
        "created_by": 1,
        "created_at": "2026-10-20T12:09:18Z"
      }
    ]
  }
}

```

### GET /playbooks/{record_id} (Marc Bteich)

Purpose: get. Access: admin,analyst,auditor. Authentication: Bearer JWT.

Path parameters: record_id. IDs must identify existing records.

Postman example: `GET {{base_playbooks}}/playbooks/{{playbook_id}}`.

Executed response example: HTTP 200; Newman request "Verify ordered actions". Credentials are redacted.

```json

{
  "status": "success",
  "message": "OK",
  "data": {
    "id": 1,
    "name": "Postman laboratory response",
    "description": "Lab procedure",
    "incident_category": "Malware",
    "severity": "High",
    "created_by": 1,
    "created_at": "2026-10-20T12:09:18Z",
    "actions": [
      {
        "id": 2,
        "playbook_id": 1,
        "description": "Collect evidence",
        "step_number": 1,
        "status": "Pending",
        "assigned_user_id": null,
        "completion_date": null,
        "execution_history": [
          {
            "actor_id": 3,
            "at": "2026-10-20T12:09:18Z",
            "from_status": null,
            "to_status": "Pending",
            "assigned_user_id": null,
            "completion_date": null
          }
        ]
      },
      {
        "id": 1,
        "playbook_id": 1,
        "description": "Contain host",
        "step_number": 2,
        "status": "Pending",
        "assigned_user_id": null,
        "completion_date": null,
        "execution_history": [
          {
            "actor_id": 3,
            "at": "2026-10-20T12:09:18Z",
            "from_status": null,
            "to_status": "Pending",
            "assigned_user_id": null,
            "completion_date": null
          }
        ]
      }
    ]
  }
}

```

### POST /playbooks/{record_id}/actions (Marc Bteich)

Purpose: add action. Access: admin,analyst. Authentication: Bearer JWT.

Path parameters: record_id. IDs must identify existing records.

Postman example: `POST {{base_playbooks}}/playbooks/{{playbook_id}}/actions`.

Request body example (template; credentials remain private):

```json

{
  "description": "Contain host",
  "step_number": 2
}

```

Executed response example: HTTP 201; Newman request "Add second step first". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Action created",
  "data": {
    "id": 1,
    "playbook_id": 1,
    "description": "Contain host",
    "step_number": 2,
    "status": "Pending",
    "assigned_user_id": null,
    "completion_date": null,
    "execution_history": [
      {
        "actor_id": 3,
        "at": "2026-10-20T12:09:18Z",
        "from_status": null,
        "to_status": "Pending",
        "assigned_user_id": null,
        "completion_date": null
      }
    ]
  }
}

```

### PUT /actions/{record_id}/status (Marc Bteich)

Purpose: update action. Access: admin,analyst. Authentication: Bearer JWT.

Path parameters: record_id. IDs must identify existing records.

Postman example: `PUT {{base_playbooks}}/actions/{{action_id}}/status`.

Request body example (template; credentials remain private):

```json

{
  "status": "Completed"
}

```

Executed response example: HTTP 200; Newman request "Start assigned action". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Action updated",
  "data": {
    "id": 2,
    "playbook_id": 1,
    "description": "Collect evidence",
    "step_number": 1,
    "status": "In Progress",
    "assigned_user_id": 3,
    "completion_date": null,
    "execution_history": [
      {
        "actor_id": 3,
        "at": "2026-10-20T12:09:18Z",
        "from_status": null,
        "to_status": "Pending",
        "assigned_user_id": null,
        "completion_date": null
      },
      {
        "actor_id": 3,
        "at": "2026-10-20T12:09:19Z",
        "from_status": "Pending",
        "to_status": "In Progress",
        "assigned_user_id": 3,
        "completion_date": null
      }
    ]
  }
}

```

### DELETE /playbooks/{record_id} (Marc Bteich)

Purpose: delete. Access: admin. Authentication: Bearer JWT.

Path parameters: record_id. IDs must identify existing records.

Postman example: `DELETE {{base_playbooks}}/playbooks/{{playbook_id}}`.

Executed response example: HTTP 200; Newman request "Delete playbook". Credentials are redacted.

```json

{
  "status": "success",
  "message": "Playbook deleted",
  "data": null
}

```

## Person B field rules and responses (Marc Bteich)

| Service | Required create fields | Allowed updates / behavior |

|---|---|---|

| Assets | asset_name, asset_type, ip_address, owner_id, department, criticality | name, owner, department, criticality, status; optional operating_system/location on create; status defaults Active |

| Threats | threat_type, threat_value, description, severity, source | description, severity, source; canonical IP/domain/hash; unique type/value; recent means latest five by date/id |

| Vulnerabilities | title, description, cve_id, cvss_score, severity, asset_id, discovery_source | description, severity, CVSS, next status only; Open initially; resolution_date automatic on Resolved |

| Playbooks | name, description, incident_category, severity | add actions with description/positive step_number and optional assigned_user_id; update action with next status and/or assigned_user_id; completion_date automatic |

| Reports | no body | HTTP source stats only; admin/auditor; unavailable source returns 503 |

Assets types: Server, Workstation, Database, Application, Network Device, Cloud Resource. Threat types follow common/enums.py exactly: IP Address, Domain, File Hash, Malware Signature, Other. File hashes accept 32/40/64 hex characters. CVEs match CVE-[four digits]-[at least four digits]. CVSS is a finite JSON number 0–10 with at most one decimal place, matching NUMERIC(3,1). Severity/criticality: Low, Medium, High, Critical.

Vulnerability lifecycle: Open → Under Investigation → In Progress → Resolved → Closed. Action lifecycle: Pending → In Progress → Completed. Same-state, skipped and backward transitions are rejected. Assign an active user before action execution. Client-supplied history, completion dates and resolution dates are rejected.

Search: Assets name/type/ip/department/criticality; Threats type/value/severity/source; Vulnerabilities cve/severity/asset/status. Text fragments match literally and case-insensitively; other values are exact. Multiple filters combine with AND. Empty searches, duplicate parameters, unknown fields and invalid values return 400. No matches return an empty list with 200.

List/search responses use data: {count, assets|threats|vulnerabilities|playbooks: [...]}. Single resources return data containing their fields and id. A playbook detail includes actions sorted by step_number; action responses include execution_history. Reports contain report_type/generated_at/generated_by plus named totals/groupings. See the actual redacted request/response evidence for executed examples.
