import re
from pyswip import Prolog
from typing import Tuple, List, Optional

def to_prolog_name(name: str) -> str:
    """Convert a name to Prolog format (lowercase)."""
    return name.strip().lower()

def validate_name(name: str) -> Tuple[bool, str]:
    """Validate name according to specifications."""
    if not name or not name.strip():
        return False, "Name cannot be empty."
    
    name = name.strip()
    
    # Check if name contains only letters
    if not name.replace(' ', '').isalpha():
        return False, f"Name '{name}' must contain only letters."
    
    # Check if name has spaces (should not according to specs)
    if ' ' in name:
        return False, f"Name '{name}' cannot contain spaces."
    
    # Check if first letter is capitalized and rest are lowercase
    if not (name[0].isupper() and name[1:].islower()):
        return False, f"Name '{name}' must have first letter capitalized and rest lowercase."
    
    # Names are assumed to be valid according to specifications
    # No need to restrict to a predefined set
    
    return True, ""

def update_relationships_after_fact_addition(fact: str, person_names: set):
    """Apply intelligent relationship updates after adding a fact."""
    # This function was causing incorrect parent relationships to be added
    # For now, we'll disable automatic relationship updates to prevent bugs
    # The Prolog rules should handle relationship inference automatically
    pass

def cleanup_impossible_relationships():
    """Clean up any impossible relationships from the knowledge base."""
    try:
        prolog = Prolog()
        prolog.consult(current_kb_file)
        
        # Check for self-relationships and remove them
        results = list(prolog.query("parent_of(X, X)"))
        for result in results:
            person = result["X"]
            # Remove the self-relationship
            prolog.retract(f"parent_of({person}, {person})")
        
        # Check for circular relationships and remove them
        results = list(prolog.query("parent_of(X, Y), parent_of(Y, X)"))
        for result in results:
            person1 = result["X"]
            person2 = result["Y"]
            # Remove the circular relationship
            prolog.retract(f"parent_of({person1}, {person2})")
            prolog.retract(f"parent_of({person2}, {person1})")
            
    except Exception as e:
        print(f"Error cleaning up relationships: {e}")

def check_complex_incestual_scenarios(fact: str, person_names: set) -> Tuple[bool, str]:
    """Check for complex incestual scenarios involving multiple people."""
    try:
        prolog = Prolog()
        prolog.consult(current_kb_file)
        
        # Check if adding this fact would create a scenario where siblings become parents of the same child
        if "parent_of(" in fact:
            for name1 in person_names:
                for name2 in person_names:
                    if name1 != name2:
                        # Check if name1 and name2 are siblings and both would be parents of the same child
                        try:
                            sibling_results = list(prolog.query(f"sibling_of({name1}, {name2})"))
                            if sibling_results:
                                # Find what child they would both be parents of
                                for name3 in person_names:
                                    if name3 != name1 and name3 != name2:
                                        if f"parent_of({name1}, {name3})" in fact and f"parent_of({name2}, {name3})" in fact:
                                            return False, f"That's impossible! Incestual relationship detected! {name1.capitalize()} and {name2.capitalize()} are siblings and cannot both be parents of {name3.capitalize()}."
                        except:
                            pass
        
        # Check for aunt/nephew or uncle/niece becoming parents of the same child
        if "parent_of(" in fact:
            for name1 in person_names:
                for name2 in person_names:
                    if name1 != name2:
                        # Check various aunt/nephew combinations
                        try:
                            aunt_results = list(prolog.query(f"aunt_of({name1}, {name2})"))
                            if aunt_results:
                                for name3 in person_names:
                                    if name3 != name1 and name3 != name2:
                                        if f"parent_of({name1}, {name3})" in fact and f"parent_of({name2}, {name3})" in fact:
                                            return False, f"That's impossible! Incestual relationship detected! {name1.capitalize()} is {name2.capitalize()}'s aunt and they cannot both be parents of {name3.capitalize()}."
                        except:
                            pass
                        
                        try:
                            uncle_results = list(prolog.query(f"uncle_of({name1}, {name2})"))
                            if uncle_results:
                                for name3 in person_names:
                                    if name3 != name1 and name3 != name2:
                                        if f"parent_of({name1}, {name3})" in fact and f"parent_of({name2}, {name3})" in fact:
                                            return False, f"That's impossible! Incestual relationship detected! {name1.capitalize()} is {name2.capitalize()}'s uncle and they cannot both be parents of {name3.capitalize()}."
                        except:
                            pass
        
        # Check for cousin relationships becoming parents of the same child
        if "parent_of(" in fact:
            for name1 in person_names:
                for name2 in person_names:
                    if name1 != name2:
                        try:
                            cousin_results = list(prolog.query(f"cousin_of({name1}, {name2})"))
                            if cousin_results:
                                for name3 in person_names:
                                    if name3 != name1 and name3 != name2:
                                        if f"parent_of({name1}, {name3})" in fact and f"parent_of({name2}, {name3})" in fact:
                                            return False, f"That's impossible! Incestual relationship detected! {name1.capitalize()} and {name2.capitalize()} are cousins and cannot both be parents of {name3.capitalize()}."
                        except:
                            pass
                            
    except Exception as e:
        print(f"Error checking complex scenarios: {e}")
    
    return True, ""

