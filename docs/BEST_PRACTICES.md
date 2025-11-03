# 🏆 Guía de Mejores Prácticas - Python

Esta guía documenta las mejores prácticas para desarrollo Python profesional, incluyendo herramientas de calidad de código, patrones de diseño, y convenciones.

## 📋 Tabla de Contenidos

- [🛠️ Herramientas de Calidad](#️-herramientas-de-calidad)
- [📝 Estilo de Código](#-estilo-de-código)
- [🔍 Análisis de Código](#-análisis-de-código)
- [🧪 Testing](#-testing)
- [📚 Patrones de Diseño](#-patrones-de-diseño)
- [🚀 Optimización](#-optimización)

---

## 🛠️ Herramientas de Calidad

### **Ruff** ⚡ - Linter/Formateador Ultra-Rápido

**Reemplaza a:** flake8, isort, black, pydocstyle, pyupgrade, autoflake, etc.

```bash
# Instalar
uv add --dev ruff

# Ejecutar
uv run ruff check . --fix    # Lint + auto-fix
uv run ruff format .         # Formatear código
```

**Configuración en `pyproject.toml`:**
```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "UP", "N", "S", "BLE", "FBT", "A", "COM", "C90", "DJ", "EM", "EXE", "FA", "ISC", "ICN", "G", "INP", "PIE", "T20", "PYI", "RET", "SLF", "SLOT", "SIM", "TID", "TCH", "INT", "ARG", "PTH", "ERA", "PD", "PGH", "PL", "TRY", "FLY", "NPY", "AIR", "PERF", "FURB", "LOG", "RUF"]
ignore = ["S101", "S104", "PLR0913", "PLR2004", "FBT001", "FBT002", "FBT003", "A003", "COM812", "ISC001", "Q000", "Q001", "Q002", "Q003"]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]
"tests/**/*.py" = ["S101", "PLR2004", "S"]
"scripts/**/*.py" = ["T201"]
```

### **MyPy** 🔍 - Type Checking

```bash
# Instalar
uv add --dev mypy

# Ejecutar
uv run mypy .
```

**Configuración:**
```toml
[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[[tool.mypy.overrides]]
module = ["tests.*"]
ignore_errors = true
```

### **Bandit** 🔒 - Seguridad

```bash
# Instalar
uv add --dev bandit[toml]

# Ejecutar
uv run bandit -r . -c pyproject.toml
```

**Configuración:**
```toml
[tool.bandit]
exclude_dirs = ["tests", ".venv", "venv"]
skips = ["B101"]  # Skip assert_used (común en tests)
```

### **Pre-commit** 🤖 - Git Hooks Automáticos

```bash
# Instalar
uv add --dev pre-commit

# Configurar hooks
pre-commit install

# Ejecutar en todos los archivos
pre-commit run --all-files
```

**Configuración en `.pre-commit-config.yaml`:**
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy

  - repo: https://github.com/PyCQA/bandit
    rev: 1.8.0
    hooks:
      - id: bandit
```

---

## 📝 Estilo de Código

### ✅ **Imports Ordenados**

```python
# ❌ MAL
import os, sys
from typing import Dict, List
import json
from pathlib import Path
import requests

# ✅ BIEN
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests  # Third-party
from mypackage import MyClass  # Local
```

### ✅ **Type Hints Completos**

```python
# ❌ MAL
def process_data(data):
    pass

# ✅ BIEN
from typing import Dict, List, Optional, Any

def process_data(data: List[Dict[str, Any]]) -> Optional[Dict[str, str]]:
    """Process user data and return formatted result."""
    pass
```

### ✅ **Nombres Descriptivos**

```python
# ❌ MAL
def calc(x, y, z):
    r = x * y + z
    return r

# ✅ BIEN
def calculate_total_price(unit_price: float, quantity: int, tax_rate: float) -> float:
    """Calculate total price including tax."""
    subtotal = unit_price * quantity
    tax_amount = subtotal * tax_rate
    total_price = subtotal + tax_amount
    return total_price
```

### ✅ **Constantes en lugar de Literales**

```python
# ❌ MAL
def is_adult(age):
    return age >= 18

# ✅ BIEN
ADULT_AGE_THRESHOLD = 18

def is_adult(age: int) -> bool:
    return age >= ADULT_AGE_THRESHOLD
```

### ✅ **Validación de Input**

```python
# ❌ MAL
def divide(a, b):
    return a / b

# ✅ BIEN
def divide(dividend: float, divisor: float) -> float:
    if divisor == 0:
        raise ValueError("Divisor cannot be zero")
    return dividend / divisor
```

### ✅ **Manejo de Errores Específico**

```python
# ❌ MAL
try:
    result = risky_operation()
except:
    pass  # Silent fail

# ✅ BIEN
import logging
logger = logging.getLogger(__name__)

try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise
except Exception as e:
    logger.exception("Unexpected error occurred")
    raise
```

### ✅ **Funciones Pequeñas y Focalizadas**

```python
# ❌ MAL: Función hace muchas cosas
def process_users(users):
    valid_users = []
    for user in users:
        if user.get('age', 0) >= 18:
            user['is_adult'] = True
            valid_users.append(user)
    return valid_users

# ✅ BIEN: Funciones separadas por responsabilidad
def is_adult(age: int) -> bool:
    return age >= 18

def validate_user(user: Dict[str, Any]) -> bool:
    return isinstance(user.get('age'), int) and user['age'] > 0

def mark_as_adult(user: Dict[str, Any]) -> Dict[str, Any]:
    return {**user, 'is_adult': is_adult(user['age'])}

def filter_adult_users(users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        mark_as_adult(user)
        for user in users
        if validate_user(user) and is_adult(user['age'])
    ]
```

---

## 🔍 Análisis de Código

### **Reglas Importantes de Ruff**

| Código | Descripción | Ejemplo |
|--------|-------------|---------|
| `F401` | Import no usado | `import os  # no se usa` |
| `F841` | Variable no usada | `result = func()  # no se usa result` |
| `E501` | Línea demasiado larga | Líneas > 100 caracteres |
| `B007` | Variable de loop no usada | `for _ in range(10): pass` |
| `S101` | Uso de assert | `assert condition` (usar en tests únicamente) |
| `PLR0913` | Demasiados argumentos | > 5 argumentos en función |
| `C901` | Complejidad ciclomática alta | > 10 (configurado) |

### **Type Checking con MyPy**

```python
# ✅ Buenas prácticas de typing
from typing import Dict, List, Optional, Union, Any, Callable

def process_items(
    items: List[Dict[str, Union[str, int]]],
    callback: Optional[Callable[[Dict[str, Any]], bool]] = None
) -> List[Dict[str, Any]]:
    pass

# ✅ Generic types
from typing import TypeVar, Generic

T = TypeVar('T')

class Stack(Generic[T]):
    def push(self, item: T) -> None: ...
    def pop(self) -> T: ...
```

---

## 🧪 Testing

### **Estructura de Tests**

```
tests/
├── __init__.py
├── conftest.py          # Configuración compartida
├── test_unit/          # Tests unitarios
├── test_integration/   # Tests de integración
├── test_api/          # Tests de API
└── fixtures/
    └── sample_data.py
```

### **Ejemplo de Test Completo**

```python
import pytest
from unittest.mock import Mock, patch
from mypackage.user_service import UserService

class TestUserService:
    @pytest.fixture
    def user_service(self):
        return UserService()

    @pytest.fixture
    def sample_user(self):
        return {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30
        }

    def test_create_user_success(self, user_service, sample_user):
        """Test successful user creation."""
        # Arrange
        with patch.object(user_service, '_save_to_db') as mock_save:
            mock_save.return_value = sample_user["id"]

        # Act
        result = user_service.create_user(sample_user)

        # Assert
        assert result["id"] == sample_user["id"]
        assert result["name"] == sample_user["name"]
        mock_save.assert_called_once_with(sample_user)

    def test_create_user_validation_error(self, user_service):
        """Test user creation with invalid data."""
        invalid_user = {"name": "", "email": "invalid"}

        with pytest.raises(ValueError, match="Invalid user data"):
            user_service.create_user(invalid_user)

    @pytest.mark.parametrize("age,is_adult", [
        (17, False),
        (18, True),
        (25, True),
    ])
    def test_is_adult(self, user_service, age, is_adult):
        """Test adult age validation with multiple cases."""
        assert user_service.is_adult(age) == is_adult
```

### **Configuración de Pytest**

```toml
[tool.pytest.ini_options]
minversion = "6.0"
addopts = "-ra -q --cov=app --cov-report=term-missing --cov-report=html"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

[tool.coverage.run]
source = ["app"]
omit = [
    "*/tests/*",
    "*/test_*.py",
    "*/conftest.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "raise AssertionError",
    "raise NotImplementedError",
    "if 0:",
    "if __name__ == .__main__.:",
]
```

---

## 📚 Patrones de Diseño

### **1. Single Responsibility Principle (SRP)**

```python
# ❌ MAL: Clase hace muchas cosas
class UserManager:
    def __init__(self):
        self.db = Database()
        self.email = EmailService()
        self.cache = Cache()

    def create_user(self, data):
        # Validar
        # Guardar en BD
        # Enviar email
        # Cachear
        pass

# ✅ BIEN: Separar responsabilidades
class UserValidator:
    def validate(self, data: Dict) -> bool: ...

class UserRepository:
    def save(self, user: User) -> User: ...

class EmailService:
    def send_welcome(self, user: User) -> None: ...

class UserService:
    def __init__(self, validator, repository, email_service):
        self.validator = validator
        self.repository = repository
        self.email_service = email_service

    def create_user(self, data: Dict) -> User:
        if not self.validator.validate(data):
            raise ValueError("Invalid data")

        user = self.repository.save(User(**data))
        self.email_service.send_welcome(user)
        return user
```

### **2. Dependency Injection**

```python
# ✅ BIEN: Inyección de dependencias
from typing import Protocol

class DatabaseProtocol(Protocol):
    def save(self, user: User) -> User: ...
    def find_by_id(self, user_id: int) -> Optional[User]: ...

class UserService:
    def __init__(self, db: DatabaseProtocol):
        self.db = db

    def create_user(self, data: Dict) -> User:
        user = User(**data)
        return self.db.save(user)

# En tests
def test_user_creation():
    mock_db = Mock()
    service = UserService(mock_db)
    # Test...
```

### **3. Factory Pattern**

```python
from typing import Dict, Type
from abc import ABC, abstractmethod

class Notifier(ABC):
    @abstractmethod
    def send(self, message: str, recipient: str) -> None: ...

class EmailNotifier(Notifier):
    def send(self, message: str, recipient: str) -> None:
        print(f"Sending email to {recipient}: {message}")

class SMSNotifier(Notifier):
    def send(self, message: str, recipient: str) -> None:
        print(f"Sending SMS to {recipient}: {message}")

class NotifierFactory:
    _notifiers: Dict[str, Type[Notifier]] = {
        "email": EmailNotifier,
        "sms": SMSNotifier,
    }

    @classmethod
    def create(cls, notification_type: str) -> Notifier:
        notifier_class = cls._notifiers.get(notification_type.lower())
        if not notifier_class:
            raise ValueError(f"Unknown notification type: {notification_type}")
        return notifier_class()

# Uso
notifier = NotifierFactory.create("email")
notifier.send("Hello!", "user@example.com")
```

---

## 🚀 Optimización

### **1. List Comprehensions vs Loops**

```python
# ❌ MAL: Loop tradicional ineficiente
result = []
for item in data:
    if item > 0:
        result.append(item * 2)

# ✅ BIEN: List comprehension
result = [item * 2 for item in data if item > 0]
```

### **2. Generators para Datos Grandes**

```python
# ❌ MAL: Carga todo en memoria
def load_all_users():
    users = []
    for user in database.query("SELECT * FROM users"):
        users.append(process_user(user))
    return users  # Lista completa en memoria

# ✅ BIEN: Generator
def load_users_generator():
    for user in database.query("SELECT * FROM users"):
        yield process_user(user)  # Un usuario a la vez

# Uso
for user in load_users_generator():
    process_user(user)  # No carga todo en memoria
```

### **3. Caching Inteligente**

```python
from functools import lru_cache
import time

class APICache:
    def __init__(self, ttl_seconds: int = 300):
        self.cache = {}
        self.ttl = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        self.cache[key] = (value, time.time())

@lru_cache(maxsize=128)
def expensive_api_call(user_id: int) -> Dict[str, Any]:
    # API call aquí
    time.sleep(0.1)  # Simular delay
    return {"user_id": user_id, "data": f"User {user_id}"}
```

### **4. Async/Await para I/O**

```python
import asyncio
import aiohttp

# ❌ MAL: Sincrónico (bloqueante)
def fetch_users():
    results = []
    for user_id in user_ids:
        response = requests.get(f"https://api.example.com/users/{user_id}")
        results.append(response.json())
    return results

# ✅ BIEN: Asincrónico (no bloqueante)
async def fetch_users_async(user_ids: List[int]) -> List[Dict]:
    async with aiohttp.ClientSession() as session:
        tasks = []
        for user_id in user_ids:
            task = session.get(f"https://api.example.com/users/{user_id}")
            tasks.append(task)

        responses = await asyncio.gather(*tasks)
        return [await resp.json() for resp in responses]
```

---

## 🎯 Checklist de Calidad

### **Antes de Commit**

- [ ] `ruff check . --fix` - Sin errores de lint
- [ ] `ruff format .` - Código formateado
- [ ] `mypy .` - Sin errores de tipos
- [ ] `bandit -r .` - Sin vulnerabilidades de seguridad
- [ ] `pytest --cov=app --cov-report=term-missing` - Tests pasan, cobertura > 80%

### **Antes de Push**

- [ ] Pre-commit hooks pasan
- [ ] Documentación actualizada
- [ ] Variables de entorno documentadas
- [ ] Logs apropiados agregados
- [ ] Manejo de errores completo

### **Antes de Deploy**

- [ ] Tests de integración pasan
- [ ] Performance benchmarks OK
- [ ] Security audit completado
- [ ] Configuración de producción verificada

---

## 📖 Recursos Adicionales

- [**PEP 8**](https://pep8.org/) - Guía oficial de estilo Python
- [**Typing Documentation**](https://docs.python.org/3/library/typing.html)
- [**FastAPI Best Practices**](https://fastapi.tiangolo.com/tutorial/best-practices/)
- [**Python Design Patterns**](https://python-patterns.guide/)
- [**Effective Python**](https://effectivepython.com/) - Libro recomendado

---

*Esta guía se basa en las mejores prácticas de la industria Python y se actualiza regularmente.*
