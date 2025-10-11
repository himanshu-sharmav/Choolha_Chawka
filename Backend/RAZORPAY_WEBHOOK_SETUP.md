# Razorpay Webhook Implementation

## Overview

This implementation provides reliable payment status updates using Razorpay webhooks, eliminating dependency on frontend payment confirmation which can be unreliable due to network issues, browser closures, or user navigation.

## Features

- ✅ **Reliable Payment Processing**: Webhooks ensure payment status is updated even if frontend confirmation fails
- ✅ **Signature Verification**: Secure webhook signature validation using HMAC-SHA256
- ✅ **Duplicate Prevention**: Prevents duplicate payment processing
- ✅ **Comprehensive Logging**: Detailed logging for debugging and monitoring
- ✅ **Error Handling**: Robust error handling with proper HTTP status codes
- ✅ **Notification Integration**: Automatic email notifications for payment success/failure

## Webhook Endpoint

**URL**: `/api/payments/webhook/razorpay/`  
**Method**: `POST`  
**Content-Type**: `application/json`

## Supported Events

### 1. Payment Captured (`payment.captured`)
Triggered when a payment is successfully captured.

**Webhook Payload Example**:
```json
{
  "event": "payment.captured",
  "payload": {
    "payment": {
      "id": "pay_1234567890",
      "order_id": "order_1234567890",
      "amount": 50000,
      "currency": "INR",
      "status": "captured",
      "method": "card",
      "created_at": 1640995200
    }
  }
}
```

### 2. Payment Failed (`payment.failed`)
Triggered when a payment fails.

**Webhook Payload Example**:
```json
{
  "event": "payment.failed",
  "payload": {
    "payment": {
      "id": "pay_1234567890",
      "order_id": "order_1234567890",
      "amount": 50000,
      "currency": "INR",
      "status": "failed",
      "error_code": "BAD_REQUEST_ERROR",
      "error_description": "Payment failed due to insufficient funds"
    }
  }
}
```

### 3. Order Paid (`order.paid`)
Alternative event for successful payments (logged but handled by `payment.captured`).

## Configuration

### Environment Variables

Add these to your environment variables:

```bash
# Razorpay Configuration
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret  # Optional for development
```

### Razorpay Dashboard Setup

1. **Login to Razorpay Dashboard**
2. **Go to Settings → Webhooks**
3. **Create New Webhook**:
   - **URL**: `https://yourdomain.com/api/payments/webhook/razorpay/`
   - **Events**: Select `payment.captured` and `payment.failed`
   - **Secret**: Generate a webhook secret (optional but recommended)

## Implementation Details

### Webhook View (`RazorpayWebhookView`)

Located in `payments/views.py`, this view handles:
- Signature verification
- Event parsing and routing
- Error handling and logging
- HTTP response management

### Service Methods (`RazorpayService`)

Located in `payments/services.py`:

#### `handle_webhook_payment_captured()`
- Updates order status to 'paid'
- Creates payment record with 'SUCCESS' status
- Activates subscription
- Sends success notifications
- Prevents duplicate processing

#### `handle_webhook_payment_failed()`
- Updates order status to 'failed'
- Creates payment record with 'FAILED' status
- Sends failure notifications
- Stores error details

## Security Features

### Signature Verification
```python
def _verify_webhook_signature(self, body, signature):
    webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
    expected_signature = hmac.new(
        webhook_secret.encode('utf-8'),
        body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)
```

### CSRF Exemption
The webhook view is exempt from CSRF protection as it's called by Razorpay servers.

## Error Handling

### HTTP Status Codes
- **200**: Success
- **400**: Bad Request (invalid signature, malformed data)
- **500**: Internal Server Error

### Logging
All webhook events are logged with appropriate log levels:
- `INFO`: Successful processing
- `ERROR`: Processing failures
- `WARNING`: Configuration issues

## Testing

### Local Testing
You can test the webhook locally using tools like ngrok:

1. **Install ngrok**: `npm install -g ngrok`
2. **Expose local server**: `ngrok http 8000`
3. **Use ngrok URL** in Razorpay webhook configuration
4. **Test with sample payloads**

### Production Testing
Use Razorpay's webhook testing tools in the dashboard to send test events.

## Monitoring

### Log Monitoring
Monitor these log patterns:
- `🔔 [RazorpayWebhook] Received webhook`
- `💰 [RazorpayWebhook] Payment captured`
- `💸 [RazorpayWebhook] Payment failed`
- `❌ [RazorpayWebhook]` (errors)

### Database Monitoring
Monitor these tables for webhook processing:
- `payments_payment` - Payment records
- `payments_razorpayorder` - Order status updates
- `subscriptions_subscription` - Subscription activation

## Benefits Over Frontend Confirmation

### Reliability
- ✅ **Network Independent**: Works even if user loses internet
- ✅ **Browser Independent**: Works even if user closes browser
- ✅ **Server-Side**: Guaranteed execution on your servers

### Security
- ✅ **Signature Verification**: Ensures webhooks are from Razorpay
- ✅ **Server-Side Processing**: No client-side manipulation possible

### User Experience
- ✅ **No User Dependency**: Payment processing doesn't rely on user actions
- ✅ **Automatic Notifications**: Users get notified regardless of their actions

## Migration from Frontend Confirmation

### Current Flow (Frontend Dependent)
1. User completes payment
2. Frontend calls `/api/payments/orders/verify_payment/`
3. Backend verifies and processes payment
4. **❌ Problem**: If frontend fails, payment is not processed

### New Flow (Webhook Based)
1. User completes payment
2. Razorpay sends webhook to `/api/payments/webhook/razorpay/`
3. Backend processes payment automatically
4. **✅ Solution**: Payment is always processed reliably

### Recommended Approach
- **Keep frontend verification** for immediate user feedback
- **Use webhooks** as the authoritative source for payment status
- **Handle both flows** gracefully (webhook may arrive before or after frontend call)

## Troubleshooting

### Common Issues

1. **Webhook Not Receiving Events**
   - Check webhook URL is accessible
   - Verify webhook is enabled in Razorpay dashboard
   - Check firewall/network settings

2. **Signature Verification Failing**
   - Verify `RAZORPAY_WEBHOOK_SECRET` is correct
   - Check webhook secret in Razorpay dashboard
   - Ensure raw request body is used for verification

3. **Duplicate Payments**
   - Check `gateway_payment_id` uniqueness
   - Verify duplicate prevention logic
   - Monitor payment records for duplicates

### Debug Commands

```bash
# Check webhook endpoint
curl -X POST https://yourdomain.com/api/payments/webhook/razorpay/ \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'

# Check Django logs
tail -f logs/django.log | grep "RazorpayWebhook"

# Check payment records
python manage.py shell -c "
from payments.models import Payment
print('Recent payments:', Payment.objects.all()[:5])
"
```

## Future Enhancements

- [ ] **Retry Logic**: Implement webhook retry for failed processing
- [ ] **Webhook Analytics**: Track webhook success/failure rates
- [ ] **Event Filtering**: Filter webhook events by subscription type
- [ ] **Batch Processing**: Handle multiple webhook events efficiently
- [ ] **Webhook Replay**: Ability to replay failed webhook events

## Support

For issues with this implementation:
1. Check Django logs for error messages
2. Verify Razorpay webhook configuration
3. Test with Razorpay's webhook testing tools
4. Contact Razorpay support for webhook-related issues