def validate_relationship(statement: str, fact: str) -> Tuple[bool, str]:
    """Validate if a relationship is logically possible before adding it."""
    
    # Load current knowledge base
    try:
        prolog = Prolog()
        prolog.consult(current_kb_file)
    except:
        # If file doesn't exist or is empty, allow the first fact
        return True, ""
    
    # Extract person names from the fact
    person_names = set()
    for match in re.finditer(r'\(([^,]+),\s*([^)]+)\)', fact):
        person_names.add(to_prolog_name(match.group(1)))
        person_names.add(to_prolog_name(match.group(2)))
    
    # Check for self-relationships (impossible)
    for name in person_names:
        if f"parent_of({name}, {name})" in fact or f"child_of({name}, {name})" in fact:
            return False, f"That's impossible! {name.capitalize()} cannot be their own parent or child."
    
    # Check for circular parent-child relationships
    for name1 in person_names:
        for name2 in person_names:
            if name1 != name2:
                # Check if adding this would create a circular relationship
                if f"parent_of({name1}, {name2})" in fact:
                    # Check if name2 is already a parent of name1
                    try:
                        results = list(prolog.query(f"parent_of({name2}, {name1})"))
                        if results:
                            return False, f"That's impossible! This would create a circular relationship. {name2.capitalize()} is already a parent of {name1.capitalize()}."
                    except:
                        pass
                    
                    # Check if name2 is already a grandparent of name1
                    try:
                        results = list(prolog.query(f"grandparent_of({name2}, {name1})"))
                        if results:
                            return False, f"That's impossible! This would create a circular relationship. {name2.capitalize()} is already a grandparent of {name1.capitalize()}."
                    except:
                        pass
    
    # Check for gender contradictions
    for name in person_names:
        # Only block if the *opposite* gender is already set
        if re.search(rf'\bmale\({name}\)\.', fact):
            # Check if person is already marked as female (contradiction)
            try:
                results = list(prolog.query(f"female({name})"))
                if results and len(results) > 0:
                    return False, f"That's impossible! {name.capitalize()} cannot be both male and female."
            except Exception as e:
                pass
        elif re.search(rf'\bfemale\({name}\)\.', fact):
            # Check if person is already marked as male (contradiction)
            try:
                results = list(prolog.query(f"male({name})"))
                if results and len(results) > 0:
                    return False, f"That's impossible! {name.capitalize()} cannot be both male and female."
            except Exception as e:
                pass
        # Additional gender validation for parent relationships
        if f"parent_of({name}," in fact:
            # Check if this person is being made a father (male) but is already female (contradiction)
            if "father" in statement.lower() or "son" in statement.lower():
                try:
                    results = list(prolog.query(f"female({name})"))
                    if results and len(results) > 0:
                        return False, f"That's impossible! {name.capitalize()} cannot be both male and female."
                except:
                    pass
            # Check if this person is being made a mother (female) but is already male (contradiction)
            elif "mother" in statement.lower() or "daughter" in statement.lower():
                try:
                    results = list(prolog.query(f"male({name})"))
                    if results and len(results) > 0:
                        return False, f"That's impossible! {name.capitalize()} cannot be both male and female."
                except:
                    pass
    
    # Check for impossible parent relationships and incestual relationships
    for name1 in person_names:
        for name2 in person_names:
            if name1 != name2:
                if f"parent_of({name1}, {name2})" in fact:
                    # Check if this parent relationship already exists
                    try:
                        existing_parent = list(prolog.query(f"parent_of({name1}, {name2})"))
                        if existing_parent and len(existing_parent) > 0:
                            # If the parent relationship already exists, this is just adding gender info
                            # Check if the fact only contains gender facts or existing parent facts
                            fact_lines = fact.split('\n')
                            only_gender_or_existing = True
                            for line in fact_lines:
                                line = line.strip()
                                if line and not line.startswith('male(') and not line.startswith('female('):
                                    # Check if this is an existing parent fact
                                    if line.startswith('parent_of('):
                                        # Extract the parent relationship from the line
                                        match = re.search(r'parent_of\(([^,]+),\s*([^)]+)\)', line)
                                        if match:
                                            parent = match.group(1)
                                            child = match.group(2)
                                            existing = list(prolog.query(f"parent_of({parent}, {child})"))
                                            if not existing:
                                                only_gender_or_existing = False
                                                break
                                    else:
                                        only_gender_or_existing = False
                                        break
                            
                            if only_gender_or_existing:
                                # This is just adding gender info to existing relationships, allow it
                                continue
                    except Exception as e:
                        # If query fails, continue with normal validation
                        pass
                    
                    # Check if they are already siblings (incestual)
                    try:
                        results = list(prolog.query(f"sibling_of({name1}, {name2})"))
                        if results and len(results) > 0:
                            return False, f"That's impossible! Incestual relationship detected! {name1.capitalize()} and {name2.capitalize()} are siblings, so {name1.capitalize()} cannot be {name2.capitalize()}'s parent."
                    except Exception as e:
                        # If query fails, the relationship doesn't exist, which is fine
                        pass
                    
                    # Check if they are already cousins (incestual)
                    try:
                        results = list(prolog.query(f"cousin_of({name1}, {name2})"))
                        if results and len(results) > 0:
                            return False, f"That's impossible! Incestual relationship detected! {name1.capitalize()} and {name2.capitalize()} are cousins, so {name1.capitalize()} cannot be {name2.capitalize()}'s parent."
                    except Exception as e:
                        # If query fails, the relationship doesn't exist, which is fine
                        pass
                    
                    # Check if they are aunt/nephew or uncle/niece (incestual)
                    try:
                        results = list(prolog.query(f"aunt_of({name1}, {name2})"))
                        if results and len(results) > 0:
                            return False, f"That's impossible! Incestual relationship detected! {name1.capitalize()} is {name2.capitalize()}'s aunt, so {name1.capitalize()} cannot be {name2.capitalize()}'s parent."
                    except Exception as e:
                        # If query fails, the relationship doesn't exist, which is fine
                        pass
                    
                    try:
                        results = list(prolog.query(f"uncle_of({name1}, {name2})"))
                        if results and len(results) > 0:
                            return False, f"That's impossible! Incestual relationship detected! {name1.capitalize()} is {name2.capitalize()}'s uncle, so {name1.capitalize()} cannot be {name2.capitalize()}'s parent."
                    except Exception as e:
                        # If query fails, the relationship doesn't exist, which is fine
                        pass
                    
                    try:
                        results = list(prolog.query(f"niece_of({name1}, {name2})"))
                        if results and len(results) > 0:
                            return False, f"That's impossible! Incestual relationship detected! {name1.capitalize()} is {name2.capitalize()}'s niece, so {name1.capitalize()} cannot be {name2.capitalize()}'s parent."
                    except Exception as e:
                        # If query fails, the relationship doesn't exist, which is fine
                        pass
                    
                    try:
                        results = list(prolog.query(f"nephew_of({name1}, {name2})"))
                        if results and len(results) > 0:
                            return False, f"That's impossible! Incestual relationship detected! {name1.capitalize()} is {name2.capitalize()}'s nephew, so {name1.capitalize()} cannot be {name2.capitalize()}'s parent."
                    except Exception as e:
                        # If query fails, the relationship doesn't exist, which is fine
                        pass
                    
                    # Check if name2 is already a parent of name1 (direct circular)
                    try:
                        results = list(prolog.query(f"parent_of({name2}, {name1})"))
                        if results and len(results) > 0:
                            return False, f"That's impossible! This would create a circular relationship. {name2.capitalize()} is already a parent of {name1.capitalize()}."
                    except Exception as e:
                        # If query fails, the relationship doesn't exist, which is fine
                        pass
                    
                    # Check if name2 is already a grandparent of name1 (circular)
                    try:
                        results = list(prolog.query(f"grandparent_of({name2}, {name1})"))
                        if results and len(results) > 0:
                            return False, f"That's impossible! This would create a circular relationship. {name2.capitalize()} is already a grandparent of {name1.capitalize()}."
                    except Exception as e:
                        # If query fails, the relationship doesn't exist, which is fine
                        pass
                    
                    # Check for multi-generation cycles (ancestor-descendant cycles)
                    try:
                        # Check if name2 is an ancestor of name1 (would create a cycle)
                        results = list(prolog.query(f"ancestor_of({name2}, {name1})"))
                        if results and len(results) > 0:
                            return False, f"That's impossible! This would create a circular relationship. {name2.capitalize()} is already an ancestor of {name1.capitalize()}."
                    except Exception as e:
                        # If query fails, the relationship doesn't exist, which is fine
                        pass
                    
                    # Check if they are already parent-child in reverse (impossible)
                    try:
                        results = list(prolog.query(f"child_of({name1}, {name2})"))
                        if results and len(results) > 0:
                            return False, f"That's impossible! {name1.capitalize()} is already a child of {name2.capitalize()}, so {name1.capitalize()} cannot be {name2.capitalize()}'s parent."
                    except Exception as e:
                        # If query fails, the relationship doesn't exist, which is fine
                        pass
                    
                    # Check if name2 is already a child of name1 (circular)
                    try:
                        results = list(prolog.query(f"child_of({name2}, {name1})"))
                        if results and len(results) > 0:
                            return False, f"That's impossible! This would create a circular relationship. {name2.capitalize()} is already a child of {name1.capitalize()}."
                    except Exception as e:
                        # If query fails, the relationship doesn't exist, which is fine
                        pass
                    
                    # Check for incestual parent relationships
                    # If name1 is already a parent of name2's parent, this could create incestual relationships
                    try:
                        # Check if name1 is already a parent of name2's parent
                        results = list(prolog.query(f"parent_of({name1}, X), parent_of(X, {name2})"))
                        if results and len(results) > 0:
                            return False, f"That's impossible! Incestual relationship detected! {name1.capitalize()} is already a parent of {name2.capitalize()}'s parent, which would create an incestual situation."
                    except Exception as e:
                        pass
                    
                    # Check if name2 is already a parent of name1's parent
                    try:
                        results = list(prolog.query(f"parent_of({name2}, X), parent_of(X, {name1})"))
                        if results and len(results) > 0:
                            return False, f"That's impossible! Incestual relationship detected! {name2.capitalize()} is already a parent of {name1.capitalize()}'s parent, which would create an incestual situation."
                    except Exception as e:
                        pass
    
    # Check for sibling relationship validation (prevent incestual siblings)
    for name1 in person_names:
        for name2 in person_names:
            if name1 != name2:
                if "sibling_of(" in fact and (f"sibling_of({name1}, {name2})" in fact or f"sibling_of({name2}, {name1})" in fact):
                    # Check if they are already parent-child (impossible for siblings)
                    try:
                        results = list(prolog.query(f"parent_of({name1}, {name2})"))
                        if results and len(results) > 0:
                            return False, f"That's impossible! Incestual relationship detected! {name1.capitalize()} is already a parent of {name2.capitalize()}, so they cannot be siblings."
                    except Exception as e:
                        # If query fails, the relationship doesn't exist, which is fine
                        pass
                    
                    try:
                        results = list(prolog.query(f"parent_of({name2}, {name1})"))
                        if results and len(results) > 0:
                            return False, f"That's impossible! Incestual relationship detected! {name2.capitalize()} is already a parent of {name1.capitalize()}, so they cannot be siblings."
                    except Exception as e:
                        # If query fails, the relationship doesn't exist, which is fine
                        pass
                    
                    # Check if they are already grandparent-grandchild
                    try:
                        results = list(prolog.query(f"grandparent_of({name1}, {name2})"))
                        if results and len(results) > 0:
                            return False, f"That's impossible! Incestual relationship detected! {name1.capitalize()} is already a grandparent of {name2.capitalize()}, so they cannot be siblings."
                    except Exception as e:
                        # If query fails, the relationship doesn't exist, which is fine
                        pass
                    
                    try:
                        results = list(prolog.query(f"grandparent_of({name2}, {name1})"))
                        if results and len(results) > 0:
                            return False, f"That's impossible! Incestual relationship detected! {name2.capitalize()} is already a grandparent of {name1.capitalize()}, so they cannot be siblings."
                    except Exception as e:
                        # If query fails, the relationship doesn't exist, which is fine
                        pass
    
    # Check for existing impossible relationships in the knowledge base
    try:
        # Check for self-relationships
        for name in person_names:
            try:
                results = list(prolog.query(f"impossible_self_relationship({name})"))
                if results and len(results) > 0:
                    return False, f"That's impossible! {name.capitalize()} has an impossible self-relationship in the knowledge base."
            except Exception as e:
                # If query fails, the relationship doesn't exist, which is fine
                pass
        
        # Check for circular relationships
        for name1 in person_names:
            for name2 in person_names:
                if name1 != name2:
                    try:
                        results = list(prolog.query(f"impossible_circular({name1}, {name2})"))
                        if results and len(results) > 0:
                            return False, f"That's impossible! There is already a circular relationship between {name1.capitalize()} and {name2.capitalize()} in the knowledge base."
                    except Exception as e:
                        # If query fails, the relationship doesn't exist, which is fine
                        pass
        
        # Check for incestual relationships in existing knowledge base
        for name1 in person_names:
            for name2 in person_names:
                if name1 != name2:
                    # Check for sibling-parent relationships
                    try:
                        sibling_results = list(prolog.query(f"sibling_of({name1}, {name2})"))
                        parent_results = list(prolog.query(f"parent_of({name1}, {name2})"))
                        if sibling_results and len(sibling_results) > 0 and parent_results and len(parent_results) > 0:
                            return False, f"That's impossible! Incestual relationship detected in knowledge base! {name1.capitalize()} is both a sibling and parent of {name2.capitalize()}."
                    except Exception as e:
                        # If query fails, the relationship doesn't exist, which is fine
                        pass
                    
                    # Check for cousin-parent relationships
                    try:
                        cousin_results = list(prolog.query(f"cousin_of({name1}, {name2})"))
                        parent_results = list(prolog.query(f"parent_of({name1}, {name2})"))
                        if cousin_results and len(cousin_results) > 0 and parent_results and len(parent_results) > 0:
                            return False, f"That's impossible! Incestual relationship detected in knowledge base! {name1.capitalize()} is both a cousin and parent of {name2.capitalize()}."
                    except Exception as e:
                        # If query fails, the relationship doesn't exist, which is fine
                        pass
    except:
        pass
    
    return True, ""

