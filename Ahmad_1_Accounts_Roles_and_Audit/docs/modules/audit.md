# Module: Audit (`apps/audit`)

**Delivers:** NFR-18 audit log of security-sensitive actions; denied attempts (BR-5, C1)
**Owns:** `AuditLog`
**Public interface:** `services.record(actor, action, entity_type, entity_id, before, after, outcome)`

## Design decisions

**D1. Append-only.** `AuditLog` refuses updates and deletes, and the admin site has no edit or delete.
**D2. Denied attempts are logged automatically** by `access.permissions.require` and by self-approval checks.
**D3. Before/after as JSON**, so a reviewer can see exactly what changed (e.g. Blueprint thresholds, Section 9.8).

## To build
- [ ] Log logins, role changes, Blueprint publishes and AI threshold changes.
- [ ] A read-only audit page for the System Administrator with filters.
