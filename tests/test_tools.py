#!/usr/bin/env python3
"""Test script for iCards MCP tools."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.mcp.utils import validate_deck_name

def test_deck_name_validation():
    """Test deck name validation with various inputs."""
    print("=== Testing Deck Name Validation ===")

    test_cases = [
        # (deck_name, expected_result, description)
        ("Normal Deck Name", True, "Normal deck name should be valid"),
        ("Fundamentos de Física: Conceptos Clave para Estudiantes", True, "Deck name with colon should be valid (this was the issue)"),
        ("Deck with numbers 123", True, "Deck name with numbers should be valid"),
        ("Deck with (parentheses)", True, "Deck name with parentheses should be valid"),
        ("Deck with - dash", True, "Deck name with dash should be valid"),
        ("Deck with _ underscore", True, "Deck name with underscore should be valid"),
        ("Deck with <angle>", False, "Deck name with angle brackets should be invalid"),
        ('Deck with "quotes"', False, 'Deck name with quotes should be invalid'),
        ("Deck with | pipe", False, "Deck name with pipe should be invalid"),
        ("Deck with ? question", False, "Deck name with question mark should be invalid"),
        ("Deck with * asterisk", False, "Deck name with asterisk should be invalid"),
        ("", False, "Empty string should be invalid"),
        (None, False, "None should be invalid"),
        ("   ", False, "Whitespace only should be invalid"),
        ("A" * 101, False, "Name longer than 100 chars should be invalid"),
    ]

    all_passed = True
    for deck_name, expected, description in test_cases:
        try:
            result = validate_deck_name(deck_name)
            if result == expected:
                print(f"✅ {description}")
            else:
                print(f"❌ {description} - Expected {expected}, got {result}")
                all_passed = False
        except Exception as e:
            print(f"❌ {description} - Exception: {e}")
            all_passed = False

    print(f"\n{'🎉 All tests passed!' if all_passed else '❌ Some tests failed!'}")
    return all_passed

if __name__ == "__main__":
    success = test_deck_name_validation()
    sys.exit(0 if success else 1)
