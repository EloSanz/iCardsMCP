"""Module to load instructions from a markdown file."""

import logging
import os
import re

logger = logging.getLogger(__name__)


def extract_critical_rules(content: str) -> str:
    """
    Extract critical behavioral rules from instructions markdown.
    
    Looks for sections marked as IMPORTANTE, REGLA OBLIGATORIA, CRÍTICA, etc.
    
    Args:
        content: Full markdown content
        
    Returns:
        str: Extracted critical rules or empty string if none found
    """
    # Try to find the "IMPORTANTE" section about assistant rules
    patterns = [
        r'## 🤖 IMPORTANTE:.*?(?=\n## |\Z)',  # Section from IMPORTANTE to next ## or end
        r'⚠️ REGLA OBLIGATORIA:.*?(?=\n\n##|\Z)',  # Specific rule section
        r'### ⚠️ REGLA CRÍTICA.*?(?=\n###|\Z)',  # Critical rule section
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            extracted = match.group(0).strip()
            logger.debug(f"Extracted critical rules: {len(extracted)} chars")
            return extracted
    
    logger.warning("No critical rules section found in instructions")
    return ""


def load_instructions(instructions_path: str) -> str:
    """
    Load instructions from a markdown file.

    Args:
        instructions_path: Path to the instructions file
    Returns:
        str: String containing the instructions in markdown format
    """
    if not os.path.exists(instructions_path):
        logger.warning(f"❌ Instructions file not found: {instructions_path}")
        return ""

    try:
        with open(instructions_path, encoding="utf-8") as f:
            content = f.read()
            logger.info(f"✅ Loaded instructions from {instructions_path} ({len(content)} chars)")
            return content
    except Exception as e:
        logger.error(f"❌ Error loading instructions: {str(e)}")
        return ""


def get_critical_rules(instructions_path: str) -> str:
    """
    Load instructions and extract only the critical behavioral rules.

    This is useful for including mandatory rules in tool descriptions
    without duplicating the entire instructions file.

    Args:
        instructions_path: Path to the instructions file

    Returns:
        str: Critical rules extracted from the instructions
    """
    full_content = load_instructions(instructions_path)
    if not full_content:
        return ""

    critical = extract_critical_rules(full_content)
    if critical:
        logger.info(f"✅ Extracted critical rules from instructions ({len(critical)} chars)")
        return critical

    # Fallback: if no critical section found, return a generic reminder
    return "⚠️ Read full instructions before responding."


# Contextual instruction helpers for better user guidance
def get_instructions_for_add_flashcard(deck_name: str) -> str:
    return f"¡Flashcard agregada exitosamente! 💡 RECUERDA: Es mejor crear flashcards SIN tags inicialmente y organizar después. Ahora puedes: • Agregar más flashcards individuales con 'add_flashcard' • Para múltiples flashcards usa 'bulk_create_flashcards' (más eficiente) • Crear un template con 'create_flashcard_template' • Agregar tags después con 'assign_tags_to_flashcards' • Ver todas las flashcards del mazo con 'list_flashcards(deck_name=\"{deck_name}\")' • ¿Quieres organizar tus flashcards por tags para mejor estudio?"


def get_instructions_for_list_decks() -> str:
    return "Aquí tienes todos tus mazos con indicadores de organización. Los mazos con ⚠️ necesitan organizar flashcards sin tags. Puedes: • Crear un nuevo mazo con 'create_deck' • Ver detalles de un mazo específico con 'get_deck_info' • Organizar mazos desorganizados con 'list_untagged_flashcards' + 'assign_tags_to_flashcards' • Agregar flashcards a cualquier mazo con 'add_flashcard'"


def get_instructions_for_get_deck_info(deck_name: str) -> str:
    return f"Información básica del mazo '{deck_name}' obtenida. Para estadísticas DETALLADAS usa 'get_deck_stats(deck_name=\"{deck_name}\")'. Aquí puedes: • Agregar flashcards con 'add_flashcard(deck_name=\"{deck_name}\")' • Ver todas las flashcards con 'list_flashcards(deck_name=\"{deck_name}\")' • Ver estadísticas completas con 'get_deck_stats(deck_name=\"{deck_name}\")'"


def get_instructions_for_create_deck(deck_name: str) -> str:
    return f"¡Mazo '{deck_name}' creado exitosamente! Ahora puedes: • Agregar tu primera flashcard con 'add_flashcard(deck_name=\"{deck_name}\", front=\"...\", back=\"...\")' • Crear un template de contenido con 'create_flashcard_template' • Ver los detalles del mazo con 'get_deck_info(deck_name=\"{deck_name}\")'"


def get_instructions_for_create_template() -> str:
    return "Template de flashcard creado. Úsalo como guía para: • Crear flashcards consistentes • Mantener un formato estándar • Agregar contenido a tus mazos"


def get_instructions_for_list_flashcards(deck_name: str) -> str:
    return f"Flashcards del mazo '{deck_name}' listadas. Puedes: • Agregar más flashcards con 'add_flashcard' • Editar alguna flashcard con 'update_flashcard' • Asignar tags con 'assign_tags_to_flashcards'"


def get_instructions_for_count_flashcards(deck_name: str) -> str:
    return f"Conteo de flashcards obtenido. Para gestionar el contenido: • Agregar flashcards con 'add_flashcard(deck_name=\"{deck_name}\")' • Ver detalles completos con 'list_flashcards(deck_name=\"{deck_name}\")' • Obtener estadísticas con 'get_deck_info(deck_name=\"{deck_name}\")'"


def get_instructions_for_assign_tags(deck_name: str) -> str:
    return f"Tags asignados exitosamente. Ahora puedes: • Verificar los cambios con 'list_flashcards(deck_name=\"{deck_name}\")' • Obtener estadísticas del mazo con 'get_deck_info(deck_name=\"{deck_name}\")' • Continuar organizando tu contenido"


def get_instructions_for_bulk_create(deck_name: str, created_count: int = 0) -> str:
    return f"¡{created_count} flashcards creadas exitosamente! 💡 PERFECTO: Se crearon sin tags para organizar después. Puedes: • Ver todas las flashcards con 'list_flashcards(deck_name=\"{deck_name}\")' • Agregar más flashcards con 'bulk_create_flashcards' (recomendado para múltiples) • Organizar por tags con 'assign_tags_to_flashcards' • ¿Quieres organizar estas flashcards por tags para mejor estudio?"


def get_instructions_for_get_deck_stats(deck_name: str) -> str:
    return f"Estadísticas DETALLADAS de '{deck_name}' obtenidas con análisis completo. Para acciones específicas: • Si hay flashcards sin tags: 'list_untagged_flashcards(deck_name=\"{deck_name}\")' • Para estudiar: 'list_flashcards(deck_name=\"{deck_name}\")' • Para agregar más contenido: 'add_flashcard(deck_name=\"{deck_name}\")'"

def get_instructions_for_list_untagged(deck_name: str, untagged_count: int) -> str:
    if untagged_count == 0:
        return f"¡Excelente! 🎉 Todas las flashcards del mazo '{deck_name}' ya están perfectamente organizadas con tags. Tu mazo está listo para estudiar. Puedes: • Ver todas las flashcards organizadas con 'list_flashcards(deck_name=\"{deck_name}\")' • Obtener estadísticas completas con 'get_deck_stats(deck_name=\"{deck_name}\")' • Crear más flashcards si quieres expandir el contenido"

    return f"Encontré {untagged_count} flashcards sin organizar en '{deck_name}'. Perfecto para: • Organizar por tags con 'assign_tags_to_flashcards' • Crear nuevos tags si necesitas categorías adicionales • Ver el progreso con 'list_flashcards(deck_name=\"{deck_name}\")' • Ver estadísticas completas con 'get_deck_stats(deck_name=\"{deck_name}\")'"

def get_instructions_for_update_flashcard(deck_name: str) -> str:
    return f"Flashcard actualizada exitosamente. Puedes: • Verificar los cambios con 'list_flashcards(deck_name=\"{deck_name}\")' • Continuar editando otras flashcards • Agregar nuevas flashcards al mazo"