# Global variable to track current knowledge base file
current_kb_file = "relationships.pl"

def add_fact_to_prolog(statement: str) -> str:
    """Translate a user statement into a Prolog fact and assert it."""
    
    # Using regex and parsing user input - EXACT patterns from specifications
    statement_patterns = [
        # Original patterns with periods
        ("X and Y are siblings", r"([A-Z][a-z]+) and ([A-Z][a-z]+) are siblings\.?", 
         lambda m: f"parent_of(parent_{to_prolog_name(m.group(1))}_{to_prolog_name(m.group(2))}, {to_prolog_name(m.group(1))}).\nparent_of(parent_{to_prolog_name(m.group(1))}_{to_prolog_name(m.group(2))}, {to_prolog_name(m.group(2))})."),
        
        ("X is a sister of Y", r"([A-Z][a-z]+) is a sister of ([A-Z][a-z]+)\.?", 
         lambda m: f"sibling_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))}).\nfemale({to_prolog_name(m.group(1))})."),
        
        ("X is the mother of Y", r"([A-Z][a-z]+) is the mother of ([A-Z][a-z]+)\.?", 
         lambda m: f"parent_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))}).\nfemale({to_prolog_name(m.group(1))})."),
        
        ("X is a grandmother of Y", r"([A-Z][a-z]+) is a grandmother of ([A-Z][a-z]+)\.?", 
         lambda m: f"grandparent_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))}).\nfemale({to_prolog_name(m.group(1))})."),
        
        ("X is a child of Y", r"([A-Z][a-z]+) is a child of ([A-Z][a-z]+)\.?", 
         lambda m: f"parent_of({to_prolog_name(m.group(2))}, {to_prolog_name(m.group(1))})."),
        
        ("X is a daughter of Y", r"([A-Z][a-z]+) is a daughter of ([A-Z][a-z]+)\.?", 
         lambda m: f"parent_of({to_prolog_name(m.group(2))}, {to_prolog_name(m.group(1))}).\nfemale({to_prolog_name(m.group(1))})."),
        
        ("X is a son of Y", r"([A-Z][a-z]+) is a son of ([A-Z][a-z]+)\.?", 
         lambda m: f"parent_of({to_prolog_name(m.group(2))}, {to_prolog_name(m.group(1))}).\nmale({to_prolog_name(m.group(1))})."),
        
        ("X is the father of Y", r"([A-Z][a-z]+) is the father of ([A-Z][a-z]+)\.?", 
         lambda m: f"parent_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))}).\nmale({to_prolog_name(m.group(1))})."),
        
        ("X is a grandfather of Y", r"([A-Z][a-z]+) is a grandfather of ([A-Z][a-z]+)\.?", 
         lambda m: f"grandparent_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))}).\nmale({to_prolog_name(m.group(1))})."),
        
        ("X is a brother of Y", r"([A-Z][a-z]+) is a brother of ([A-Z][a-z]+)\.?", 
         lambda m: f"sibling_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))}).\nmale({to_prolog_name(m.group(1))})."),
        
        ("X and Y are the parents of Z", r"([A-Z][a-z]+) and ([A-Z][a-z]+) are the parents of ([A-Z][a-z]+)\.?", 
         lambda m: f"parent_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(3))}).\nparent_of({to_prolog_name(m.group(2))}, {to_prolog_name(m.group(3))})."),
        
        ("X is an uncle of Y", r"([A-Z][a-z]+) is an uncle of ([A-Z][a-z]+)\.?", 
         lambda m: f"uncle_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})."),
        
        ("X is an aunt of Y", r"([A-Z][a-z]+) is an aunt of ([A-Z][a-z]+)\.?", 
         lambda m: f"aunt_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})."),
        
        # Additional relationship patterns with periods
        ("X is a niece of Y", r"([A-Z][a-z]+) is a niece of ([A-Z][a-z]+)\.?", 
         lambda m: f"niece_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})."),
        
        ("X is a nephew of Y", r"([A-Z][a-z]+) is a nephew of ([A-Z][a-z]+)\.?", 
         lambda m: f"nephew_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})."),
        
        ("X is a cousin of Y", r"([A-Z][a-z]+) is a cousin of ([A-Z][a-z]+)\.?", 
         lambda m: f"cousin_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})."),
        
        ("X is a grandchild of Y", r"([A-Z][a-z]+) is a grandchild of ([A-Z][a-z]+)\.?", 
         lambda m: f"grandchild_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})."),
        
        ("X is a granddaughter of Y", r"([A-Z][a-z]+) is a granddaughter of ([A-Z][a-z]+)\.?", 
         lambda m: f"granddaughter_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})."),
        
        ("X is a grandson of Y", r"([A-Z][a-z]+) is a grandson of ([A-Z][a-z]+)\.?", 
         lambda m: f"grandson_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})."),
        

        
        ("X is a half-sister of Y", r"([A-Z][a-z]+) is a half-sister of ([A-Z][a-z]+)\.?", 
         lambda m: f"half_sister_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})."),
        
        ("X is a half-brother of Y", r"([A-Z][a-z]+) is a half-brother of ([A-Z][a-z]+)\.?", 
         lambda m: f"half_brother_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})."),
        

    ]

    for _, pattern, func in statement_patterns:
        match = re.fullmatch(pattern, statement.strip())
        if match:
            # Validate all names in the match
            for i in range(1, len(match.groups()) + 1):
                name = match.group(i)
                is_valid_name, name_error = validate_name(name)
                if not is_valid_name:
                    return name_error
            
            fact = func(match)
            
            # Validate the relationship before adding it
            is_valid, error_message = validate_relationship(statement, fact)
            if not is_valid:
                return error_message
            
            # Check for complex incestual scenarios
            person_names = set()
            for match in re.finditer(r'\(([^,]+),\s*([^)]+)\)', fact):
                person_names.add(to_prolog_name(match.group(1)))
                person_names.add(to_prolog_name(match.group(2)))
            
            is_valid_complex, complex_error = check_complex_incestual_scenarios(fact, person_names)
            if not is_valid_complex:
                return f"That's impossible! {complex_error}"
            
            # Read current contents
            with open(current_kb_file, "r", encoding="utf-8") as f:
                old_contents = f.read()
            
            # Check if fact already exists to prevent duplicates
            fact_lines = fact.split('\n')
            new_facts = []
            for fact_line in fact_lines:
                if fact_line.strip():
                    # Special handling for gender facts - always add if not already present
                    if fact_line.strip().startswith('female(') or fact_line.strip().startswith('male('):
                        if fact_line.strip() not in old_contents:
                            new_facts.append(fact_line)
                    # For non-gender facts, only add if not already present
                    elif fact_line.strip() not in old_contents:
                        new_facts.append(fact_line)
            
            if new_facts:
                # Write new facts at the top
                with open(current_kb_file, "w", encoding="utf-8") as f:
                    f.write('\n'.join(new_facts) + '\n' + old_contents)
                
                # Reload Prolog knowledge base
                prolog = Prolog()
                prolog.consult(current_kb_file)
                
                # Apply intelligent relationship updates
                update_relationships_after_fact_addition(fact, person_names)
                
                return "I learned something new."
            else:
                return "I already knew that."
    
    # If no pattern matched, check if it's a name validation issue
    # Extract potential names from the statement
    potential_names = re.findall(r'\b[A-Z][a-z]+\b', statement)
    for name in potential_names:
        is_valid, error_msg = validate_name(name)
        if not is_valid:
            return error_msg
    
    # If no name validation issues, provide helpful suggestions
    suggestions = [
        "Try statements like: 'Alice is the mother of Bob'",
        "Or: 'John and Mary are siblings'", 
        "Or: 'Tom is the father of Sarah'",
        "Or: 'Lisa is a sister of Mike'",
        "Or: 'David is a grandfather of Emma'"
    ]
    return f"[Unrecognized statement]: {statement}\n\nSuggestions:\n" + "\n".join(suggestions)

