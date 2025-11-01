# Study System Module

## Overview

The study system module manages interactive flashcard study sessions with spaced repetition algorithms, progress tracking, and comprehensive statistics.

## High-Level Flow

```plantuml
@startuml
!theme plain
hide empty description

title Study Session Flow - High Level

start
:POST /api/study/start
Input: {deckId, limit?, tagId?}
note right
  **Session Initialization:**
  - Validate deck access
  - Load due flashcards
  - Create study queue
  - Initialize session stats
  - Return first card
end note

:Session created with sessionId
note right
  Response: {sessionId, currentCard, sessionStats}
end note

:GET /api/study/:sessionId/next
note right
  **Get Next Card:**
  - Retrieve next card from queue
  - Update progress tracking
  - Return card or session finished
end note

:Next card returned
note right
  Response: {currentCard, progress, sessionStats}
end note

:POST /api/study/:sessionId/review
Input: {cardId, difficulty}
note right
  **Review Card:**
  - Validate difficulty (1-3)
  - Update spaced repetition data
  - Mark card as reviewed
  - Update session statistics
end note

:Card reviewed successfully
note right
  Response: {cardUpdated, sessionStats}
end note

if (More cards available?) then (yes)
  :Continue studying
else (no)
  :POST /api/study/:sessionId/finish
  note right
    **Finish Session:**
    - Calculate final statistics
    - Mark session as completed
    - Return completion summary
  end note

  :Session completed
  note right
    Response: {finalStats, completionRate}
  end note
endif

stop

@enduml
```

## Session Management

### Session Lifecycle

**Session States:**
- **Active**: Session in progress, cards being reviewed
- **Finished**: Session completed, all cards reviewed
- **Expired**: Session TTL exceeded (30 minutes)

**Session Storage:**
- In-memory storage (Map) for development
- TTL: 30 minutes from creation
- Automatic cleanup of expired sessions

### Study Queue Algorithm

The system uses a `StudyQueue` class that manages card presentation order:

```javascript
// StudyQueue implementation
class StudyQueue {
  constructor(cards) {
    this.queue = [...cards];
    this.currentIndex = 0;
  }

  next() {
    if (this.currentIndex < this.queue.length) {
      return this.queue[this.currentIndex++];
    }
    return null;
  }

  hasNext() {
    return this.currentIndex < this.queue.length;
  }

  getProgress() {
    return {
      current: this.currentIndex,
      total: this.queue.length,
      remaining: this.queue.length - this.currentIndex,
      percentage: Math.round((this.currentIndex / this.queue.length) * 100)
    };
  }
}
```

## Study Endpoints

### 1. Start Study Session

**Purpose:** Initializes a new study session for a deck.

**Endpoint:** `POST /api/study/start`

**Authentication:** Required (JWT token)

**Request Body:**
```json
{
  "deckId": 1,
  "limit": 20,
  "tagId": 5
}
```

**Validation Rules:**
- `deckId`: Required, integer, user must own the deck
- `limit`: Optional, integer, 1-50 (default: 20)
- `tagId`: Optional, integer, filters cards by tag

