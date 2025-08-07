import re
from typing import Dict, Any
from fact_manager import FactManager

class ClarificationHandler:
    def __init__(self):
        self.fact_manager = FactManager()
    
    def handle_response(self, response: str, clarification_context: Dict[str, Any]) -> str:
        """Handle clarification responses from the user."""
        response = response.lower().strip()
        
        print(f"DEBUG: handle_response called with response='{response}'")
        print(f"DEBUG: clarification_context={clarification_context}")
        
        # Check for grandparent clarification first (most specific)
        if "grandparent" in clarification_context:
            return self._handle_grandparent_response(response, clarification_context)
        # Check for sophisticated aunt/uncle clarification
        elif clarification_context.get("clarification_type") == "aunt_uncle_sophisticated":
            return self._handle_aunt_uncle_sophisticated_response(response, clarification_context)
        # Check for aunt/uncle sibling clarification
        elif clarification_context.get("clarification_type") == "aunt_uncle_sibling":
            return self._handle_aunt_uncle_sibling_response(response, clarification_context)
        # Check for aunt/uncle half-sibling shared parent clarification
        elif clarification_context.get("clarification_type") == "aunt_uncle_half_sibling_shared_parent":
            return self._handle_aunt_uncle_half_sibling_shared_parent_response(response, clarification_context)
        # Check for full sibling clarification
        elif clarification_context.get("clarification_type") == "full_sibling":
            return self._handle_full_sibling_response(response, clarification_context)
        # Check for half-sibling shared parent clarification
        elif clarification_context.get("clarification_type") == "half_sibling_shared_parent":
            return self._handle_half_sibling_shared_parent_response(response, clarification_context)
        # Check for sibling parent clarifications (more specific)
        elif response == "yes" and clarification_context.get("siblings") and "," in clarification_context.get("siblings", ""):
            print(f"DEBUG: Calling _handle_sibling_parent_yes_response")
            return self._handle_sibling_parent_yes_response(clarification_context)
        elif response == "no" and clarification_context.get("siblings") and "," in clarification_context.get("siblings", ""):
            print(f"DEBUG: Calling _handle_sibling_parent_no_response")
            return self._handle_sibling_parent_no_response(clarification_context)
        elif response == "yes":
            return self._handle_yes_response(clarification_context)
        elif response == "no":
            return self._handle_no_response(clarification_context)


        elif response in ["father", "mother"]:
            return self._handle_aunt_uncle_response(response, clarification_context)
        elif response in ["half-sibling", "half-brother", "half-sister"]:
            return self._handle_sibling_response(response, clarification_context)
        elif response == "none":
            return self._handle_sibling_none_response(clarification_context)
        else:
            # Check if this is a name (for sibling parent clarification)
            if clarification_context.get("siblings") == "sibling_clarification":
                return self._handle_sibling_parent_response(response, clarification_context)
            else:
                return "Please respond with 'yes' or 'no'."
    
    def _handle_yes_response(self, context: Dict[str, Any]) -> str:
        """Handle 'yes' responses for parent clarifications."""
        new_parent = context["new_parent"]
        child = context["child"]
        siblings = context["siblings"]
        
        if siblings == "update_shared_parent":
            return self.fact_manager.update_shared_parent_relationships(new_parent, child)
        elif siblings and siblings != "sibling_clarification":
            return self.fact_manager.add_parent_for_all_siblings(new_parent, child, siblings)
        else:
            return self.fact_manager.add_parent_for_child_only(new_parent, child)
    
    def _handle_no_response(self, context: Dict[str, Any]) -> str:
        """Handle 'no' responses for parent clarifications."""
        new_parent = context["new_parent"]
        child = context["child"]
        siblings = context["siblings"]
        
        if siblings and siblings != "sibling_clarification":
            return self.fact_manager.add_parent_for_child_only(new_parent, child)
        else:
            return self.fact_manager.add_parent_for_child_only(new_parent, child)
    

    
    def _handle_aunt_uncle_response(self, response: str, context: Dict[str, Any]) -> str:
        """Handle aunt/uncle clarification responses."""
        aunt_uncle = context["new_parent"]
        niece_nephew = context["child"]
        parent = context["siblings"]
        original_statement = context.get("original_statement", "")
        
        if response == "father":
            return self.fact_manager.add_aunt_uncle_father_relationship(aunt_uncle, parent, niece_nephew, original_statement)
        elif response == "mother":
            return self.fact_manager.add_aunt_uncle_mother_relationship(aunt_uncle, parent, niece_nephew, original_statement)
        else:
            return f"That's impossible! Invalid response '{response}' for aunt/uncle clarification."
    
    def _handle_aunt_uncle_sophisticated_response(self, response: str, context: Dict[str, Any]) -> str:
        """Handle sophisticated aunt/uncle clarification responses."""
        aunt_uncle = context["aunt_uncle"]
        niece_nephew = context["niece_nephew"]
        parent = context["parent"]
        original_statement = context.get("original_statement", "")
        
        # Store the maternal/paternal response for later use
        is_maternal = (response == "yes")
        
        # Determine the correct parent to ask about based on maternal/paternal
        from pyswip import Prolog
        from utils import safe_prolog_query
        from fact_manager import current_kb_file
        
        prolog = Prolog()
        prolog.consult(current_kb_file)
        
        # Find the correct parent based on maternal/paternal
        if is_maternal:
            # For maternal aunt/uncle, find the mother of the niece/nephew
            mother_results = safe_prolog_query(prolog, f"mother_of(X, {niece_nephew})")
            if mother_results:
                target_parent = mother_results[0]["X"]
            else:
                # Fallback to the original parent if mother not found
                target_parent = parent
        else:
            # For paternal aunt/uncle, find the father of the niece/nephew
            father_results = safe_prolog_query(prolog, f"father_of(X, {niece_nephew})")
            if father_results:
                target_parent = father_results[0]["X"]
            else:
                # Fallback to the original parent if father not found
                target_parent = parent
        
        # Update context for the next clarification
        context.update({
            "aunt_uncle": aunt_uncle,
            "niece_nephew": niece_nephew,
            "parent": target_parent,  # Use the correct parent
            "is_maternal": is_maternal,
            "original_statement": original_statement,
            "clarification_type": "aunt_uncle_sibling"
        })
        
        # Ask if they are full siblings
        return f"Clarification needed: Are {aunt_uncle.capitalize()} and {target_parent.capitalize()} full siblings? Answer with exactly 'yes' or 'no'."
    
    def _handle_aunt_uncle_sibling_response(self, response: str, context: Dict[str, Any]) -> str:
        """Handle aunt/uncle sibling clarification responses."""
        aunt_uncle = context["aunt_uncle"]
        niece_nephew = context["niece_nephew"]
        parent = context["parent"]
        is_maternal = context["is_maternal"]
        original_statement = context.get("original_statement", "")
        
        if response == "yes":
            # Full siblings - add sophisticated aunt/uncle relationship
            return self.fact_manager.add_aunt_uncle_sophisticated_relationship(
                aunt_uncle, niece_nephew, parent, is_maternal, original_statement
            )
        elif response == "no":
            # Half siblings - ask which parent they share (same as sibling logic)
            context["clarification_type"] = "aunt_uncle_half_sibling_shared_parent"
            context["aunt_uncle"] = aunt_uncle
            context["parent"] = parent
            context["niece_nephew"] = niece_nephew
            context["is_maternal"] = is_maternal
            context["original_statement"] = original_statement
            return f"Do {aunt_uncle.capitalize()} and {parent.capitalize()} share a mother? Answer with exactly 'yes' or 'no' (without the apostrophes)."
        else:
            return f"That's impossible! Invalid response '{response}' for aunt/uncle sibling clarification."
    
    def _handle_aunt_uncle_shared_parent_response(self, response: str, context: Dict[str, Any]) -> str:
        """Handle aunt/uncle shared parent clarification responses."""
        aunt_uncle = context["aunt_uncle"]
        niece_nephew = context["niece_nephew"]
        parent = context["parent"]
        original_statement = context.get("original_statement", "")
        
        # Add half-sibling aunt/uncle relationship with shared parent
        return self.fact_manager.add_aunt_uncle_half_sibling_relationship(
            aunt_uncle, niece_nephew, parent, response, original_statement
        )
    
    def _handle_aunt_uncle_half_sibling_shared_parent_response(self, response: str, context: Dict[str, Any]) -> str:
        """Handle aunt/uncle half-sibling shared parent clarification responses."""
        aunt_uncle = context["aunt_uncle"]
        niece_nephew = context["niece_nephew"]
        parent = context["parent"]
        is_maternal = context["is_maternal"]
        original_statement = context.get("original_statement", "")
        
        if response == "yes":
            # They share a mother, so the father is the different parent
            return self.fact_manager.add_aunt_uncle_half_sibling_with_shared_mother(
                aunt_uncle, niece_nephew, parent, is_maternal, original_statement
            )
        elif response == "no":
            # They share a father, so the mother is the different parent
            return self.fact_manager.add_aunt_uncle_half_sibling_with_shared_father(
                aunt_uncle, niece_nephew, parent, is_maternal, original_statement
            )
        else:
            return "Please respond with exactly 'yes' or 'no' (without the apostrophes)."
    
    def _handle_full_sibling_response(self, response: str, context: Dict[str, Any]) -> str:
        """Handle full sibling clarification responses."""
        person1 = context["person1"]
        person2 = context["person2"]
        original_statement = context.get("original_statement", "")
        
        if response == "yes":
            return self.fact_manager.add_full_sibling_relationship(person1, person2, original_statement)
        elif response == "no":
            # For half-siblings, ask which parent they share
            context["clarification_type"] = "half_sibling_shared_parent"
            context["person1"] = person1
            context["person2"] = person2
            return f"Do {person1.capitalize()} and {person2.capitalize()} share a mother? Answer with exactly 'yes' or 'no' (without the apostrophes)."
        else:
            return "Please respond with exactly 'yes' or 'no' (without the apostrophes)."
    
    def _handle_half_sibling_shared_parent_response(self, response: str, context: Dict[str, Any]) -> str:
        """Handle half-sibling shared parent clarification responses."""
        person1 = context["person1"]
        person2 = context["person2"]
        original_statement = context.get("original_statement", "")
        
        if response == "yes":
            # They share a mother, so the father is the different parent
            return self.fact_manager.add_half_sibling_with_shared_mother(person1, person2, original_statement)
        elif response == "no":
            # They share a father, so the mother is the different parent
            return self.fact_manager.add_half_sibling_with_shared_father(person1, person2, original_statement)
        else:
            return "Please respond with exactly 'yes' or 'no' (without the apostrophes)."
    
    def _handle_sibling_response(self, response: str, context: Dict[str, Any]) -> str:
        """Handle sibling clarification responses."""
        person1 = context["new_parent"]
        person2 = context["child"]
        original_statement = context.get("original_statement", "")
        
        if response == "half-sibling":
            return self.fact_manager.add_half_sibling_relationship(person1, person2)
        elif response == "half-brother":
            return self.fact_manager.add_half_brother_relationship(person1, person2)
        elif response == "half-sister":
            return self.fact_manager.add_half_sister_relationship(person1, person2)
        else:
            return f"That's impossible! Invalid response '{response}' for sibling clarification."
    
    def _handle_sibling_parent_response(self, parent_name: str, context: Dict[str, Any]) -> str:
        """Handle sibling parent clarification responses."""
        person1 = context["person1"]
        person2 = context["person2"]
        
        # Add the shared mother relationship
        result = self.fact_manager.add_shared_mother_relationship(parent_name, person1, person2)
        
        # Ask for the father
        context["shared_mother"] = parent_name
        context["siblings"] = "sibling_father_clarification"
        
        return f"{result}\n\nNow, who is the father of both {person1.capitalize()} and {person2.capitalize()}? (If they have different fathers, say 'none')"
    
    def _handle_sibling_none_response(self, context: Dict[str, Any]) -> str:
        """Handle 'none' response for sibling parent clarification."""
        person1 = context["person1"]
        person2 = context["person2"]
        
        return f"I understand that {person1.capitalize()} and {person2.capitalize()} don't share a mother. This means they are not full siblings. Would you like to specify them as half-siblings instead?"
    
    def _handle_sibling_parent_yes_response(self, context: Dict[str, Any]) -> str:
        """Handle 'yes' response for sibling parent clarification."""
        new_parent = context["new_parent"]
        child = context["child"]
        siblings = context["siblings"]
        original_statement = context.get("original_statement", "")
        
        # Get the siblings that were mentioned in the clarification (the ones that need the parent)
        # The clarification context should have the specific siblings that need the parent
        siblings_needing_parent = context.get("siblings_needing_parent", siblings)
        
        # Parse the siblings that need the parent
        sibling_names = [s.strip() for s in siblings_needing_parent.split(',')]
        # Remove the child from the sibling list to avoid duplicates
        unique_siblings = [s for s in sibling_names if s != child]
        # Create list with child first, then unique siblings that need the parent
        children_needing_parent = f"{child},{','.join(unique_siblings)}"
        print(f"DEBUG: _handle_sibling_parent_yes_response - children_needing_parent={children_needing_parent}")
        return self.fact_manager.add_parent_for_all_siblings(new_parent, child, children_needing_parent, original_statement)
    

    
    def _handle_grandparent_response(self, response: str, context: Dict[str, Any]) -> str:
        """Handle grandparent clarification responses."""
        grandparent = context["grandparent"]
        grandchild = context["grandchild"]
        grandparent_gender = context["grandparent_gender"]
        original_statement = context.get("original_statement", "")
        
        # Determine grandparent type based on response
        if grandparent_gender == "female":
            if response == "yes":
                grandparent_type = "maternal"
            elif response == "no":
                grandparent_type = "paternal"
            else:
                return "Please answer with exactly 'yes' or 'no'."
        elif grandparent_gender == "male":
            if response == "yes":
                grandparent_type = "paternal"
            elif response == "no":
                grandparent_type = "maternal"
            else:
                return "Please answer with exactly 'yes' or 'no'."
        else:
            if response == "maternal":
                grandparent_type = "maternal"
            elif response == "paternal":
                grandparent_type = "paternal"
            else:
                return "Please answer with exactly 'maternal' or 'paternal'."
        
        # Use the FactManager method instead of duplicating logic
        return self.fact_manager.add_grandparent_relationship(grandparent, grandchild, grandparent_gender, grandparent_type, original_statement)
    
    def _handle_sibling_parent_no_response(self, context: Dict[str, Any]) -> str:
        """Handle 'no' response for sibling parent clarification."""
        new_parent = context["new_parent"]
        child = context["child"]
        siblings = context["siblings"]
        original_statement = context.get("original_statement", "")
        
        # Pass the full siblings string to handle ALL siblings
        print(f"DEBUG: _handle_sibling_parent_no_response - calling add_parent_with_shared_parent with siblings={siblings}")
        return self.fact_manager.add_parent_with_shared_parent(new_parent, child, siblings, original_statement) 