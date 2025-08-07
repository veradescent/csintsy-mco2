import re
from typing import Tuple, Set
from pyswip import Prolog
from utils import to_prolog_name, safe_prolog_query, validate_prolog_file

# Global variable for current knowledge base file
current_kb_file = "relationships.pl"

class RelationshipValidator:
    def __init__(self):
        pass
    
    def validate_relationship(self, statement: str, fact: str) -> Tuple[bool, str]:
        """Validate a relationship before adding it to the knowledge base."""
        try:
            # Check if the file has any existing facts (not just rules)
            try:
                with open(current_kb_file, "r") as f:
                    content = f.read()
                print(f"DEBUG: File content length: {len(content)}")
                # Check if there are any actual facts (not just rules)
                has_facts = bool(re.search(r'^[a-z_]+\([a-z0-9_, ]+\)\.$', content, re.MULTILINE))
                print(f"DEBUG: has_facts = {has_facts}")
                if has_facts:
                    facts = re.findall(r'^[a-z_]+\([a-z0-9_, ]+\)\.$', content, re.MULTILINE)
                    print(f"DEBUG: Found facts: {facts}")
            except Exception as e:
                print(f"DEBUG: Error reading file: {e}")
                has_facts = False
            
            # Always perform validation, even if no facts exist yet
            # This ensures sibling clarification is triggered for all new sibling relationships
            if not has_facts:
                print(f"No existing facts in {current_kb_file}, but performing validation for new relationships")
                # For sibling relationships, always trigger clarification
                if "sibling_of" in fact:
                    # Extract sibling names
                    match = re.search(r'sibling_of\(([^,]+),\s*([^)]+)\)', fact)
                    if match:
                        person1 = match.group(1)
                        person2 = match.group(2)
                        return False, f"ask_full_sibling_clarification:{person1}:{person2}"
                
                # For parent relationships, check if there are any sibling relationships in the file
                if "parent_of" in fact:
                    try:
                        # Check if there are any sibling relationships in the file
                        with open(current_kb_file, "r") as f:
                            content = f.read()
                        sibling_matches = re.findall(r'sibling_of\(([^,]+),\s*([^)]+)\)', content)
                        if sibling_matches:
                            # Extract the child name from the parent fact
                            parent_match = re.search(r'parent_of\(([^,]+),\s*([^)]+)\)', fact)
                            if parent_match:
                                child = parent_match.group(2)
                                # Find siblings of this child (check both directions)
                                siblings = []
                                for sib1, sib2 in sibling_matches:
                                    if sib1 == child:
                                        siblings.append(sib2)
                                    elif sib2 == child:
                                        siblings.append(sib1)
                                if siblings:
                                    parent = parent_match.group(1)
                                    return False, f"ask_sibling_parent_clarification:{parent}:{child}:{','.join(siblings)}"
                    except Exception as e:
                        print(f"Error checking parent relationships: {e}")
                
                # For other relationships, allow them to be added
                return True, ""
            
            # Skip validation if Prolog file is invalid
            if not validate_prolog_file(current_kb_file):
                print(f"Skipping validation due to invalid file: {current_kb_file}")
                return True, "file_invalid"
            
            # Try to consult the file, but skip validation if it fails
            try:
                prolog = Prolog()
                prolog.consult(current_kb_file)
            except Exception as e:
                print(f"Skipping validation due to Prolog consultation error: {e}")
                return True, "consultation_error"
            
            # Extract person names from the fact
            person_names = set()
            for match in re.finditer(r'\(([^,]+),\s*([^)]+)\)', fact):
                person_names.add(to_prolog_name(match.group(1)))
                person_names.add(to_prolog_name(match.group(2)))
            
            # Check for gender contradictions
            gender_error = self._check_gender_contradictions(statement, fact, prolog, True)
            if gender_error:
                return False, gender_error
            
            # Check for impossible parent relationships
            parent_error = self._check_parent_relationships(statement, fact, prolog, True)
            if parent_error:
                return False, parent_error
            
            # Check for sibling relationship conflicts
            sibling_error = self._check_sibling_relationships(statement, fact, prolog, True)
            if sibling_error:
                return False, sibling_error
            
            # Check for grandparent relationship validation
            grandparent_error = self._check_grandparent_relationships(statement, fact, prolog, True)
            if grandparent_error:
                return False, grandparent_error
            
            # Check for aunt/uncle relationship validation
            aunt_uncle_error = self._check_aunt_uncle_relationships(statement, fact, prolog, True)
            if aunt_uncle_error:
                return False, aunt_uncle_error
            
            # Check for complex incestual scenarios
            incest_error = self._check_incestual_scenarios(fact, person_names, prolog, True)
            if incest_error:
                return False, incest_error
            
            return True, ""
            
        except Exception as e:
            print(f"Error during validation: {e}")
            return True, "validation_error"
    
    def check_sibling_possibility(self, person1: str, person2: str) -> Tuple[bool, str]:
        """Check if two people can be siblings without causing conflicts."""
        try:
            # Skip validation if Prolog file is invalid
            if not validate_prolog_file(current_kb_file):
                print(f"Skipping sibling possibility check due to invalid file: {current_kb_file}")
                return True, ""
            
            # Try to consult the file, but skip validation if it fails
            try:
                prolog = Prolog()
                prolog.consult(current_kb_file)
            except Exception as e:
                print(f"Skipping sibling possibility check due to Prolog consultation error: {e}")
                return True, ""
            
            # Check if they are already siblings
            existing_sibling = safe_prolog_query(prolog, f"sibling_of({person1}, {person2})")
            if existing_sibling:
                return False, f"{person1.capitalize()} and {person2.capitalize()} are already siblings."
            
            # Check if person1 is a parent of person2
            parent_check = safe_prolog_query(prolog, f"parent_of({person1}, {person2})")
            if parent_check:
                return False, f"{person1.capitalize()} cannot be a sibling of {person2.capitalize()} because {person1.capitalize()} is {person2.capitalize()}'s parent."
            
            # Check if person2 is a parent of person1
            parent_check = safe_prolog_query(prolog, f"parent_of({person2}, {person1})")
            if parent_check:
                return False, f"{person1.capitalize()} cannot be a sibling of {person2.capitalize()} because {person2.capitalize()} is {person1.capitalize()}'s parent."
            
            # Check if person1 is a grandparent of person2
            grandparent_check = safe_prolog_query(prolog, f"grandparent_of({person1}, {person2})")
            if grandparent_check:
                return False, f"{person1.capitalize()} cannot be a sibling of {person2.capitalize()} because {person1.capitalize()} is {person2.capitalize()}'s grandparent."
            
            # Check if person2 is a grandparent of person1
            grandparent_check = safe_prolog_query(prolog, f"grandparent_of({person2}, {person1})")
            if grandparent_check:
                return False, f"{person1.capitalize()} cannot be a sibling of {person2.capitalize()} because {person2.capitalize()} is {person1.capitalize()}'s grandparent."
            
            # Check if person1 is a great-grandparent of person2
            great_grandparent_check = safe_prolog_query(prolog, f"parent_of({person1}, Z), parent_of(Z, W), parent_of(W, {person2})")
            if great_grandparent_check:
                return False, f"{person1.capitalize()} cannot be a sibling of {person2.capitalize()} because {person1.capitalize()} is {person2.capitalize()}'s great-grandparent."
            
            # Check if person2 is a great-grandparent of person1
            great_grandparent_check = safe_prolog_query(prolog, f"parent_of({person2}, Z), parent_of(Z, W), parent_of(W, {person1})")
            if great_grandparent_check:
                return False, f"{person1.capitalize()} cannot be a sibling of {person2.capitalize()} because {person2.capitalize()} is {person1.capitalize()}'s great-grandparent."
            
            # Check if they are cousins (have different parents who are siblings)
            cousin_check = safe_prolog_query(prolog, f"parent_of(P1, {person1}), parent_of(P2, {person2}), sibling_of(P1, P2), P1 \\= P2")
            if cousin_check:
                return False, f"{person1.capitalize()} and {person2.capitalize()} cannot be siblings because they are cousins (their parents are siblings)."
            
            # Check if they are second cousins (grandparents are siblings)
            second_cousin_check = safe_prolog_query(prolog, f"parent_of(GP1, P1), parent_of(P1, {person1}), parent_of(GP2, P2), parent_of(P2, {person2}), sibling_of(GP1, GP2), GP1 \\= GP2")
            if second_cousin_check:
                return False, f"{person1.capitalize()} and {person2.capitalize()} cannot be siblings because they are second cousins (their grandparents are siblings)."
            
            # Check if one is an aunt/uncle of the other
            aunt_uncle_check = safe_prolog_query(prolog, f"aunt_of({person1}, {person2})")
            if aunt_uncle_check:
                return False, f"{person1.capitalize()} cannot be a sibling of {person2.capitalize()} because {person1.capitalize()} is {person2.capitalize()}'s aunt."
            
            aunt_uncle_check = safe_prolog_query(prolog, f"uncle_of({person1}, {person2})")
            if aunt_uncle_check:
                return False, f"{person1.capitalize()} cannot be a sibling of {person2.capitalize()} because {person1.capitalize()} is {person2.capitalize()}'s uncle."
            
            aunt_uncle_check = safe_prolog_query(prolog, f"aunt_of({person2}, {person1})")
            if aunt_uncle_check:
                return False, f"{person1.capitalize()} cannot be a sibling of {person2.capitalize()} because {person2.capitalize()} is {person1.capitalize()}'s aunt."
            
            aunt_uncle_check = safe_prolog_query(prolog, f"uncle_of({person2}, {person1})")
            if aunt_uncle_check:
                return False, f"{person1.capitalize()} cannot be a sibling of {person2.capitalize()} because {person2.capitalize()} is {person1.capitalize()}'s uncle."
            
            # Check if one is a niece/nephew of the other
            niece_nephew_check = safe_prolog_query(prolog, f"niece_of({person1}, {person2})")
            if niece_nephew_check:
                return False, f"{person1.capitalize()} cannot be a sibling of {person2.capitalize()} because {person1.capitalize()} is {person2.capitalize()}'s niece."
            
            niece_nephew_check = safe_prolog_query(prolog, f"nephew_of({person1}, {person2})")
            if niece_nephew_check:
                return False, f"{person1.capitalize()} cannot be a sibling of {person2.capitalize()} because {person1.capitalize()} is {person2.capitalize()}'s nephew."
            
            niece_nephew_check = safe_prolog_query(prolog, f"niece_of({person2}, {person1})")
            if niece_nephew_check:
                return False, f"{person1.capitalize()} cannot be a sibling of {person2.capitalize()} because {person2.capitalize()} is {person1.capitalize()}'s niece."
            
            niece_nephew_check = safe_prolog_query(prolog, f"nephew_of({person2}, {person1})")
            if niece_nephew_check:
                return False, f"{person1.capitalize()} cannot be a sibling of {person2.capitalize()} because {person2.capitalize()} is {person1.capitalize()}'s nephew."
            
            # Check if they are already related in a way that precludes being siblings
            relative_check = safe_prolog_query(prolog, f"relative({person1}, {person2}), not(sibling_of({person1}, {person2}))")
            if relative_check:
                # Get the specific relationship type for better error message
                relationship_types = []
                
                # Check for specific relationship types
                if safe_prolog_query(prolog, f"parent_of({person1}, {person2})"):
                    relationship_types.append("parent")
                elif safe_prolog_query(prolog, f"parent_of({person2}, {person1})"):
                    relationship_types.append("child")
                elif safe_prolog_query(prolog, f"grandparent_of({person1}, {person2})"):
                    relationship_types.append("grandparent")
                elif safe_prolog_query(prolog, f"grandparent_of({person2}, {person1})"):
                    relationship_types.append("grandchild")
                elif safe_prolog_query(prolog, f"aunt_of({person1}, {person2})"):
                    relationship_types.append("aunt")
                elif safe_prolog_query(prolog, f"uncle_of({person1}, {person2})"):
                    relationship_types.append("uncle")
                elif safe_prolog_query(prolog, f"aunt_of({person2}, {person1})"):
                    relationship_types.append("niece")
                elif safe_prolog_query(prolog, f"uncle_of({person2}, {person1})"):
                    relationship_types.append("nephew")
                elif safe_prolog_query(prolog, f"cousin_of({person1}, {person2})"):
                    relationship_types.append("cousin")
                
                if relationship_types:
                    relationship_str = relationship_types[0]
                    return False, f"{person1.capitalize()} and {person2.capitalize()} cannot be siblings because they are already {relationship_str}s."
                else:
                    return False, f"{person1.capitalize()} and {person2.capitalize()} cannot be siblings because they are already related in a way that precludes being siblings."
            
            # If we get here, they can be siblings
            return True, ""
            
        except Exception as e:
            print(f"Error checking sibling possibility: {e}")
            return True, "validation_error"
    
    def _check_gender_contradictions(self, statement: str, fact: str, prolog, has_content: bool) -> str:
        """Check for gender contradictions in the statement."""
        if not has_content:
            return ""
            
        try:
            # Extract person names from the fact
            person_names = set()
            for match in re.finditer(r'\(([^,]+),\s*([^)]+)\)', fact):
                person_names.add(to_prolog_name(match.group(1)))
                person_names.add(to_prolog_name(match.group(2)))
            
            # For gender facts, check if the person already has the opposite gender
            if re.search(r'\bfather\b', statement.lower()) and "parent_of" in fact:
                # Extract the parent name from the fact
                parent_match = re.search(r'parent_of\(([^,]+),\s*([^)]+)\)', fact)
                if parent_match:
                    parent_name = to_prolog_name(parent_match.group(1))
                    # Check if parent is already female
                    try:
                        female_results = list(prolog.query(f"female({parent_name})"))
                        if female_results:
                            return f"That's impossible! {parent_match.group(1).capitalize()} cannot be a father because they are already female."
                    except Exception as e:
                        print(f"Error checking female predicate: {e}")
                        
            elif re.search(r'\bmother\b', statement.lower()) and "parent_of" in fact:
                # Extract the parent name from the fact
                parent_match = re.search(r'parent_of\(([^,]+),\s*([^)]+)\)', fact)
                if parent_match:
                    parent_name = to_prolog_name(parent_match.group(1))
                    # Check if parent is already male
                    try:
                        male_results = list(prolog.query(f"male({parent_name})"))
                        if male_results:
                            return f"That's impossible! {parent_match.group(1).capitalize()} cannot be a mother because they are already male."
                    except Exception as e:
                        print(f"Error checking male predicate: {e}")
            
            # For explicit gender statements, check contradictions
            elif re.search(r'\bmale\(', fact):
                person_match = re.search(r'male\(([^)]+)\)', fact)
                if person_match:
                    person_name = to_prolog_name(person_match.group(1))
                    # Check if person is already female
                    try:
                        female_results = list(prolog.query(f"female({person_name})"))
                        if female_results:
                            return f"That's impossible! {person_match.group(1).capitalize()} cannot be male because they are already female."
                    except Exception as e:
                        print(f"Error checking female predicate: {e}")
                        
            elif re.search(r'\bfemale\(', fact):
                person_match = re.search(r'female\(([^)]+)\)', fact)
                if person_match:
                    person_name = to_prolog_name(person_match.group(1))
                    # Check if person is already male
                    try:
                        male_results = list(prolog.query(f"male({person_name})"))
                        if male_results:
                            return f"That's impossible! {person_match.group(1).capitalize()} cannot be female because they are already male."
                    except Exception as e:
                        print(f"Error checking male predicate: {e}")
                        
        except Exception as e:
            print(f"Error in gender contradiction check: {e}")
            
        return ""
    
    def _check_parent_relationships(self, statement: str, fact: str, prolog, has_content: bool) -> str:
        """Check for impossible parent relationships."""
        print(f"DEBUG: _check_parent_relationships called with statement='{statement}', fact='{fact}'")
        
        if "parent_of" not in fact:
            return ""
        
        # Extract parent and child names
        match = re.search(r'parent_of\(([^,]+),\s*([^)]+)\)', fact)
        if not match:
            return ""
        
        parent = match.group(1)
        child = match.group(2)
        
        # Check for hierarchical validation for parent-child relationships
        if has_content:
            hierarchical_error = self._check_parent_child_hierarchical_validation(parent, child, prolog)
            if hierarchical_error:
                return hierarchical_error
        
        # Skip parent validation for grandparent relationships
        if "grandparent" in statement.lower():
            return self._check_grandparent_parent_relationship(parent, child, prolog)
        
        # Check for multiple parents of the same gender
        if has_content:
            try:
                # First, check if the child already has two parents (regardless of gender)
                existing_parents = safe_prolog_query(prolog, f"parent_of(X, {child})")
                if existing_parents:
                    existing_parent_names = [result["X"] for result in existing_parents]
                    
                    # Check if this new parent is already a parent
                    if parent in existing_parent_names:
                        return ""  # Same parent, no conflict
                    
                    # Check if the existing parent is a shared parent (check this BEFORE checking for third parent)
                    print(f"DEBUG: Checking if shared parent is in existing_parent_names: {existing_parent_names}")
                    has_shared_parent = any(name.startswith("shared_mother_") or name.startswith("shared_father_") for name in existing_parent_names)
                    if has_shared_parent:
                        print(f"DEBUG: Found shared parent conflict for {child}")
                        return self._handle_shared_parent_conflict(parent, child, prolog, statement)
                    else:
                        print(f"DEBUG: shared parent not found in existing_parent_names")
                        # If child already has 2 parents and none are shared, prevent adding a third
                        if len(existing_parent_names) >= 2:
                            return f"That's impossible! {child.capitalize()} already has two parents ({', '.join([p.capitalize() for p in existing_parent_names])}). A person cannot have more than two parents."
                    
                    # Now check for gender-specific conflicts
                    # Determine the gender of the new parent
                    new_parent_male = safe_prolog_query(prolog, f"male({parent})")
                    new_parent_female = safe_prolog_query(prolog, f"female({parent})")
                    
                    # Check for existing parents of the same gender
                    if new_parent_male:
                        # Check for existing male parents
                        existing_male_parents = []
                        for parent_result in existing_parents:
                            parent_name = parent_result["X"]
                            if safe_prolog_query(prolog, f"male({parent_name})"):
                                existing_male_parents.append(parent_name)
                        
                        if existing_male_parents:
                            existing_father = existing_male_parents[0]
                            return f"That's impossible! {child.capitalize()} already has a father ({existing_father.capitalize()}). A person can only have one father."
                    elif new_parent_female:
                        # Check for existing female parents
                        existing_female_parents = []
                        for parent_result in existing_parents:
                            parent_name = parent_result["X"]
                            if safe_prolog_query(prolog, f"female({parent_name})"):
                                existing_female_parents.append(parent_name)
                        
                        if existing_female_parents:
                            existing_mother = existing_female_parents[0]
                            return f"That's impossible! {child.capitalize()} already has a mother ({existing_mother.capitalize()}). A person can only have one mother."
                    
                    # If the parent's gender is not known, check based on the statement
                    if not new_parent_male and not new_parent_female:
                        if "father" in statement.lower():
                            # Check for existing male parents
                            existing_male_parents = []
                            for parent_result in existing_parents:
                                parent_name = parent_result["X"]
                                if safe_prolog_query(prolog, f"male({parent_name})"):
                                    existing_male_parents.append(parent_name)
                            
                            if existing_male_parents:
                                existing_father = existing_male_parents[0]
                                return f"That's impossible! {child.capitalize()} already has a father ({existing_father.capitalize()}). A person can only have one father."
                        elif "mother" in statement.lower():
                            # Check for existing female parents
                            existing_female_parents = []
                            for parent_result in existing_parents:
                                parent_name = parent_result["X"]
                                if safe_prolog_query(prolog, f"female({parent_name})"):
                                    existing_female_parents.append(parent_name)
                            
                            if existing_female_parents:
                                existing_mother = existing_female_parents[0]
                                return f"That's impossible! {child.capitalize()} already has a mother ({existing_mother.capitalize()}). A person can only have one mother."
                        
            except Exception as e:
                print(f"Error checking multiple parents: {e}")
        
        # Check for sibling clarification (triggered when adding parent to sibling set)
        if has_content:
            try:
                # Find the complete sibling set for the child
                all_siblings = set()
                
                # First, find direct siblings
                siblings = safe_prolog_query(prolog, f"sibling_of({child}, X)")
                if siblings:
                    for sib in siblings:
                        all_siblings.add(sib["X"])
                
                # Also check the reverse direction
                siblings = safe_prolog_query(prolog, f"sibling_of(X, {child})")
                if siblings:
                    for sib in siblings:
                        all_siblings.add(sib["X"])
                
                # Now find all siblings of each sibling to get the complete set
                siblings_to_check = list(all_siblings.copy())
                for sibling in siblings_to_check:
                    # Find siblings of this sibling
                    sib_siblings = safe_prolog_query(prolog, f"sibling_of({sibling}, X)")
                    if sib_siblings:
                        for sib in sib_siblings:
                            all_siblings.add(sib["X"])
                    
                    # Also check reverse direction
                    sib_siblings = safe_prolog_query(prolog, f"sibling_of(X, {sibling})")
                    if sib_siblings:
                        for sib in sib_siblings:
                            all_siblings.add(sib["X"])
                
                if all_siblings:
                    sibling_names = list(all_siblings)
                    if sibling_names:
                        # Determine the type of parent being added
                        parent_type = None
                        if "mother" in statement.lower():
                            parent_type = "mother"
                        elif "father" in statement.lower():
                            parent_type = "father"
                        else:
                            parent_type = "parent"  # generic
                        
                        # Check if these are full siblings or half-siblings
                        # For full siblings, we don't need clarification - just replace shared parents
                        # For half-siblings, we need clarification
                        
                        # First check if the child has a half_sibling_of relationship with any of the siblings
                        # This indicates they are half-siblings
                        child_has_half_sibling_relationship = False
                        for sibling_name in sibling_names:
                            if sibling_name != child:  # Check with other siblings
                                # Check if they have a half_sibling_of relationship (check both directions)
                                half_sibling_relationship = safe_prolog_query(prolog, f"half_sibling_of({child}, {sibling_name})")
                                if not half_sibling_relationship:
                                    # Check the reverse direction
                                    half_sibling_relationship = safe_prolog_query(prolog, f"half_sibling_of({sibling_name}, {child})")
                                if half_sibling_relationship:
                                    child_has_half_sibling_relationship = True
                                    print(f"DEBUG: {child} has half sibling relationship with {sibling_name}")
                                    break
                        
                        # If child has half sibling relationship, these are half-siblings - do NOT share parents
                        if child_has_half_sibling_relationship:
                            print(f"DEBUG: {child} has half sibling relationship, these are half-siblings - not sharing parent automatically")
                            return ""  # Allow the parent to be added only to the specific child
                        
                        # Now check if the child has a sibling_of relationship with any of the siblings
                        # This indicates they are full siblings, regardless of shared parents
                        child_has_full_sibling_relationship = False
                        for sibling_name in sibling_names:
                            if sibling_name != child:  # Check with other siblings
                                # Check if they have a sibling_of relationship (full siblings)
                                sibling_relationship = safe_prolog_query(prolog, f"sibling_of({child}, {sibling_name})")
                                if sibling_relationship:
                                    # Also check if they DON'T have a half_sibling_of relationship
                                    half_sibling_relationship = safe_prolog_query(prolog, f"half_sibling_of({child}, {sibling_name})")
                                    if not half_sibling_relationship:
                                        child_has_full_sibling_relationship = True
                                        print(f"DEBUG: {child} has full sibling relationship with {sibling_name}")
                                        break
                        
                        # If child has full sibling relationship, these are full siblings - no clarification needed
                        if child_has_full_sibling_relationship:
                            print(f"DEBUG: {child} has full sibling relationship, these are full siblings - no clarification needed")
                            # For full siblings, automatically add the parent to all siblings
                            return f"add_parent_to_full_siblings:{parent}:{child}:{','.join(sibling_names)}"
                        else:
                            # These are half-siblings, check if any siblings need this parent type
                            siblings_needing_parent = []
                            print(f"DEBUG: Checking half-siblings for {child}: {sibling_names}")
                            
                            # Check each sibling (EXCLUDING the child being added)
                            for sibling_name in sibling_names:
                                if sibling_name != child:  # Only check OTHER siblings, not the child being added
                                    sibling_parents = safe_prolog_query(prolog, f"parent_of(X, {sibling_name})")
                                    sibling_has_parent_type = False
                                    if sibling_parents:
                                        for parent_result in sibling_parents:
                                            parent_name = parent_result["X"]
                                            if parent_type == "mother":
                                                parent_gender = safe_prolog_query(prolog, f"female({parent_name})")
                                                if parent_gender:
                                                    sibling_has_parent_type = True
                                                    break
                                            elif parent_type == "father":
                                                parent_gender = safe_prolog_query(prolog, f"male({parent_name})")
                                                if parent_gender:
                                                    sibling_has_parent_type = True
                                                    break
                                            else:
                                                # For generic parent, just check if any parent exists
                                                sibling_has_parent_type = True
                                                break
                                    
                                    if not sibling_has_parent_type:
                                        siblings_needing_parent.append(sibling_name)
                                        print(f"DEBUG: {sibling_name} needs {parent_type}")
                            
                            # For half-siblings, do NOT automatically share parents
                            # Just add the parent to the specific child
                            print(f"DEBUG: Half-siblings detected, not sharing parent automatically")
                            return ""  # Allow the parent to be added only to the specific child
            except Exception as e:
                print(f"Error checking siblings: {e}")
        
        # Check existing parents
        print(f"DEBUG: has_content = {has_content}")
        if has_content:  # Only query if we have content
            try:
                print(f"DEBUG: Querying existing parents for {child}")
                existing_parents = safe_prolog_query(prolog, f"parent_of(X, {child})")
                print(f"DEBUG: {child} has existing parents: {existing_parents}")
                if existing_parents:
                    existing_parent_names = [result["X"] for result in existing_parents]
                    print(f"DEBUG: existing_parent_names = {existing_parent_names}")
                    
                    # Check if this new parent is already a parent
                    if parent in existing_parent_names:
                        print(f"DEBUG: {parent} is already a parent of {child}")
                        return ""  # Same parent, no conflict
                    
                    # Check if the existing parent is a shared parent (check this BEFORE checking for third parent)
                    print(f"DEBUG: Checking if shared parent is in existing_parent_names: {existing_parent_names}")
                    has_shared_parent = any(name.startswith("shared_mother_") or name.startswith("shared_father_") for name in existing_parent_names)
                    if has_shared_parent:
                        print(f"DEBUG: Found shared parent conflict for {child}")
                        return self._handle_shared_parent_conflict(parent, child, prolog, statement)
                    else:
                        print(f"DEBUG: shared parent not found in existing_parent_names")
                        # Also check for gender conflicts with existing parents
                        gender_error = self._check_parent_gender_conflicts(parent, child, existing_parent_names, prolog)
                        if gender_error:
                            print(f"DEBUG: Gender conflict found: {gender_error}")
                            return gender_error
                    
                    # Check for gender conflicts
                    print(f"DEBUG: Checking gender conflicts for {parent} and {child}")
                    gender_error = self._check_parent_gender_conflicts(parent, child, existing_parent_names, prolog)
                    if gender_error:
                        print(f"DEBUG: Gender conflict found: {gender_error}")
                        return gender_error
                    
            except Exception as e:
                print(f"Error checking parent relationships: {e}")
        
        return ""
    
    def _check_grandparent_parent_relationship(self, grandparent: str, grandchild: str, prolog) -> str:
        """Check grandparent relationship validation."""
        try:
            # Find the parent of the grandchild
            parent_results = safe_prolog_query(prolog, f"parent_of(Z, {grandchild})")
            if not parent_results:
                return f"Cannot establish grandparent relationship: {grandchild.capitalize()} has no known parent."
        except Exception as e:
            print(f"Error checking grandparent relationship: {e}")
        
        return ""
    
    def _handle_shared_parent_conflict(self, new_parent: str, child: str, prolog, statement: str) -> str:
        """Handle conflicts with shared_parent relationships."""
        print(f"DEBUG: _handle_shared_parent_conflict called with new_parent={new_parent}, child={child}")
        try:
            # Check if any shared parent exists (with unique names)
            shared_parents = safe_prolog_query(prolog, f"parent_of(X, {child})")
            shared_mother_exists = False
            shared_father_exists = False
            
            for result in shared_parents:
                parent_name = result["X"]
                if parent_name.startswith("shared_mother_"):
                    shared_mother_exists = True
                elif parent_name.startswith("shared_father_"):
                    shared_father_exists = True
            
            # Determine the type of parent being added
            parent_type = None
            if "mother" in statement.lower():
                parent_type = "mother"
            elif "father" in statement.lower():
                parent_type = "father"
            else:
                # Try to determine from the new parent's gender
                new_parent_male = safe_prolog_query(prolog, f"male({new_parent})")
                new_parent_female = safe_prolog_query(prolog, f"female({new_parent})")
                if new_parent_male:
                    parent_type = "father"
                elif new_parent_female:
                    parent_type = "mother"
            
            # If shared_father exists and we're adding a father, delete shared_father and add father
            if shared_father_exists and parent_type == "father":
                print(f"DEBUG: Returning delete_shared_parent_add_father for {new_parent}")
                return f"delete_shared_parent_add_father:{new_parent}:{child}"
            
            # If shared_mother exists and we're adding a mother, delete shared_mother and add mother
            if shared_mother_exists and parent_type == "mother":
                print(f"DEBUG: Returning delete_shared_parent_add_mother for {new_parent}")
                return f"delete_shared_parent_add_mother:{new_parent}:{child}"
            
            # Otherwise, ask for clarification
            siblings = safe_prolog_query(prolog, f"sibling_of({child}, X)")
            sibling_names = [result["X"] for result in siblings]
            
            if sibling_names:
                sibling_list = ", ".join([s.capitalize() for s in sibling_names])
                return f"ask_clarification:{new_parent}:{child}:{sibling_list}"
            else:
                return "update_shared_parent"
        except Exception as e:
            print(f"Error handling shared parent conflict: {e}")
            return "update_shared_parent"
    
    def _check_parent_gender_conflicts(self, new_parent: str, child: str, existing_parents: list, prolog) -> str:
        """Check for gender conflicts between parents."""
        try:
            # Check if new parent is male
            new_parent_male = safe_prolog_query(prolog, f"male({new_parent})")
            new_parent_female = safe_prolog_query(prolog, f"female({new_parent})")
            
            # Check existing parents' genders
            existing_male_parents = []
            existing_female_parents = []
            
            for parent_name in existing_parents:
                if safe_prolog_query(prolog, f"male({parent_name})"):
                    existing_male_parents.append(parent_name)
                elif safe_prolog_query(prolog, f"female({parent_name})"):
                    existing_female_parents.append(parent_name)
            
            # If new parent is male and there's already a male parent
            if new_parent_male and existing_male_parents:
                # Check if the existing male parent is a placeholder (shared_father)
                has_shared_father = any(parent.startswith("shared_father_") for parent in existing_male_parents)
                if has_shared_father:
                    print(f"DEBUG: Replacing shared_father with {new_parent}")
                    return f"delete_shared_parent_add_father:{new_parent}:{child}"
                else:
                    return f"That's impossible! {child.capitalize()} already has a father ({existing_male_parents[0].capitalize()}). A person can only have one father."
            
            # If new parent is female and there's already a female parent
            if new_parent_female and existing_female_parents:
                # Check if the existing female parent is a placeholder (shared_mother)
                has_shared_mother = any(parent.startswith("shared_mother_") for parent in existing_female_parents)
                if has_shared_mother:
                    print(f"DEBUG: Replacing shared_mother with {new_parent}")
                    return f"delete_shared_parent_add_mother:{new_parent}:{child}"
                else:
                    return f"That's impossible! {child.capitalize()} already has a mother ({existing_female_parents[0].capitalize()}). A person can only have one mother."
            
        except Exception as e:
            print(f"Error checking gender conflicts: {e}")
        
        return ""
    
    def _check_sibling_relationships(self, statement: str, fact: str, prolog, has_content: bool) -> str:
        """Check for sibling relationship conflicts."""
        # Check for sibling_of and half_sibling_of facts
        sibling_match = re.search(r'sibling_of\(([^,]+),\s*([^)]+)\)', fact)
        half_sibling_match = re.search(r'half_sibling_of\(([^,]+),\s*([^)]+)\)', fact)
        
        if not sibling_match and not half_sibling_match:
            return ""
        
        # Extract person names
        if sibling_match:
            person1 = sibling_match.group(1)
            person2 = sibling_match.group(2)
        elif half_sibling_match:
            person1 = half_sibling_match.group(1)
            person2 = half_sibling_match.group(2)
        
        # Check if sibling relationship already exists
        if has_content:  # Only query if we have content
            try:
                existing_sibling = safe_prolog_query(prolog, f"sibling_of({person1}, {person2})")
                if existing_sibling:
                    return f"That's impossible! {person1.capitalize()} and {person2.capitalize()} are already siblings."
            except Exception as e:
                print(f"Error checking existing sibling relationship: {e}")
        
        # Check for impossible sibling relationships
        if has_content:
            try:
                # Check if person1 is a parent of person2
                parent_check = safe_prolog_query(prolog, f"parent_of({person1}, {person2})")
                if parent_check:
                    return f"That's impossible! {person1.capitalize()} cannot be a sibling of {person2.capitalize()} because {person1.capitalize()} is {person2.capitalize()}'s parent."
                
                # Check if person2 is a parent of person1
                parent_check = safe_prolog_query(prolog, f"parent_of({person2}, {person1})")
                if parent_check:
                    return f"That's impossible! {person1.capitalize()} cannot be a sibling of {person2.capitalize()} because {person2.capitalize()} is {person1.capitalize()}'s parent."
                
                # Check if person1 is a grandparent of person2
                grandparent_check = safe_prolog_query(prolog, f"grandparent_of({person1}, {person2})")
                if grandparent_check:
                    return f"That's impossible! {person1.capitalize()} cannot be a sibling of {person2.capitalize()} because {person1.capitalize()} is {person2.capitalize()}'s grandparent."
                
                # Check if person2 is a grandparent of person1
                grandparent_check = safe_prolog_query(prolog, f"grandparent_of({person2}, {person1})")
                if grandparent_check:
                    return f"That's impossible! {person1.capitalize()} cannot be a sibling of {person2.capitalize()} because {person2.capitalize()} is {person1.capitalize()}'s grandparent."
                
                # Check if person1 is a great-grandparent of person2
                great_grandparent_check = safe_prolog_query(prolog, f"parent_of({person1}, Z), parent_of(Z, W), parent_of(W, {person2})")
                if great_grandparent_check:
                    return f"That's impossible! {person1.capitalize()} cannot be a sibling of {person2.capitalize()} because {person1.capitalize()} is {person2.capitalize()}'s great-grandparent."
                
                # Check if person2 is a great-grandparent of person1
                great_grandparent_check = safe_prolog_query(prolog, f"parent_of({person2}, Z), parent_of(Z, W), parent_of(W, {person1})")
                if great_grandparent_check:
                    return f"That's impossible! {person1.capitalize()} cannot be a sibling of {person2.capitalize()} because {person2.capitalize()} is {person1.capitalize()}'s great-grandparent."
                
                # Check if they are cousins (have different parents who are siblings)
                cousin_check = safe_prolog_query(prolog, f"parent_of(P1, {person1}), parent_of(P2, {person2}), sibling_of(P1, P2), P1 \\= P2")
                if cousin_check:
                    return f"That's impossible! {person1.capitalize()} and {person2.capitalize()} cannot be siblings because they are cousins (their parents are siblings)."
                
                # Check if they are second cousins (grandparents are siblings)
                second_cousin_check = safe_prolog_query(prolog, f"parent_of(GP1, P1), parent_of(P1, {person1}), parent_of(GP2, P2), parent_of(P2, {person2}), sibling_of(GP1, GP2), GP1 \\= GP2")
                if second_cousin_check:
                    return f"That's impossible! {person1.capitalize()} and {person2.capitalize()} cannot be siblings because they are second cousins (their grandparents are siblings)."
                
                # Check if one is an aunt/uncle of the other
                aunt_uncle_check = safe_prolog_query(prolog, f"aunt_of({person1}, {person2})")
                if aunt_uncle_check:
                    return f"That's impossible! {person1.capitalize()} cannot be a sibling of {person2.capitalize()} because {person1.capitalize()} is {person2.capitalize()}'s aunt/uncle."
                
                aunt_uncle_check = safe_prolog_query(prolog, f"uncle_of({person1}, {person2})")
                if aunt_uncle_check:
                    return f"That's impossible! {person1.capitalize()} cannot be a sibling of {person2.capitalize()} because {person1.capitalize()} is {person2.capitalize()}'s uncle."
                
                aunt_uncle_check = safe_prolog_query(prolog, f"aunt_of({person2}, {person1})")
                if aunt_uncle_check:
                    return f"That's impossible! {person1.capitalize()} cannot be a sibling of {person2.capitalize()} because {person2.capitalize()} is {person1.capitalize()}'s aunt."
                
                aunt_uncle_check = safe_prolog_query(prolog, f"uncle_of({person2}, {person1})")
                if aunt_uncle_check:
                    return f"That's impossible! {person1.capitalize()} cannot be a sibling of {person2.capitalize()} because {person2.capitalize()} is {person1.capitalize()}'s uncle."
                
                # Check if one is a niece/nephew of the other
                niece_nephew_check = safe_prolog_query(prolog, f"niece_of({person1}, {person2})")
                if niece_nephew_check:
                    return f"That's impossible! {person1.capitalize()} cannot be a sibling of {person2.capitalize()} because {person1.capitalize()} is {person2.capitalize()}'s niece."
                
                niece_nephew_check = safe_prolog_query(prolog, f"nephew_of({person1}, {person2})")
                if niece_nephew_check:
                    return f"That's impossible! {person1.capitalize()} cannot be a sibling of {person2.capitalize()} because {person1.capitalize()} is {person2.capitalize()}'s nephew."
                
                niece_nephew_check = safe_prolog_query(prolog, f"niece_of({person2}, {person1})")
                if niece_nephew_check:
                    return f"That's impossible! {person1.capitalize()} cannot be a sibling of {person2.capitalize()} because {person2.capitalize()} is {person1.capitalize()}'s niece."
                
                niece_nephew_check = safe_prolog_query(prolog, f"nephew_of({person2}, {person1})")
                if niece_nephew_check:
                    return f"That's impossible! {person1.capitalize()} cannot be a sibling of {person2.capitalize()} because {person2.capitalize()} is {person1.capitalize()}'s nephew."
                
                # Check if they are already related in a way that precludes being siblings
                # This includes uncle-niece, aunt-nephew, etc.
                relative_check = safe_prolog_query(prolog, f"relative({person1}, {person2}), not(sibling_of({person1}, {person2}))")
                if relative_check:
                    # Get the specific relationship type for better error message
                    relationship_types = []
                    
                    # Check for specific relationship types
                    if safe_prolog_query(prolog, f"parent_of({person1}, {person2})"):
                        relationship_types.append("parent")
                    elif safe_prolog_query(prolog, f"parent_of({person2}, {person1})"):
                        relationship_types.append("child")
                    elif safe_prolog_query(prolog, f"grandparent_of({person1}, {person2})"):
                        relationship_types.append("grandparent")
                    elif safe_prolog_query(prolog, f"grandparent_of({person2}, {person1})"):
                        relationship_types.append("grandchild")
                    elif safe_prolog_query(prolog, f"aunt_of({person1}, {person2})"):
                        relationship_types.append("aunt")
                    elif safe_prolog_query(prolog, f"uncle_of({person1}, {person2})"):
                        relationship_types.append("uncle")
                    elif safe_prolog_query(prolog, f"aunt_of({person2}, {person1})"):
                        relationship_types.append("niece")
                    elif safe_prolog_query(prolog, f"uncle_of({person2}, {person1})"):
                        relationship_types.append("nephew")
                    elif safe_prolog_query(prolog, f"cousin_of({person1}, {person2})"):
                        relationship_types.append("cousin")
                    
                    if relationship_types:
                        relationship_str = relationship_types[0]
                        return f"That's impossible! {person1.capitalize()} and {person2.capitalize()} cannot be siblings because they are already {relationship_str}s."
                    else:
                        return f"That's impossible! {person1.capitalize()} and {person2.capitalize()} cannot be siblings because they are already related in a way that precludes being siblings."
                
            except Exception as e:
                print(f"Error checking impossible sibling relationships: {e}")
        
        # Always trigger full sibling clarification for new sibling relationships
        # This ensures we always ask if siblings are full or half siblings
        return f"ask_full_sibling_clarification:{person1}:{person2}"
    
    def _check_grandparent_relationships(self, statement: str, fact: str, prolog, has_content: bool) -> str:
        """Check for grandparent relationship validation."""
        # Check for direct grandmother/grandfather statements
        grandmother_match = re.search(r'grandmother_of\(([^,]+),\s*([^)]+)\)', fact)
        grandfather_match = re.search(r'grandfather_of\(([^,]+),\s*([^)]+)\)', fact)
        
        if grandmother_match:
            grandparent = grandmother_match.group(1)
            grandchild = grandmother_match.group(2)
            
            # Check for hierarchical validation FIRST
            hierarchical_error = self._check_hierarchical_validation(grandparent, grandchild, prolog, has_content)
            if hierarchical_error:
                return hierarchical_error
                
            return f"handle_direct_grandparent:{grandparent}:{grandchild}:female"
        elif grandfather_match:
            grandparent = grandfather_match.group(1)
            grandchild = grandfather_match.group(2)
            
            # Check for hierarchical validation FIRST
            hierarchical_error = self._check_hierarchical_validation(grandparent, grandchild, prolog, has_content)
            if hierarchical_error:
                return hierarchical_error
                
            return f"handle_direct_grandparent:{grandparent}:{grandchild}:male"
        elif "grandparent_of" in fact:
            # Generic grandparent relationship
            match = re.search(r'grandparent_of\(([^,]+),\s*([^)]+)\)', fact)
            if match:
                grandparent = match.group(1)
                grandchild = match.group(2)
                
                # Check for hierarchical validation FIRST
                hierarchical_error = self._check_hierarchical_validation(grandparent, grandchild, prolog, has_content)
                if hierarchical_error:
                    return hierarchical_error
                    
                return f"handle_direct_grandparent:{grandparent}:{grandchild}:unknown"
        
        return ""
    
    def _check_hierarchical_validation(self, grandparent: str, grandchild: str, prolog, has_content: bool) -> str:
        """Check for hierarchical validation to prevent impossible relationships."""
        if not has_content:
            return ""
            
        try:
            # Check if grandchild is already a parent of grandparent (impossible hierarchy)
            grandchild_is_parent = safe_prolog_query(prolog, f"parent_of({grandchild}, {grandparent})")
            if grandchild_is_parent:
                return f"That's impossible! {grandchild.capitalize()} cannot be a grandparent of {grandparent.capitalize()} because {grandchild.capitalize()} is {grandparent.capitalize()}'s parent."
            
            # Check if grandchild is already a grandparent of grandparent (impossible hierarchy)
            grandchild_is_grandparent = safe_prolog_query(prolog, f"grandparent_of({grandchild}, {grandparent})")
            if grandchild_is_grandparent:
                return f"That's impossible! {grandchild.capitalize()} cannot be a grandparent of {grandparent.capitalize()} because {grandchild.capitalize()} is already {grandparent.capitalize()}'s grandparent."
            
            # Check if grandchild is already an ancestor of grandparent (impossible hierarchy)
            grandchild_is_ancestor = safe_prolog_query(prolog, f"ancestor_of({grandchild}, {grandparent})")
            if grandchild_is_ancestor:
                return f"That's impossible! {grandchild.capitalize()} cannot be a grandparent of {grandparent.capitalize()} because {grandchild.capitalize()} is {grandparent.capitalize()}'s ancestor."
            
            # Check if grandparent is already a child of grandchild (impossible hierarchy)
            grandparent_is_child = safe_prolog_query(prolog, f"parent_of({grandparent}, {grandchild})")
            if grandparent_is_child:
                return f"That's impossible! {grandparent.capitalize()} cannot be a grandparent of {grandchild.capitalize()} because {grandparent.capitalize()} is {grandchild.capitalize()}'s child."
            
            # Check if grandparent is already a grandchild of grandchild (impossible hierarchy)
            grandparent_is_grandchild = safe_prolog_query(prolog, f"grandchild_of({grandparent}, {grandchild})")
            if grandparent_is_grandchild:
                return f"That's impossible! {grandparent.capitalize()} cannot be a grandparent of {grandchild.capitalize()} because {grandparent.capitalize()} is {grandchild.capitalize()}'s grandchild."
            
            # Check if grandparent is already a descendant of grandchild (impossible hierarchy)
            grandparent_is_descendant = safe_prolog_query(prolog, f"ancestor_of({grandchild}, {grandparent})")
            if grandparent_is_descendant:
                return f"That's impossible! {grandparent.capitalize()} cannot be a grandparent of {grandchild.capitalize()} because {grandparent.capitalize()} is {grandchild.capitalize()}'s descendant."
            
            # Check if they are already siblings (impossible hierarchy)
            they_are_siblings = safe_prolog_query(prolog, f"sibling_of({grandparent}, {grandchild})")
            if they_are_siblings:
                return f"That's impossible! {grandparent.capitalize()} cannot be a grandparent of {grandchild.capitalize()} because they are siblings."
            
            # Check if they are cousins (impossible hierarchy)
            they_are_cousins = safe_prolog_query(prolog, f"cousin_of({grandparent}, {grandchild})")
            if they_are_cousins:
                return f"That's impossible! {grandparent.capitalize()} cannot be a grandparent of {grandchild.capitalize()} because they are cousins."
            
            # Check if grandchild is already an aunt/uncle of grandparent (impossible hierarchy)
            grandchild_is_aunt_uncle = safe_prolog_query(prolog, f"aunt_of({grandchild}, {grandparent})")
            if grandchild_is_aunt_uncle:
                return f"That's impossible! {grandchild.capitalize()} cannot be a grandparent of {grandparent.capitalize()} because {grandchild.capitalize()} is {grandparent.capitalize()}'s aunt."
            
            grandchild_is_aunt_uncle = safe_prolog_query(prolog, f"uncle_of({grandchild}, {grandparent})")
            if grandchild_is_aunt_uncle:
                return f"That's impossible! {grandchild.capitalize()} cannot be a grandparent of {grandparent.capitalize()} because {grandchild.capitalize()} is {grandparent.capitalize()}'s uncle."
            
            # Check if grandparent is already a niece/nephew of grandchild (impossible hierarchy)
            grandparent_is_niece_nephew = safe_prolog_query(prolog, f"niece_of({grandparent}, {grandchild})")
            if grandparent_is_niece_nephew:
                return f"That's impossible! {grandparent.capitalize()} cannot be a grandparent of {grandchild.capitalize()} because {grandparent.capitalize()} is {grandchild.capitalize()}'s niece."
            
            grandparent_is_niece_nephew = safe_prolog_query(prolog, f"nephew_of({grandparent}, {grandchild})")
            if grandparent_is_niece_nephew:
                return f"That's impossible! {grandparent.capitalize()} cannot be a grandparent of {grandchild.capitalize()} because {grandparent.capitalize()} is {grandchild.capitalize()}'s nephew."
            
        except Exception as e:
            print(f"Error checking hierarchical validation: {e}")
        
        return ""
    
    def _check_parent_child_hierarchical_validation(self, parent: str, child: str, prolog) -> str:
        """Check for hierarchical validation to prevent impossible parent-child relationships."""
        try:
            # Check if child is already a parent of parent (impossible hierarchy)
            child_is_parent = safe_prolog_query(prolog, f"parent_of({child}, {parent})")
            if child_is_parent:
                return f"That's impossible! {child.capitalize()} cannot be a child of {parent.capitalize()} because {child.capitalize()} is {parent.capitalize()}'s parent."
            
            # Check if child is already a grandparent of parent (impossible hierarchy)
            child_is_grandparent = safe_prolog_query(prolog, f"grandparent_of({child}, {parent})")
            if child_is_grandparent:
                return f"That's impossible! {child.capitalize()} cannot be a child of {parent.capitalize()} because {child.capitalize()} is {parent.capitalize()}'s grandparent."
            
            # Check if parent is already a child of child (impossible hierarchy)
            parent_is_child = safe_prolog_query(prolog, f"parent_of({parent}, {child})")
            if parent_is_child:
                return f"That's impossible! {parent.capitalize()} cannot be a parent of {child.capitalize()} because {parent.capitalize()} is {child.capitalize()}'s child."
            
            # Check if parent is already a grandchild of child (impossible hierarchy)
            parent_is_grandchild = safe_prolog_query(prolog, f"grandchild_of({parent}, {child})")
            if parent_is_grandchild:
                return f"That's impossible! {parent.capitalize()} cannot be a parent of {child.capitalize()} because {parent.capitalize()} is {child.capitalize()}'s grandchild."
            
            # Check if they are already siblings (impossible hierarchy)
            they_are_siblings = safe_prolog_query(prolog, f"sibling_of({parent}, {child})")
            if they_are_siblings:
                return f"That's impossible! {parent.capitalize()} cannot be a parent of {child.capitalize()} because they are siblings."
            
            # Check if they are cousins (impossible hierarchy)
            they_are_cousins = safe_prolog_query(prolog, f"cousin_of({parent}, {child})")
            if they_are_cousins:
                return f"That's impossible! {parent.capitalize()} cannot be a parent of {child.capitalize()} because they are cousins."
            
            # Check if child is already an aunt/uncle of parent (impossible hierarchy)
            child_is_aunt_uncle = safe_prolog_query(prolog, f"aunt_of({child}, {parent})")
            if child_is_aunt_uncle:
                return f"That's impossible! {child.capitalize()} cannot be a child of {parent.capitalize()} because {child.capitalize()} is {parent.capitalize()}'s aunt."
            
            child_is_aunt_uncle = safe_prolog_query(prolog, f"uncle_of({child}, {parent})")
            if child_is_aunt_uncle:
                return f"That's impossible! {child.capitalize()} cannot be a child of {parent.capitalize()} because {child.capitalize()} is {parent.capitalize()}'s uncle."
            
            # Check if parent is already a niece/nephew of child (impossible hierarchy)
            parent_is_niece_nephew = safe_prolog_query(prolog, f"niece_of({parent}, {child})")
            if parent_is_niece_nephew:
                return f"That's impossible! {parent.capitalize()} cannot be a parent of {child.capitalize()} because {parent.capitalize()} is {child.capitalize()}'s niece."
            
            parent_is_niece_nephew = safe_prolog_query(prolog, f"nephew_of({parent}, {child})")
            if parent_is_niece_nephew:
                return f"That's impossible! {parent.capitalize()} cannot be a parent of {child.capitalize()} because {parent.capitalize()} is {child.capitalize()}'s nephew."
            
        except Exception as e:
            print(f"Error checking parent-child hierarchical validation: {e}")
        
        return ""
    
    def _check_aunt_uncle_relationships(self, statement: str, fact: str, prolog, has_content: bool) -> str:
        """Check for aunt/uncle relationship validation."""
        if "aunt_of" not in fact and "uncle_of" not in fact:
            return ""
        
        # Extract aunt/uncle and niece/nephew names
        match = re.search(r'(?:aunt|uncle)_of\(([^,]+),\s*([^)]+)\)', fact)
        if not match:
            return ""
        
        aunt_uncle = match.group(1)
        niece_nephew = match.group(2)
        
        try:
            # Find the parent of the niece/nephew
            parent_results = safe_prolog_query(prolog, f"parent_of(X, {niece_nephew})")
            if parent_results:
                parent_name = parent_results[0]["X"]
                
                # Check if aunt/uncle is already related to the parent
                existing_sibling = safe_prolog_query(prolog, f"sibling_of({aunt_uncle}, {parent_name})")
                if not existing_sibling:
                    # Trigger the new sophisticated aunt/uncle clarification
                    return f"ask_aunt_uncle_sophisticated:{aunt_uncle}:{niece_nephew}:{parent_name}"
            else:
                # No parent found - add aunt/uncle fact directly
                return f"add_direct_aunt_uncle:{aunt_uncle}:{niece_nephew}"
        except Exception as e:
            print(f"Error checking aunt/uncle relationship: {e}")
        
        return ""
    
    def _check_incestual_scenarios(self, fact: str, person_names: Set[str], prolog, has_content: bool) -> str:
        """Check for complex incestual scenarios."""
        if has_content:  # Only query if we have content
            try:
                # Check for self-relationships
                for person in person_names:
                    results = safe_prolog_query(prolog, f"parent_of({person}, {person})")
                    if results:
                        return f"That's impossible! {person.capitalize()} cannot be their own parent."
                
                # Check for circular relationships
                for person1 in person_names:
                    for person2 in person_names:
                        if person1 != person2:
                            results = safe_prolog_query(prolog, f"parent_of({person1}, {person2}), parent_of({person2}, {person1})")
                            if results:
                                return f"That's impossible! {person1.capitalize()} and {person2.capitalize()} cannot be each other's parents."
                
            except Exception as e:
                print(f"Error checking incestual scenarios: {e}")
        
        return "" 