# When to Mock

Mock at **system boundaries** only:

- External APIs (payment, email, etc.)
- Databases (sometimes - prefer test DB)
- Time/randomness
- File system (sometimes)

Don't mock:

- Your own classes/modules
- Internal collaborators
- Anything you control

## Designing for Mockability

At system boundaries, design interfaces that are easy to mock:

### 1. Use dependency injection

Pass external dependencies in rather than creating them internally:

```python
# Easy to mock
def process_payment(order, payment_client):
    return payment_client.charge(order.total)


# Hard to mock
def process_payment(order):
    client = StripeClient(os.environ['STRIPE_KEY'])
    return client.charge(order.total)
```

### 2. Prefer SDK-style interfaces over generic fetchers

Create specific functions for each external operation instead of one generic function with conditional logic:

```python
# GOOD: Each function is independently mockable
api = {
    "get_user": lambda id: requests.get(f"/users/{id}"),
    "get_orders": lambda user_id: requests.get(f"/users/{user_id}/orders"),
    "create_order": lambda data: requests.post('/orders', json=data),
}


# BAD: Mocking requires conditional logic inside the mock
api = {
    "fetch": lambda endpoint, options=None: requests.request(options.get('method', 'GET'), endpoint, **(options or {})),
}
```

The SDK approach means:

- Each mock returns one specific shape
- No conditional logic in test setup
- Easier to see which endpoints a test exercises
- Type safety per endpoint