# Security Policy

## Reporting a vulnerability

Please report security issues privately through
[GitHub security advisories](https://github.com/ngine-io/discovr/security/advisories/new)
rather than opening a public issue. We aim to respond within a few working days.

## Scope

`discovr` has no authentication of its own — the bearer token it receives is the cloud provider
credential, which it forwards to the provider API and never persists. Deploy it on a trusted
network or behind a proxy that terminates TLS and restricts access. Use read-only permissions for the token if the cloud provider allows to restrict.
