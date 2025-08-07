import re
from typing import List, Tuple
from pyswip import Prolog
from utils import to_prolog_name, validate_prolog_file, safe_prolog_query

# Global variable for current knowledge base file
current_kb_file = "relationships.pl"

class QueryHandler:
    def __init__(self):
        pass
    
    def handle_question(self, question: str, question_patterns: List[Tuple]) -> str:
        """Handle questions and queries to the knowledge base."""
        # Parse the question into a Prolog query
        query = self._parse_question_to_query(question, question_patterns)
        if not query:
            return f"Unrecognized question: {question}"
        
        # Execute the query
        return self._execute_query(query, question)
    
    def _parse_question_to_query(self, question: str, question_patterns: List[Tuple]) -> str:
        """Parse a question into a Prolog query."""
        for _, pattern, func in question_patterns:
            match = re.fullmatch(pattern, question.strip())
            if match:
                # Determine which groups contain person names based on the pattern
                if "Are" in pattern and "and" in pattern and "siblings" in pattern:
                    # For "Are X and Y siblings?" pattern, groups 1 and 2 are person names
                    person_name_groups = [1, 2]
                elif "Are" in pattern and "and" in pattern and "parents" in pattern:
                    # For "Are X and Y the parents of Z?" pattern, groups 1, 2, and 3 are person names
                    person_name_groups = [1, 2, 3]
                elif "Is" in pattern and "the" in pattern and "of" in pattern:
                    # For "Is X the Y of Z?" pattern, groups 1 and 3 are person names
                    person_name_groups = [1, 3]
                elif "Is" in pattern and "a" in pattern and "of" in pattern:
                    # For "Is X a Y of Z?" pattern, groups 1 and 3 are person names
                    person_name_groups = [1, 3]
                elif "Who" in pattern:
                    # For "Who are the X of Y?" pattern, only group 1 is a person name
                    person_name_groups = [1]
                else:
                    # For simple patterns, groups 1 and 2 are person names
                    person_name_groups = [1, 2]
                
                for i in person_name_groups:
                    if i <= len(match.groups()):
                        name = match.group(i)
                        from utils import validate_name
                        is_valid_name, name_error = validate_name(name)
                        if not is_valid_name:
                            return name_error
                
                return func(match)
        
        return ""
    
    def _execute_query(self, query: str, original_question: str) -> str:
        """Execute a Prolog query and return the result."""
        try:
            # Validate the Prolog file before querying
            if not validate_prolog_file(current_kb_file):
                return f"That's impossible! The knowledge base file is invalid or corrupted."
            
            prolog = Prolog()
            prolog.consult(current_kb_file)
            
            # Special handling for sibling queries to determine if they are full or half siblings
            if "sibling_of(" in query and "Are" in original_question and "siblings" in original_question:
                return self._handle_sibling_query(prolog, query, original_question)
            
            # Special handling for brother/sister relationship checks
            if query.startswith("check_brother_sister_relationship:"):
                return self._handle_brother_sister_relationship_check(prolog, query, original_question)
            
            # Special handling for relative queries to enable inference
            if "relative(" in query:
                return self._handle_relative_query(prolog, query, original_question)
            
            # Execute the query
            results = safe_prolog_query(prolog, query)
            
            if results:
                # Handle different types of queries
                if "X" in query:  # For questions that ask for specific names
                    xs = set(str(r["X"]) for r in results if "X" in r)
                    if xs:
                        # Format response based on question type
                        if "siblings" in original_question.lower():
                            return f"The siblings of {self._extract_person_name_from_query(query).capitalize()} are {', '.join(xs)}."
                        elif "mother" in original_question.lower():
                            return f"The mother of {self._extract_person_name_from_query(query).capitalize()} is {', '.join(xs)}."
                        elif "father" in original_question.lower():
                            return f"The father of {self._extract_person_name_from_query(query).capitalize()} is {', '.join(xs)}."
                        elif "children" in original_question.lower():
                            return f"The children of {self._extract_person_name_from_query(query).capitalize()} are {', '.join(xs)}."
                        elif "nieces" in original_question.lower():
                            return f"The nieces of {self._extract_person_name_from_query(query).capitalize()} are {', '.join(xs)}."
                        elif "nephews" in original_question.lower():
                            return f"The nephews of {self._extract_person_name_from_query(query).capitalize()} are {', '.join(xs)}."
                        elif "cousins" in original_question.lower():
                            return f"The cousins of {self._extract_person_name_from_query(query).capitalize()} are {', '.join(xs)}."
                        elif "grandchildren" in original_question.lower():
                            return f"The grandchildren of {self._extract_person_name_from_query(query).capitalize()} are {', '.join(xs)}."
                        else:
                            return f"The answers are: {', '.join(xs)}."
                    else:
                        return "No."
                else:
                    # Provide more informative responses for gender queries
                    if "male(" in query:
                        person_name = self._extract_person_name_from_query(query)
                        return f"Yes, {person_name.capitalize()} is male."
                    elif "female(" in query:
                        person_name = self._extract_person_name_from_query(query)
                        return f"Yes, {person_name.capitalize()} is female."
                    else:
                        return "Yes."
            else:
                # Try inference for relationship queries
                inferred_result = self._try_inference(prolog, query, original_question)
                if inferred_result:
                    return inferred_result
                
                # For simple yes/no questions, just return "No."
                if "parent_of(" in query or "sibling_of(" in query or "mother_of(" in query or "father_of(" in query:
                    return "No."
                
                # Extract the relationship type from the query for better error messages
                relationship_type = self._get_relationship_type_from_query(query)
                person_name = self._extract_person_name_from_query(query)
                
                # Provide more specific responses for gender queries
                if "male(" in query:
                    return f"No, {person_name.capitalize()} is not male."
                elif "female(" in query:
                    return f"No, {person_name.capitalize()} is not female."
                else:
                    return f"That's impossible! {person_name.capitalize()} has no {relationship_type}."
                    
        except Exception as e:
            print(f"Error executing query '{query}': {e}")
            return f"Error executing query: {str(e)}"
    
    def _extract_person_name_from_query(self, query: str) -> str:
        """Extract person name from a Prolog query."""
        # Try to extract name from various query patterns
        patterns = [
            r'\(([^,]+),\s*[^)]+\)',  # First argument in predicate (e.g., parent_of(joan, may) -> joan)
            r'\(([^)]+)\)',  # General pattern for predicates
            r'([A-Z][a-z]+)',  # Capitalized name pattern
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return match.group(1)
        
        return "Unknown"
    
    def _handle_sibling_query(self, prolog, query: str, original_question: str) -> str:
        """Handle sibling queries to determine if they are full or half siblings."""
        # Extract person names from the query
        import re
        match = re.search(r'sibling_of\(([^,]+),\s*([^)]+)\)', query)
        if not match:
            return "That's impossible! Could not parse sibling query."
        
        person1 = match.group(1)
        person2 = match.group(2)
        
        # Check if they are siblings at all
        sibling_results = safe_prolog_query(prolog, f"sibling_of({person1}, {person2})")
        if not sibling_results:
            return "No."
        
        # Check if they are half-siblings (check both directions)
        half_sibling_results = safe_prolog_query(prolog, f"half_sibling_of({person1}, {person2})")
        if not half_sibling_results:
            # Check the reverse direction
            half_sibling_results = safe_prolog_query(prolog, f"half_sibling_of({person2}, {person1})")
        
        if half_sibling_results:
            return f"Yes, {person1.capitalize()} and {person2.capitalize()} are siblings, but they are only half-siblings."
        else:
            return f"Yes, {person1.capitalize()} and {person2.capitalize()} are siblings, and they are full siblings."
    
    def _get_relationship_type_from_query(self, query: str) -> str:
        """Get the relationship type from a Prolog query."""
        if "sibling_of" in query:
            return "siblings"
        elif "sister_of" in query:
            return "sisters"
        elif "brother_of" in query:
            return "brothers"
        elif "mother_of" in query:
            return "mother"
        elif "father_of" in query:
            return "father"
        elif "parent_of" in query:
            return "parents"
        elif "daughter_of" in query:
            return "daughters"
        elif "son_of" in query:
            return "sons"
        elif "child_of" in query:
            return "children"
        elif "uncle_of" in query:
            return "uncle"
        elif "aunt_of" in query:
            return "aunt"
        elif "niece_of" in query:
            return "nieces"
        elif "nephew_of" in query:
            return "nephews"
        elif "cousin_of" in query:
            return "cousins"
        elif "grandchild_of" in query:
            return "grandchildren"
        elif "stepchild_of" in query:
            return "stepchildren"
        elif "half_sibling_of" in query:
            return "half-siblings"
        elif "male" in query:
            return "male gender"
        elif "female" in query:
            return "female gender"
        else:
            return "relationship"
    
    def _handle_brother_sister_relationship_check(self, prolog, query: str, original_question: str) -> str:
        """Handle brother/sister relationship checks by verifying gender and sibling relationships."""
        try:
            # Parse the query: check_brother_sister_relationship:person1:relationship_type:person2
            parts = query.split(":")
            person1 = parts[1]
            relationship_type = parts[2]  # "brother" or "sister"
            person2 = parts[3]
            
            # First, check if person1 has a gender assigned
            gender_results = safe_prolog_query(prolog, f"male({person1})")
            is_male = bool(gender_results)
            
            if not is_male:
                gender_results = safe_prolog_query(prolog, f"female({person1})")
                is_female = bool(gender_results)
                
                if not is_female:
                    return f"That's impossible! {person1.capitalize()} does not have an assigned gender yet."
            
            # Check if they are siblings
            sibling_results = safe_prolog_query(prolog, f"sibling_of({person1}, {person2})")
            if not sibling_results:
                return "No."
            
            # Check if they are half-siblings
            half_sibling_results = safe_prolog_query(prolog, f"half_sibling_of({person1}, {person2})")
            
            # Determine the correct response based on gender and relationship type
            if relationship_type == "brother":
                if is_male:
                    if half_sibling_results:
                        return f"Yes, {person1.capitalize()} is a half-brother of {person2.capitalize()}."
                    else:
                        return f"Yes, {person1.capitalize()} is a full brother of {person2.capitalize()}."
                else:
                    return "No."
            elif relationship_type == "sister":
                if is_female:
                    if half_sibling_results:
                        return f"Yes, {person1.capitalize()} is a half-sister of {person2.capitalize()}."
                    else:
                        return f"Yes, {person1.capitalize()} is a full sister of {person2.capitalize()}."
                else:
                    return "No."
            else:
                return "No."
                
        except Exception as e:
            print(f"Error checking brother/sister relationship: {e}")
            return f"Error checking relationship: {str(e)}"
    
    def _handle_relative_query(self, prolog, query: str, original_question: str) -> str:
        """Handle relative queries with inference capabilities."""
        try:
            # Extract person names from the query
            match = re.search(r'relative\(([^,]+),\s*([^)]+)\)', query)
            if not match:
                return "Error parsing relative query."
            
            person1 = match.group(1)
            person2 = match.group(2)
            
            # Check if they are relatives through any relationship
            relative_results = safe_prolog_query(prolog, f"relative({person1}, {person2})")
            if relative_results:
                return "Yes."
            
            # Try inference through shared parents
            inference_result = self._try_relative_inference(prolog, person1, person2)
            if inference_result:
                return inference_result
            
            return "No."
            
        except Exception as e:
            print(f"Error handling relative query: {e}")
            return f"Error checking relationship: {str(e)}"
    
    def _try_inference(self, prolog, query: str, original_question: str) -> str:
        """Try to infer relationships when direct facts don't exist."""
        try:
            # Check for sibling inference
            if "sibling_of(" in query:
                return self._try_sibling_inference(prolog, query, original_question)
            
            # Check for parent inference
            elif "parent_of(" in query or "mother_of(" in query or "father_of(" in query:
                return self._try_parent_inference(prolog, query, original_question)
            
            # Check for aunt/uncle inference
            elif "aunt_of(" in query or "uncle_of(" in query:
                return self._try_aunt_uncle_inference(prolog, query, original_question)
            
            # Check for cousin inference
            elif "cousin_of(" in query:
                return self._try_cousin_inference(prolog, query, original_question)
            
            return None
            
        except Exception as e:
            print(f"Error trying inference: {e}")
            return None
    
    def _try_sibling_inference(self, prolog, query: str, original_question: str) -> str:
        """Try to infer sibling relationships through shared parents."""
        try:
            # Extract person names from the query
            match = re.search(r'sibling_of\(([^,]+),\s*([^)]+)\)', query)
            if not match:
                return None
            
            person1 = match.group(1)
            person2 = match.group(2)
            
            # Check if they share any parent
            shared_parent_results = safe_prolog_query(prolog, f"parent_of(X, {person1}), parent_of(X, {person2})")
            if shared_parent_results:
                # Check if they are half-siblings (check both directions)
                half_sibling_results = safe_prolog_query(prolog, f"half_sibling_of({person1}, {person2})")
                if not half_sibling_results:
                    # Check the reverse direction
                    half_sibling_results = safe_prolog_query(prolog, f"half_sibling_of({person2}, {person1})")
                if half_sibling_results:
                    return f"Yes, {person1.capitalize()} and {person2.capitalize()} are siblings, but they are only half-siblings."
                else:
                    return f"Yes, {person1.capitalize()} and {person2.capitalize()} are siblings, and they are full siblings."
            
            return None
            
        except Exception as e:
            print(f"Error trying sibling inference: {e}")
            return None
    
    def _try_parent_inference(self, prolog, query: str, original_question: str) -> str:
        """Try to infer parent relationships through other connections."""
        try:
            # Extract person names from the query
            if "parent_of(" in query:
                match = re.search(r'parent_of\(([^,]+),\s*([^)]+)\)', query)
            elif "mother_of(" in query:
                match = re.search(r'mother_of\(([^,]+),\s*([^)]+)\)', query)
            elif "father_of(" in query:
                match = re.search(r'father_of\(([^,]+),\s*([^)]+)\)', query)
            else:
                return None
            
            if not match:
                return None
            
            parent = match.group(1)
            child = match.group(2)
            
            # Check if parent is actually a parent through any relationship
            parent_results = safe_prolog_query(prolog, f"parent_of({parent}, {child})")
            if parent_results:
                return "Yes."
            
            return None
            
        except Exception as e:
            print(f"Error trying parent inference: {e}")
            return None
    
    def _try_aunt_uncle_inference(self, prolog, query: str, original_question: str) -> str:
        """Try to infer aunt/uncle relationships through sibling connections."""
        try:
            # Extract person names from the query
            if "aunt_of(" in query:
                match = re.search(r'aunt_of\(([^,]+),\s*([^)]+)\)', query)
            elif "uncle_of(" in query:
                match = re.search(r'uncle_of\(([^,]+),\s*([^)]+)\)', query)
            else:
                return None
            
            if not match:
                return None
            
            aunt_uncle = match.group(1)
            niece_nephew = match.group(2)
            
            # Check if aunt/uncle is sibling of niece/nephew's parent
            parent_results = safe_prolog_query(prolog, f"parent_of(X, {niece_nephew})")
            if parent_results:
                for parent_result in parent_results:
                    parent = parent_result["X"]
                    sibling_results = safe_prolog_query(prolog, f"sibling_of({aunt_uncle}, {parent})")
                    if sibling_results:
                        return "Yes."
            
            return None
            
        except Exception as e:
            print(f"Error trying aunt/uncle inference: {e}")
            return None
    
    def _try_cousin_inference(self, prolog, query: str, original_question: str) -> str:
        """Try to infer cousin relationships through parent connections."""
        try:
            # Extract person names from the query
            match = re.search(r'cousin_of\(([^,]+),\s*([^)]+)\)', query)
            if not match:
                return None
            
            person1 = match.group(1)
            person2 = match.group(2)
            
            # Check if their parents are siblings
            parent1_results = safe_prolog_query(prolog, f"parent_of(X, {person1})")
            parent2_results = safe_prolog_query(prolog, f"parent_of(Y, {person2})")
            
            if parent1_results and parent2_results:
                for parent1_result in parent1_results:
                    parent1 = parent1_result["X"]
                    for parent2_result in parent2_results:
                        parent2 = parent2_result["Y"]
                        if parent1 != parent2:  # Not the same parent
                            sibling_results = safe_prolog_query(prolog, f"sibling_of({parent1}, {parent2})")
                            if sibling_results:
                                return "Yes."
            
            return None
            
        except Exception as e:
            print(f"Error trying cousin inference: {e}")
            return None
    
    def _try_relative_inference(self, prolog, person1: str, person2: str) -> str:
        """Try to infer if two people are relatives through any connection."""
        try:
            # Check if they are the same person
            if person1 == person2:
                return "Yes."
            
            # Check if they are siblings
            sibling_results = safe_prolog_query(prolog, f"sibling_of({person1}, {person2})")
            if sibling_results:
                return "Yes."
            
            # Check if they are parent-child
            parent_results = safe_prolog_query(prolog, f"parent_of({person1}, {person2})")
            if parent_results:
                return "Yes."
            
            parent_results = safe_prolog_query(prolog, f"parent_of({person2}, {person1})")
            if parent_results:
                return "Yes."
            
            # Check if they are aunt/uncle-niece/nephew
            aunt_uncle_results = safe_prolog_query(prolog, f"aunt_of({person1}, {person2})")
            if aunt_uncle_results:
                return "Yes."
            
            aunt_uncle_results = safe_prolog_query(prolog, f"uncle_of({person1}, {person2})")
            if aunt_uncle_results:
                return "Yes."
            
            aunt_uncle_results = safe_prolog_query(prolog, f"aunt_of({person2}, {person1})")
            if aunt_uncle_results:
                return "Yes."
            
            aunt_uncle_results = safe_prolog_query(prolog, f"uncle_of({person2}, {person1})")
            if aunt_uncle_results:
                return "Yes."
            
            # Check if they are cousins
            cousin_results = safe_prolog_query(prolog, f"cousin_of({person1}, {person2})")
            if cousin_results:
                return "Yes."
            
            # Check if they are grandparent-grandchild
            grandparent_results = safe_prolog_query(prolog, f"grandparent_of({person1}, {person2})")
            if grandparent_results:
                return "Yes."
            
            grandparent_results = safe_prolog_query(prolog, f"grandparent_of({person2}, {person1})")
            if grandparent_results:
                return "Yes."
            
            # Check if they share any parent (siblings)
            shared_parent_results = safe_prolog_query(prolog, f"parent_of(X, {person1}), parent_of(X, {person2})")
            if shared_parent_results:
                return "Yes."
            
            # Check if their parents are siblings (cousins)
            parent1_results = safe_prolog_query(prolog, f"parent_of(X, {person1})")
            parent2_results = safe_prolog_query(prolog, f"parent_of(Y, {person2})")
            
            if parent1_results and parent2_results:
                for parent1_result in parent1_results:
                    parent1 = parent1_result["X"]
                    for parent2_result in parent2_results:
                        parent2 = parent2_result["Y"]
                        if parent1 != parent2:  # Not the same parent
                            sibling_results = safe_prolog_query(prolog, f"sibling_of({parent1}, {parent2})")
                            if sibling_results:
                                return "Yes."
            
            return None
            
        except Exception as e:
            print(f"Error trying relative inference: {e}")
            return None 