import re
from typing import Tuple

def to_prolog_name(name: str) -> str:
    """Convert a name to Prolog format (lowercase)."""
    return name.lower()

def validate_name(name: str) -> Tuple[bool, str]:
    """Validate that a name follows the required format."""
    if not name:
        return False, "Name cannot be empty."
    
    if not name[0].isupper():
        return False, f"Name '{name}' must start with a capital letter."
    
    if ' ' in name:
        return False, f"Name '{name}' cannot contain spaces."
    
    if not name.replace("'", "").replace("-", "").isalpha():
        return False, f"Name '{name}' can only contain letters, hyphens, and apostrophes."
    
    return True, ""

def safe_prolog_query(prolog, query):
    """Safely execute a Prolog query with error handling."""
    try:
        # Disable any system calls that might cause pyrun issues
        try:
            prolog.query(":- set_prolog_flag(unknown, fail).")
        except:
            pass  # Ignore if this fails
        
        # Execute the actual query
        results = list(prolog.query(query))
        return results
    except Exception as e:
        print(f"Prolog query error for '{query}': {e}")
        return []

def validate_prolog_file(file_path: str) -> bool:
    """Validate that a Prolog file can be consulted without errors."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for problematic module imports
        if "library(os)" in content or "library(system)" in content:
            print(f"File contains problematic module imports: {file_path}")
            return False
        
        # Check for any non-ASCII characters that might cause issues
        try:
            content.encode('ascii')
        except UnicodeEncodeError:
            print(f"File contains non-ASCII characters: {file_path}")
            return False
        
        # Try to consult the file with error handling
        try:
            from pyswip import Prolog
            prolog = Prolog()
            prolog.consult(file_path)
            return True
        except Exception as prolog_error:
            print(f"Prolog consultation error: {prolog_error}")
            # If Prolog consultation fails, try to clean the file
            return clean_prolog_file(file_path)
        
    except Exception as e:
        print(f"Error validating Prolog file {file_path}: {e}")
        return False

def clean_prolog_file(file_path: str) -> bool:
    """Clean a Prolog file by removing problematic content and ensuring valid syntax."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Remove any lines that might cause issues
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue
            
            # Skip lines with problematic characters
            try:
                line.encode('ascii')
                cleaned_lines.append(line)
            except UnicodeEncodeError:
                print(f"Skipping line with non-ASCII characters: {line}")
                continue
        
        # Write the cleaned content back
        with open(file_path, "w", encoding="utf-8") as f:
            f.write('\n'.join(cleaned_lines))
        
        # Try to consult the cleaned file
        try:
            from pyswip import Prolog
            prolog = Prolog()
            prolog.consult(file_path)
            return True
        except Exception as prolog_error:
            print(f"Prolog consultation still fails after cleaning: {prolog_error}")
            return False
        
    except Exception as e:
        print(f"Error cleaning Prolog file {file_path}: {e}")
        return False

def generate_unique_shared_parent_names(person1: str, person2: str, parent_type: str = "mother") -> Tuple[str, str]:
    """
    Generate unique shared parent names for a sibling pair.
    
    Args:
        person1: First person's name
        person2: Second person's name
        parent_type: "mother" or "father"
    
    Returns:
        Tuple of (shared_parent_name, shared_parent_gender_fact)
    """
    # Create a unique identifier based on the two people's names
    # Sort names to ensure consistent ordering
    sorted_names = sorted([person1.lower(), person2.lower()])
    unique_id = "_".join(sorted_names)
    
    if parent_type == "mother":
        shared_parent_name = f"shared_mother_{unique_id}"
        gender_fact = f"female({shared_parent_name})."
    else:  # father
        shared_parent_name = f"shared_father_{unique_id}"
        gender_fact = f"male({shared_parent_name})."
    
    return shared_parent_name, gender_fact 