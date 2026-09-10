# API Spec

## ADDED Requirements

### Requirement: Chat endpoint

The service MUST expose `POST /chat` accepting `{ "message": string }` and returning `{ "answer": string, "product_id": string, "recommended_quantity": integer }`.

#### Scenario: Successful recommendation

- **GIVEN** a valid message requesting PROD-001
- **WHEN** POST /chat is called
- **THEN** the response status MUST be 200
- **AND** the body MUST include answer, product_id, and recommended_quantity

### Requirement: Health endpoint

The service MUST expose `GET /health` returning a simple OK payload.

#### Scenario: Health check

- **GIVEN** the API is running
- **WHEN** GET /health is called
- **THEN** the response status MUST be 200

### Requirement: Unknown product error

When the product cannot be resolved, the API MUST return 404.

#### Scenario: Missing product

- **GIVEN** a message for an unknown product_id
- **WHEN** POST /chat is called
- **THEN** the response status MUST be 404
