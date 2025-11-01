---
module: flashcards
version: 1.0
base_url: /api/flashcards
authentication: mixed
description: "Flashcard management endpoints for creating, reading, updating and studying flashcards"
---

# Flashcard API Endpoints

## POST /api/flashcards

**Purpose:** Creates a new individual flashcard.

**Authentication:** Required (JWT token)

**Request Body:**
```json
{
  "front": "¿Cómo se dice 'hello' en español?",
  "back": "Hola",
  "deckId": 1,
  "difficulty": 2,
  "tagId": 5
}
```

**Validation Rules:**
- `front`: Required, string, 1-1000 characters
- `back`: Required, string, 1-1000 characters
- `deckId`: Required, positive integer
- `difficulty`: Optional, integer 1-3 (default: 2)
- `tagId`: Optional, positive integer or null

**Business Rules:**
- Deck must exist and be owned by authenticated user
- Tag must exist and belong to the same deck (if provided)

**Response (Success - 201):**
```json
{
  "success": true,
  "message": "Flashcard creada exitosamente",
  "data": {
    "id": 1,
    "front": "¿Cómo se dice 'hello' en español?",
    "back": "Hola",
    "deckId": 1,
    "difficulty": 2,
    "lastReviewed": null,
    "nextReview": null,
    "reviewCount": 0,
    "tagId": 5,
    "tag": {
      "id": 5,
      "name": "grammar"
    },
    "createdAt": "2024-01-15T11:00:00.000Z",
    "updatedAt": "2024-01-15T11:00:00.000Z"
  }
}
```

## POST /api/flashcards/batch

**Purpose:** Creates multiple flashcards in a single transaction.

**Authentication:** Required (JWT token)

**Request Body:**
```json
{
  "flashcards": [
    {
      "front": "¿Cómo se dice 'hello' en español?",
      "back": "Hola",
      "deckId": 1,
      "difficulty": 2
    },
    {
      "front": "¿Cómo se dice 'goodbye' en español?",
      "back": "Adiós",
      "deckId": 1,
      "difficulty": 1
    }
  ]
}
```

**Validation Process:**
1. **Structure validation**: Checks for `flashcards` array
2. **Individual validation**: Validates each flashcard using `FlashcardDto.validateCreate`
3. **Business rules**: Verifies deck ownership for all flashcards
4. **Transaction safety**: All-or-nothing creation

**Response (Success - 201):**
```json
{
  "success": true,
  "message": "2 flashcards creadas exitosamente",
  "data": [
    {
      "id": 1,
      "front": "¿Cómo se dice 'hello' en español?",
      "back": "Hola",
      "deckId": 1,
      "difficulty": 2,
      "reviewCount": 0,
      "createdAt": "2024-01-15T11:00:00.000Z",
      "updatedAt": "2024-01-15T11:00:00.000Z"
    },
    {
      "id": 2,
      "front": "¿Cómo se dice 'goodbye' en español?",
      "back": "Adiós",
      "deckId": 1,
      "difficulty": 1,
      "reviewCount": 0,
      "createdAt": "2024-01-15T11:00:00.000Z",
      "updatedAt": "2024-01-15T11:00:00.000Z"
    }
  ]
}
```

**Error Handling:**
- **Partial failures**: Complete rollback if any validation fails
- **Detailed errors**: Returns specific validation errors for each flashcard

## GET /api/flashcards

**Purpose:** Retrieves all flashcards (admin/debug endpoint).

**Authentication:** Required (JWT token)

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Flashcards obtenidas exitosamente",
  "data": [
    {
      "id": 1,
      "front": "¿Cómo se dice 'hello' en español?",
      "back": "Hola",
      "deckId": 1,
      "difficulty": 2,
      "reviewCount": 3,
      "createdAt": "2024-01-15T11:00:00.000Z",
      "updatedAt": "2024-01-15T11:05:00.000Z"
    }
  ],
  "count": 1
}
```

## GET /api/flashcards/:id

**Purpose:** Retrieves a specific flashcard.

**Authentication:** Required (JWT token)

**URL Parameters:**
- `id` (integer): Flashcard ID

### 5. Get Flashcards by Deck

**Purpose:** Retrieves all flashcards for a specific deck with optional tag filtering.

**Endpoint:** `GET /api/flashcards/deck/:deckId`

**Authentication:** Required (JWT token)

**URL Parameters:**
- `deckId` (integer): Deck ID

**Query Parameters:**
- `page` (integer): Page number (default: 0)
- `pageSize` (integer): Items per page (default: 15)
- `tagId` (integer): Optional tag filter

**Response (Success - 200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "front": "¿Cómo se dice 'hello' en español?",
      "back": "Hola",
      "deckId": 1,
      "difficulty": 2,
      "tagId": 5,
      "tag": {
        "id": 5,
        "name": "vocabulary"
      }
    }
  ],
  "total": 1,
  "page": 0,
  "pageSize": 15,
  "message": "Flashcards del deck obtenidas exitosamente"
}
```

### 6. Update Flashcard

**Purpose:** Updates an existing flashcard.

**Endpoint:** `PUT /api/flashcards/:id`

**Authentication:** Required (JWT token)

**Request Body (all fields optional):**
```json
{
  "front": "¿Cómo se dice 'hello' en español?",
  "back": "Hola",
  "difficulty": 1,
  "tagId": null
}
```

### 7. Delete Flashcard

**Purpose:** Permanently deletes a flashcard.

**Endpoint:** `DELETE /api/flashcards/:id`

**Authentication:** Required (JWT token)

## Search Operations

### 1. Search in Deck (Public)

**Purpose:** Searches flashcards within a specific deck by content.

**Endpoint:** `GET /api/flashcards/deck/:deckId/search`

**Authentication:** ❌ Public (no auth required)

