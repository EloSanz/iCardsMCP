---
module: tags
version: 1.0
base_url: /api/decks/:deckId/tags
authentication: required
description: "Tag management endpoints for organizing flashcards within decks"
---

# Tag API Endpoints

## GET /api/decks/:deckId/tags

**Purpose:** Retrieves all tags associated with a specific deck.

**Authentication:** Required (JWT token)

**URL Parameters:**
- `deckId` (integer): Parent deck identifier

**Authorization Logic:**
```javascript
// Verify user owns the deck
const isOwner = await TagRepository.validateDeckOwnership(deckId, userId);
if (!isOwner) {
  return { error: 'Access denied. Deck does not belong to user.' };
}
```

**Response (Success - 200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "grammar",
      "deckId": 1,
      "flashcardCount": 5,
      "createdAt": "2024-01-15T10:45:00.000Z",
      "updatedAt": "2024-01-15T10:45:00.000Z"
    },
    {
      "id": 2,
      "name": "vocabulary",
      "deckId": 1,
      "flashcardCount": 12,
      "createdAt": "2024-01-15T10:50:00.000Z",
      "updatedAt": "2024-01-15T10:50:00.000Z"
    }
  ],
  "total": 2,
  "message": "Tags retrieved successfully"
}
```

**Error Responses:**

**Access Denied (403):**
```json
{
  "success": false,
  "error": "Access denied. Deck does not belong to user."
}
```

## GET /api/decks/:deckId/tags/:tagId

**Purpose:** Retrieves a specific tag within a deck.

**Authentication:** Required (JWT token)

**URL Parameters:**
- `deckId` (integer): Parent deck identifier
- `tagId` (integer): Tag identifier

**Business Rules:**
- Tag must exist within the specified deck
- User must own the parent deck

**Response (Success - 200):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "grammar",
    "deckId": 1,
    "flashcardCount": 5,
    "createdAt": "2024-01-15T10:45:00.000Z",
    "updatedAt": "2024-01-15T10:45:00.000Z"
  },
  "message": "Tag retrieved successfully"
}
```

**Error Responses:**

**Tag Not Found (404):**
```json
{
  "success": false,
  "error": "Tag not found in this deck"
}
```

### 3. Create Tag

**Purpose:** Creates a new tag within a specific deck.

**Endpoint:** `POST /api/decks/:deckId/tags`

**Authentication:** Required (JWT token)

**URL Parameters:**
- `deckId` (integer): Parent deck identifier

**Request Body:**
```json
{
  "name": "advanced-grammar"
}
```

**Validation Rules:**
- `name`: Required, string, unique within the deck
- `deckId`: Automatically set from URL parameter

**Uniqueness Constraint:**
```sql
@@unique([name, deckId])
```
- Tag names must be unique within each deck
- Same tag name can exist in different decks

**Response (Success - 201):**
```json
{
  "success": true,
  "data": {
    "id": 3,
    "name": "advanced-grammar",
    "deckId": 1,
    "flashcardCount": 0,
    "createdAt": "2024-01-15T11:00:00.000Z",
    "updatedAt": "2024-01-15T11:00:00.000Z"
  },
  "message": "Tag created successfully"
}
```

**Error Responses:**

**Duplicate Name (409):**
```json
{
  "success": false,
  "error": "Tag name already exists in this deck"
}
```

### 4. Update Tag

**Purpose:** Updates an existing tag's name.

**Endpoint:** `PUT /api/decks/:deckId/tags/:tagId`

**Authentication:** Required (JWT token)

**URL Parameters:**
- `deckId` (integer): Parent deck identifier
- `tagId` (integer): Tag identifier to update

**Request Body:**
```json
{
  "name": "intermediate-grammar"
}
```

**Business Rules:**
- Only the `name` field can be updated
- New name must be unique within the deck
- Tag must exist within the specified deck

**Response (Success - 200):**
```json
{
  "success": true,
  "data": {
    "id": 3,
    "name": "intermediate-grammar",
    "deckId": 1,
    "flashcardCount": 0,
    "createdAt": "2024-01-15T11:00:00.000Z",
    "updatedAt": "2024-01-15T11:05:00.000Z"
  },
  "message": "Tag updated successfully"
}
```

### 5. Delete Tag

**Purpose:** Permanently removes a tag from a deck.

**Endpoint:** `DELETE /api/decks/:deckId/tags/:tagId`

**Authentication:** Required (JWT token)

**URL Parameters:**
- `deckId` (integer): Parent deck identifier
- `tagId` (integer): Tag identifier to delete

**Cascade Behavior:**
- Tag association is removed from all related flashcards
- Flashcards are not deleted, only the tag relationship
- Tag record is permanently deleted

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Tag deleted successfully"
}
```

**Error Responses:**

**Tag Not Found (404):**
```json
{
  "success": false,
  "error": "Tag not found in this deck"
}
```

## Usage Examples

### Get All Tags for a Deck
```bash
curl -X GET http://localhost:3000/api/decks/1/tags \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Create New Tag
```bash
curl -X POST http://localhost:3000/api/decks/1/tags \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"name": "vocabulary"}'
```

### Update Tag Name
```bash
curl -X PUT http://localhost:3000/api/decks/1/tags/5 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"name": "basic-vocabulary"}'
```

### Delete Tag
```bash
curl -X DELETE http://localhost:3000/api/decks/1/tags/5 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```


---