def query_prolog(question: str) -> str:
    """Translate a user question into a Prolog query and get the result."""
    
    # Map question templates to regex and Prolog templates - EXACT patterns from specifications
    question_patterns = [
        # Original patterns
        ("Are X and Y siblings?", r"Are ([A-Z][a-z]+) and ([A-Z][a-z]+) siblings\?", lambda m: f"sibling_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Are X and Y half-siblings?", r"Are ([A-Z][a-z]+) and ([A-Z][a-z]+) half-siblings\?", lambda m: f"half_sibling_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Is X a sister of Y?", r"Is ([A-Z][a-z]+) a sister of ([A-Z][a-z]+)\?", lambda m: f"sister_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Is X a brother of Y?", r"Is ([A-Z][a-z]+) a brother of ([A-Z][a-z]+)\?", lambda m: f"brother_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Is X the mother of Y?", r"Is ([A-Z][a-z]+) the mother of ([A-Z][a-z]+)\?", lambda m: f"mother_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Is X the father of Y?", r"Is ([A-Z][a-z]+) the father of ([A-Z][a-z]+)\?", lambda m: f"father_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Are X and Y the parents of Z?", r"Are ([A-Z][a-z]+) and ([A-Z][a-z]+) the parents of ([A-Z][a-z]+)\?", lambda m: f"parent_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(3))}), parent_of({to_prolog_name(m.group(2))}, {to_prolog_name(m.group(3))})"),
        ("Is X a grandmother of Y?", r"Is ([A-Z][a-z]+) a grandmother of ([A-Z][a-z]+)\?", lambda m: f"grandmother_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Is X a grandfather of Y?", r"Is ([A-Z][a-z]+) a grandfather of ([A-Z][a-z]+)\?", lambda m: f"grandfather_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Is X a daughter of Y?", r"Is ([A-Z][a-z]+) a daughter of ([A-Z][a-z]+)\?", lambda m: f"daughter_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Is X a son of Y?", r"Is ([A-Z][a-z]+) a son of ([A-Z][a-z]+)\?", lambda m: f"son_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Is X a child of Y?", r"Is ([A-Z][a-z]+) a child of ([A-Z][a-z]+)\?", lambda m: f"child_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Are X, Y, and Z children of W?", r"Are ([A-Z][a-z]+), ([A-Z][a-z]+), and ([A-Z][a-z]+) children of ([A-Z][a-z]+)\?", lambda m: f"child_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(4))}), child_of({to_prolog_name(m.group(2))}, {to_prolog_name(m.group(4))}), child_of({to_prolog_name(m.group(3))}, {to_prolog_name(m.group(4))})"),
        ("Is X an uncle of Y?", r"Is ([A-Z][a-z]+) an uncle of ([A-Z][a-z]+)\?", lambda m: f"uncle_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Is X an aunt of Y?", r"Is ([A-Z][a-z]+) an aunt of ([A-Z][a-z]+)\?", lambda m: f"aunt_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Who are the siblings of X?", r"Who are the siblings of ([A-Z][a-z]+)\?", lambda m: f"sibling_of(X, {to_prolog_name(m.group(1))})"),
        ("Who are the sisters of X?", r"Who are the sisters of ([A-Z][a-z]+)\?", lambda m: f"sister_of(X, {to_prolog_name(m.group(1))})"),
        ("Who are the brothers of X?", r"Who are the brothers of ([A-Z][a-z]+)\?", lambda m: f"brother_of(X, {to_prolog_name(m.group(1))})"),
        ("Who is the mother of X?", r"Who is the mother of ([A-Z][a-z]+)\?", lambda m: f"mother_of(X, {to_prolog_name(m.group(1))})"),
        ("Who is the father of X?", r"Who is the father of ([A-Z][a-z]+)\?", lambda m: f"father_of(X, {to_prolog_name(m.group(1))})"),
        ("Who are the parents of X?", r"Who are the parents of ([A-Z][a-z]+)\?", lambda m: f"parent_of(X, {to_prolog_name(m.group(1))})"),
        ("Who are the daughters of X?", r"Who are the daughters of ([A-Z][a-z]+)\?", lambda m: f"daughter_of(X, {to_prolog_name(m.group(1))})"),
        ("Who are the sons of X?", r"Who are the sons of ([A-Z][a-z]+)\?", lambda m: f"son_of(X, {to_prolog_name(m.group(1))})"),
        ("Who are the children of X?", r"Who are the children of ([A-Z][a-z]+)\?", lambda m: f"child_of(X, {to_prolog_name(m.group(1))})"),
        ("Who is the uncle of X?", r"Who is the uncle of ([A-Z][a-z]+)\?", lambda m: f"uncle_of(X, {to_prolog_name(m.group(1))})"),
        ("Are X and Y relatives?", r"Are ([A-Z][a-z]+) and ([A-Z][a-z]+) relatives\?", lambda m: f"relative({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        
        # Additional relationship patterns
        ("Is X a niece of Y?", r"Is ([A-Z][a-z]+) a niece of ([A-Z][a-z]+)\?", lambda m: f"niece_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Is X a nephew of Y?", r"Is ([A-Z][a-z]+) a nephew of ([A-Z][a-z]+)\?", lambda m: f"nephew_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Is X a cousin of Y?", r"Is ([A-Z][a-z]+) a cousin of ([A-Z][a-z]+)\?", lambda m: f"cousin_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Is X a grandchild of Y?", r"Is ([A-Z][a-z]+) a grandchild of ([A-Z][a-z]+)\?", lambda m: f"grandchild_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Is X a granddaughter of Y?", r"Is ([A-Z][a-z]+) a granddaughter of ([A-Z][a-z]+)\?", lambda m: f"granddaughter_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Is X a grandson of Y?", r"Is ([A-Z][a-z]+) a grandson of ([A-Z][a-z]+)\?", lambda m: f"grandson_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),

        ("Is X a half-sister of Y?", r"Is ([A-Z][a-z]+) a half-sister of ([A-Z][a-z]+)\?", lambda m: f"half_sister_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Is X a half-brother of Y?", r"Is ([A-Z][a-z]+) a half-brother of ([A-Z][a-z]+)\?", lambda m: f"half_brother_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),

        
        # Who questions for new relationships
        ("Who are the nieces of X?", r"Who are the nieces of ([A-Z][a-z]+)\?", lambda m: f"niece_of(X, {to_prolog_name(m.group(1))})"),
        ("Who are the nephews of X?", r"Who are the nephews of ([A-Z][a-z]+)\?", lambda m: f"nephew_of(X, {to_prolog_name(m.group(1))})"),
        ("Who are the cousins of X?", r"Who are the cousins of ([A-Z][a-z]+)\?", lambda m: f"cousin_of(X, {to_prolog_name(m.group(1))})"),
        ("Who are the grandchildren of X?", r"Who are the grandchildren of ([A-Z][a-z]+)\?", lambda m: f"grandchild_of(X, {to_prolog_name(m.group(1))})"),

        ("Who are the half-siblings of X?", r"Who are the half-siblings of ([A-Z][a-z]+)\?", lambda m: f"half_sibling_of(X, {to_prolog_name(m.group(1))})"),
        
        # Cousin relationship queries
        ("Are X and Y cousins?", r"Are ([A-Z][a-z]+) and ([A-Z][a-z]+) cousins\?", lambda m: f"cousin_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
    ]

    try:
        for _, pattern, func in question_patterns:
            match = re.fullmatch(pattern, question.strip()) # To check if input matches the pattern
            if match:
                # Validate all names in the match
                for i in range(1, len(match.groups()) + 1):
                    name = match.group(i)
                    is_valid_name, name_error = validate_name(name)
                    if not is_valid_name:
                        return name_error
                
                query = func(match)
                
                prolog = Prolog()
                prolog.consult(current_kb_file)

                if "X" in query: # For questions that ask for specific names
                    results = list(prolog.query(query))
                    if results:
                        xs = set(str(r["X"]) for r in results if "X" in r)
                        if xs:
                            return f"Answers: {', '.join(xs)}"
                        else:
                            return "No."
                    else:
                        # Extract the relationship type from the query for better error messages
                        relationship_type = "relationship"
                        if "sibling_of" in query:
                            relationship_type = "siblings"
                        elif "sister_of" in query:
                            relationship_type = "sisters"
                        elif "brother_of" in query:
                            relationship_type = "brothers"
                        elif "mother_of" in query:
                            relationship_type = "mother"
                        elif "father_of" in query:
                            relationship_type = "father"
                        elif "parent_of" in query:
                            relationship_type = "parents"
                        elif "daughter_of" in query:
                            relationship_type = "daughters"
                        elif "son_of" in query:
                            relationship_type = "sons"
                        elif "child_of" in query:
                            relationship_type = "children"
                        elif "uncle_of" in query:
                            relationship_type = "uncle"
                        elif "aunt_of" in query:
                            relationship_type = "aunt"
                        elif "niece_of" in query:
                            relationship_type = "nieces"
                        elif "nephew_of" in query:
                            relationship_type = "nephews"
                        elif "cousin_of" in query:
                            relationship_type = "cousins"
                        elif "grandchild_of" in query:
                            relationship_type = "grandchildren"
                        elif "stepchild_of" in query:
                            relationship_type = "stepchildren"
                        elif "half_sibling_of" in query:
                            relationship_type = "half-siblings"
                        
                        # Extract the person's name from the query
                        person_name = ""
                        for i in range(1, len(match.groups()) + 1):
                            person_name = match.group(i)
                            break
                        
                        return f"That's impossible. {person_name} has no {relationship_type}."
                else:
                    results = list(prolog.query(query))
                    if results:
                        return "Yes."
                    else:
                        return "No."
        return f"[Unrecognized statement]: {question}"
    except Exception as e:
        return f"[Error executing query: {str(e)}]"

def parse_input(user_input: str) -> str:
    """Parse user input to determine if it's a statement or question and translate to Prolog."""
    if user_input.endswith("?"):
        return query_prolog(user_input)
    else:
        return add_fact_to_prolog(user_input) 