**URL Parameters:**
- `deckId` (integer): Deck ID to search in

**Query Parameters:**
- `q` (string): Search term
- `page` (integer): Page number (default: 0)
- `pageSize` (integer): Items per page (default: 15)

**Search Behavior:**
- Searches in both `front` and `back` fields
- Case-insensitive matching
- Returns paginated results

**Response (Success - 200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "front": "¿Cómo se dice 'hello' en español?",
      "back": "Hola",
      "deckId": 1,
      "difficulty": 2
    }
  ],
  "total": 1,
  "page": 0,
  "pageSize": 15,
  "message": "Búsqueda de flashcards en deck"
}
```

### 2. Global Search (Authenticated)

**Purpose:** Searches across all user flashcards.

**Endpoint:** `GET /api/flashcards/search`

**Authentication:** Required (JWT token)

**Query Parameters:**
- `q` (string): **Required** - Search term
- `deckId` (integer): Optional deck filter

**Search Logic:**
```javascript
// Searches in front AND back fields
card.front.toLowerCase().includes(searchTerm.toLowerCase()) ||
card.back.toLowerCase().includes(searchTerm.toLowerCase())
```

## Study Operations

### 1. Get Due Flashcards

**Purpose:** Retrieves flashcards ready for review based on spaced repetition algorithm.

**Endpoint:** `GET /api/flashcards/due`

**Authentication:** Required (JWT token)

**Query Parameters:**
- `deckId` (integer): Optional - Filter by specific deck

**Spaced Repetition Logic:**
- Returns cards where `nextReview <= currentDate` OR `nextReview IS NULL`
- Cards are ordered by next review date (oldest first)
- Includes cards never reviewed (`nextReview = null`)

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Flashcards para revisión obtenidas exitosamente",
  "data": [
    {
      "id": 1,
      "front": "¿Cómo se dice 'hello' en español?",
      "back": "Hola",
      "deckId": 1,
      "difficulty": 2,
      "lastReviewed": "2024-01-14T11:00:00.000Z",
      "nextReview": "2024-01-15T11:00:00.000Z",
      "reviewCount": 3
    }
  ],
  "count": 1
}
```

### 2. Mark Flashcard as Reviewed

**Purpose:** Updates flashcard after review with new difficulty assessment.

**Endpoint:** `PUT /api/flashcards/:id/review`

**Authentication:** Required (JWT token)

**URL Parameters:**
- `id` (integer): Flashcard ID

**Request Body:**
```json
{
  "difficulty": 2
}
```

**Spaced Repetition Algorithm:**
- **Difficulty 1 (Easy)**: Next review in 4 days
- **Difficulty 2 (Normal)**: Next review in 1 day
- **Difficulty 3 (Hard)**: Next review in 4 hours

**Algorithm Implementation:**
```javascript
const intervals = {
  1: 4 * 24 * 60 * 60 * 1000,  // 4 days
  2: 1 * 24 * 60 * 60 * 1000,  // 1 day
  3: 4 * 60 * 60 * 1000        // 4 hours
};

const nextReviewDate = new Date(Date.now() + intervals[difficulty]);
```

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Flashcard marcada como revisada exitosamente",
  "data": {
    "id": 1,
    "front": "¿Cómo se dice 'hello' en español?",
    "back": "Hola",
    "difficulty": 2,
    "lastReviewed": "2024-01-15T11:00:00.000Z",
    "nextReview": "2024-01-16T11:00:00.000Z",
    "reviewCount": 4
  }
}
```

## AI-Powered Features

### Generate Flashcards with AI

**Purpose:** Uses OpenAI to generate flashcards from text content.

**Endpoint:** `POST /api/flashcards/ai-generate`

**Authentication:** ❌ Public (no auth required)

**Request Body:**
```json
{
  "text": "The water cycle involves evaporation, condensation, and precipitation..."
}
```

**AI Process:**
1. **Content Analysis**: OpenAI analyzes the provided text
2. **Flashcard Generation**: Creates Q&A pairs automatically
3. **Format Standardization**: Returns consistent flashcard format
4. **No Persistence**: Results not saved to database

**Response (Success - 200):**
```json
{
  "flashcards": [
    {
      "front": "What is the first stage of the water cycle?",
      "back": "Evaporation"
    },
    {
      "front": "What happens during condensation?",
      "back": "Water vapor turns into liquid water droplets"
    },
    {
      "front": "What is precipitation?",
      "back": "Water falling from clouds as rain, snow, etc."
    }
  ]
}
```

**Error Handling:**
- **Empty text**: Returns 400 with validation message
- **API errors**: Returns 500 with generic error message
- **Rate limits**: Handled by OpenAI client with retries

## Usage Examples

### Create Single Flashcard
```bash
curl -X POST http://localhost:3000/api/flashcards \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "front": "¿Cómo se dice '\''hello'\'' en español?",
    "back": "Hola",
    "deckId": 1,
    "difficulty": 2
  }'
```

### Bulk Create Flashcards
```bash
curl -X POST http://localhost:3000/api/flashcards/batch \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "flashcards": [
      {"front": "Question 1", "back": "Answer 1", "deckId": 1},
      {"front": "Question 2", "back": "Answer 2", "deckId": 1}
    ]
  }'
```

### Get Due Cards for Study
```bash
curl -X GET http://localhost:3000/api/flashcards/due/1 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Mark Card as Reviewed
```bash
curl -X PUT http://localhost:3000/api/flashcards/1/review \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"difficulty": 2}'
```

### AI Generation
```bash
curl -X POST http://localhost:3000/api/flashcards/ai-generate \
  -H "Content-Type: application/json" \
  -d '{"text": "Photosynthesis is the process by which plants convert sunlight into energy..."}'
```

---