**Session Creation Process:**
1. **Access validation**: Verify user owns the deck
2. **Card loading**: Retrieve flashcards from deck (filtered by tag if provided)
3. **Queue initialization**: Create StudyQueue with loaded cards
4. **Session storage**: Store session with TTL
5. **First card**: Return first card for study

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Sesión de estudio iniciada exitosamente",
  "data": {
    "sessionId": "study_550e8400-e29b-41d4-a716-446655440001",
    "totalCards": 15,
    "currentCard": {
      "id": 1,
      "front": "¿Cómo se dice 'hello' en español?",
      "back": "Hola",
      "difficulty": 2,
      "reviewCount": 3,
      "lastReviewed": "2024-01-14T11:00:00.000Z",
      "nextReview": "2024-01-15T11:00:00.000Z",
      "createdAt": "2024-01-10T10:00:00.000Z",
      "updatedAt": "2024-01-14T11:00:00.000Z"
    },
    "queueLength": 14,
    "sessionStats": {
      "cardsReviewed": 0,
      "easyCount": 0,
      "normalCount": 0,
      "hardCount": 0,
      "timeSpent": 0,
      "averageResponseTime": 0
    },
    "deckName": "Spanish Vocabulary"
  }
}
```

### 2. Get Next Card

**Purpose:** Retrieves the next flashcard in the study session.

**Endpoint:** `GET /api/study/:sessionId/next`

**Authentication:** Required (JWT token)

**URL Parameters:**
- `sessionId` (string): Study session identifier

**Logic Flow:**
1. **Session validation**: Check session exists and is active
2. **Queue check**: Verify more cards are available
3. **Progress update**: Calculate current progress
4. **Card retrieval**: Get next card from queue

**Session Completion Response:**
```json
{
  "success": true,
  "message": "Sesión completada",
  "data": {
    "sessionFinished": true,
    "message": "No hay más cards en esta sesión",
    "finalStats": {
      "cardsReviewed": 15,
      "easyCount": 8,
      "normalCount": 5,
      "hardCount": 2,
      "timeSpent": 1200,
      "averageResponseTime": 80
    }
  }
}
```

**Next Card Response:**
```json
{
  "success": true,
  "message": "Siguiente card obtenida exitosamente",
  "data": {
    "currentCard": {
      "id": 2,
      "front": "¿Cómo se dice 'goodbye' en español?",
      "back": "Adiós",
      "difficulty": 1,
      "reviewCount": 5
    },
    "queueLength": 13,
    "progress": {
      "current": 1,
      "total": 15,
      "remaining": 14,
      "percentage": 7
    },
    "sessionStats": {
      "cardsReviewed": 1,
      "easyCount": 1,
      "normalCount": 0,
      "hardCount": 0,
      "timeSpent": 45,
      "averageResponseTime": 45
    }
  }
}
```

### 3. Review Card

**Purpose:** Marks a flashcard as reviewed and updates spaced repetition data.

**Endpoint:** `POST /api/study/:sessionId/review`

**Authentication:** Required (JWT token)

**URL Parameters:**
- `sessionId` (string): Study session identifier

**Request Body:**
```json
{
  "cardId": 1,
  "difficulty": 2
}
```

**Validation Rules:**
- `cardId`: Required, integer, must exist in session
- `difficulty`: Required, integer, values: 1 (easy), 2 (normal), 3 (hard)

**Spaced Repetition Algorithm:**
```javascript
const intervals = {
  1: 4 * 24 * 60 * 60 * 1000,  // 4 days (easy)
  2: 1 * 24 * 60 * 60 * 1000,  // 1 day (normal)
  3: 4 * 60 * 60 * 1000        // 4 hours (hard)
};

const nextReviewDate = new Date(Date.now() + intervals[difficulty]);
```

**Statistics Update:**
- Increment `cardsReviewed` counter
- Update difficulty counters (`easyCount`, `normalCount`, `hardCount`)
- Calculate response time
- Update average response time

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Card marcada como revisada exitosamente",
  "data": {
    "cardUpdated": {
      "id": 1,
      "front": "¿Cómo se dice 'hello' en español?",
      "back": "Hola",
      "difficulty": 2,
      "reviewCount": 4,
      "lastReviewed": "2024-01-15T11:00:00.000Z",
      "nextReview": "2024-01-16T11:00:00.000Z"
    },
    "sessionStats": {
      "cardsReviewed": 2,
      "easyCount": 1,
      "normalCount": 1,
      "hardCount": 0,
      "timeSpent": 90,
      "averageResponseTime": 45
    }
  }
}
```

### 4. Get Session Status

**Purpose:** Retrieves current status and statistics of a study session.

**Endpoint:** `GET /api/study/:sessionId/status`

**Authentication:** Required (JWT token)

