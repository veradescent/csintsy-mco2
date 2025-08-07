import re
import os
import time
from pyswip import Prolog
from typing import Tuple, List, Optional, Dict, Any

# Import modular components
from validation import RelationshipValidator
from clarification import ClarificationHandler
from fact_manager import FactManager
from query_handler import QueryHandler
from utils import to_prolog_name, validate_name

# Global variables
current_kb_file = "relationships.pl"



class FamilyRelationshipParser:
    def __init__(self):
        self.validator = RelationshipValidator()
        self.clarification_handler = ClarificationHandler()
        self.fact_manager = FactManager()
        self.query_handler = QueryHandler()
        
        # Statement patterns for parsing
        self.statement_patterns = [
            ("parent", r"^([A-Z][a-z]+) is the (father|mother) of ([A-Z][a-z]+)\.$", 
             lambda m: f"parent_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(3))}).\n{'male' if m.group(2) == 'father' else 'female'}({to_prolog_name(m.group(1))})."),
            
            ("sibling", r"^([A-Z][a-z]+) and ([A-Z][a-z]+) are (siblings?|brothers?|sisters?)\.$",
             lambda m: f"sibling_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))}).\n{'male' if m.group(3).startswith('brother') else 'female' if m.group(3).startswith('sister') else ''}({to_prolog_name(m.group(1))}).\n{'male' if m.group(3).startswith('brother') else 'female' if m.group(3).startswith('sister') else ''}({to_prolog_name(m.group(2))})."),
            
            ("individual_sibling", r"^([A-Z][a-z]+) is a (sister|brother) of ([A-Z][a-z]+)\.$",
             lambda m: self._handle_individual_sibling(m.group(1), m.group(2), m.group(3))),
            
            ("grandparent", r"^([A-Z][a-z]+) is the (grandmother|grandfather) of ([A-Z][a-z]+)\.$",
             lambda m: f"{'grandmother' if m.group(2) == 'grandmother' else 'grandfather'}_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(3))}).\n{'female' if m.group(2) == 'grandmother' else 'male'}({to_prolog_name(m.group(1))})."),
            
            ("grandparent_individual", r"^([A-Z][a-z]+) is a (grandmother|grandfather) of ([A-Z][a-z]+)\.$",
             lambda m: f"{'grandmother' if m.group(2) == 'grandmother' else 'grandfather'}_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(3))}).\n{'female' if m.group(2) == 'grandmother' else 'male'}({to_prolog_name(m.group(1))})."),
            
            ("aunt_uncle", r"^([A-Z][a-z]+) is the (aunt|uncle) of ([A-Z][a-z]+)\.$",
             lambda m: f"{'aunt' if m.group(2) == 'aunt' else 'uncle'}_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(3))}).\n{'female' if m.group(2) == 'aunt' else 'male'}({to_prolog_name(m.group(1))})."),
            
            ("aunt_uncle_individual", r"^([A-Z][a-z]+) is an (aunt|uncle) of ([A-Z][a-z]+)\.$",
             lambda m: f"{'aunt' if m.group(2) == 'aunt' else 'uncle'}_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(3))}).\n{'female' if m.group(2) == 'aunt' else 'male'}({to_prolog_name(m.group(1))})."),
            
            ("niece_nephew", r"^([A-Z][a-z]+) is a (niece|nephew) of ([A-Z][a-z]+)\.$",
             lambda m: f"{'niece' if m.group(2) == 'niece' else 'nephew'}_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(3))}).\n{'female' if m.group(2) == 'niece' else 'male'}({to_prolog_name(m.group(1))})."),
            
            ("cousin", r"^([A-Z][a-z]+) is a cousin of ([A-Z][a-z]+)\.$",
             lambda m: f"cousin_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})."),
            
            ("grandchild", r"^([A-Z][a-z]+) is a grandchild of ([A-Z][a-z]+)\.$",
             lambda m: f"grandchild_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(3))})."),
            
            ("granddaughter", r"^([A-Z][a-z]+) is a granddaughter of ([A-Z][a-z]+)\.$",
             lambda m: f"granddaughter_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))}).\nfemale({to_prolog_name(m.group(1))})."),
            
            ("grandson", r"^([A-Z][a-z]+) is a grandson of ([A-Z][a-z]+)\.$",
             lambda m: f"grandson_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))}).\nmale({to_prolog_name(m.group(1))})."),
            
            ("daughter", r"^([A-Z][a-z]+) is a daughter of ([A-Z][a-z]+)\.$",
             lambda m: f"parent_of({to_prolog_name(m.group(2))}, {to_prolog_name(m.group(1))}).\nfemale({to_prolog_name(m.group(1))})."),
            
            ("son", r"^([A-Z][a-z]+) is a son of ([A-Z][a-z]+)\.$",
             lambda m: f"parent_of({to_prolog_name(m.group(2))}, {to_prolog_name(m.group(1))}).\nmale({to_prolog_name(m.group(1))})."),
            
            ("child_of", r"^([A-Z][a-z]+) is a child of ([A-Z][a-z]+)\.$",
         lambda m: f"parent_of({to_prolog_name(m.group(2))}, {to_prolog_name(m.group(1))})."),
        
            ("parents_of", r"^([A-Z][a-z]+) and ([A-Z][a-z]+) are the parents of ([A-Z][a-z]+)\.$",
             lambda m: f"parent_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(3))}).\nparent_of({to_prolog_name(m.group(2))}, {to_prolog_name(m.group(3))})."),
            
            ("children_of", r"^([A-Z][a-z]+) and ([A-Z][a-z]+) are children of ([A-Z][a-z]+)\.$",
             lambda m: f"parent_of({to_prolog_name(m.group(3))}, {to_prolog_name(m.group(1))}).\nparent_of({to_prolog_name(m.group(3))}, {to_prolog_name(m.group(2))})."),
            
            ("multi_siblings", r"^([A-Z][a-z]+(?:, [A-Z][a-z]+)*(?:, and [A-Z][a-z]+)?) are siblings\.$",
             lambda m: self._handle_multi_siblings(m.group(1))),
            
            ("multi_children", r"^([A-Z][a-z]+(?:, [A-Z][a-z]+)*) are children of ([A-Z][a-z]+)\.$",
             lambda m: self._handle_multi_children(m.group(1), m.group(2))),
            
            ("gender", r"^([A-Z][a-z]+) is (male|female)\.$",
             lambda m: f"{m.group(2)}({to_prolog_name(m.group(1))})."),
        ]
        
        # Question patterns for queries
        self.question_patterns = [
            ("sibling", r"^Are ([A-Z][a-z]+) and ([A-Z][a-z]+) (siblings?|brothers?|sisters?)\?$",
             lambda m: f"sibling_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
            
            ("parent", r"^Is ([A-Z][a-z]+) the (father|mother) of ([A-Z][a-z]+)\?$",
             lambda m: f"parent_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(3))})"),
            
            ("individual_sibling", r"^Is ([A-Z][a-z]+) a (sister|brother) of ([A-Z][a-z]+)\?$",
             lambda m: self._handle_brother_sister_question(m.group(1), m.group(2), m.group(3))),
            
            ("child", r"^Is ([A-Z][a-z]+) a child of ([A-Z][a-z]+)\?$",
             lambda m: f"child_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
            
            ("daughter", r"^Is ([A-Z][a-z]+) a daughter of ([A-Z][a-z]+)\?$",
             lambda m: f"daughter_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
            
            ("son", r"^Is ([A-Z][a-z]+) a son of ([A-Z][a-z]+)\?$",
             lambda m: f"son_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
            
            ("grandparent", r"^Is ([A-Z][a-z]+) the (grandmother|grandfather) of ([A-Z][a-z]+)\?$",
             lambda m: f"{'grandmother' if m.group(2) == 'grandmother' else 'grandfather'}_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(3))})"),
            
            ("grandparent_individual", r"^Is ([A-Z][a-z]+) a (grandmother|grandfather) of ([A-Z][a-z]+)\?$",
             lambda m: f"{'grandmother' if m.group(2) == 'grandmother' else 'grandfather'}_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(3))})"),
            
            ("aunt_uncle", r"^Is ([A-Z][a-z]+) the (aunt|uncle) of ([A-Z][a-z]+)\?$",
             lambda m: f"{'aunt' if m.group(2) == 'aunt' else 'uncle'}_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(3))})"),
            
            ("aunt_uncle_individual", r"^Is ([A-Z][a-z]+) an (aunt|uncle) of ([A-Z][a-z]+)\?$",
             lambda m: f"{'aunt' if m.group(2) == 'aunt' else 'uncle'}_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(3))})"),
            
            ("aunt_uncle_the", r"^Is ([A-Z][a-z]+) the (aunt|uncle) of ([A-Z][a-z]+)\?$",
             lambda m: f"{'aunt' if m.group(2) == 'aunt' else 'uncle'}_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(3))})"),
            
            ("niece_nephew_the", r"^Is ([A-Z][a-z]+) the (niece|nephew) of ([A-Z][a-z]+)\?$",
             lambda m: f"{'niece' if m.group(2) == 'niece' else 'nephew'}_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(3))})"),
            
            ("parents_of", r"^Are ([A-Z][a-z]+) and ([A-Z][a-z]+) the parents of ([A-Z][a-z]+)\?$",
             lambda m: f"parent_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(3))}), parent_of({to_prolog_name(m.group(2))}, {to_prolog_name(m.group(3))})"),
            
            ("children_of", r"^Are ([A-Z][a-z]+) and ([A-Z][a-z]+) children of ([A-Z][a-z]+)\?$",
             lambda m: f"child_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(3))}), child_of({to_prolog_name(m.group(2))}, {to_prolog_name(m.group(3))})"),
            
            ("who_siblings", r"^Who are the siblings of ([A-Z][a-z]+)\?$",
             lambda m: f"sibling_of(X, {to_prolog_name(m.group(1))})"),
            
            ("who_mother", r"^Who is the mother of ([A-Z][a-z]+)\?$",
             lambda m: f"mother_of(X, {to_prolog_name(m.group(1))})"),
            
            ("who_father", r"^Who is the father of ([A-Z][a-z]+)\?$",
             lambda m: f"father_of(X, {to_prolog_name(m.group(1))})"),
            
            ("who_children", r"^Who are the children of ([A-Z][a-z]+)\?$",
             lambda m: f"child_of(X, {to_prolog_name(m.group(1))})"),
            
            ("niece_nephew", r"^Is ([A-Z][a-z]+) a (niece|nephew) of ([A-Z][a-z]+)\?$",
             lambda m: f"{'niece' if m.group(2) == 'niece' else 'nephew'}_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(3))})"),
            
            ("cousin", r"^Is ([A-Z][a-z]+) a cousin of ([A-Z][a-z]+)\?$",
             lambda m: f"cousin_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
            
            ("grandchild", r"^Is ([A-Z][a-z]+) a grandchild of ([A-Z][a-z]+)\?$",
             lambda m: f"grandchild_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
            
            ("granddaughter", r"^Is ([A-Z][a-z]+) a granddaughter of ([A-Z][a-z]+)\?$",
             lambda m: f"granddaughter_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
            
            ("grandson", r"^Is ([A-Z][a-z]+) a grandson of ([A-Z][a-z]+)\?$",
             lambda m: f"grandson_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
            
            ("gender", r"^Is ([A-Z][a-z]+) (male|female)\?$",
             lambda m: f"{m.group(2)}({to_prolog_name(m.group(1))})"),
            
            ("relative", r"^Are ([A-Z][a-z]+) and ([A-Z][a-z]+) relatives\?$",
             lambda m: f"relative({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
            
            ("who_nieces", r"^Who are the nieces of ([A-Z][a-z]+)\?$",
             lambda m: f"niece_of(X, {to_prolog_name(m.group(1))})"),
            
            ("who_nephews", r"^Who are the nephews of ([A-Z][a-z]+)\?$",
             lambda m: f"nephew_of(X, {to_prolog_name(m.group(1))})"),
            
            ("who_cousins", r"^Who are the cousins of ([A-Z][a-z]+)\?$",
             lambda m: f"cousin_of(X, {to_prolog_name(m.group(1))})"),
            
            ("who_grandchildren", r"^Who are the grandchildren of ([A-Z][a-z]+)\?$",
             lambda m: f"grandchild_of(X, {to_prolog_name(m.group(1))})"),
        ]
    
    def _handle_multi_siblings(self, names_str: str) -> str:
        """Handle multi-person sibling statements."""
        # Handle both comma-separated and "and" formats
        # Split by commas and clean up "and"
        names = []
        for part in names_str.split(','):
            part = part.strip()
            if part.startswith('and '):
                part = part[4:]  # Remove "and " prefix
            names.append(part)
        facts = []
        
        # Only add sibling relationships, not shared_parent facts yet
        # Shared_parent will be added later when it's established they don't share the first parent
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                facts.append(f"sibling_of({to_prolog_name(names[i])}, {to_prolog_name(names[j])}).")
        
        return '\n'.join(facts)
    
    def _handle_multi_children(self, names_str: str, parent: str) -> str:
        """Handle multi-person children statements."""
        names = [name.strip() for name in names_str.split(',')]
        facts = []
        
        # Add parent relationships
        for name in names:
            facts.append(f"parent_of({to_prolog_name(parent)}, {to_prolog_name(name)}).")
        
        # Add sibling relationships
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                facts.append(f"sibling_of({to_prolog_name(names[i])}, {to_prolog_name(names[j])}).")
        
        return '\n'.join(facts)
    
    def _handle_individual_sibling(self, new_sibling: str, sibling_type: str, existing_person: str) -> str:
        """Handle individual sibling statements with gender-specific facts."""
        # Generate the same sibling fact as regular siblings, plus gender fact
        # The validation will trigger the clarification process to establish parent relationships
        if sibling_type == "brother":
            return f"sibling_of({to_prolog_name(new_sibling)}, {to_prolog_name(existing_person)}).\nmale({to_prolog_name(new_sibling)})."
        elif sibling_type == "sister":
            return f"sibling_of({to_prolog_name(new_sibling)}, {to_prolog_name(existing_person)}).\nfemale({to_prolog_name(new_sibling)})."
        else:
            return f"sibling_of({to_prolog_name(new_sibling)}, {to_prolog_name(existing_person)})."
    
    def _handle_brother_sister_question(self, person1: str, relationship_type: str, person2: str) -> str:
        """Handle brother/sister questions by checking gender and sibling relationships."""
        # This will be handled by the query handler to check gender and sibling relationships
        return f"check_brother_sister_relationship:{to_prolog_name(person1)}:{relationship_type}:{to_prolog_name(person2)}"
    
    def parse_input(self, user_input: str) -> str:
        """Main entry point for parsing user input."""
        from fact_manager import clarification_context
        
        # Handle clarification responses first
        if clarification_context and user_input.lower().strip() in ["yes", "no", "mother", "father", "uncle", "aunt", "half-sibling", "half-brother", "half-sister"]:
            return self.clarification_handler.handle_response(user_input, clarification_context)
        
        # Check if it's a question
        if user_input.strip().endswith('?'):
            return self.query_handler.handle_question(user_input, self.question_patterns)
        
        # Handle statements
        return self.fact_manager.add_fact(user_input, self.statement_patterns, self.validator)

def parse_input(user_input: str) -> str:
    """Global function for backward compatibility."""
    parser = FamilyRelationshipParser()
    return parser.parse_input(user_input)

def query_prolog(question: str) -> str:
    """Global function for backward compatibility."""
    query_handler = QueryHandler()
    return query_handler.handle_question(question, [])

def add_fact_to_prolog(statement: str) -> str:
    """Global function for backward compatibility."""
    fact_manager = FactManager()
    validator = RelationshipValidator()
    return fact_manager.add_fact(statement, [], validator)