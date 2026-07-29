---
name: django-patterns
description: Build and review Django apps across settings, ORM, views, forms, admin, and deployment boundaries.
origin: ECC
---

# Django Patterns

## When to use

- implementing or reviewing Django models, queries, views, forms, middleware, admin, or settings
- organizing Django apps and service/domain boundaries
- checking framework-specific behavior before changing production Django code

## Workflow

1. Identify the Django version, installed apps, middleware, settings modules, and database constraints.
2. Keep domain rules close to models/services and transport behavior in views/forms/serializers.
3. Use ORM features deliberately; inspect query counts and transactions for data changes.
4. Apply Django security and deployment settings through the dedicated security skill when risk is involved.
5. Verify with migrations, Django checks, and focused tests.

## Constraints

- Follow current Django docs for ORM, settings, middleware, auth, and async limitations.
- Avoid signals for core business flow unless decoupling is genuinely needed and tested.
- Move settings/model/view/admin examples to references.

## References

- [moved Django patterns and examples](references/full-guidance.md)
- [verification sources](references/official-docs.md)

## Expected output

- A brief summary of the change or recommendation.
- Commands/checks run, or the reason verification was not run.
- Any version assumptions or official-doc checks that matter for the result.