**URL Parameters:**
- `sessionId` (string): Study session identifier

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Estado de sesión obtenido exitosamente",
  "data": {
    "sessionId": "study_550e8400-e29b-41d4-a716-446655440001",
    "status": "active",
    "totalCards": 15,
    "cardsReviewed": 5,
    "remainingCards": 10,
    "progress": {
      "current": 5,
      "total": 15,
      "remaining": 10,
      "percentage": 33
    },
    "sessionStats": {
      "cardsReviewed": 5,
      "easyCount": 3,
      "normalCount": 1,
      "hardCount": 1,
      "timeSpent": 240,
      "averageResponseTime": 48
    },
    "currentCard": {
      "id": 6,
      "front": "¿Cómo se dice 'thank you' en español?",
      "back": "Gracias",
      "difficulty": 2
    }
  }
}
```

### 5. Finish Session

**Purpose:** Completes a study session and returns final statistics.

**Endpoint:** `POST /api/study/:sessionId/finish`

**Authentication:** Required (JWT token)

**URL Parameters:**
- `sessionId` (string): Study session identifier

**Completion Logic:**
1. **Status update**: Mark session as "finished"
2. **Final statistics**: Calculate completion rate and final metrics
3. **Cleanup**: Schedule session deletion (5 minutes delay)
4. **Response**: Return final session summary

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Sesión de estudio finalizada exitosamente",
  "data": {
    "sessionId": "study_550e8400-e29b-41d4-a716-446655440001",
    "finalStats": {
      "cardsReviewed": 15,
      "easyCount": 8,
      "normalCount": 5,
      "hardCount": 2,
      "timeSpent": 1200,
      "averageResponseTime": 80,
      "finishedAt": "2024-01-15T11:20:00.000Z",
      "completionRate": 100
    }
  }
}
```

### 6. Get Global Statistics

**Purpose:** Retrieves system-wide study statistics (admin/debug endpoint).

**Endpoint:** `GET /api/study/stats`

**Authentication:** Required (JWT token)

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Estadísticas globales obtenidas exitosamente",
  "data": {
    "totalSessions": 5,
    "activeSessions": 2,
    "totalCardsReviewed": 47,
    "averageSessionTime": 850
  }
}
```

## Error Handling

### Session Errors

**Session Not Found (404):**
```json
{
  "success": false,
  "message": "Sesión no encontrada o expirada"
}
```

**Session Expired (404):**
```json
{
  "success": false,
  "message": "La sesión de estudio ha expirado"
}
```

**Invalid Difficulty (400):**
```json
{
  "success": false,
  "message": "La dificultad debe ser 1 (fácil), 2 (normal) o 3 (difícil)"
}
```

**Deck Access Denied (400):**
```json
{
  "success": false,
  "message": "Error al iniciar sesión de estudio: Deck no encontrado o sin permisos de acceso (userId: 1, deckId: 999)"
}
```

**No Cards Available (400):**
```json
{
  "success": false,
  "message": "Error al iniciar sesión de estudio: No hay flashcards disponibles para estudiar en este deck (deckId: 1, cards found: 0)"
}
```

## Session Statistics

### Statistics Structure

```javascript
{
  cardsReviewed: 15,     // Total cards reviewed in session
  easyCount: 8,          // Cards marked as easy (1)
  normalCount: 5,        // Cards marked as normal (2)
  hardCount: 2,          // Cards marked as hard (3)
  timeSpent: 1200,       // Total session time in seconds
  averageResponseTime: 80 // Average response time per card in seconds
}
```

### Progress Tracking

```javascript
{
  current: 5,      // Current card index (0-based)
  total: 15,       // Total cards in session
  remaining: 10,   // Cards left to review
  percentage: 33   // Completion percentage
}
```

## Usage Examples

### Start Study Session
```bash
curl -X POST http://localhost:3000/api/study/start \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "deckId": 1,
    "limit": 10,
    "tagId": 5
  }'
```

### Review Card
```bash
curl -X POST http://localhost:3000/api/study/study_123/review \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "cardId": 1,
    "difficulty": 2
  }'
```

### Check Session Status
```bash
curl -X GET http://localhost:3000/api/study/study_123/status \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Finish Session
```bash
curl -X POST http://localhost:3000/api/study/study_123/finish \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

*The study system provides comprehensive session management with spaced repetition, progress tracking, and detailed statistics for effective flashcard learning.*
