# Owner Subscription Management API

## Modify Subscription Days

Allows mess owners to add or remove days from any user's subscription.

### Endpoint

```
POST /api/subscriptions/{subscription_id}/modify_days/
```

### Authentication

- **Required**: Yes
- **Permission**: Mess Owner only (`IsMessOwner`)

### Request Body

```json
{
  "days_to_add": 5,
  "reason": "Compensation for service disruption"
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `days_to_add` | integer | Yes | Number of days to add (use negative value to remove days) |
| `reason` | string | No | Reason for modifying subscription days (max 500 characters) |

#### Validation Rules

- `days_to_add` cannot be 0
- `days_to_add` must be between -365 and 365
- New end date cannot be in the past

### Response

#### Success Response (200 OK)

```json
{
  "success": true,
  "message": "Successfully added 5 day(s) to subscription for john_doe",
  "subscription_id": 123,
  "user": {
    "id": 45,
    "username": "john_doe",
    "email": "john@example.com",
    "phone": "+919876543210"
  },
  "modification": {
    "original_end_date": "2025-01-15",
    "new_end_date": "2025-01-20",
    "days_modified": 5,
    "reason": "Compensation for service disruption",
    "modified_by": "owner_username",
    "modified_at": "2025-01-10T14:30:00Z"
  },
  "status": {
    "original": "ACTIVE",
    "current": "ACTIVE",
    "changed": false
  },
  "subscription": {
    // Full subscription object
  }
}
```

#### Error Responses

**400 Bad Request** - Invalid input

```json
{
  "success": false,
  "errors": {
    "days_to_add": ["days_to_add cannot be zero"]
  }
}
```

**400 Bad Request** - End date in past

```json
{
  "success": false,
  "message": "Cannot set end date to the past. New end date would be 2024-12-01"
}
```

**403 Forbidden** - Not a mess owner

```json
{
  "detail": "You do not have permission to perform this action."
}
```

**404 Not Found** - Subscription not found

```json
{
  "detail": "Not found."
}
```

### Use Cases

#### 1. Add Days (Compensation)

```bash
curl -X POST https://your-api.com/api/subscriptions/123/modify_days/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "days_to_add": 7,
    "reason": "Compensation for kitchen closure during festival"
  }'
```

#### 2. Remove Days (Correction)

```bash
curl -X POST https://your-api.com/api/subscriptions/123/modify_days/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "days_to_add": -3,
    "reason": "Correction for duplicate leave days"
  }'
```

#### 3. Reactivate Expired Subscription

If a subscription is expired and you add days that extend beyond today, it will automatically be reactivated:

```bash
curl -X POST https://your-api.com/api/subscriptions/123/modify_days/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "days_to_add": 30,
    "reason": "Special extension for loyal customer"
  }'
```

Response will include:
```json
{
  "message": "Successfully added 30 day(s) to subscription for john_doe and reactivated subscription (was EXPIRED)",
  "status": {
    "original": "EXPIRED",
    "current": "ACTIVE",
    "changed": true
  }
}
```

### Notes

- This endpoint does not affect payment amounts or pending payments
- The modification is immediate and does not require user confirmation
- All modifications are logged with the owner's username and timestamp
- If the subscription was expired and the new end date is in the future, it will be automatically reactivated
- This is separate from the leave system - use leave requests for user-initiated day extensions

### Related Endpoints

- `POST /api/subscriptions/{id}/renew/` - Renew expired subscription (user action)
- `GET /api/subscriptions/` - List all subscriptions
- `GET /api/subscriptions/{id}/` - Get subscription details
