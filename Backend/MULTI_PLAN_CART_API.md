# Multi-Plan Cart API Documentation

## Overview

This API enables users to add multiple subscription plans to a cart, customize duration for each plan, and checkout with a single payment. All prices are calculated based on daily rates.

## Base URL
```
/api/subscriptions/
```

## Authentication
All cart endpoints require JWT authentication:
```
Authorization: Bearer <access_token>
```

---

## Plans API

### GET /plans/
Get all available plans (public endpoint - no auth required).

**Response:**
```json
[
  {
    "id": 1,
    "code": "MESS_BREAKFAST",
    "name": "Breakfast Only - Mess",
    "description": "",
    "service_type": "mess",
    "base_price": 1200,
    "included_meals": ["breakfast"],
    "duration_days": 30,
    "min_duration_days": 7,
    "max_duration_days": 90,
    "allow_custom_duration": true,
    "daily_rate": 40.0,
    "is_active": true
  }
]
```

**Query Parameters:**
- `service_type`: Filter by "mess" or "tiffin"

---

## Cart API

### GET /cart/
Get current user's cart with all items.

**Response:**
```json
{
  "id": 1,
  "items": [
    {
      "id": 1,
      "plan": {
        "id": 1,
        "code": "MESS_BREAKFAST",
        "name": "Breakfast Only - Mess",
        "base_price": 1200,
        "daily_rate": 40.0,
        ...
      },
      "plan_name": "Breakfast Only - Mess",
      "custom_duration_days": 15,
      "daily_rate": "40.00",
      "calculated_price": 600,
      "created_at": "2026-01-03T03:47:00Z",
      "updated_at": "2026-01-03T03:47:00Z"
    }
  ],
  "total": 600,
  "item_count": 1,
  "created_at": "2026-01-03T03:47:00Z",
  "updated_at": "2026-01-03T03:47:00Z"
}
```

---

### POST /cart/add/
Add a plan to cart with custom duration.

**Request Body:**
```json
{
  "plan_id": 1,
  "duration_days": 15
}
```

**Response (201):**
```json
{
  "success": true,
  "message": "Added Breakfast Only - Mess to cart",
  "item": {
    "id": 1,
    "plan": {...},
    "plan_name": "Breakfast Only - Mess",
    "custom_duration_days": 15,
    "daily_rate": "40.00",
    "calculated_price": 600
  }
}
```

**Error Responses:**
- `400` - Plan already in cart
- `400` - Duration outside allowed range
- `400` - Active subscription exists for this plan

---

### PATCH /cart/{item_id}/update/
Update duration for a cart item.

**Request Body:**
```json
{
  "duration_days": 20
}
```

**Response:**
```json
{
  "success": true,
  "message": "Updated duration to 20 days",
  "item": {
    "id": 1,
    "custom_duration_days": 20,
    "calculated_price": 800,
    ...
  }
}
```

---

### DELETE /cart/{item_id}/remove/
Remove an item from cart.

**Response:**
```json
{
  "success": true,
  "message": "Item removed from cart"
}
```

---

### DELETE /cart/clear/
Clear all items from cart.

**Response:**
```json
{
  "success": true,
  "message": "Cart cleared"
}
```

---

## Checkout API

### POST /cart/checkout/
Initiate checkout and create Razorpay order.

**Response:**
```json
{
  "success": true,
  "bundle_order_id": 1,
  "razorpay_order_id": "order_RzAnAvfarh3tnI",
  "amount": 1300,
  "currency": "INR",
  "key_id": "rzp_test_..."
}
```

**Error Responses:**
- `400` - Cart is empty
- `400` - Plan no longer available
- `400` - Duration no longer valid
- `400` - Active subscription exists

---

### POST /cart/verify/
Verify payment and complete checkout.

