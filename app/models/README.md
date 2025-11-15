# iCards MCP - Typed Models System

## 🎯 **Overview**

Este sistema de modelos tipados proporciona **validación robusta**, **type safety** y **mejor mantenibilidad** para todas las operaciones de iCards MCP. Utiliza Pydantic para crear modelos fuertemente tipados que mapean directamente a la API de iCards.

## 📁 **Architecture**

```
app/models/
├── __init__.py          # Exports all models
├── common.py            # Shared types and base models
├── auth.py              # Authentication models
├── decks.py             # Deck-related models
├── flashcards.py        # Flashcard models
├── tags.py              # Tag models
├── mcp_tools.py         # MCP tool validation models
└── README.md           # This file

app/mcp/
├── helpers.py           # Helper functions for statistics and processing
├── instructions.py      # Contextual instruction functions
├── tools.py            # MCP tool definitions (cleaned up)
├── utils.py            # Utility functions for formatting
└── ...
```

## 🏗️ **Model Categories**

### **1. Base Models** (`common.py`)
Modelos fundamentales compartidos por todos los demás:

- `APIResponse` - Respuesta base de API
- `DifficultyLevel` - Niveles de dificultad (1-5)
- `Visibility` - Configuraciones de visibilidad
- `TimestampedModel` - Campos de timestamp
- `PaginationParams` - Parámetros de paginación

### **2. Domain Models** (`auth.py`, `decks.py`, `flashcards.py`, `tags.py`)

Modelos que representan entidades del negocio:

#### **Authentication**
```python
class User(IDModel, TimestampedModel):
    username: str
    email: EmailStr
    isActive: bool
    lastLoginAt: Optional[datetime]

class UserCreate(BaseModel):
    username: str  # Validado: 3-50 chars, sin caracteres especiales
    password: str  # Validado: 8+ chars, mayúscula, minúscula, número
    email: EmailStr
```

#### **Decks**
```python
class Deck(IDModel, NamedModel, DescribedModel, TimestampedModel):
    coverUrl: Optional[str]
    visibility: Visibility
    stats: Optional[DeckStats]
    tags: Optional[List[TagSummary]]
    cardCount: Optional[int]

class DeckStats(BaseModel):
    flashcardsCount: int
    organizationPercentage: Optional[float]
    untaggedFlashcardsCount: Optional[int]
    averageDifficulty: Optional[float]
    difficultyDistribution: Dict[str, int]
```

#### **Flashcards**
```python
class Flashcard(IDModel, TimestampedModel):
    front: str          # Validado: 1-5000 chars, no vacío
    back: str           # Validado: 1-5000 chars, no vacío
    difficulty: DifficultyLevel
    deckId: int
    tagId: Optional[int]
    tag: Optional[TagReference]

class FlashcardCreate(BaseModel):
    front: str
    back: str
    deckId: int
    difficulty: DifficultyLevel = DifficultyLevel.BEGINNER
```

#### **Tags**
```python
class Tag(IDModel, NamedModel, DescribedModel, ColorModel, TimestampedModel):
    deckId: int
    flashcardCount: int
    color: Optional[str]  # Validado: formato hex (#RRGGBB)

class TagBulkOperation(BaseModel):
    operation: str       # Validado: 'add' | 'remove'
    resource_type: str   # Validado: 'flashcard' | 'deck'
    resource_ids: List[int]
    tag_ids: List[int]
```

### **3. MCP Tool Models** (`mcp_tools.py`)

Modelos específicos para validar inputs de tools MCP:

```python
class CreateDeckParams(BaseModel):
    name: str                    # Validado: 1-255 chars, no vacío
    description: Optional[str]   # Validado: max 1000 chars
    generate_cover: bool = False

class AddFlashcardParams(BaseModel):
    front: str                   # Validado: 1-5000 chars, no vacío
    back: str                    # Validado: 1-5000 chars, no vacío
    deck_name: str              # Validado: 1-255 chars, no vacío
    difficulty_level: DifficultyLevel = DifficultyLevel.BEGINNER
```

## 🔧 **Usage Examples**

### **Creating Typed Parameters**
```python
from app.models import CreateDeckParams, AddFlashcardParams

# ✅ Valid parameters
deck_params = CreateDeckParams(
    name="Spanish Vocabulary",
    description="Basic Spanish words and phrases",
    generate_cover=True
)

# ❌ Will raise ValidationError
try:
    invalid_params = CreateDeckParams(name="")  # Empty name
except ValidationError as e:
    print(f"Validation error: {e}")
```

