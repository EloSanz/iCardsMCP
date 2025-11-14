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
