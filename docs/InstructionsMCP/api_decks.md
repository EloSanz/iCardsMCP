---
module: decks
version: 1.0
base_url: /api/decks
authentication: required
description: "Deck management endpoints for creating, reading, updating and deleting flashcard decks"
---

# Deck API Endpoints

## GET /api/decks

**Purpose:** Retrieves all decks owned by the authenticated user.

**Authentication:** Required (JWT token)

**Query Parameters:** None

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Decks obtenidos exitosamente",
  "data": [
    {
      "id": 1,
      "name": "Spanish Vocabulary",
      "description": "Basic Spanish words and phrases",
      "coverUrl": "data:image/jpeg;base64,/9j/4AAQSkZJRgABA...",
      "createdAt": "2024-01-15T10:30:00.000Z",
      "updatedAt": "2024-01-15T11:00:00.000Z"
    }
  ],
  "count": 1
}
```

**Error Responses:**

**Unauthorized (401):**
```json
{
  "success": false,
  "message": "Token de autenticación requerido"
}
```

## GET /api/decks/mcp

**Purpose:** Retrieves all decks owned by the authenticated user (MCP optimized - without coverUrl).

This endpoint is specifically designed for MCP tools to reduce payload size and improve performance by excluding cover images from the database query itself.

**Authentication:** Required (JWT token)

**Query Parameters:** None

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Decks obtenidos exitosamente (sin coverUrl)",
  "data": [
    {
      "id": 1,
      "name": "Spanish Vocabulary",
      "description": "Basic Spanish words and phrases",
      "createdAt": "2024-01-15T10:30:00.000Z",
      "updatedAt": "2024-01-15T11:00:00.000Z"
    }
  ],
  "count": 1
}
```

**Note:** This endpoint excludes `coverUrl` field at the database level for better performance in MCP contexts.

**Error Responses:** Same as GET /api/decks

## GET /api/decks/:id

**Purpose:** Retrieves a specific deck with ownership verification.

**Authentication:** Required (JWT token)

**URL Parameters:**
- `id` (integer): Deck ID to retrieve

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Deck obtenido exitosamente",
  "data": {
    "id": 1,
    "name": "Spanish Vocabulary",
    "description": "Basic Spanish words and phrases",
    "coverUrl": "data:image/jpeg;base64,/9j/4AAQSkZJRgABA...",
    "createdAt": "2024-01-15T10:30:00.000Z",
    "updatedAt": "2024-01-15T11:00:00.000Z"
  }
}
```

**Error Responses:**

**Not Found (404):**
```json
{
  "success": false,
  "message": "Deck no encontrado"
}
```

**Forbidden (403):**
```json
{
  "success": false,
  "message": "No tienes permiso para ver este deck"
}
```

## POST /api/decks

**Purpose:** Creates a new deck with optional AI-generated cover image.

**Authentication:** Required (JWT token)

**Request Body:**
```json
{
  "name": "Spanish Vocabulary",
  "description": "Basic Spanish words and phrases for beginners",
  "generateCover": true
}
```

**Validation Rules:**
- `name`: Required, string, 1-255 characters
- `description`: Optional, string, max 1000 characters
- `generateCover`: Optional, boolean, default false

**Response (Success - 201):**
```json
{
  "success": true,
  "message": "Deck creado exitosamente",
  "data": {
    "id": 1,
    "name": "Spanish Vocabulary",
    "description": "Basic Spanish words and phrases for beginners",
    "coverUrl": null,
    "createdAt": "2024-01-15T10:30:00.000Z",
    "updatedAt": "2024-01-15T10:30:00.000Z"
  }
}
```

**AI Cover Generation:**
- Runs asynchronously after deck creation
- Uses OpenAI DALL-E to generate relevant cover image
- Updates `coverUrl` field with base64-encoded image
- No notification sent to client (fire-and-forget)

**Error Responses:**

**Validation Error (400):**
```json
{
  "success": false,
  "message": "Validation error",
  "errors": ["El nombre es requerido y debe ser una cadena de texto"]
}
```

## PUT /api/decks/:id

**Purpose:** Updates an existing deck's information.

**Authentication:** Required (JWT token)

**URL Parameters:**
- `id` (integer): Deck ID to update

**Request Body (all fields optional):**
```json
{
  "name": "Advanced Spanish Vocabulary",
  "description": "Intermediate to advanced Spanish words and phrases"
}
```

**Ownership Verification:**
- Checks if authenticated user owns the deck
- Returns 403 Forbidden if access denied

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Deck actualizado exitosamente",
  "data": {
    "id": 1,
    "name": "Advanced Spanish Vocabulary",
    "description": "Intermediate to advanced Spanish words and phrases",
    "coverUrl": "data:image/jpeg;base64,/9j/4AAQSkZJRgABA...",
    "createdAt": "2024-01-15T10:30:00.000Z",
    "updatedAt": "2024-01-15T11:00:00.000Z"
  }
}
```

