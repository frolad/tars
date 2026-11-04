# When to mock

Adapted from Matt Pocock's `tdd` skill; see `NOTICE.md`. The code examples are his.

Mock at system boundaries only:

- external APIs, such as payment or email;
- the database, sometimes; a test database or a local stand-in comes first;
- time and randomness;
- the file system, sometimes.

Your own classes and modules, internal collaborators, and anything else you control are tested for real. Which way a test crosses a boundary depends on the kind of dependency (`SKILL.md`, "Seams"), and a new fake or port is asked first.

## Designing for mocks at a boundary

For new code at a system boundary. Changing existing code to take a dependency is a refactor: ask first, as sttp-software-coding says.

**1. Pass the dependency in instead of creating it inside.**

```typescript
// Easy to mock
function processPayment(order, paymentClient) {
  return paymentClient.charge(order.total);
}

// Hard to mock
function processPayment(order) {
  const client = new StripeClient(process.env.STRIPE_KEY);
  return client.charge(order.total);
}
```

**2. One function per external operation instead of one generic fetcher.**

```typescript
// GOOD: Each function is independently mockable
const api = {
  getUser: (id) => fetch(`/users/${id}`),
  getOrders: (userId) => fetch(`/users/${userId}/orders`),
  createOrder: (data) => fetch('/orders', { method: 'POST', body: data }),
};

// BAD: Mocking requires conditional logic inside the mock
const api = {
  fetch: (endpoint, options) => fetch(endpoint, options),
};
```

With one function per operation, each mock returns one shape, the test setup has no conditions, a test shows which endpoints it uses, and each endpoint keeps its own types.