**Request Body:**
```json
{
  "bundle_order_id": 1,
  "razorpay_payment_id": "pay_xxx",
  "razorpay_signature": "signature_xxx"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully subscribed to 2 plan(s)",
  "bundle_order": {
    "id": 1,
    "total_amount": 1300,
    "status": "PAID",
    "razorpay_order_id": "order_xxx",
    "razorpay_payment_id": "pay_xxx",
    "subscriptions": [...],
    "subscription_count": 2,
    "created_at": "2026-01-03T03:50:00Z",
    "paid_at": "2026-01-03T03:51:00Z"
  }
}
```

**Error Responses:**
- `400` - Missing required fields
- `400` - Payment verification failed
- `404` - Bundle order not found

---

## Price Calculation

Prices are calculated using daily rates:

```
calculated_price = daily_rate × duration_days
```

Where:
- `daily_rate = base_price / duration_days` (from plan)
- Or `daily_rate_override` if set on plan

**Example:**
- Plan: Breakfast Only (₹1200 for 30 days)
- Daily rate: ₹40
- Custom duration: 15 days
- Calculated price: ₹40 × 15 = ₹600

---

## Frontend Integration Flow

### 1. Display Plans
```javascript
// Fetch plans
const plans = await fetch('/api/subscriptions/plans/');

// Display with duration slider
// min: plan.min_duration_days (default: 7)
// max: plan.max_duration_days (default: 90)
// default: plan.duration_days (default: 30)
```

### 2. Add to Cart
```javascript
await fetch('/api/subscriptions/cart/add/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    plan_id: selectedPlan.id,
    duration_days: sliderValue
  })
});
```

### 3. Update Duration
```javascript
await fetch(`/api/subscriptions/cart/${itemId}/update/`, {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    duration_days: newDuration
  })
});
```

### 4. Checkout with Razorpay
```javascript
// 1. Create order
const checkout = await fetch('/api/subscriptions/cart/checkout/', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` }
});
const { razorpay_order_id, amount, key_id, bundle_order_id } = await checkout.json();

// 2. Open Razorpay
const options = {
  key: key_id,
  amount: amount * 100, // paise
  currency: 'INR',
  order_id: razorpay_order_id,
  handler: async (response) => {
    // 3. Verify payment
    await fetch('/api/subscriptions/cart/verify/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        bundle_order_id: bundle_order_id,
        razorpay_payment_id: response.razorpay_payment_id,
        razorpay_signature: response.razorpay_signature
      })
    });
  }
};
const rzp = new Razorpay(options);
rzp.open();
```

---

## Available Plans (Default)

| Code | Name | Base Price | Daily Rate | Meals |
|------|------|------------|------------|-------|
| MESS_BREAKFAST | Breakfast Only - Mess | ₹1200 | ₹40 | breakfast |
| MESS_SINGLE | Single Meal - Mess | ₹1800 | ₹60 | lunch |
| MESS_LUNCH_DINNER | Lunch + Dinner - Mess | ₹3000 | ₹100 | lunch, dinner |
| MESS_FULL | Full Day - Mess | ₹4000 | ₹133 | breakfast, lunch, dinner |
| TIFFIN_BREAKFAST | Breakfast Only - Tiffin | ₹1500 | ₹50 | breakfast |
| TIFFIN_SINGLE | Single Meal - Tiffin | ₹2100 | ₹70 | lunch |
| TIFFIN_LUNCH_DINNER | Lunch + Dinner - Tiffin | ₹3600 | ₹120 | lunch, dinner |
| TIFFIN_FULL | Full Day - Tiffin | ₹4800 | ₹160 | breakfast, lunch, dinner |

All plans allow custom duration: 7-90 days.

---

## Error Handling

All error responses follow this format:
```json
{
  "success": false,
  "errors": {
    "field_name": "Error message"
  }
}
```

Or for general errors:
```json
{
  "success": false,
  "message": "Error description"
}
```

---

## Notes

1. **One plan per cart**: Users cannot add the same plan twice
2. **No active subscription**: Users cannot add a plan they already have an active subscription for
3. **Duration validation**: Duration must be within plan's min/max range
4. **Cart persists**: Cart is saved server-side, persists across sessions
5. **Breakfast is separate**: Breakfast is now a separate plan, not an addon
