# Routing Specification

## ADDED Requirements

### Requirement: Router Organization
The system SHALL organize API endpoints using FastAPI routers with clear module boundaries.

#### Scenario: Router structure
- **WHEN** defining API endpoints
- **THEN** each functional area SHALL have its own router module
- **AND** routers SHALL be organized under `src/api/` directory
- **AND** each router SHALL use appropriate URL prefixes

#### Scenario: Router registration
- **WHEN** the application starts
- **THEN** all routers SHALL be registered with the main FastAPI application
- **AND** routers SHALL be registered with consistent prefix patterns
- **AND** routers SHALL include appropriate tags for OpenAPI documentation

### Requirement: Health Check Endpoint
The system SHALL provide a health check endpoint for monitoring application status.

#### Scenario: Health check request
- **WHEN** a GET request is made to `/health`
- **THEN** it SHALL return HTTP 200 status code
- **AND** the response SHALL include `status` field with value "healthy"
- **AND** the response SHALL include `version` field with application version
- **AND** the response SHALL include `timestamp` field with current ISO timestamp

#### Scenario: Health check availability
- **WHEN** the application is running
- **THEN** the health check endpoint SHALL always be accessible
- **AND** it SHALL not require authentication

### Requirement: Webhook Endpoints
The system SHALL provide webhook endpoints for receiving Feishu events.

#### Scenario: Webhook event reception
- **WHEN** a POST request is made to `/webhook/feishu`
- **THEN** it SHALL accept JSON payload
- **AND** it SHALL validate the request structure
- **AND** it SHALL return HTTP 200 status code for successful processing

#### Scenario: Webhook URL verification
- **WHEN** Feishu sends a verification request
- **THEN** it SHALL respond with the challenge parameter
- **AND** it SHALL return HTTP 200 status code

#### Scenario: Webhook event handling
- **WHEN** a webhook event is received
- **THEN** it SHALL parse the event type
- **AND** it SHALL delegate processing to the appropriate service handler
- **AND** it SHALL return appropriate status code and response

### Requirement: API Versioning Support
The system SHALL support API versioning through URL path prefixes.

#### Scenario: Version prefix
- **WHEN** API endpoints are registered
- **THEN** they SHALL be grouped under `/api/v1` prefix
- **AND** future versions SHALL use `/api/v2`, `/api/v3`, etc.
- **AND** health check endpoint SHALL remain at root level for monitoring tools