### **Using Typed Service**
```python
from app.services.typed_service import TypedService

typed_service = TypedService.get_instance()

# Type-safe deck creation
deck = await typed_service.create_deck(deck_params)
print(f"Created deck: {deck.name} (ID: {deck.id})")

# Type-safe flashcard addition
flashcard_params = AddFlashcardParams(
    front="Hola",
    back="Hello",
    deck_name="Spanish Vocabulary"
)
flashcard = await typed_service.add_flashcard(flashcard_params)
```

### **Tool Integration**
```python
@mcp_server.tool(name="create_deck")
async def create_deck(name: str, description: str = "", generate_cover: bool = False):
    try:
        # Create typed parameters with validation
        params = CreateDeckParams(
            name=name,
            description=description,
            generate_cover=generate_cover
        )

        # Use typed service
        typed_service = TypedService.get_instance()
        deck = await typed_service.create_deck(params)

        return {
            "success": True,
            "deck": deck.dict(),
            "message": f"Deck '{deck.name}' created successfully"
        }

    except ValidationError as e:
        return {"error": "Validation error", "message": str(e)}
```

## ✅ **Benefits**

### **Type Safety**
- **Compile-time validation** con mypy
- **IDE support** completo (autocompletado, refactoring)
- **Runtime validation** automática con Pydantic
- **Pydantic V2 migration** completa con `@field_validator`

### **Error Prevention**
- **Validación automática** de inputs
- **Mensajes de error** específicos y útiles
- **Constraints enforcement** (longitud, formato, rangos)

### **Maintainability**
- **Single source of truth** para validaciones
- **DRY principle** - no repetir lógica de validación
- **Easy to extend** - agregar nuevos campos/validaciones

### **Developer Experience**
- **Clear contracts** entre services y tools
- **Self-documenting code** con type hints
- **Better debugging** con modelos estructurados

## 🔄 **Migration Strategy**

### **Phase 1: Foundation** ✅
- [x] Crear modelos base
- [x] Implementar validaciones comunes
- [x] Crear TypedService wrapper

### **Phase 2: Integration** ✅
- [x] Refactorizar tools críticas (`create_deck`, `add_flashcard`)
- [x] Migrar a Pydantic V2 (`@field_validator` en lugar de `@validator`)
- [x] Actualizar sintaxis de validadores para Pydantic V2
- [ ] Migrar tools restantes gradualmente
- [ ] Actualizar tests para usar modelos tipados

### **Phase 3: Enhancement** 📋
- [ ] Agregar validaciones custom avanzadas
- [ ] Implementar caching inteligente
- [ ] Crear modelos para responses complejas
- [ ] Documentar patrones de uso

## 🧪 **Testing**

```python
def test_deck_creation_validation():
    # ✅ Valid deck
    params = CreateDeckParams(name="Test Deck", description="A test")
    assert params.name == "Test Deck"

    # ❌ Invalid deck name
    with pytest.raises(ValidationError):
        CreateDeckParams(name="")

    # ❌ Invalid description length
    with pytest.raises(ValidationError):
        CreateDeckParams(name="Test", description="x" * 1001)
```

## 📊 **Coverage**

### **API Endpoints Covered**
- ✅ Authentication: Register, Login
- ✅ Decks: CRUD + Stats + Tags + Clone
- ✅ Flashcards: CRUD + Bulk + AI Generation + Review
- ✅ Tags: CRUD + Bulk Operations

### **MCP Tools Covered**
- ✅ `create_deck` - Modelos tipados implementados
- ✅ `add_flashcard` - Modelos tipados implementados
- 🔄 `list_decks` - Pendiente migración
- 🔄 `get_deck_info` - Pendiente migración
- 🔄 Resto de tools - Pendientes

## 🚀 **Next Steps**

1. **Completar migración** de todas las tools
2. **Implementar caching** basado en modelos
3. **Crear validadores custom** para lógica de negocio compleja
4. **Documentar** patrones de uso avanzados
5. **Crear tests** exhaustivos para validaciones

---

**🎯 Resultado**: Sistema más robusto, mantenible y type-safe que previene errores y mejora la experiencia de desarrollo.
