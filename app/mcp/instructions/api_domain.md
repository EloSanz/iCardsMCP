# API Domain Models

## Summary

This document provides a comprehensive overview of the main domain entities and DTOs in the Flashcard Learning Platform API. The API uses a clean architecture with separate layers for domain models, DTOs, and database entities.

1. **User**: Authentication and user management entity
2. **Deck**: Collection of flashcards with AI-generated covers
3. **Flashcard**: Individual study cards with spaced repetition data
4. **Tag**: Organization labels associated with decks
5. **DTOs**: Data Transfer Objects for API communication

All entities use Prisma ORM for database mapping, and all date fields use ISO 8601 format. String IDs are auto-incrementing integers, and all entities include audit fields (createdAt, updatedAt).

## Table of Contents

1. [User](#user)
2. [Deck](#deck)
3. [Flashcard](#flashcard)
4. [Tag](#tag)
5. [DTOs and Response Formats](#dtos-and-response-formats)

---

## User

The `User` entity represents authenticated users in the system. It handles authentication and authorization for accessing protected resources.

<!-- tabs:start -->

### **Database Model**

```sql
model User {
  id        Int      @id @default(autoincrement())
  username  String   @unique
  password  String
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  // Relations
  decks     Deck[]
}
```

### **Fields**

- `id`: Integer - Unique identifier (auto-increment)
- `username`: String - Unique username for authentication
- `password`: String - Hashed password using bcrypt
- `createdAt`: DateTime - Account creation timestamp
- `updatedAt`: DateTime - Last account modification timestamp

### **Class**

```javascript
// Domain model representation
class User {
  constructor(data = {}) {
    this.id = data.id;
    this.username = data.username;
    this.password = data.password;
    this.createdAt = data.createdAt;
    this.updatedAt = data.updatedAt;
  }
}
```

### **JSON Schema**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "id": {"type": "integer", "minimum": 1},
    "username": {"type": "string", "minLength": 3, "maxLength": 30},
    "password": {"type": "string"},
    "createdAt": {"type": "string", "format": "date-time"},
    "updatedAt": {"type": "string", "format": "date-time"}
  },
  "required": ["id", "username", "createdAt", "updatedAt"]
}
```

### **JSON Example**

```json
{
  "id": 1,
  "username": "johndoe",
  "createdAt": "2024-01-15T10:00:00.000Z",
  "updatedAt": "2024-01-15T10:00:00.000Z"
}
```

<!-- tabs:end -->

---

## Deck

The `Deck` entity represents collections of flashcards. Decks can have AI-generated covers and are owned by users.

<!-- tabs:start -->

### **Database Model**

```sql
model Deck {
  id          Int      @id @default(autoincrement())
  name        String
  description String   @db.Text
  coverUrl    String?  // AI-generated cover URL
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  // Relations
  userId      Int
  user        User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  flashcards  Flashcard[]
  tags        Tag[]
}
```

### **Fields**

- `id`: Integer - Unique identifier (auto-increment)
- `name`: String - Deck name (max 255 chars)
- `description`: String - Deck description (max 1000 chars, optional)
- `coverUrl`: String - URL of AI-generated cover image (optional)
- `userId`: Integer - Owner user ID (foreign key)
- `createdAt`: DateTime - Deck creation timestamp
- `updatedAt`: DateTime - Last deck modification timestamp

### **Class**

```javascript
class Deck {
  constructor(data = {}) {
    this.id = data.id;
    this.name = data.name;
    this.description = data.description;
    this.coverUrl = data.coverUrl;
    this.userId = data.userId;
    this.createdAt = data.createdAt;
    this.updatedAt = data.updatedAt;
  }
}
```

### **JSON Schema**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "id": {"type": "integer", "minimum": 1},
    "name": {"type": "string", "maxLength": 255},
    "description": {"type": "string", "maxLength": 1000},
    "coverUrl": {"type": "string", "format": "uri"},
    "createdAt": {"type": "string", "format": "date-time"},
    "updatedAt": {"type": "string", "format": "date-time"}
  },
  "required": ["id", "name", "createdAt", "updatedAt"]
}
```

### **JSON Example**

```json
{
  "id": 1,
  "name": "Spanish Vocabulary",
  "description": "Basic Spanish words and phrases for beginners",
  "coverUrl": "https://example.com/covers/spanish-vocab.jpg",
  "createdAt": "2024-01-15T10:30:00.000Z",
  "updatedAt": "2024-01-15T10:30:00.000Z"
}
```

<!-- tabs:end -->

---

## Flashcard

The `Flashcard` entity represents individual study cards with spaced repetition tracking.

<!-- tabs:start -->

### **Database Model**

```sql
model Flashcard {
  id          Int      @id @default(autoincrement())
  front       String   @db.Text  // Question/prompt
  back        String   @db.Text  // Answer/explanation
  deckId      Int      // Foreign key to Deck
  deck        Deck     @relation(fields: [deckId], references: [id], onDelete: Cascade)

  // Spaced repetition fields
  difficulty  Int?     @default(2) // 1=easy, 2=normal, 3=hard
  lastReviewed DateTime?
  nextReview  DateTime?
  reviewCount Int      @default(0)

  // Relations
  tagId       Int?
  tag         Tag?     @relation(fields: [tagId], references: [id])

  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
}
```

### **Fields**

- `id`: Integer - Unique identifier (auto-increment)
- `front`: String - Question or prompt text (max 1000 chars)
- `back`: String - Answer or explanation text (max 1000 chars)
- `deckId`: Integer - Parent deck ID (foreign key)
- `difficulty`: Integer - Difficulty level (1-3, default: 2)
- `lastReviewed`: DateTime - Last review timestamp (optional)
- `nextReview`: DateTime - Next scheduled review timestamp (optional)
- `reviewCount`: Integer - Total review count (default: 0)
- `tagId`: Integer - Associated tag ID (optional, nullable)
- `createdAt`: DateTime - Flashcard creation timestamp
- `updatedAt`: DateTime - Last flashcard modification timestamp

### **Class**

```javascript
class Flashcard {
  constructor(data = {}) {
    this.id = data.id;
    this.front = data.front;
    this.back = data.back;
    this.deckId = data.deckId;
    this.difficulty = data.difficulty || 2;
    this.lastReviewed = data.lastReviewed;
    this.nextReview = data.nextReview;
    this.reviewCount = data.reviewCount || 0;
    this.tagId = data.tagId;
    this.createdAt = data.createdAt;
    this.updatedAt = data.updatedAt;
  }
}
```

### **JSON Schema**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "id": {"type": "integer", "minimum": 1},
    "front": {"type": "string", "maxLength": 1000},
    "back": {"type": "string", "maxLength": 1000},
    "deckId": {"type": "integer", "minimum": 1},
    "difficulty": {"type": "integer", "minimum": 1, "maximum": 3, "default": 2},
    "lastReviewed": {"type": "string", "format": "date-time"},
    "nextReview": {"type": "string", "format": "date-time"},
    "reviewCount": {"type": "integer", "minimum": 0, "default": 0},
    "tagId": {"type": "integer", "minimum": 1},
    "createdAt": {"type": "string", "format": "date-time"},
    "updatedAt": {"type": "string", "format": "date-time"}
  },
  "required": ["id", "front", "back", "deckId", "createdAt", "updatedAt"]
}
```

### **JSON Example**

```json
{
  "id": 1,
  "front": "¿Cómo se dice 'hello' en español?",
  "back": "Hola",
  "deckId": 1,
  "difficulty": 2,
  "lastReviewed": "2024-01-15T11:00:00.000Z",
  "nextReview": "2024-01-16T11:00:00.000Z",
  "reviewCount": 3,
  "createdAt": "2024-01-15T10:30:00.000Z",
  "updatedAt": "2024-01-15T11:00:00.000Z"
}
```

<!-- tabs:end -->

---

## Tag

The `Tag` entity represents organizational labels that can be associated with flashcards within a deck.

<!-- tabs:start -->

### **Database Model**

```sql
model Tag {
  id        Int        @id @default(autoincrement())
  name      String
  deckId    Int
  deck      Deck       @relation(fields: [deckId], references: [id], onDelete: Cascade)
  flashcards Flashcard[]
  createdAt DateTime   @default(now())
  updatedAt DateTime   @updatedAt

  @@unique([name, deckId])
}
```

### **Fields**

- `id`: Integer - Unique identifier (auto-increment)
- `name`: String - Tag name
- `deckId`: Integer - Parent deck ID (foreign key)
- `createdAt`: DateTime - Tag creation timestamp
- `updatedAt`: DateTime - Last tag modification timestamp

### **Class**

```javascript
class Tag {
  constructor(data = {}) {
    this.id = data.id;
    this.name = data.name;
    this.deckId = data.deckId;
    this.createdAt = data.createdAt;
    this.updatedAt = data.updatedAt;
  }
}
```

### **JSON Schema**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "id": {"type": "integer", "minimum": 1},
    "name": {"type": "string"},
    "deckId": {"type": "integer", "minimum": 1},
    "createdAt": {"type": "string", "format": "date-time"},
    "updatedAt": {"type": "string", "format": "date-time"}
  },
  "required": ["id", "name", "deckId", "createdAt", "updatedAt"]
}
```

### **JSON Example**

```json
{
  "id": 1,
  "name": "grammar",
  "deckId": 1,
  "createdAt": "2024-01-15T10:45:00.000Z",
  "updatedAt": "2024-01-15T10:45:00.000Z"
}
```

<!-- tabs:end -->

---

## DTOs and Response Formats

The API uses Data Transfer Objects (DTOs) to standardize request/response formats across all endpoints.

### Response Format Structure

All API responses follow a consistent structure:

```json
{
  "success": true|false,
  "message": "Operation result description",
  "data": { /* Entity data */ },
  "count": 0, /* Optional: for list responses */
  "timestamp": "ISO 8601 datetime", /* Only for errors */
  "errors": ["error1", "error2"] /* Only for validation errors */
}
```

### Success Response Examples

#### Single Entity
```json
{
  "success": true,
  "message": "Deck created successfully",
  "data": {
    "id": 1,
    "name": "Spanish Vocabulary",
    "description": "Basic Spanish words",
    "createdAt": "2024-01-15T10:30:00.000Z",
    "updatedAt": "2024-01-15T10:30:00.000Z"
  }
}
```

#### List Response
```json
{
  "success": true,
  "message": "Decks retrieved successfully",
  "data": [
    {
      "id": 1,
      "name": "Spanish Vocabulary",
      "description": "Basic Spanish words",
      "createdAt": "2024-01-15T10:30:00.000Z",
      "updatedAt": "2024-01-15T10:30:00.000Z"
    }
  ],
  "count": 1
}
```

### Error Response Examples

#### Validation Error
```json
{
  "success": false,
  "message": "Validation errors",
  "errors": [
    "Name is required and must be a string",
    "Description must be less than 1000 characters"
  ],
  "statusCode": 400,
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

#### Not Found Error
```json
{
  "success": false,
  "message": "Deck not found",
  "statusCode": 404,
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### DTO Classes

#### DeckDto
- `fromModel(model)` - Convert database model to DTO
- `fromModels(models)` - Convert array of models to DTOs
- `validateCreate(data)` - Validate creation input
- `validateUpdate(data)` - Validate update input
- `toResponse()` - Convert to API response format

#### FlashcardDto
- Inherits all DeckDto methods
- Additional validation for flashcard-specific fields
- Support for spaced repetition fields

#### TagDto
- Basic DTO for tag operations
- Includes flashcard count in responses

---

*All entities support full CRUD operations through the REST API with proper validation and error handling.*