## DELETE /api/decks/:id

**Purpose:** Permanently deletes a deck and all associated flashcards/tags.

**Authentication:** Required (JWT token)

**URL Parameters:**
- `id` (integer): Deck ID to delete

**Database Behavior:**
- **Cascade delete**: Removes all associated flashcards and tags
- **Foreign key constraints**: Ensures data integrity

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Deck eliminado exitosamente",
  "data": null
}
```

## AI-Powered Features

## POST /api/decks/suggest-topics

**Purpose:** Analyzes existing user decks to suggest new learning topics using AI.

**Authentication:** Required (JWT token)

**Request Body:**
```json
{
  "count": 3
}
```

**Algorithm:**
1. **Data Collection**: Retrieves all user deck names and descriptions
2. **AI Analysis**: Uses OpenAI to analyze existing topics
3. **Suggestion Generation**: Creates complementary topic suggestions
4. **Response**: Returns array of suggested topics

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Temas sugeridos exitosamente",
  "data": {
    "topics": [
      "Spanish Grammar Rules",
      "Spanish Idioms and Expressions",
      "Spanish Pronunciation Guide"
    ]
  }
}
```

## POST /api/decks/generate-with-ai

**Purpose:** Creates complete decks with flashcards using AI generation.

**Authentication:** Required (JWT token)

**Request Body:**
```json
{
  "mode": "free",
  "topic": "Spanish Vocabulary for Cooking",
  "flashcardCount": 15,
  "generateCover": true
}
```

**Generation Modes:**

#### Mode: "free"
- Basic topic-based generation
- Generates flashcards from topic description
- Standard difficulty distribution

#### Mode: "configured"
```json
{
  "mode": "configured",
  "topic": "French Vocabulary",
  "flashcardCount": 20,
  "difficulty": "intermediate",
  "tags": ["verbs", "nouns", "grammar"],
  "generateCover": true
}
```

#### Mode: "suggested"
- Uses suggested topics from AI analysis
- Same as "free" mode but with AI-suggested topics

**AI Generation Process:**
1. **Content Creation**: OpenAI generates flashcards based on topic
2. **Deck Creation**: Creates deck with generated cover
3. **Flashcard Creation**: Bulk creates flashcards with proper validation
4. **Tag Creation**: Creates and associates tags if specified
5. **Cover Generation**: Generates AI cover image

**Response (Success - 201):**
```json
{
  "success": true,
  "message": "Deck 'Spanish Cooking Vocabulary' generado exitosamente con 15 flashcards",
  "data": {
    "deck": {
      "id": 2,
      "name": "Spanish Cooking Vocabulary",
      "description": "Essential Spanish words for cooking and kitchen",
      "coverUrl": "data:image/jpeg;base64,/9j/4AAQSkZJRgABA...",
      "createdAt": "2024-01-15T11:00:00.000Z",
      "updatedAt": "2024-01-15T11:00:00.000Z"
    },
    "flashcardsCreated": 15,
    "tagsCreated": 3,
    "coverGenerated": true
  }
}
```

## Usage Examples

### Create Deck with AI Cover
```bash
curl -X POST http://localhost:3000/api/decks \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Python Programming",
    "description": "Learn Python basics",
    "generateCover": true
  }'
```

### Generate AI Deck
```bash
curl -X POST http://localhost:3000/api/decks/generate-with-ai \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "configured",
    "topic": "Machine Learning Algorithms",
    "flashcardCount": 20,
    "difficulty": "advanced",
    "tags": ["ml", "algorithms", "ai"],
    "generateCover": true
  }'
```

### Get Topic Suggestions
```bash
curl -X POST http://localhost:3000/api/decks/suggest-topics \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"count": 5}'
```

## GET /api/decks/flashcards-count

**Purpose:** Retrieves the total count of flashcards across all user decks.

**Authentication:** Required (JWT token)

**Query Parameters:** None

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Flashcards count for all decks retrieved successfully",
  "data": {
    "totalFlashcards": 150,
    "byDeck": [
      {
        "deckId": 1,
        "deckName": "Spanish Vocabulary",
        "flashcardsCount": 50
      },
      {
        "deckId": 2,
        "deckName": "Python Basics",
        "flashcardsCount": 100
      }
    ]
  }
}
```

## GET /api/decks/untagged-flashcards-count

**Purpose:** Retrieves the count of untagged flashcards across all user decks.

**Authentication:** Required (JWT token)

**Query Parameters:** None

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Untagged flashcards count across all decks retrieved successfully",
  "data": {
    "totalUntaggedFlashcards": 25,
    "byDeck": [
      {
        "deckId": 1,
        "deckName": "Spanish Vocabulary",
        "untaggedCount": 10
      },
      {
        "deckId": 2,
        "deckName": "Python Basics",
        "untaggedCount": 15
      }
    ]
  }
}
```

