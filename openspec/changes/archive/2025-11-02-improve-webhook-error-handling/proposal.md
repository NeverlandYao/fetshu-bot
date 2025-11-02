# Improve Webhook Error Handling

## Why
Currently, when a webhook request is sent without a body, the server crashes with an unhandled exception. The `await request.json()` call in `src/api/webhook.py:59` raises an exception when parsing fails, and this is not caught before attempting to process the request. This creates a poor user experience and makes the API fragile.

## What Changes
- Add validation for request body before attempting to parse JSON
- Add specific exception handling for JSON parsing errors
- Return appropriate HTTP 400 status codes with clear error messages for malformed requests
- Differentiate between client errors (4xx) and server errors (5xx)
- Ensure webhook endpoint handles edge cases gracefully:
  - Missing request body
  - Invalid JSON syntax
  - Empty request body
  - Malformed content-type headers

## Impact
- Affected specs: `error-handling` (new capability), `routing` (webhook endpoint behavior)
- Affected code: `src/api/webhook.py`, potentially `src/app.py` for centralized error handling
- No breaking changes - only improved error responses
- Better debugging experience for API consumers
