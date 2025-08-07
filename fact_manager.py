import re
import time
from typing import List, Tuple
from pyswip import Prolog
from utils import to_prolog_name, validate_prolog_file, safe_prolog_query
from rule_writer import write_correct_rules

# Global variable for current knowledge base file
current_kb_file = "relationships.pl"

# Global variable for clarification context
clarification_context = None

class FactManager:
    def __init__(self):
        pass
    
    def add_fact(self, statement: str, statement_patterns: List[Tuple], validator) -> str:
        global clarification_context
        
        # Parse the statement into a fact
        fact, name_error = self._parse_statement_to_fact(statement, statement_patterns)
        if name_error:
            return name_error
        if not fact:
            return f"Unrecognized or invalid statement: {statement}"
        
        # Validate the relationship
        is_valid, error_message = validator.validate_relationship(statement, fact)
        if not is_valid:
            if error_message.startswith("ask_clarification:"):
                return self._handle_parent_clarification(error_message, statement)

            elif error_message.startswith("ask_aunt_uncle_clarification:"):
                return self._handle_aunt_uncle_clarification(error_message, statement)
            elif error_message.startswith("ask_aunt_uncle_sophisticated:"):
                return self._handle_aunt_uncle_sophisticated(error_message, statement)
            elif error_message.startswith("add_direct_aunt_uncle:"):
                return self._handle_direct_aunt_uncle(error_message, statement)
            elif error_message.startswith("ask_sibling_clarification:"):
                return self._handle_sibling_clarification(error_message, statement)

            elif error_message.startswith("ask_sibling_parent_clarification:"):
                return self._handle_sibling_parent_clarification(error_message, statement)
            elif error_message.startswith("ask_full_sibling_clarification:"):
                return self._handle_full_sibling_clarification(error_message, statement)
            elif error_message.startswith("add_parent_to_full_siblings:"):
                return self._handle_add_parent_to_full_siblings(error_message, statement)
            elif error_message.startswith("handle_direct_grandparent:"):
                return self._handle_direct_grandparent(error_message, statement)
            elif error_message.startswith("ask_grandparent_clarification:"):
                return self._handle_grandparent_clarification(error_message, statement)
            elif error_message.startswith("ask_child_clarification:"):
                return self._handle_child_clarification(error_message, statement)
            elif error_message.startswith("delete_shared_parent_add_father:"):
                return self._handle_delete_shared_parent_add_father(error_message, statement)
            elif error_message.startswith("delete_shared_parent_add_mother:"):
                return self._handle_delete_shared_parent_add_mother(error_message, statement)
            else:
                return error_message
        
        # Add the fact to the knowledge base
        return self._write_fact_to_file(fact, statement)
    
    def _parse_statement_to_fact(self, statement: str, statement_patterns: List[Tuple]) -> Tuple[str, str]:
        for _, pattern, func in statement_patterns:
            match = re.fullmatch(pattern, statement.strip())
            if match:
                # Determine which groups contain person names based on the pattern
                if "are siblings" in pattern or "are children of" in pattern:
                    # For multi-person patterns, skip name validation as names will be parsed in handler
                    pass
                elif "sibling" in pattern and "and" in pattern:
                    # For "X and Y are siblings" patterns, groups 1 and 2 are person names
                    person_name_groups = [1, 2]
                elif "parent" in pattern and "and" in pattern:
                    # For "X and Y are parents of Z" patterns, groups 1, 2, and 3 are person names
                    person_name_groups = [1, 2, 3]
                elif "is (male|female)" in pattern:
                    # For gender patterns like "X is male/female", only group 1 is a person name
                    person_name_groups = [1]
                elif len(match.groups()) >= 3:
                    # For most other patterns, groups 1 and 3 are person names (group 2 is relationship type)
                    person_name_groups = [1, 3]
                else:
                    # For simple patterns, groups 1 and 2 are person names
                    person_name_groups = [1, 2]
                
                # Skip validation for multi-person patterns
                if "are siblings" not in pattern and "are children of" not in pattern:
                    for i in person_name_groups:
                        if i <= len(match.groups()):
                            name = match.group(i)
                            from utils import validate_name
                            is_valid_name, name_error = validate_name(name)
                            if not is_valid_name:
                                return "", name_error
                return func(match), ""
        return "", ""
    
    def _handle_parent_clarification(self, error_message: str, statement: str) -> str:
        """Handle parent clarification requests."""
        global clarification_context
        
        parts = error_message.split(":")
        new_parent = parts[1]
        child = parts[2]
        siblings = parts[3]
        
        clarification_context = {
            "new_parent": new_parent,
            "child": child,
            "siblings": siblings,
            "original_statement": statement
        }
        
        return f"Clarification needed: Is {new_parent.capitalize()} also the parent of {siblings}? Answer with: yes or no."
    

    
    def _handle_aunt_uncle_clarification(self, error_message: str, statement: str) -> str:
        """Handle aunt/uncle clarification requests."""
        global clarification_context
        
        parts = error_message.split(":")
        aunt_uncle = parts[1]
        niece_nephew = parts[2]
        parent = parts[3]
        
        clarification_context = {
            "new_parent": aunt_uncle,
            "original_statement": statement,
            "child": niece_nephew,
            "siblings": f"{parent}"
        }
        
        # Check if this is aunt or uncle based on the original statement
        if "aunt" in statement.lower():
            return f"Clarification needed: Is {aunt_uncle.capitalize()} the sister of {parent.capitalize()}'s father or mother? Answer with: father or mother."
        else:
            return f"Clarification needed: Is {aunt_uncle.capitalize()} the brother of {parent.capitalize()}'s father or mother? Answer with: father or mother."
    
    def _handle_aunt_uncle_sophisticated(self, error_message: str, statement: str) -> str:
        """Handle sophisticated aunt/uncle clarification requests."""
        global clarification_context
        
        parts = error_message.split(":")
        aunt_uncle = parts[1]
        niece_nephew = parts[2]
        parent = parts[3]
        
        clarification_context = {
            "aunt_uncle": aunt_uncle,
            "niece_nephew": niece_nephew,
            "parent": parent,
            "original_statement": statement,
            "clarification_type": "aunt_uncle_sophisticated"
        }
        
        # Check if this is aunt or uncle based on the original statement
        if "aunt" in statement.lower():
            return f"Clarification needed: Is {aunt_uncle.capitalize()} a maternal aunt of {niece_nephew.capitalize()}? Answer with exactly 'yes' or 'no'."
        else:
            return f"Clarification needed: Is {aunt_uncle.capitalize()} a maternal uncle of {niece_nephew.capitalize()}? Answer with exactly 'yes' or 'no'."
    
    def _handle_direct_aunt_uncle(self, error_message: str, statement: str) -> str:
        """Handle direct aunt/uncle addition when niece/nephew has no parent."""
        parts = error_message.split(":")
        aunt_uncle = parts[1]
        niece_nephew = parts[2]
        
        try:
            # Read current contents
            with open(current_kb_file, "r", encoding="utf-8") as f:
                old_contents = f.read()
            
            # Add aunt/uncle relationship directly
            if "aunt" in statement.lower():
                new_facts = [
                    f"aunt_of({to_prolog_name(aunt_uncle)}, {to_prolog_name(niece_nephew)}).",
                    f"female({to_prolog_name(aunt_uncle)})."
                ]
            else:
                new_facts = [
                    f"uncle_of({to_prolog_name(aunt_uncle)}, {to_prolog_name(niece_nephew)}).",
                    f"male({to_prolog_name(aunt_uncle)})."
                ]
            
            # Write new facts at the top
            with open(current_kb_file, "w", encoding="utf-8") as f:
                f.write('\n'.join(new_facts) + '\n' + old_contents)
            
            return "OK! I learned something new."
            
        except Exception as e:
            print(f"Error adding direct aunt/uncle relationship: {e}")
            return f"Error adding relationship: {str(e)}"
    
    def _handle_sibling_clarification(self, error_message: str, statement: str) -> str:
        """Handle sibling clarification requests."""
        global clarification_context
        
        parts = error_message.split(":")
        person1 = parts[1]
        person2 = parts[2]
        
        clarification_context = {
            "person1": person1,
            "person2": person2,
            "siblings": "sibling_clarification",
            "original_statement": statement
        }
        
        return f"Clarification needed: To establish that {person1.capitalize()} and {person2.capitalize()} are siblings, I need to know their shared parent(s). Who is the mother of both {person1.capitalize()} and {person2.capitalize()}? (If they have different mothers, say 'none')"
    
    def _handle_full_sibling_clarification(self, error_message: str, statement: str) -> str:
        """Handle full sibling clarification requests."""
        global clarification_context
        
        parts = error_message.split(":")
        person1 = parts[1]
        person2 = parts[2]
        
        clarification_context = {
            "person1": person1,
            "person2": person2,
            "clarification_type": "full_sibling",
            "original_statement": statement
        }
        
        return f"Are {person1.capitalize()} and {person2.capitalize()} full siblings? Answer with exactly 'yes' or 'no' (without the apostrophes)."
    
    def _handle_add_parent_to_full_siblings(self, error_message: str, statement: str) -> str:
        """Handle adding a parent to all full siblings."""
        parts = error_message.split(":")
        parent = parts[1]
        child = parts[2]
        siblings_str = parts[3]
        
        # Parse the siblings list
        sibling_names = [s.strip() for s in siblings_str.split(',')]
        
        # Read current contents
        with open(current_kb_file, "r", encoding="utf-8") as f:
            old_contents = f.read()
        
        # Add parent relationship to all siblings
        new_facts = []
        for sibling in sibling_names:
            parent_fact = f"parent_of({parent}, {sibling})."
            if parent_fact not in old_contents:
                new_facts.append(parent_fact)
        
        # Add gender fact for the parent if not already present
        from pyswip import Prolog
        from utils import safe_prolog_query
        
        prolog = Prolog()
        prolog.consult(current_kb_file)
        
        # Determine parent gender from the statement
        if "mother" in statement.lower():
            gender_fact = f"female({parent})."
            if gender_fact not in old_contents:
                new_facts.append(gender_fact)
        elif "father" in statement.lower():
            gender_fact = f"male({parent})."
            if gender_fact not in old_contents:
                new_facts.append(gender_fact)
        
        if new_facts:
            return self._write_organized_facts_to_file(new_facts)
        else:
            return "I already knew that."
    
    def _handle_direct_grandparent(self, error_message: str, statement: str) -> str:
        """Handle direct grandparent statements with maternal/paternal clarification."""
        parts = error_message.split(":")
        grandparent = parts[1]
        grandchild = parts[2]
        grandparent_gender = parts[3]  # "male", "female", or "unknown"
        
        from pyswip import Prolog
        from utils import safe_prolog_query
        
        # Read current contents
        with open(current_kb_file, "r", encoding="utf-8") as f:
            old_contents = f.read()
        
        prolog = Prolog()
        prolog.consult(current_kb_file)
        
        # Find the parent(s) of the grandchild
        parent_results = safe_prolog_query(prolog, f"parent_of(X, {grandchild})")
        if not parent_results:
            # If grandchild has no parents, just add the grandparent relationship
            new_facts = []
            if grandparent_gender == "female":
                grandparent_fact = f"grandmother_of({grandparent}, {grandchild})."
            elif grandparent_gender == "male":
                grandparent_fact = f"grandfather_of({grandparent}, {grandchild})."
            else:
                grandparent_fact = f"grandparent_of({grandparent}, {grandchild})."
            
            if grandparent_fact not in old_contents:
                new_facts.append(grandparent_fact)
            
            # Add gender fact
            if grandparent_gender == "female":
                gender_fact = f"female({grandparent})."
                if gender_fact not in old_contents:
                    new_facts.append(gender_fact)
            elif grandparent_gender == "male":
                gender_fact = f"male({grandparent})."
                if gender_fact not in old_contents:
                    new_facts.append(gender_fact)
            
            if new_facts:
                return self._write_organized_facts_to_file(new_facts)
            else:
                return "I already knew that."
        
        # Check if this grandparent already exists for this grandchild
        if grandparent_gender == "female":
            existing_grandmother = safe_prolog_query(prolog, f"grandmother_of({grandparent}, {grandchild})")
            if existing_grandmother:
                return f"That's impossible! {grandparent.capitalize()} is already a grandmother of {grandchild.capitalize()}."
        elif grandparent_gender == "male":
            existing_grandfather = safe_prolog_query(prolog, f"grandfather_of({grandparent}, {grandchild})")
            if existing_grandfather:
                return f"That's impossible! {grandparent.capitalize()} is already a grandfather of {grandchild.capitalize()}."
        else:
            existing_grandparent = safe_prolog_query(prolog, f"grandparent_of({grandparent}, {grandchild})")
            if existing_grandparent:
                return f"That's impossible! {grandparent.capitalize()} is already a grandparent of {grandchild.capitalize()}."
        
        # Store the grandparent context for clarification
        global clarification_context
        clarification_context = {
            "grandparent": grandparent,
            "grandchild": grandchild,
            "grandparent_gender": grandparent_gender,
            "original_statement": statement
        }
        
        # Ask for clarification about maternal vs paternal
        if grandparent_gender == "female":
            return f"Is {grandparent.capitalize()} a maternal grandmother of {grandchild.capitalize()}? Answer with exactly 'yes' or 'no' (without the apostrophes)."
        elif grandparent_gender == "male":
            return f"Is {grandparent.capitalize()} a paternal grandfather of {grandchild.capitalize()}? Answer with exactly 'yes' or 'no' (without the apostrophes)."
        else:
            return f"Is {grandparent.capitalize()} a maternal or paternal grandparent of {grandchild.capitalize()}? Answer with exactly 'maternal' or 'paternal' (without the apostrophes)."
    
    def add_grandparent_relationship(self, grandparent: str, grandchild: str, grandparent_gender: str, grandparent_type: str, original_statement: str = "") -> str:
        """Add grandparent relationship based on clarification response."""
        from pyswip import Prolog
        from utils import safe_prolog_query
        
        # Read current contents
        with open(current_kb_file, "r", encoding="utf-8") as f:
            old_contents = f.read()
        
        prolog = Prolog()
        prolog.consult(current_kb_file)
        
        # Find the parent(s) of the grandchild
        parent_results = safe_prolog_query(prolog, f"parent_of(X, {grandchild})")
        if not parent_results:
            return "Error: No parents found for the grandchild."
        
        new_facts = []
        
        if grandparent_type == "maternal":
            # Find the mother of the grandchild
            mother_results = safe_prolog_query(prolog, f"mother_of(X, {grandchild})")
            if not mother_results:
                return f"That's impossible! {grandchild.capitalize()} doesn't have a mother. Please specify which parent {grandparent.capitalize()} is related to."
            
            mother = mother_results[0]["X"]
            
            # Check if mother already has a mother
            mother_has_mother = safe_prolog_query(prolog, f"mother_of(X, {mother})")
            if mother_has_mother:
                # Mother already has a mother, make grandparent an aunt of the mother (not the grandchild)
                existing_grandmother = mother_has_mother[0]["X"]
                
                # Add aunt relationship: new grandmother is aunt of the mother
                aunt_fact = f"aunt_of({grandparent}, {mother})."
                if aunt_fact not in old_contents:
                    new_facts.append(aunt_fact)
                
                # Add sibling relationship between existing grandmother and new grandmother
                sibling_fact = f"sibling_of({existing_grandmother}, {grandparent})."
                if sibling_fact not in old_contents:
                    new_facts.append(sibling_fact)
                
                # Add gender fact for new grandmother if not already present
                if grandparent_gender == "female":
                    gender_fact = f"female({grandparent})."
                    if gender_fact not in old_contents:
                        new_facts.append(gender_fact)
                
                # Add gender fact for existing grandmother if not already present
                existing_grandmother_female = safe_prolog_query(prolog, f"female({existing_grandmother})")
                if not existing_grandmother_female:
                    existing_grandmother_gender_fact = f"female({existing_grandmother})."
                    if existing_grandmother_gender_fact not in old_contents:
                        new_facts.append(existing_grandmother_gender_fact)
            else:
                # Mother has no mother, make grandparent the mother's mother
                parent_fact = f"parent_of({grandparent}, {mother})."
                if parent_fact not in old_contents:
                    new_facts.append(parent_fact)
        
        elif grandparent_type == "paternal":
            # Find the father of the grandchild
            father_results = safe_prolog_query(prolog, f"father_of(X, {grandchild})")
            if not father_results:
                return f"That's impossible! {grandchild.capitalize()} doesn't have a father. Please specify which parent {grandparent.capitalize()} is related to."
            
            father = father_results[0]["X"]
            
            # Check if father already has a mother (for paternal grandmother)
            if grandparent_gender == "female":
                father_has_mother = safe_prolog_query(prolog, f"mother_of(X, {father})")
                if father_has_mother:
                    # Father already has a mother, make grandparent an aunt of the father (not the grandchild)
                    existing_grandmother = father_has_mother[0]["X"]
                    
                    # Add aunt relationship: new grandmother is aunt of the father
                    aunt_fact = f"aunt_of({grandparent}, {father})."
                    if aunt_fact not in old_contents:
                        new_facts.append(aunt_fact)
                    
                    # Add sibling relationship between existing grandmother and new grandmother
                    sibling_fact = f"sibling_of({existing_grandmother}, {grandparent})."
                    if sibling_fact not in old_contents:
                        new_facts.append(sibling_fact)
                    
                    # Add gender fact for new grandmother if not already present
                    if grandparent_gender == "female":
                        gender_fact = f"female({grandparent})."
                        if gender_fact not in old_contents:
                            new_facts.append(gender_fact)
                    
                    # Add gender fact for existing grandmother if not already present
                    existing_grandmother_female = safe_prolog_query(prolog, f"female({existing_grandmother})")
                    if not existing_grandmother_female:
                        existing_grandmother_gender_fact = f"female({existing_grandmother})."
                        if existing_grandmother_gender_fact not in old_contents:
                            new_facts.append(existing_grandmother_gender_fact)
                else:
                    # Father has no mother, make grandparent the father's mother
                    parent_fact = f"parent_of({grandparent}, {father})."
                    if parent_fact not in old_contents:
                        new_facts.append(parent_fact)
            else:  # male grandparent (paternal grandfather)
                father_has_father = safe_prolog_query(prolog, f"father_of(X, {father})")
                if father_has_father:
                    # Father already has a father, make grandparent an uncle of the father (not the grandchild)
                    existing_grandfather = father_has_father[0]["X"]
                    
                    # Add uncle relationship: new grandfather is uncle of the father
                    uncle_fact = f"uncle_of({grandparent}, {father})."
                    if uncle_fact not in old_contents:
                        new_facts.append(uncle_fact)
                    
                    # Add sibling relationship between existing grandfather and new grandfather
                    sibling_fact = f"sibling_of({existing_grandfather}, {grandparent})."
                    if sibling_fact not in old_contents:
                        new_facts.append(sibling_fact)
                    
                    # Add gender fact for new grandfather if not already present
                    if grandparent_gender == "male":
                        gender_fact = f"male({grandparent})."
                        if gender_fact not in old_contents:
                            new_facts.append(gender_fact)
                    
                    # Add gender fact for existing grandfather if not already present
                    existing_grandfather_male = safe_prolog_query(prolog, f"male({existing_grandfather})")
                    if not existing_grandfather_male:
                        existing_grandfather_gender_fact = f"male({existing_grandfather})."
                        if existing_grandfather_gender_fact not in old_contents:
                            new_facts.append(existing_grandfather_gender_fact)
                else:
                    # Father has no father, make grandparent the father's father
                    parent_fact = f"parent_of({grandparent}, {father})."
                    if parent_fact not in old_contents:
                        new_facts.append(parent_fact)
        
        else:
            # Unknown type, just add grandparent relationship
            grandparent_fact = f"grandparent_of({grandparent}, {grandchild})."
            if grandparent_fact not in old_contents:
                new_facts.append(grandparent_fact)
        
        # Add the grandparent-grandchild relationship based on gender and type
        if grandparent_gender == "female":
            if grandparent_type == "maternal":
                grandparent_fact = f"grandmother_of({grandparent}, {grandchild})."
            else:  # paternal
                grandparent_fact = f"grandmother_of({grandparent}, {grandchild})."
        elif grandparent_gender == "male":
            if grandparent_type == "maternal":
                grandparent_fact = f"grandfather_of({grandparent}, {grandchild})."
            else:  # paternal
                grandparent_fact = f"grandfather_of({grandparent}, {grandchild})."
        else:
            grandparent_fact = f"grandparent_of({grandparent}, {grandchild})."
        
        if grandparent_fact not in old_contents:
            new_facts.append(grandparent_fact)
        
        # Add gender fact based on actual gender
        if grandparent_gender == "female":
            gender_fact = f"female({grandparent})."
            if gender_fact not in old_contents:
                new_facts.append(gender_fact)
        elif grandparent_gender == "male":
            gender_fact = f"male({grandparent})."
            if gender_fact not in old_contents:
                new_facts.append(gender_fact)
        
        if new_facts:
            return self._write_organized_facts_to_file(new_facts)
        else:
            return "I already knew that."
    

    
    def _handle_child_clarification(self, error_message: str, statement: str) -> str:
        """Handle child clarification requests."""
        global clarification_context
        
        parts = error_message.split(":")
        parent = parts[1]
        child = parts[2]
        existing_children = parts[3]
        
        clarification_context = {
            "new_parent": parent,
            "child": child,
            "siblings": existing_children,
            "original_statement": statement
        }
        
        return f"Clarification needed: Is {parent.capitalize()} also the parent of {existing_children}? Answer with: yes or no."
    
    def _handle_sibling_parent_clarification(self, error_message: str, statement: str) -> str:
        """Handle sibling parent clarification requests."""
        global clarification_context
        
        print(f"DEBUG: _handle_sibling_parent_clarification")
        print(f"DEBUG: error_message={error_message}")
        
        parts = error_message.split(":")
        new_parent = parts[1]
        child = parts[2]
        siblings = parts[3]
        siblings_needing_parent = parts[4] if len(parts) > 4 else siblings
        
        print(f"DEBUG: parts={parts}")
        print(f"DEBUG: new_parent={new_parent}, child={child}, siblings={siblings}")
        print(f"DEBUG: siblings_needing_parent={siblings_needing_parent}")
        
        clarification_context = {
            "new_parent": new_parent,
            "child": child,
            "siblings": siblings,
            "siblings_needing_parent": siblings_needing_parent,
            "original_statement": statement
        }
        
        print(f"DEBUG: clarification_context={clarification_context}")
        
        # Parse the siblings that need this parent type
        siblings_needing_parent_list = [s.strip() for s in siblings_needing_parent.split(',')]
        # Remove the child from the list since we're asking about siblings specifically
        siblings_only = [s for s in siblings_needing_parent_list if s != child]
        
        if siblings_only:
            # Determine if it's mother or father based on the original statement
            if "mother" in statement.lower():
                parent_type = "mother"
            elif "father" in statement.lower():
                parent_type = "father"
            else:
                parent_type = "parent"  # fallback
            
            # Create a list of sibling names that need this type of parent
            sibling_list = self._format_list_with_and([s.capitalize() for s in siblings_only])
            
            return f"Clarification needed: Is {new_parent.capitalize()} also the {parent_type} of {sibling_list}? Please answer with exactly 'yes' or 'no' (without the apostrophes)."
        else:
            return f"Clarification needed: Is {new_parent.capitalize()} also the parent of the other sibling? Please answer with exactly 'yes' or 'no' (without the apostrophes)."
    
    def _handle_delete_shared_parent_add_father(self, error_message: str, statement: str) -> str:
        """Handle deletion of shared_parent and addition of father for all siblings."""
        parts = error_message.split(":")
        new_parent = parts[1]
        child = parts[2]
        
        return self._delete_shared_parent_and_add_parent(new_parent, child, "male")
    
    def _handle_delete_shared_parent_add_mother(self, error_message: str, statement: str) -> str:
        """Handle deletion of shared_parent and addition of mother for all siblings."""
        parts = error_message.split(":")
        new_parent = parts[1]
        child = parts[2]
        
        return self._delete_shared_parent_and_add_parent(new_parent, child, "female")
    
    def _delete_shared_parent_and_add_parent(self, new_parent: str, child: str, gender: str) -> str:
        """Delete specific shared parent (with unique names) and add new parent for all siblings."""
        try:
            # Read current contents
            with open(current_kb_file, "r", encoding="utf-8") as f:
                old_contents = f.read()
            
            # Find the specific shared parent for this child
            from pyswip import Prolog
            from utils import to_prolog_name, safe_prolog_query
            prolog = Prolog()
            prolog.consult(current_kb_file)
            
            # Find the shared parent that this child has
            shared_parent_name = None
            shared_parent_children = []
            
            try:
                # Get all parents of this child
                parent_results = safe_prolog_query(prolog, f"parent_of(X, {child})")
                for result in parent_results:
                    parent_name = result["X"]
                    # Check if this is a shared parent of the correct gender
                    if gender == "female" and parent_name.startswith("shared_mother_"):
                        shared_parent_name = parent_name
                        break
                    elif gender == "male" and parent_name.startswith("shared_father_"):
                        shared_parent_name = parent_name
                        break
                
                if shared_parent_name:
                    # Find all children of this specific shared parent
                    children_results = safe_prolog_query(prolog, f"parent_of({shared_parent_name}, X)")
                    for result in children_results:
                        shared_parent_children.append(result["X"])
                        
            except Exception as e:
                print(f"Error querying shared parent children: {e}")
            
            if not shared_parent_name:
                print(f"DEBUG: No shared parent found for {child} with gender {gender}")
                return f"Error: No shared parent found for {child}"
            
            print(f"DEBUG: Replacing {shared_parent_name} with {new_parent}")
            
            # Create new facts to add
            new_facts = []
            
            # Add parent relationships for all children of the specific shared parent
            for child_name in shared_parent_children:
                parent_fact = f"parent_of({to_prolog_name(new_parent)}, {to_prolog_name(child_name)})."
                if parent_fact not in old_contents:
                    new_facts.append(parent_fact)
            
            # Add gender fact for the new parent
            gender_fact = f"{gender}({to_prolog_name(new_parent)})."
            if gender_fact not in old_contents:
                new_facts.append(gender_fact)
            
            # Remove only the specific shared parent facts and add new facts using organized method
            lines = old_contents.split('\n')
            filtered_lines = []
            for line in lines:
                # Skip lines that contain the specific shared parent being replaced
                # This includes parent_of facts and gender facts
                if shared_parent_name not in line:
                    filtered_lines.append(line)
            
            # Write the filtered content back to the file
            with open(current_kb_file, "w", encoding="utf-8") as f:
                f.write('\n'.join(filtered_lines))
            
            # Now add the new facts using the organized method
            return self._write_organized_facts_to_file(new_facts)
            
        except Exception as e:
            print(f"Error deleting shared parent: {e}")
            return f"Error deleting shared parent: {str(e)}"
    
    def _format_list_with_and(self, items: list) -> str:
        """Format a list with 'and' before the last item."""
        if len(items) == 1:
            return items[0]
        elif len(items) == 2:
            return f"{items[0]} and {items[1]}"
        else:
            return f"{', '.join(items[:-1])}, and {items[-1]}"
    

    

    
    def _write_organized_facts_to_file(self, new_facts: list, statement: str = "") -> str:
        """Write facts to file with proper organization."""
        try:
            # Read current contents
            with open(current_kb_file, "r", encoding="utf-8") as f:
                old_contents = f.read()
            
            # Only allow valid Prolog facts (predicate(args).), skip invalid lines
            valid_fact_pattern = re.compile(r"^[a-z_]+\([a-z0-9_, ']+\)\.$")
            valid_new_facts = []
            for fact_line in new_facts:
                if fact_line.strip() and valid_fact_pattern.match(fact_line.strip()):
                    # Special handling for gender facts - always add if not already present
                    if fact_line.strip().startswith('female(') or fact_line.strip().startswith('male('):
                        if fact_line.strip() not in old_contents:
                            valid_new_facts.append(fact_line)
                    # For non-gender facts, only add if not already present
                    elif fact_line.strip() not in old_contents:
                        valid_new_facts.append(fact_line)
                else:
                    if fact_line.strip():
                        print(f"Skipping invalid fact line: {fact_line}")
            
            if valid_new_facts:
                # Organize the file properly: facts at top, then discontiguous declarations, then rules
                lines = old_contents.split('\n')
                fact_lines = []
                rule_lines = []
                discontiguous_lines = []
                comment_lines = []
                
                # Handle multi-line rules properly
                i = 0
                while i < len(lines):
                    line_stripped = lines[i].strip()
                    
                    if line_stripped.startswith('%'):
                        comment_lines.append(lines[i])
                    elif line_stripped == '':
                        pass
                    elif line_stripped.startswith(':- discontiguous'):
                        discontiguous_lines.append(line_stripped)
                    elif line_stripped.endswith('.') and ':-' not in line_stripped:
                        # This is a fact (ends with . but doesn't contain :-)
                        fact_lines.append(line_stripped)
                    elif ':-' in line_stripped:
                        # This is a rule (contains :-)
                        # Check if it's a multi-line rule
                        rule_text = line_stripped
                        j = i + 1
                        while j < len(lines) and not lines[j].strip().endswith('.'):
                            rule_text += ' ' + lines[j].strip()
                            j += 1
                        if j < len(lines) and lines[j].strip().endswith('.'):
                            rule_text += ' ' + lines[j].strip()
                            i = j  # Skip the lines we've already processed
                        rule_lines.append(rule_text)
                    elif line_stripped.endswith('.'):
                        # Fallback for any other lines ending with .
                        fact_lines.append(line_stripped)
                    
                    i += 1
                
                # Deduplicate existing facts and add new facts
                fact_lines = list(set(fact_lines))  # Remove duplicates from existing facts
                fact_lines.extend(valid_new_facts)
                
                # Deduplicate discontiguous declarations
                discontiguous_lines = list(set(discontiguous_lines))
                discontiguous_lines.sort()  # Sort for consistent ordering
                
                # Ensure all necessary discontiguous declarations are present
                required_declarations = [
                    ':- discontiguous parent_of/2.',
                    ':- discontiguous male/1.',
                    ':- discontiguous female/1.',
                    ':- discontiguous sibling_of/2.',
                    ':- discontiguous half_sibling_of/2.',
                    ':- discontiguous brother_of/2.',
                    ':- discontiguous sister_of/2.',
                    ':- discontiguous uncle_of/2.',
                    ':- discontiguous aunt_of/2.',
                    ':- discontiguous niece_of/2.',
                    ':- discontiguous nephew_of/2.',
                    ':- discontiguous cousin_of/2.',
                    ':- discontiguous relative/2.',
                    ':- discontiguous ancestor_of/2.',
                    ':- discontiguous grandparent_of/2.',
                    ':- discontiguous grandchild_of/2.',
                    ':- discontiguous grandmother_of/2.',
                    ':- discontiguous grandfather_of/2.',
                    ':- discontiguous granddaughter_of/2.',
                    ':- discontiguous grandson_of/2.',
                    ':- discontiguous father_of/2.',
                    ':- discontiguous mother_of/2.',
                    ':- discontiguous child_of/2.',
                    ':- discontiguous son_of/2.',
                    ':- discontiguous daughter_of/2.',
                    ':- discontiguous half_brother_of/2.',
                    ':- discontiguous half_sister_of/2.',
                    ':- discontiguous impossible_circular/2.',
                    ':- discontiguous incestual_sibling_parent/2.'
                ]
                
                # Add any missing required declarations
                for decl in required_declarations:
                    if decl not in discontiguous_lines:
                        discontiguous_lines.append(decl)
                
                # Sort again to ensure consistent ordering
                discontiguous_lines.sort()
                
                # Write organized file
                with open(current_kb_file, "w", encoding="utf-8") as f:
                    # Write discontiguous declarations first (at the very top)
                    f.write("% Discontiguous declarations to suppress warnings\n")
                    for decl in discontiguous_lines:
                        f.write(decl + '\n')
                    f.write('\n% Family Relationship Facts\n')
                    for fact in fact_lines:
                        f.write(fact + '\n')
                    f.write('\n% Family Relationship Rules\n\n')
                    # Write rules without discontiguous declarations to avoid duplicates
                    self._write_rules_without_declarations(f)
                
                # Add a small delay to ensure file is fully written
                time.sleep(0.1)
                
                # Contingency check: Clean up any shared parent conflicts
                self._cleanup_shared_parent_conflicts()
                
                return "OK! I learned something new."
            else:
                return "I already knew that."
        except Exception as e:
            print(f"Error writing organized facts to file: {e}")
            return f"Error adding facts: {str(e)}"
    
    def _write_fact_to_file(self, fact: str, statement: str) -> str:
        """Write a single fact to file with proper organization."""
        fact_lines = fact.split('\n')
        return self._write_organized_facts_to_file(fact_lines, statement)
    
    def _update_relationships_after_fact_addition(self, fact: str, person_names: set):
        """Update relationships after adding a fact."""
        try:
            # This can be expanded to add more intelligent relationship updates
            pass
        except Exception as e:
            print(f"Error updating relationships: {e}")
    
    def _cleanup_shared_parent_conflicts(self):
        """Clean up any shared parent conflicts by detecting real parents and replacing placeholders."""
        try:
            from pyswip import Prolog
            from utils import safe_prolog_query
            
            # Read current contents
            with open(current_kb_file, "r", encoding="utf-8") as f:
                old_contents = f.read()
            
            # Check if there are any shared parent facts (with unique names)
            has_shared_parents = any("shared_mother_" in line or "shared_father_" in line for line in old_contents.split('\n'))
            if not has_shared_parents:
                return  # No shared parents to clean up
            
            prolog = Prolog()
            prolog.consult(current_kb_file)
            
            # Find all real parents (non-shared parents)
            real_parents = []
            try:
                # Get all parent relationships
                parent_results = safe_prolog_query(prolog, "parent_of(X, Y)")
                for result in parent_results:
                    parent = result["X"]
                    child = result["Y"]
                    # Check if this is not a shared parent
                    if not (parent.startswith("shared_mother_") or parent.startswith("shared_father_")):
                        real_parents.append((parent, child))
            except Exception as e:
                print(f"Error querying real parents: {e}")
                return
            
            # Check for conflicts where a real parent and shared parent exist for the same child
            conflicts_to_resolve = []
            
            for real_parent, child in real_parents:
                # Check if this child also has a shared parent of the same gender
                try:
                    # Determine real parent's gender
                    real_parent_male = safe_prolog_query(prolog, f"male({real_parent})")
                    real_parent_female = safe_prolog_query(prolog, f"female({real_parent})")
                    
                    if real_parent_male:
                        # Check if child has any shared_father
                        child_parents = safe_prolog_query(prolog, f"parent_of(X, {child})")
                        for parent_result in child_parents:
                            parent_name = parent_result["X"]
                            if parent_name.startswith("shared_father_"):
                                conflicts_to_resolve.append((parent_name, real_parent, child))
                                break
                    elif real_parent_female:
                        # Check if child has any shared_mother
                        child_parents = safe_prolog_query(prolog, f"parent_of(X, {child})")
                        for parent_result in child_parents:
                            parent_name = parent_result["X"]
                            if parent_name.startswith("shared_mother_"):
                                conflicts_to_resolve.append((parent_name, real_parent, child))
                                break
                except Exception as e:
                    print(f"Error checking shared parent conflicts: {e}")
            
            # Resolve conflicts
            for shared_parent, real_parent, child in conflicts_to_resolve:
                print(f"DEBUG: Resolving conflict - replacing {shared_parent} with {real_parent} for {child}")
                gender = "male" if shared_parent.startswith("shared_father_") else "female"
                self._delete_shared_parent_and_add_parent(real_parent, child, gender)
                
        except Exception as e:
            print(f"Error in cleanup_shared_parent_conflicts: {e}")
    
    def _write_rules_without_declarations(self, f):
        """Write Prolog rules without discontiguous declarations to avoid duplicates."""
        f.write("% ========================================\n")
        f.write("% Basic Parent-Child Relationships\n")
        f.write("% ========================================\n")
        f.write("father_of(X, Y) :- parent_of(X, Y), male(X), X \\= Y.\n")
        f.write("mother_of(X, Y) :- parent_of(X, Y), female(X), X \\= Y.\n")
        f.write("child_of(Y, X) :- parent_of(X, Y), X \\= Y.\n")
        f.write("son_of(Y, X) :- child_of(Y, X), male(Y).\n")
        f.write("daughter_of(Y, X) :- child_of(Y, X), female(Y).\n")
        f.write("\n")
        
        f.write("% ========================================\n")
        f.write("% Sibling Relationships\n")
        f.write("% ========================================\n")
        f.write("sibling_of(X, Y) :- parent_of(Z, X), parent_of(Z, Y), X \\= Y, Z \\= X, Z \\= Y.\n")
        f.write("brother_of(X, Y) :- sibling_of(X, Y), male(X).\n")
        f.write("sister_of(X, Y) :- sibling_of(X, Y), female(X).\n")
        f.write("\n")
        f.write("% Half-sibling relationships\n")
        f.write("half_sibling_of(X, Y) :- parent_of(Z, X), parent_of(Z, Y), X \\= Y, parent_of(W1, X), parent_of(W2, Y), W1 \\= W2, W1 \\= Z, W2 \\= Z.\n")
        f.write("half_brother_of(X, Y) :- half_sibling_of(X, Y), male(X).\n")
        f.write("half_sister_of(X, Y) :- half_sibling_of(X, Y), female(X).\n")
        f.write("\n")
        
        f.write("% ========================================\n")
        f.write("% Grandparent-Grandchild Relationships\n")
        f.write("% ========================================\n")
        f.write("grandparent_of(X, Y) :- parent_of(X, Z), parent_of(Z, Y), X \\= Y.\n")
        f.write("grandmother_of(X, Y) :- grandparent_of(X, Y), female(X).\n")
        f.write("grandfather_of(X, Y) :- grandparent_of(X, Y), male(X).\n")
        f.write("grandchild_of(Y, X) :- grandparent_of(X, Y), X \\= Y.\n")
        f.write("granddaughter_of(Y, X) :- grandchild_of(Y, X), female(Y).\n")
        f.write("grandson_of(Y, X) :- grandchild_of(Y, X), male(Y).\n")
        f.write("\n")
        
        f.write("% ========================================\n")
        f.write("% Uncle/Aunt - Niece/Nephew Relationships\n")
        f.write("% ========================================\n")
        f.write("uncle_of(X, Y) :- brother_of(X, Z), parent_of(Z, Y), X \\= Y.\n")
        f.write("aunt_of(X, Y) :- sister_of(X, Z), parent_of(Z, Y), X \\= Y.\n")
        f.write("niece_of(Y, X) :- female(Y), uncle_of(X, Y), X \\= Y.\n")
        f.write("niece_of(Y, X) :- female(Y), aunt_of(X, Y), X \\= Y.\n")
        f.write("nephew_of(Y, X) :- male(Y), uncle_of(X, Y), X \\= Y.\n")
        f.write("nephew_of(Y, X) :- male(Y), aunt_of(X, Y), X \\= Y.\n")
        f.write("\n")
        


        
        f.write("% ========================================\n")
        f.write("% Cousin Relationships\n")
        f.write("% ========================================\n")
        f.write("cousin_of(X, Y) :- parent_of(Z1, X), parent_of(Z2, Y), sibling_of(Z1, Z2), X \\= Y.\n")
        f.write("\n")
        
        f.write("% ========================================\n")
        f.write("% General Relative Relationships\n")
        f.write("% ========================================\n")
        f.write("relative(X, Y) :- parent_of(X, Y).\n")
        f.write("relative(X, Y) :- parent_of(Y, X).\n")
        f.write("relative(X, Y) :- child_of(X, Y).\n")
        f.write("relative(X, Y) :- child_of(Y, X).\n")
        f.write("relative(X, Y) :- sibling_of(X, Y).\n")
        f.write("relative(X, Y) :- sibling_of(Y, X).\n")
        f.write("relative(X, Y) :- grandparent_of(X, Y).\n")
        f.write("relative(X, Y) :- grandparent_of(Y, X).\n")
        f.write("relative(X, Y) :- uncle_of(X, Y).\n")
        f.write("relative(X, Y) :- uncle_of(Y, X).\n")
        f.write("relative(X, Y) :- aunt_of(X, Y).\n")
        f.write("relative(X, Y) :- aunt_of(Y, X).\n")
        f.write("relative(X, Y) :- cousin_of(X, Y).\n")
        f.write("relative(X, Y) :- cousin_of(Y, X).\n")
        f.write("relative(X, Y) :- half_sibling_of(X, Y).\n")
        f.write("relative(X, Y) :- half_sibling_of(Y, X).\n")
        f.write("\n")
        
        f.write("% ========================================\n")
        f.write("% Ancestor-Descendant Relationships\n")
        f.write("% ========================================\n")
        f.write("ancestor_of(X, Y) :- parent_of(X, Y).\n")
        f.write("ancestor_of(X, Y) :- parent_of(X, Z), parent_of(Z, Y), X \\= Y.\n")
        f.write("ancestor_of(X, Y) :- parent_of(X, Z1), parent_of(Z1, Z2), parent_of(Z2, Y), X \\= Y, Z1 \\= Y.\n")
        f.write("\n")
        
        f.write("% ========================================\n")
        f.write("% Validation Rules (for detecting invalid relationships)\n")
        f.write("% ========================================\n")
        f.write("impossible_circular(X, Y) :- parent_of(X, Y), parent_of(Y, X).\n")
        f.write("incestual_sibling_parent(X, Y) :- sibling_of(X, Y), parent_of(X, Y).\n")
        f.write("incestual_sibling_parent(X, Y) :- sibling_of(X, Y), parent_of(Y, X).\n")
    
    def update_shared_parent_relationships(self, new_parent: str, child: str) -> str:
        """Update all shared_parent relationships to use the actual parent name."""
        try:
            # Read current contents
            with open(current_kb_file, "r", encoding="utf-8") as f:
                old_contents = f.read()
            
            # Find all shared_parent relationships for this child's siblings
            shared_parent_pattern = r'parent_of\(shared_parent,\s*([^)]+)\)'
            sibling_matches = re.findall(shared_parent_pattern, old_contents)
            
            # Replace shared_parent with the actual parent name
            new_contents = old_contents.replace("parent_of(shared_parent, ", f"parent_of({new_parent}, ")
            
            # Write back to file
            with open(current_kb_file, "w", encoding="utf-8") as f:
                f.write(new_contents)
            
            return f"I updated the shared parent to {new_parent.capitalize()} for all siblings."
            
        except Exception as e:
            print(f"Error updating shared parent relationships: {e}")
            return f"Error updating relationships: {str(e)}"
    
    def add_parent_for_all_siblings(self, new_parent: str, child: str, siblings: str, original_statement: str = "") -> str:
        """Add parent relationship for all specified siblings."""
        try:
            # Read current contents
            with open(current_kb_file, "r", encoding="utf-8") as f:
                old_contents = f.read()
            
            # Parse sibling names
            sibling_names = [s.strip() for s in siblings.split(',')]
            print(f"DEBUG: add_parent_for_all_siblings called with new_parent={new_parent}, child={child}, siblings={siblings}")
            print(f"DEBUG: sibling_names={sibling_names}")
            
            # Determine parent gender and type from original statement
            if "mother" in original_statement.lower():
                parent_gender = "female"
                parent_type = "mother"
            elif "father" in original_statement.lower():
                parent_gender = "male"
                parent_type = "father"
            else:
                parent_gender = "female"  # default
                parent_type = "parent"  # fallback
            
            # Validate that we're not adding a second parent of the same gender
            from pyswip import Prolog
            prolog = Prolog()
            prolog.consult(current_kb_file)
            
            # Check each sibling for existing parents of the same gender
            for sibling in sibling_names:
                existing_parents = safe_prolog_query(prolog, f"parent_of(X, {sibling})")
                if existing_parents:
                    existing_parent_names = [result["X"] for result in existing_parents]
                    
                    # Check for gender conflicts
                    existing_male_parents = []
                    existing_female_parents = []
                    
                    for parent_name in existing_parent_names:
                        if safe_prolog_query(prolog, f"male({parent_name})"):
                            existing_male_parents.append(parent_name)
                        elif safe_prolog_query(prolog, f"female({parent_name})"):
                            existing_female_parents.append(parent_name)
                    
                    # If new parent is male and there's already a male parent
                    if parent_gender == "male" and existing_male_parents:
                        return f"That's impossible! {sibling.capitalize()} already has a father ({existing_male_parents[0].capitalize()}). A person can only have one father."
                    
                    # If new parent is female and there's already a female parent
                    if parent_gender == "female" and existing_female_parents:
                        return f"That's impossible! {sibling.capitalize()} already has a mother ({existing_female_parents[0].capitalize()}). A person can only have one mother."
            
            # Add parent relationships for all siblings
            new_facts = []
            for sibling in sibling_names:
                fact = f"parent_of({to_prolog_name(new_parent)}, {to_prolog_name(sibling)})."
                print(f"DEBUG: checking fact={fact}")
                print(f"DEBUG: fact in old_contents = {fact in old_contents}")
                # Only add if not already present
                if fact not in old_contents:
                    new_facts.append(fact)
                    print(f"DEBUG: added fact={fact}")
                else:
                    print(f"DEBUG: skipped fact={fact} (already exists)")
            
            print(f"DEBUG: new_facts={new_facts}")
            
            # Add gender fact for the parent
            parent_gender_fact = f"{parent_gender}({to_prolog_name(new_parent)})."
            if parent_gender_fact not in old_contents:
                new_facts.append(parent_gender_fact)
                print(f"DEBUG: Adding parent gender fact: {parent_gender_fact}")
            else:
                print(f"DEBUG: Parent gender fact already exists: {parent_gender_fact}")
            
            # Write all new facts at once to avoid duplicate checking issues
            if new_facts:
                # Organize the file properly: facts at top, then discontiguous declarations, then rules
                lines = old_contents.split('\n')
                fact_lines = []
                rule_lines = []
                discontiguous_lines = []
                comment_lines = []
                
                # Handle multi-line rules properly
                i = 0
                while i < len(lines):
                    line_stripped = lines[i].strip()
                    
                    if line_stripped.startswith('%'):
                        comment_lines.append(lines[i])
                    elif line_stripped == '':
                        pass
                    elif line_stripped.startswith(':- discontiguous'):
                        discontiguous_lines.append(line_stripped)
                    elif line_stripped.endswith('.') and ':-' not in line_stripped:
                        # This is a fact (ends with . but doesn't contain :-)
                        fact_lines.append(line_stripped)
                    elif ':-' in line_stripped:
                        # This is a rule (contains :-)
                        # Check if it's a multi-line rule
                        rule_text = line_stripped
                        j = i + 1
                        while j < len(lines) and not lines[j].strip().endswith('.'):
                            rule_text += ' ' + lines[j].strip()
                            j += 1
                        if j < len(lines) and lines[j].strip().endswith('.'):
                            rule_text += ' ' + lines[j].strip()
                            i = j  # Skip the lines we've already processed
                        rule_lines.append(rule_text)
                    elif line_stripped.endswith('.'):
                        # Fallback for any other lines ending with .
                        fact_lines.append(line_stripped)
                    
                    i += 1
                
                # Add new facts to existing facts
                fact_lines.extend(new_facts)
                
                # Deduplicate discontiguous declarations
                discontiguous_lines = list(set(discontiguous_lines))
                discontiguous_lines.sort()  # Sort for consistent ordering
                
                # Ensure all necessary discontiguous declarations are present
                required_declarations = [
                    ':- discontiguous parent_of/2.',
                    ':- discontiguous male/1.',
                    ':- discontiguous female/1.',
                    ':- discontiguous sibling_of/2.',
                    ':- discontiguous half_sibling_of/2.',
                    ':- discontiguous brother_of/2.',
                    ':- discontiguous sister_of/2.',
                    ':- discontiguous uncle_of/2.',
                    ':- discontiguous aunt_of/2.',
                    ':- discontiguous niece_of/2.',
                    ':- discontiguous nephew_of/2.',
                    ':- discontiguous cousin_of/2.',
                    ':- discontiguous relative/2.',
                    ':- discontiguous ancestor_of/2.',
                    ':- discontiguous grandparent_of/2.',
                    ':- discontiguous grandchild_of/2.',
                    ':- discontiguous grandmother_of/2.',
                    ':- discontiguous grandfather_of/2.',
                    ':- discontiguous granddaughter_of/2.',
                    ':- discontiguous grandson_of/2.',
                    ':- discontiguous father_of/2.',
                    ':- discontiguous mother_of/2.',
                    ':- discontiguous child_of/2.',
                    ':- discontiguous son_of/2.',
                    ':- discontiguous daughter_of/2.',
                    ':- discontiguous half_brother_of/2.',
                    ':- discontiguous half_sister_of/2.',
                    ':- discontiguous impossible_circular/2.',
                    ':- discontiguous incestual_sibling_parent/2.'
                ]
                
                # Add any missing required declarations
                for decl in required_declarations:
                    if decl not in discontiguous_lines:
                        discontiguous_lines.append(decl)
                
                # Sort again to ensure consistent ordering
                discontiguous_lines.sort()
                
                # Write organized file
                with open(current_kb_file, "w", encoding="utf-8") as f:
                    # Write discontiguous declarations first (at the very top)
                    f.write("% Discontiguous declarations to suppress warnings\n")
                    for decl in discontiguous_lines:
                        f.write(decl + '\n')
                    f.write('\n% Family Relationship Facts\n')
                    for fact in fact_lines:
                        f.write(fact + '\n')
                    f.write('\n% Family Relationship Rules\n\n')
                    # Write rules without discontiguous declarations to avoid duplicates
                    self._write_rules_without_declarations(f)
                
                # Add a small delay to ensure file is fully written
                time.sleep(0.1)
            else:
                print(f"DEBUG: No new facts to add")
            
            return "OK! I learned something new."
            
        except Exception as e:
            print(f"Error adding parent for all siblings: {e}")
            return f"Error adding relationships: {str(e)}"
    
    def add_parent_with_shared_parent(self, new_parent: str, child: str, siblings_str: str, original_statement: str) -> str:
        """Add parent relationship for child and shared_parent for ALL siblings, plus half_sibling facts."""
        print(f"DEBUG: add_parent_with_shared_parent called with new_parent={new_parent}, child={child}, siblings_str={siblings_str}")
        try:
            # Parse all siblings
            sibling_names = [s.strip() for s in siblings_str.split(',')]
            # Remove the child from the sibling list
            other_siblings = [s for s in sibling_names if s != child]
            
            # Read current contents
            with open(current_kb_file, "r", encoding="utf-8") as f:
                old_contents = f.read()
            
            # Check if siblings already share a parent before adding shared_parent facts
            from pyswip import Prolog
            prolog = Prolog()
            prolog.consult(current_kb_file)
            
            # Find all siblings
            all_siblings = set()
            siblings = safe_prolog_query(prolog, f"sibling_of({child}, X)")
            if siblings:
                for sib in siblings:
                    all_siblings.add(sib["X"])
            
            siblings = safe_prolog_query(prolog, f"sibling_of(X, {child})")
            if siblings:
                for sib in siblings:
                    all_siblings.add(sib["X"])
            
            # Check if all siblings already share a parent
            siblings_already_share_parent = False
            if all_siblings:
                # Check if all siblings have at least one common parent
                all_parents = []
                for sibling in all_siblings:
                    sibling_parents = safe_prolog_query(prolog, f"parent_of(X, {sibling})")
                    if sibling_parents:
                        for parent_result in sibling_parents:
                            all_parents.append(parent_result["X"])
                
                # If all siblings have the same parent(s), they already share a parent
                if len(set(all_parents)) == 1 and len(all_parents) >= len(all_siblings):
                    siblings_already_share_parent = True
                    print(f"DEBUG: Siblings already share parent(s): {set(all_parents)}")
                
                # Also check if all siblings have at least one parent of the opposite gender
                # This handles cases where they share a mother but need a father, or vice versa
                opposite_gender = "male" if "mother" in original_statement.lower() else "female" if "father" in original_statement.lower() else None
                if opposite_gender and not siblings_already_share_parent:
                    all_have_opposite_gender_parent = True
                    for sibling in all_siblings:
                        sibling_parents = safe_prolog_query(prolog, f"parent_of(X, {sibling})")
                        has_opposite_gender_parent = False
                        if sibling_parents:
                            for parent_result in sibling_parents:
                                parent_name = parent_result["X"]
                                if opposite_gender == "male":
                                    parent_gender = safe_prolog_query(prolog, f"male({parent_name})")
                                else:
                                    parent_gender = safe_prolog_query(prolog, f"female({parent_name})")
                                if parent_gender:
                                    has_opposite_gender_parent = True
                                    break
                        if not has_opposite_gender_parent:
                            all_have_opposite_gender_parent = False
                            break
                    
                    if all_have_opposite_gender_parent:
                        siblings_already_share_parent = True
                        print(f"DEBUG: Siblings already share a {opposite_gender} parent")
            
            # Determine parent type and shared_parent gender
            if "mother" in original_statement.lower():
                parent_type = "mother"
                shared_parent_gender = "male"  # If mother is added, shared_parent is father
            elif "father" in original_statement.lower():
                parent_type = "father"
                shared_parent_gender = "female"  # If father is added, shared_parent is mother
            else:
                parent_type = "parent"  # fallback
                shared_parent_gender = "male"  # Default to male if unclear
            
            # Create facts to add
            new_facts = []
            
            # Add the specific parent relationship
            parent_fact = f"parent_of({to_prolog_name(new_parent)}, {to_prolog_name(child)})."
            if parent_fact not in old_contents:
                new_facts.append(parent_fact)
                print(f"DEBUG: Adding parent fact: {parent_fact}")
            else:
                print(f"DEBUG: Parent fact already exists: {parent_fact}")
            
            # Add gender fact for the specific parent
            if "mother" in original_statement.lower():
                parent_gender = "female"
            elif "father" in original_statement.lower():
                parent_gender = "male"
            else:
                parent_gender = "female"  # default
            
            parent_gender_fact = f"{parent_gender}({to_prolog_name(new_parent)})."
            if parent_gender_fact not in old_contents:
                new_facts.append(parent_gender_fact)
                print(f"DEBUG: Adding parent gender fact: {parent_gender_fact}")
            else:
                print(f"DEBUG: Parent gender fact already exists: {parent_gender_fact}")
            
            # Only add shared_parent facts if siblings don't already share a parent
            if not siblings_already_share_parent:
                # Add shared_parent relationship for ALL siblings (including the child)
                # This is because they all need the opposite gender parent
                all_siblings = [child] + other_siblings
                for sibling_name in all_siblings:
                    shared_parent_sibling_fact = f"parent_of(shared_parent, {to_prolog_name(sibling_name)})."
                    if shared_parent_sibling_fact not in old_contents:
                        new_facts.append(shared_parent_sibling_fact)
                        print(f"DEBUG: Adding shared parent fact for {sibling_name}: {shared_parent_sibling_fact}")
                    else:
                        print(f"DEBUG: Shared parent fact already exists for {sibling_name}: {shared_parent_sibling_fact}")
                
                # Add gender fact for shared_parent
                shared_parent_gender_fact = f"{shared_parent_gender}(shared_parent)."
                if shared_parent_gender_fact not in old_contents:
                    new_facts.append(shared_parent_gender_fact)
                    print(f"DEBUG: Adding shared parent gender fact: {shared_parent_gender_fact}")
                else:
                    print(f"DEBUG: Shared parent gender fact already exists: {shared_parent_gender_fact}")
            else:
                print(f"DEBUG: Skipping shared_parent facts - siblings already share a parent")
            
            # Note: We don't add half_sibling_of facts here because the Prolog rules
            # will automatically determine half-sibling relationships based on parent facts.
            # This allows for mixed sibling sets where some are full siblings and others are half-siblings.
            
            print(f"DEBUG: All new facts to add: {new_facts}")
            
            # Write all new facts at once
            if new_facts:
                # Organize the file properly: facts at top, then discontiguous declarations, then rules
                lines = old_contents.split('\n')
                fact_lines = []
                rule_lines = []
                discontiguous_lines = []
                comment_lines = []
                
                # Handle multi-line rules properly
                i = 0
                while i < len(lines):
                    line_stripped = lines[i].strip()
                    
                    if line_stripped.startswith('%'):
                        comment_lines.append(lines[i])
                    elif line_stripped == '':
                        pass
                    elif line_stripped.startswith(':- discontiguous'):
                        discontiguous_lines.append(line_stripped)
                    elif line_stripped.endswith('.') and ':-' not in line_stripped:
                        # This is a fact (ends with . but doesn't contain :-)
                        fact_lines.append(line_stripped)
                    elif ':-' in line_stripped:
                        # This is a rule (contains :-)
                        # Check if it's a multi-line rule
                        rule_text = line_stripped
                        j = i + 1
                        while j < len(lines) and not lines[j].strip().endswith('.'):
                            rule_text += ' ' + lines[j].strip()
                            j += 1
                        if j < len(lines) and lines[j].strip().endswith('.'):
                            rule_text += ' ' + lines[j].strip()
                            i = j  # Skip the lines we've already processed
                        rule_lines.append(rule_text)
                    elif line_stripped.endswith('.'):
                        # Fallback for any other lines ending with .
                        fact_lines.append(line_stripped)
                    
                    i += 1
                
                # Add new facts to existing facts
                fact_lines.extend(new_facts)
                
                # Deduplicate discontiguous declarations
                discontiguous_lines = list(set(discontiguous_lines))
                discontiguous_lines.sort()  # Sort for consistent ordering
                
                # Ensure all necessary discontiguous declarations are present
                required_declarations = [
                    ':- discontiguous parent_of/2.',
                    ':- discontiguous male/1.',
                    ':- discontiguous female/1.',
                    ':- discontiguous sibling_of/2.',
                    ':- discontiguous half_sibling_of/2.',
                    ':- discontiguous brother_of/2.',
                    ':- discontiguous sister_of/2.',
                    ':- discontiguous uncle_of/2.',
                    ':- discontiguous aunt_of/2.',
                    ':- discontiguous niece_of/2.',
                    ':- discontiguous nephew_of/2.',
                    ':- discontiguous cousin_of/2.',
                    ':- discontiguous relative/2.',
                    ':- discontiguous ancestor_of/2.',
                    ':- discontiguous grandparent_of/2.',
                    ':- discontiguous grandchild_of/2.',
                    ':- discontiguous grandmother_of/2.',
                    ':- discontiguous grandfather_of/2.',
                    ':- discontiguous granddaughter_of/2.',
                    ':- discontiguous grandson_of/2.',
                    ':- discontiguous father_of/2.',
                    ':- discontiguous mother_of/2.',
                    ':- discontiguous child_of/2.',
                    ':- discontiguous son_of/2.',
                    ':- discontiguous daughter_of/2.',
                    ':- discontiguous half_brother_of/2.',
                    ':- discontiguous half_sister_of/2.',
                    ':- discontiguous impossible_circular/2.',
                    ':- discontiguous incestual_sibling_parent/2.'
                ]
                
                # Add any missing required declarations
                for decl in required_declarations:
                    if decl not in discontiguous_lines:
                        discontiguous_lines.append(decl)
                
                # Sort again to ensure consistent ordering
                discontiguous_lines.sort()
                
                # Write organized file
                with open(current_kb_file, "w", encoding="utf-8") as f:
                    # Write discontiguous declarations first (at the very top)
                    f.write("% Discontiguous declarations to suppress warnings\n")
                    for decl in discontiguous_lines:
                        f.write(decl + '\n')
                    f.write('\n% Family Relationship Facts\n')
                    for fact in fact_lines:
                        f.write(fact + '\n')
                    f.write('\n% Family Relationship Rules\n\n')
                    for rule in rule_lines:
                        f.write(rule + '\n')
                
                # Add a small delay to ensure file is fully written
                time.sleep(0.1)
            
            # Format response message
            return "OK! I learned something new."
            
        except Exception as e:
            print(f"Error adding parent with shared parent: {e}")
            return f"Error adding relationships: {str(e)}"
    
    def add_parent_for_child_only(self, new_parent: str, child: str) -> str:
        """Add parent relationship for a single child."""
        try:
            # Read current contents
            with open(current_kb_file, "r", encoding="utf-8") as f:
                old_contents = f.read()
            
            # Add parent relationship
            new_fact = f"parent_of({to_prolog_name(new_parent)}, {to_prolog_name(child)})."
            
            # Write new fact using organized method
            return self._write_organized_facts_to_file([new_fact])
            
        except Exception as e:
            print(f"Error adding parent for child only: {e}")
            return f"Error adding relationship: {str(e)}"
    
    def add_half_sibling_relationship(self, person1: str, person2: str) -> str:
        """Add half-sibling relationship."""
        try:
            # Read current contents
            with open(current_kb_file, "r", encoding="utf-8") as f:
                old_contents = f.read()
            
            # Add half-sibling relationship
            new_facts = [
                f"half_sibling_of({to_prolog_name(person1)}, {to_prolog_name(person2)}).",
                f"sibling_of({to_prolog_name(person1)}, {to_prolog_name(person2)})."
            ]
            
            # Write new facts using organized method
            return self._write_organized_facts_to_file(new_facts)
            
        except Exception as e:
            print(f"Error adding half-sibling relationship: {e}")
            return f"Error adding relationship: {str(e)}"
    
    def add_half_brother_relationship(self, person1: str, person2: str) -> str:
        """Add half-brother relationship."""
        try:
            # Read current contents
            with open(current_kb_file, "r", encoding="utf-8") as f:
                old_contents = f.read()
            
            # Add half-brother relationship
            new_facts = [
                f"half_brother_of({to_prolog_name(person1)}, {to_prolog_name(person2)}).",
                f"half_sibling_of({to_prolog_name(person1)}, {to_prolog_name(person2)}).",
                f"sibling_of({to_prolog_name(person1)}, {to_prolog_name(person2)}).",
                f"male({to_prolog_name(person1)})."
            ]
            
            # Write new facts using organized method
            return self._write_organized_facts_to_file(new_facts)
                
        except Exception as e:
            print(f"Error adding half-brother relationship: {e}")
            return f"Error adding relationship: {str(e)}"
    
    def add_half_sister_relationship(self, person1: str, person2: str) -> str:
        """Add half-sister relationship."""
        try:
            # Read current contents
            with open(current_kb_file, "r", encoding="utf-8") as f:
                old_contents = f.read()
            
            # Add half-sister relationship
            new_facts = [
                f"half_sister_of({to_prolog_name(person1)}, {to_prolog_name(person2)}).",
                f"half_sibling_of({to_prolog_name(person1)}, {to_prolog_name(person2)}).",
                f"sibling_of({to_prolog_name(person1)}, {to_prolog_name(person2)}).",
                f"female({to_prolog_name(person1)})."
            ]
            
            # Write new facts using organized method
            return self._write_organized_facts_to_file(new_facts)
            
        except Exception as e:
            print(f"Error adding half-sister relationship: {e}")
            return f"Error adding relationship: {str(e)}"
    

    
    def add_aunt_uncle_father_relationship(self, aunt_uncle: str, parent: str, niece_nephew: str, original_statement: str = "") -> str:
        """Add aunt/uncle relationship where aunt/uncle is sibling of parent's father."""
        try:
            # Read current contents
            with open(current_kb_file, "r", encoding="utf-8") as f:
                old_contents = f.read()
            
            # Find parent's father
            parent_father_results = re.findall(rf'parent_of\(([^,]+),\s*{parent}\)', old_contents)
            parent_father = None
            for father_match in parent_father_results:
                # Check if this father is male
                if re.search(rf'male\({father_match}\)', old_contents):
                    parent_father = father_match
                    break
            
            if not parent_father:
                return f"That's impossible! Could not find {parent.capitalize()}'s father in the knowledge base."
            
            # Add sibling relationship and aunt/uncle relationship
            if "aunt" in original_statement.lower():
                new_facts = [
                    f"sibling_of({to_prolog_name(aunt_uncle)}, {to_prolog_name(parent_father)}).",
                    f"aunt_of({to_prolog_name(aunt_uncle)}, {to_prolog_name(parent)}).",
                    f"female({to_prolog_name(aunt_uncle)})."
                ]
            else:
                new_facts = [
                    f"sibling_of({to_prolog_name(aunt_uncle)}, {to_prolog_name(parent_father)}).",
                    f"uncle_of({to_prolog_name(aunt_uncle)}, {to_prolog_name(parent)}).",
                    f"male({to_prolog_name(aunt_uncle)})."
                ]
            
            # Write new facts at the top
            with open(current_kb_file, "w", encoding="utf-8") as f:
                f.write('\n'.join(new_facts) + '\n' + old_contents)
            
            relationship_type = "aunt" if "aunt" in original_statement.lower() else "uncle"
            return "OK! I learned something new."
            
        except Exception as e:
            print(f"Error adding aunt/uncle father relationship: {e}")
            return f"Error adding relationship: {str(e)}"
    
    def add_aunt_uncle_mother_relationship(self, aunt_uncle: str, parent: str, niece_nephew: str, original_statement: str = "") -> str:
        """Add aunt/uncle relationship where aunt/uncle is sibling of parent's mother."""
        try:
            # Read current contents
            with open(current_kb_file, "r", encoding="utf-8") as f:
                old_contents = f.read()
            
            # Find parent's mother
            parent_mother_results = re.findall(rf'parent_of\(([^,]+),\s*{parent}\)', old_contents)
            parent_mother = None
            for mother_match in parent_mother_results:
                # Check if this mother is female
                if re.search(rf'female\({mother_match}\)', old_contents):
                    parent_mother = mother_match
                    break
            
            if not parent_mother:
                return f"That's impossible! Could not find {parent.capitalize()}'s mother in the knowledge base."
            
            # Add sibling relationship and aunt/uncle relationship
            if "aunt" in original_statement.lower():
                new_facts = [
                    f"sibling_of({to_prolog_name(aunt_uncle)}, {to_prolog_name(parent_mother)}).",
                    f"aunt_of({to_prolog_name(aunt_uncle)}, {to_prolog_name(parent)}).",
                    f"female({to_prolog_name(aunt_uncle)})."
                ]
            else:
                new_facts = [
                    f"sibling_of({to_prolog_name(aunt_uncle)}, {to_prolog_name(parent_mother)}).",
                    f"uncle_of({to_prolog_name(aunt_uncle)}, {to_prolog_name(parent)}).",
                    f"male({to_prolog_name(aunt_uncle)})."
                ]
            
            # Write new facts at the top
            with open(current_kb_file, "w", encoding="utf-8") as f:
                f.write('\n'.join(new_facts) + '\n' + old_contents)
            
            relationship_type = "aunt" if "aunt" in original_statement.lower() else "uncle"
            return "OK! I learned something new."
            
        except Exception as e:
            print(f"Error adding aunt/uncle mother relationship: {e}")
            return f"Error adding relationship: {str(e)}"
    
    def add_aunt_uncle_sophisticated_relationship(self, aunt_uncle: str, niece_nephew: str, parent: str, is_maternal: bool, original_statement: str = "") -> str:
        """Add sophisticated aunt/uncle relationship with maternal/paternal logic."""
        try:
            from pyswip import Prolog
            from utils import safe_prolog_query
            
            # Read current contents
            with open(current_kb_file, "r", encoding="utf-8") as f:
                old_contents = f.read()
            
            # Check if the parent has parents
            prolog = Prolog()
            prolog.consult(current_kb_file)
            
            parent_parents = safe_prolog_query(prolog, f"parent_of(X, {to_prolog_name(parent)})")
            parent_parent_names = [result["X"] for result in parent_parents]
            
            new_facts = []
            
            # If parent has no parents, create shared parents (like sibling process)
            if not parent_parent_names:
                # Create shared parents for aunt/uncle and parent with unique names
                from utils import generate_unique_shared_parent_names
                
                shared_mother_name, shared_mother_gender = generate_unique_shared_parent_names(aunt_uncle, parent, "mother")
                shared_father_name, shared_father_gender = generate_unique_shared_parent_names(aunt_uncle, parent, "father")
                
                shared_mother_fact = f"parent_of({shared_mother_name}, {to_prolog_name(aunt_uncle)})."
                shared_mother_fact2 = f"parent_of({shared_mother_name}, {to_prolog_name(parent)})."
                
                shared_father_fact = f"parent_of({shared_father_name}, {to_prolog_name(aunt_uncle)})."
                shared_father_fact2 = f"parent_of({shared_father_name}, {to_prolog_name(parent)})."
                
                if shared_mother_fact not in old_contents:
                    new_facts.append(shared_mother_fact)
                if shared_mother_fact2 not in old_contents:
                    new_facts.append(shared_mother_fact2)
                if shared_mother_gender not in old_contents:
                    new_facts.append(shared_mother_gender)
                if shared_father_fact not in old_contents:
                    new_facts.append(shared_father_fact)
                if shared_father_fact2 not in old_contents:
                    new_facts.append(shared_father_fact2)
                if shared_father_gender not in old_contents:
                    new_facts.append(shared_father_gender)
                
                # Add sibling relationship between aunt/uncle and parent
                sibling_fact = f"sibling_of({to_prolog_name(aunt_uncle)}, {to_prolog_name(parent)})."
                if sibling_fact not in old_contents:
                    new_facts.append(sibling_fact)
            else:
                # Parent has parents, find the appropriate one based on maternal/paternal
                target_parent = None
                if is_maternal:
                    # Find the mother of the niece/nephew's parent
                    for parent_name in parent_parent_names:
                        if re.search(rf'female\({parent_name}\)', old_contents):
                            target_parent = parent_name
                            break
                else:
                    # Find the father of the niece/nephew's parent
                    for parent_name in parent_parent_names:
                        if re.search(rf'male\({parent_name}\)', old_contents):
                            target_parent = parent_name
                            break
                
                if not target_parent:
                    parent_type = "mother" if is_maternal else "father"
                    return f"That's impossible! Could not find {parent.capitalize()}'s {parent_type} in the knowledge base."
                
                # Add sibling relationship between aunt/uncle and target parent
                sibling_fact = f"sibling_of({to_prolog_name(aunt_uncle)}, {to_prolog_name(target_parent)})."
                if sibling_fact not in old_contents:
                    new_facts.append(sibling_fact)
            
            # Add aunt/uncle relationship
            if "aunt" in original_statement.lower():
                aunt_fact = f"aunt_of({to_prolog_name(aunt_uncle)}, {to_prolog_name(niece_nephew)})."
                gender_fact = f"female({to_prolog_name(aunt_uncle)})."
                if aunt_fact not in old_contents:
                    new_facts.append(aunt_fact)
                if gender_fact not in old_contents:
                    new_facts.append(gender_fact)
            else:
                uncle_fact = f"uncle_of({to_prolog_name(aunt_uncle)}, {to_prolog_name(niece_nephew)})."
                gender_fact = f"male({to_prolog_name(aunt_uncle)})."
                if uncle_fact not in old_contents:
                    new_facts.append(uncle_fact)
                if gender_fact not in old_contents:
                    new_facts.append(gender_fact)
            
            if new_facts:
                # Write new facts using organized method
                return self._write_organized_facts_to_file(new_facts)
            else:
                return "I already knew that."
            
        except Exception as e:
            print(f"Error adding sophisticated aunt/uncle relationship: {e}")
            return f"Error adding relationship: {str(e)}"
    
    def add_aunt_uncle_half_sibling_relationship(self, aunt_uncle: str, niece_nephew: str, parent: str, shared_parent: str, original_statement: str = "") -> str:
        """Add aunt/uncle relationship where aunt/uncle is half-sibling of parent."""
        try:
            # Read current contents
            with open(current_kb_file, "r", encoding="utf-8") as f:
                old_contents = f.read()
            
            # Add half-sibling relationship between aunt/uncle and parent
            new_facts = [f"half_sibling_of({to_prolog_name(aunt_uncle)}, {to_prolog_name(parent)})."]
            
            # Add shared parent relationship
            new_facts.append(f"parent_of({to_prolog_name(shared_parent)}, {to_prolog_name(aunt_uncle)}).")
            new_facts.append(f"parent_of({to_prolog_name(shared_parent)}, {to_prolog_name(parent)}).")
            
            # Add aunt/uncle relationship
            if "aunt" in original_statement.lower():
                new_facts.append(f"aunt_of({to_prolog_name(aunt_uncle)}, {to_prolog_name(niece_nephew)}).")
                new_facts.append(f"female({to_prolog_name(aunt_uncle)}).")
            else:
                new_facts.append(f"uncle_of({to_prolog_name(aunt_uncle)}, {to_prolog_name(niece_nephew)}).")
                new_facts.append(f"male({to_prolog_name(aunt_uncle)}).")
            
            # Write new facts at the top
            with open(current_kb_file, "w", encoding="utf-8") as f:
                f.write('\n'.join(new_facts) + '\n' + old_contents)
            
            return "OK! I learned something new."
            
        except Exception as e:
            print(f"Error adding aunt/uncle half-sibling relationship: {e}")
            return f"Error adding relationship: {str(e)}"
    
    def add_aunt_uncle_half_sibling_with_shared_mother(self, aunt_uncle: str, niece_nephew: str, parent: str, is_maternal: bool, original_statement: str = "") -> str:
        """Add aunt/uncle relationship where aunt/uncle and parent share a mother."""
        try:
            # Read current contents
            with open(current_kb_file, "r", encoding="utf-8") as f:
                old_contents = f.read()
            
            # Add half-sibling relationship between aunt/uncle and parent
            new_facts = [f"half_sibling_of({to_prolog_name(aunt_uncle)}, {to_prolog_name(parent)})."]
            
            # Add shared mother relationship with unique name
            from utils import generate_unique_shared_parent_names
            shared_mother_name, shared_mother_gender = generate_unique_shared_parent_names(aunt_uncle, parent, "mother")
            
            new_facts.append(f"parent_of({shared_mother_name}, {to_prolog_name(aunt_uncle)}).")
            new_facts.append(f"parent_of({shared_mother_name}, {to_prolog_name(parent)}).")
            new_facts.append(shared_mother_gender)
            
            # Add aunt/uncle relationship
            if "aunt" in original_statement.lower():
                new_facts.append(f"aunt_of({to_prolog_name(aunt_uncle)}, {to_prolog_name(niece_nephew)}).")
                new_facts.append(f"female({to_prolog_name(aunt_uncle)}).")
            else:
                new_facts.append(f"uncle_of({to_prolog_name(aunt_uncle)}, {to_prolog_name(niece_nephew)}).")
                new_facts.append(f"male({to_prolog_name(aunt_uncle)}).")
            
            # Write new facts at the top
            with open(current_kb_file, "w", encoding="utf-8") as f:
                f.write('\n'.join(new_facts) + '\n' + old_contents)
            
            return "OK! I learned something new."
            
        except Exception as e:
            print(f"Error adding aunt/uncle half-sibling with shared mother: {e}")
            return f"Error adding relationship: {str(e)}"
    
    def add_aunt_uncle_half_sibling_with_shared_father(self, aunt_uncle: str, niece_nephew: str, parent: str, is_maternal: bool, original_statement: str = "") -> str:
        """Add aunt/uncle relationship where aunt/uncle and parent share a father."""
        try:
            # Read current contents
            with open(current_kb_file, "r", encoding="utf-8") as f:
                old_contents = f.read()
            
            # Add half-sibling relationship between aunt/uncle and parent
            new_facts = [f"half_sibling_of({to_prolog_name(aunt_uncle)}, {to_prolog_name(parent)})."]
            
            # Add shared father relationship with unique name
            from utils import generate_unique_shared_parent_names
            shared_father_name, shared_father_gender = generate_unique_shared_parent_names(aunt_uncle, parent, "father")
            
            new_facts.append(f"parent_of({shared_father_name}, {to_prolog_name(aunt_uncle)}).")
            new_facts.append(f"parent_of({shared_father_name}, {to_prolog_name(parent)}).")
            new_facts.append(shared_father_gender)
            
            # Add aunt/uncle relationship
            if "aunt" in original_statement.lower():
                new_facts.append(f"aunt_of({to_prolog_name(aunt_uncle)}, {to_prolog_name(niece_nephew)}).")
                new_facts.append(f"female({to_prolog_name(aunt_uncle)}).")
            else:
                new_facts.append(f"uncle_of({to_prolog_name(aunt_uncle)}, {to_prolog_name(niece_nephew)}).")
                new_facts.append(f"male({to_prolog_name(aunt_uncle)}).")
            
            # Write new facts at the top
            with open(current_kb_file, "w", encoding="utf-8") as f:
                f.write('\n'.join(new_facts) + '\n' + old_contents)
            
            return "OK! I learned something new."
            
        except Exception as e:
            print(f"Error adding aunt/uncle half-sibling with shared father: {e}")
            return f"Error adding relationship: {str(e)}"
    
    def add_shared_mother_relationship(self, mother: str, person1: str, person2: str) -> str:
        """Add shared mother relationship for siblings."""
        try:
            # Read current contents
            with open(current_kb_file, "r", encoding="utf-8") as f:
                old_contents = f.read()
            
            # Add parent relationships and gender
            mother_person1_fact = f"parent_of({to_prolog_name(mother)}, {to_prolog_name(person1)})."
            mother_person2_fact = f"parent_of({to_prolog_name(mother)}, {to_prolog_name(person2)})."
            mother_gender_fact = f"female({to_prolog_name(mother)})."
            
            new_facts = []
            if mother_person1_fact not in old_contents:
                new_facts.append(mother_person1_fact)
            if mother_person2_fact not in old_contents:
                new_facts.append(mother_person2_fact)
            if mother_gender_fact not in old_contents:
                new_facts.append(mother_gender_fact)
            
            if new_facts:
                # Write new facts using organized method
                return self._write_organized_facts_to_file(new_facts)
            else:
                return "I already knew that."
                
        except Exception as e:
            print(f"Error adding shared mother relationship: {e}")
            return f"Error adding relationship: {str(e)}"
    
    def add_full_sibling_relationship(self, person1: str, person2: str, original_statement: str = "") -> str:
        """Add full sibling relationship with shared parents."""
        try:
            from pyswip import Prolog
            from utils import safe_prolog_query
            
            # Read current contents
            with open(current_kb_file, "r", encoding="utf-8") as f:
                old_contents = f.read()
            
            # Add sibling relationship
            sibling_fact = f"sibling_of({to_prolog_name(person1)}, {to_prolog_name(person2)})."
            
            # Check for existing parents of both persons
            prolog = Prolog()
            prolog.consult(current_kb_file)
            
            # Get existing parents for both persons
            person1_parents = safe_prolog_query(prolog, f"parent_of(X, {to_prolog_name(person1)})")
            person2_parents = safe_prolog_query(prolog, f"parent_of(X, {to_prolog_name(person2)})")
            
            person1_parent_names = [result["X"] for result in person1_parents]
            person2_parent_names = [result["X"] for result in person2_parents]
            
            new_facts = []
            if sibling_fact not in old_contents:
                new_facts.append(sibling_fact)
            
            # Add gender facts from the original statement if it was a brother/sister statement
            if original_statement:
                if "brother" in original_statement.lower():
                    gender_fact = f"male({to_prolog_name(person1)})."
                    if gender_fact not in old_contents:
                        new_facts.append(gender_fact)
                elif "sister" in original_statement.lower():
                    gender_fact = f"female({to_prolog_name(person1)})."
                    if gender_fact not in old_contents:
                        new_facts.append(gender_fact)
            
            # Check if person1 has existing parents that should be shared
            for parent_name in person1_parent_names:
                if parent_name not in person2_parent_names:
                    # This parent exists for person1 but not person2, so add it to person2
                    parent_fact = f"parent_of({parent_name}, {to_prolog_name(person2)})."
                    if parent_fact not in old_contents:
                        new_facts.append(parent_fact)
            
            # Check if person2 has existing parents that should be shared
            for parent_name in person2_parent_names:
                if parent_name not in person1_parent_names:
                    # This parent exists for person2 but not person1, so add it to person1
                    parent_fact = f"parent_of({parent_name}, {to_prolog_name(person1)})."
                    if parent_fact not in old_contents:
                        new_facts.append(parent_fact)
            
            # If no existing parents were found, create placeholder parents
            if not person1_parent_names and not person2_parent_names:
                # Add shared parents with unique names
                from utils import generate_unique_shared_parent_names
                
                shared_mother_name, shared_mother_gender = generate_unique_shared_parent_names(person1, person2, "mother")
                shared_father_name, shared_father_gender = generate_unique_shared_parent_names(person1, person2, "father")
                
                shared_mother_fact = f"parent_of({shared_mother_name}, {to_prolog_name(person1)})."
                shared_mother_fact2 = f"parent_of({shared_mother_name}, {to_prolog_name(person2)})."
                
                shared_father_fact = f"parent_of({shared_father_name}, {to_prolog_name(person1)})."
                shared_father_fact2 = f"parent_of({shared_father_name}, {to_prolog_name(person2)})."
                
                if shared_mother_fact not in old_contents:
                    new_facts.append(shared_mother_fact)
                if shared_mother_fact2 not in old_contents:
                    new_facts.append(shared_mother_fact2)
                if shared_mother_gender not in old_contents:
                    new_facts.append(shared_mother_gender)
                if shared_father_fact not in old_contents:
                    new_facts.append(shared_father_fact)
                if shared_father_fact2 not in old_contents:
                    new_facts.append(shared_father_fact2)
                if shared_father_gender not in old_contents:
                    new_facts.append(shared_father_gender)
            
            if new_facts:
                # Write new facts using organized method
                return self._write_organized_facts_to_file(new_facts)
            else:
                return "I already knew that."
                
        except Exception as e:
            print(f"Error adding full sibling relationship: {e}")
            return f"Error adding relationship: {str(e)}"
    
    def add_half_sibling_relationship_only(self, person1: str, person2: str) -> str:
        """Add half-sibling relationship without shared parents."""
        try:
            # Read current contents
            with open(current_kb_file, "r", encoding="utf-8") as f:
                old_contents = f.read()
            
            # Add sibling relationship
            sibling_fact = f"sibling_of({to_prolog_name(person1)}, {to_prolog_name(person2)})."
            
            # Add half-sibling relationship
            half_sibling_fact = f"half_sibling_of({to_prolog_name(person1)}, {to_prolog_name(person2)})."
            
            new_facts = []
            if sibling_fact not in old_contents:
                new_facts.append(sibling_fact)
            if half_sibling_fact not in old_contents:
                new_facts.append(half_sibling_fact)
            
            if new_facts:
                # Write new facts using organized method
                return self._write_organized_facts_to_file(new_facts)
            else:
                return "I already knew that."
                
        except Exception as e:
            print(f"Error adding half-sibling relationship: {e}")
            return f"Error adding relationship: {str(e)}"
    
    def add_half_sibling_with_shared_mother(self, person1: str, person2: str, original_statement: str = "") -> str:
        """Add half-sibling relationship where they share a mother."""
        try:
            from pyswip import Prolog
            from utils import safe_prolog_query
            
            # Read current contents
            with open(current_kb_file, "r", encoding="utf-8") as f:
                old_contents = f.read()
            
            # Add half-sibling relationship (not regular sibling relationship)
            half_sibling_fact = f"half_sibling_of({to_prolog_name(person1)}, {to_prolog_name(person2)})."
            
            new_facts = []
            if half_sibling_fact not in old_contents:
                new_facts.append(half_sibling_fact)
            
            # Add gender facts from the original statement if it was a brother/sister statement
            if original_statement:
                if "brother" in original_statement.lower():
                    gender_fact = f"male({to_prolog_name(person1)})."
                    if gender_fact not in old_contents:
                        new_facts.append(gender_fact)
                elif "sister" in original_statement.lower():
                    gender_fact = f"female({to_prolog_name(person1)})."
                    if gender_fact not in old_contents:
                        new_facts.append(gender_fact)
            
            # Check for existing mothers of both persons
            prolog = Prolog()
            prolog.consult(current_kb_file)
            
            person1_mothers = safe_prolog_query(prolog, f"mother_of(X, {to_prolog_name(person1)})")
            person2_mothers = safe_prolog_query(prolog, f"mother_of(X, {to_prolog_name(person2)})")
            
            person1_mother_names = [result["X"] for result in person1_mothers]
            person2_mother_names = [result["X"] for result in person2_mothers]
            
            # If person1 has a mother that person2 doesn't have, add it to person2
            for mother_name in person1_mother_names:
                if mother_name not in person2_mother_names:
                    mother_fact = f"parent_of({mother_name}, {to_prolog_name(person2)})."
                    if mother_fact not in old_contents:
                        new_facts.append(mother_fact)
            
            # If person2 has a mother that person1 doesn't have, add it to person1
            for mother_name in person2_mother_names:
                if mother_name not in person1_mother_names:
                    mother_fact = f"parent_of({mother_name}, {to_prolog_name(person1)})."
                    if mother_fact not in old_contents:
                        new_facts.append(mother_fact)
            
            # If no existing mothers found, create a shared mother with unique name
            if not person1_mother_names and not person2_mother_names:
                from utils import generate_unique_shared_parent_names
                shared_mother_name, shared_mother_gender = generate_unique_shared_parent_names(person1, person2, "mother")
                
                shared_mother_fact1 = f"parent_of({shared_mother_name}, {to_prolog_name(person1)})."
                shared_mother_fact2 = f"parent_of({shared_mother_name}, {to_prolog_name(person2)})."
                
                if shared_mother_fact1 not in old_contents:
                    new_facts.append(shared_mother_fact1)
                if shared_mother_fact2 not in old_contents:
                    new_facts.append(shared_mother_fact2)
                if shared_mother_gender not in old_contents:
                    new_facts.append(shared_mother_gender)
            
            # Check for other children with the same mother and add half-sibling relationships
            if person1_mother_names or person2_mother_names:
                all_mothers = set(person1_mother_names + person2_mother_names)
                for mother in all_mothers:
                    # Find all children of this mother
                    children = safe_prolog_query(prolog, f"child_of(X, {mother})")
                    if children:
                        child_names = [result["X"] for result in children]
                        # Add half-sibling relationships between all children
                        for i, child1 in enumerate(child_names):
                            for child2 in child_names[i+1:]:
                                if child1 != child2:
                                    half_sib_fact = f"half_sibling_of({child1}, {child2})."
                                    if half_sib_fact not in old_contents:
                                        new_facts.append(half_sib_fact)
            
            if new_facts:
                return self._write_organized_facts_to_file(new_facts)
            else:
                return "I already knew that."
                
        except Exception as e:
            print(f"Error adding half-sibling with shared mother: {e}")
            return f"Error adding relationship: {str(e)}"
    
    def add_half_sibling_with_shared_father(self, person1: str, person2: str, original_statement: str = "") -> str:
        """Add half-sibling relationship where they share a father."""
        try:
            from pyswip import Prolog
            from utils import safe_prolog_query
            
            # Read current contents
            with open(current_kb_file, "r", encoding="utf-8") as f:
                old_contents = f.read()
            
            # Add half-sibling relationship (not regular sibling relationship)
            half_sibling_fact = f"half_sibling_of({to_prolog_name(person1)}, {to_prolog_name(person2)})."
            
            new_facts = []
            if half_sibling_fact not in old_contents:
                new_facts.append(half_sibling_fact)
            
            # Add gender facts from the original statement if it was a brother/sister statement
            if original_statement:
                if "brother" in original_statement.lower():
                    gender_fact = f"male({to_prolog_name(person1)})."
                    if gender_fact not in old_contents:
                        new_facts.append(gender_fact)
                elif "sister" in original_statement.lower():
                    gender_fact = f"female({to_prolog_name(person1)})."
                    if gender_fact not in old_contents:
                        new_facts.append(gender_fact)
            
            # Check for existing fathers of both persons
            prolog = Prolog()
            prolog.consult(current_kb_file)
            
            person1_fathers = safe_prolog_query(prolog, f"father_of(X, {to_prolog_name(person1)})")
            person2_fathers = safe_prolog_query(prolog, f"father_of(X, {to_prolog_name(person2)})")
            
            person1_father_names = [result["X"] for result in person1_fathers]
            person2_father_names = [result["X"] for result in person2_fathers]
            
            # If person1 has a father that person2 doesn't have, add it to person2
            for father_name in person1_father_names:
                if father_name not in person2_father_names:
                    father_fact = f"parent_of({father_name}, {to_prolog_name(person2)})."
                    if father_fact not in old_contents:
                        new_facts.append(father_fact)
            
            # If person2 has a father that person1 doesn't have, add it to person1
            for father_name in person2_father_names:
                if father_name not in person1_father_names:
                    father_fact = f"parent_of({father_name}, {to_prolog_name(person1)})."
                    if father_fact not in old_contents:
                        new_facts.append(father_fact)
            
            # If no existing fathers found, create a shared father with unique name
            if not person1_father_names and not person2_father_names:
                from utils import generate_unique_shared_parent_names
                shared_father_name, shared_father_gender = generate_unique_shared_parent_names(person1, person2, "father")
                
                shared_father_fact1 = f"parent_of({shared_father_name}, {to_prolog_name(person1)})."
                shared_father_fact2 = f"parent_of({shared_father_name}, {to_prolog_name(person2)})."
                
                if shared_father_fact1 not in old_contents:
                    new_facts.append(shared_father_fact1)
                if shared_father_fact2 not in old_contents:
                    new_facts.append(shared_father_fact2)
                if shared_father_gender not in old_contents:
                    new_facts.append(shared_father_gender)
            
            # Check for other children with the same father and add half-sibling relationships
            if person1_father_names or person2_father_names:
                all_fathers = set(person1_father_names + person2_father_names)
                for father in all_fathers:
                    # Find all children of this father
                    children = safe_prolog_query(prolog, f"child_of(X, {father})")
                    if children:
                        child_names = [result["X"] for result in children]
                        # Add half-sibling relationships between all children
                        for i, child1 in enumerate(child_names):
                            for child2 in child_names[i+1:]:
                                if child1 != child2:
                                    half_sib_fact = f"half_sibling_of({child1}, {child2})."
                                    if half_sib_fact not in old_contents:
                                        new_facts.append(half_sib_fact)
            
            if new_facts:
                return self._write_organized_facts_to_file(new_facts)
            else:
                return "I already knew that."
                
        except Exception as e:
            print(f"Error adding half-sibling with shared father: {e}")
            return f"Error adding relationship: {str(e)}"
    
    def add_sibling_with_existing_siblings(self, new_person: str, existing_person: str, is_full_sibling: bool) -> str:
        """Add a new sibling to an existing sibling group."""
        try:
            # Read current contents
            with open(current_kb_file, "r", encoding="utf-8") as f:
                old_contents = f.read()
            
            # Add sibling relationship between new person and existing person
            sibling_fact = f"sibling_of({to_prolog_name(new_person)}, {to_prolog_name(existing_person)})."
            
            new_facts = []
            if sibling_fact not in old_contents:
                new_facts.append(sibling_fact)
            
            if is_full_sibling:
                # Add shared parents for full sibling
                shared_mother_fact = f"parent_of(shared_mother, {to_prolog_name(new_person)})."
                shared_father_fact = f"parent_of(shared_father, {to_prolog_name(new_person)})."
                
                if shared_mother_fact not in old_contents:
                    new_facts.append(shared_mother_fact)
                if shared_father_fact not in old_contents:
                    new_facts.append(shared_father_fact)
                
                # Find all existing siblings and add sibling relationships
                try:
                    prolog = Prolog()
                    prolog.consult(current_kb_file)
                    
                    # Find all siblings of existing person
                    siblings = safe_prolog_query(prolog, f"sibling_of({existing_person}, X)")
                    if siblings:
                        for sib in siblings:
                            if sib["X"] != new_person:
                                sib_fact = f"sibling_of({to_prolog_name(new_person)}, {to_prolog_name(sib['X'])})."
                                if sib_fact not in old_contents:
                                    new_facts.append(sib_fact)
                except Exception as e:
                    print(f"Error finding existing siblings: {e}")
            else:
                # Add half-sibling relationship
                half_sibling_fact = f"half_sibling_of({to_prolog_name(new_person)}, {to_prolog_name(existing_person)})."
                if half_sibling_fact not in old_contents:
                    new_facts.append(half_sibling_fact)
            
            if new_facts:
                # Write new facts at the top
                with open(current_kb_file, "w", encoding="utf-8") as f:
                    f.write('\n'.join(new_facts) + '\n' + old_contents)
                
                sibling_type = "full sibling" if is_full_sibling else "half-sibling"
                return "OK! I learned something new."
            else:
                return "I already knew that."
                
        except Exception as e:
            print(f"Error adding sibling with existing siblings: {e}")
            return f"Error adding relationship: {str(e)}" 