## GET /api/decks/:deckId/tag-count

**Purpose:** Retrieves the count of tags for a specific deck.

**Authentication:** Required (JWT token)

**URL Parameters:**
- `deckId` (integer): Deck ID to count tags for

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Tag count retrieved successfully",
  "data": {
    "deckId": 1,
    "tagCount": 5
  }
}
```

**Error Responses:**
- **Forbidden (403):** User does not own this deck
- **Not Found (404):** Deck not found

## GET /api/decks/:deckId/flashcards-by-tag

**Purpose:** Retrieves the count of flashcards grouped by tag for a specific deck.

**Authentication:** Required (JWT token)

**URL Parameters:**
- `deckId` (integer): Deck ID to get flashcards by tag for

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Flashcards by tag count retrieved successfully",
  "data": {
    "deckId": 1,
    "flashcardsByTag": [
      {
        "tagId": 1,
        "tagName": "Grammar",
        "count": 15
      },
      {
        "tagId": 2,
        "tagName": "Vocabulary",
        "count": 25
      },
      {
        "tagId": 3,
        "tagName": "Verbs",
        "count": 10
      }
    ]
  }
}
```

**Error Responses:**
- **Forbidden (403):** User does not own this deck
- **Not Found (404):** Deck not found

## GET /api/decks/:deckId/untagged-flashcards-count

**Purpose:** Retrieves the count of untagged flashcards for a specific deck.

**Authentication:** Required (JWT token)

**URL Parameters:**
- `deckId` (integer): Deck ID to count untagged flashcards for

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Untagged flashcards count retrieved successfully",
  "data": {
    "deckId": 1,
    "untaggedFlashcardsCount": 8
  }
}
```

**Error Responses:**
- **Forbidden (403):** User does not own this deck
- **Not Found (404):** Deck not found

## Flashcards by Deck (with Pagination Control)

**Purpose:** Retrieves flashcards for a specific deck with flexible pagination options.

**Authentication:** Required (JWT token)

**URL Parameters:**
- `deckId` (integer): Deck ID to get flashcards for

**Query Parameters:**
- `page` (integer, optional): Page number (default: 0)
- `pageSize` (integer, optional): Items per page (default: 50, max: 100). Use `?all=true` to get all flashcards without limit
- `all` (boolean, optional): Set to 'true' to get all flashcards without pagination (ignores pageSize)
- `tagId` (integer, optional): Filter flashcards by tag ID

**Response (Success - 200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "front": "Hello",
      "back": "Hola",
      "deckId": 1,
      "difficulty": 2,
      "tagId": 1,
      "tag": {
        "id": 1,
        "name": "Greeting",
        "color": "#FF6B6B"
      },
      "createdAt": "2024-01-15T10:30:00.000Z"
    }
  ],
  "total": 25,
  "page": 0,
  "pageSize": 50,
  "message": "Flashcards obtenidas exitosamente"
}
```

**Usage Examples:**
```bash
# Default pagination (50 flashcards per page)
curl -X GET http://localhost:3000/api/flashcards/deck/1 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Custom page size (25 flashcards per page)
curl -X GET "http://localhost:3000/api/flashcards/deck/1?pageSize=25" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Get ALL flashcards (no pagination limit)
curl -X GET "http://localhost:3000/api/flashcards/deck/1?all=true" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Filter by tag
curl -X GET "http://localhost:3000/api/flashcards/deck/1?tagId=2" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## API Robustness Features

The decks API now supports specialized queries using Prisma ORM for efficient database operations:

- **Tag counting**: Optimized queries for counting tags per deck
- **Flashcard distribution**: Detailed breakdowns of flashcards by tag
- **Untagged content tracking**: Specialized endpoints for untagged flashcards
- **Flexible pagination**: Default 50 flashcards per page (upgraded from 15), with `?all=true` for unlimited results
- **Performance optimization**: Direct database-level queries without unnecessary data loading
- **Ownership verification**: All endpoints include user ownership checks
- **Comprehensive statistics**: Multiple endpoints for different types of counts and aggregations

### Pagination Behavior

- **Default limit**: 50 flashcards per page (increased from 15 for better user experience)
- **All results**: Use `?all=true` parameter to bypass pagination and get all flashcards
- **Custom limits**: Use `?pageSize=N` for custom page sizes (max 100)
- **Page navigation**: Use `?page=N` for specific page numbers

These specialized endpoints allow for granular data analysis and efficient querying without loading unnecessary data.
