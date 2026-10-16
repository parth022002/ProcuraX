# Security, privacy, and data policy

- No secrets in Git; use `.env` locally and deployment secret storage for hosting.
- Inputs, file uploads, retrieved documents and external web content are untrusted. Validate size/type, scan as feasible, and defend against prompt injection.
- Enforce access at the server/API and retrieval layer; do not trust role claims from browser state.
- Allowlist external sources; respect terms of service and rate limits; retain URL, fetch timestamp, source tier, status and content hash as relevant.
- Minimise stored personal/supplier-sensitive information; synthetic data is the default.
- Use access tags and supplier/category filters for document retrieval.
- Approval and action endpoints must verify identity, role, threshold, case state, idempotency and required decision reason.
- Keep append-only decision/approval/audit events. Never rewrite a human override to make it appear to be model truth.
- Store post-decision outcomes separately from prediction-time features. Do not train on future outcome data.
- Set request and upload limits. Avoid logging raw secrets, API keys or unnecessary confidential document text.
- Use dependency scanning and CI checks before public release.
- Production controls such as enterprise DR, KMS, Kubernetes, autoscaling and formal SLOs are outside the current PoC unless separately scoped.
