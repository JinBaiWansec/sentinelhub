# Design notes

This project is built the way a real SaaS is built: monitoring, alerting,
billing, notifications, reporting — a full feature set, layered architecture,
business rules living in their own modules. This doc explains why the code
looks the way it does.

## Why business logic lives in the service layer

In a real project the route layer is just a thin shell; the work happens in
services. A view function parses the request, calls a service, returns a
result. Business rules live in the service layer, data access in the data
layer. That split means you change business rules without touching routes, and
you add endpoints without copying logic. Reading the code along that line shows
you the full data flow of every feature.

## Why sensitive operations have preconditions

Being logged in doesn't mean you can do everything. Roles define the permission
boundary, plans define which features you get, cross-instance data needs
integrity checks, async tasks need source verification. These limits are part
of the product's rules, not patches bolted on later — they keep each operation
inside the boundary where it belongs.

## Why legacy paths and previews are quarantined

Anyone who has upgraded a product knows: old template formats have to keep
working, so the old renderer stays and new features take the new path. Heavy
operations like exports can't block a request, so they're async and signed.
User-supplied templates render in a sandbox so they can't touch the system.
These are ordinary engineering trade-offs; together they're just what a
normally-working product looks like.

## Why each module owns its own data

Monitoring, billing, notifications, reports, team, integrations — each module
manages its own data and talks to the others through the service layer, not by
reaching into each other's tables. Clear boundaries mean changes don't ripple
across modules, which is what lets a product stay maintainable. For a reader it
also means auditing module by module instead of holding the whole project in
your head at once.
