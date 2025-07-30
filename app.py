from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os
from pyswip import Prolog

app = FastAPI()

# Function to add facts to Prolog
def add_fact_to_prolog(statement):
    """Translate a user statement into a Prolog fact and assert it."""
    import re
   
    def to_prolog_name(name):
        return name.strip().lower() # Set names to lowercase

    # Using regex and parsing user input
    statement_patterns = [
        ("X and Y are siblings", r"(\w+) and (\w+) are siblings", lambda m: f"sibling_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})."),
        ("X is a sister of Y", r"(\w+) is a sister of (\w+)", lambda m: f"sister_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})."),
        ("X is a brother of Y", r"(\w+) is a brother of (\w+)", lambda m: f"brother_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})."),
        ("X is the mother of Y", r"(\w+) is the mother of (\w+)", lambda m: f"mother_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})."),
        ("X is the father of Y", r"(\w+) is the father of (\w+)", lambda m: f"father_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})."),
        ("X is a son of Y", r"(\w+) is a son of (\w+)", lambda m: f"son_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})."),
        ("X is a daughter of Y", r"(\w+) is a daughter of (\w+)", lambda m: f"daughter_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})."),
        ("X is a child of Y", r"(\w+) is a child of (\w+)", lambda m: f"child_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})."),
        ("X is a grandmother of Y", r"(\w+) is a grandmother of (\w+)", lambda m: f"grandmother_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})."),
        ("X is a grandfather of Y", r"(\w+) is a grandfather of (\w+)", lambda m: f"grandfather_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})."),
        ("X is an uncle of Y", r"(\w+) is an uncle of (\w+)", lambda m: f"uncle_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})."),
        ("X is an aunt of Y", r"(\w+) is an aunt of (\w+)", lambda m: f"aunt_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})."),
        # Special case for parents: add parent_of, father_of, mother_of, male, female
        ("X and Y are the parents of Z", r"(\w+) and (\w+) are the parents of (\w+)",
            lambda m: f"parent_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(3))}).\nparent_of({to_prolog_name(m.group(2))}, {to_prolog_name(m.group(3))}).\n"
                      f"father_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(3))}).\nmother_of({to_prolog_name(m.group(2))}, {to_prolog_name(m.group(3))}).\n"
                      f"male({to_prolog_name(m.group(1))}).\nfemale({to_prolog_name(m.group(2))})."),
        ("X, Y and Z are children of W", r"(\w+), (\w+) and (\w+) are children of (\w+)", lambda m: f"child_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(4))}).\nchild_of({to_prolog_name(m.group(2))}, {to_prolog_name(m.group(4))}).\nchild_of({to_prolog_name(m.group(3))}, {to_prolog_name(m.group(4))})."),
    ]

    for _, pattern, func in statement_patterns:
        match = re.fullmatch(pattern, statement.strip(), re.IGNORECASE)
        if match:
            fact = func(match)
            # Read current contents
            with open("relationships.pl", "r", encoding="utf-8") as f:
                old_contents = f.read()
            # Write new fact at the top
            with open("relationships.pl", "w", encoding="utf-8") as f:
                f.write(f"{fact}\n" + old_contents)
            # Reload Prolog knowledge base
            Prolog.consult("relationships.pl")
            return "OK! I learned something new."
    return f"[Unrecognized statement]: {statement}"

# Function to query Prolog
def query_prolog(question):
    """Translate a user question into a Prolog query and get the result."""
    import re
    def to_prolog_name(name):
        return name.strip().lower()

    # Map question templates to regex and Prolog templates
    question_patterns = [
        ("Are X and Y siblings?", r"Are (\w+) and (\w+) siblings\?", lambda m: f"sibling_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Is X a sister of Y?", r"Is (\w+) a sister of (\w+)\?", lambda m: f"sister_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Is X a brother of Y?", r"Is (\w+) a brother of (\w+)\?", lambda m: f"brother_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Is X the mother of Y?", r"Is (\w+) the mother of (\w+)\?", lambda m: f"mother_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Is X the father of Y?", r"Is (\w+) the father of (\w+)\?", lambda m: f"father_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Are X and Y the parents of Z?", r"Are (\w+) and (\w+) the parents of (\w+)\?", lambda m: f"parent_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(3))}), parent_of({to_prolog_name(m.group(2))}, {to_prolog_name(m.group(3))})"),
        ("Is X a grandmother of Y?", r"Is (\w+) a grandmother of (\w+)\?", lambda m: f"grandmother_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Is X a grandfather of Y?", r"Is (\w+) a grandfather of (\w+)\?", lambda m: f"grandfather_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Is X a daughter of Y?", r"Is (\w+) a daughter of (\w+)\?", lambda m: f"daughter_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Is X a son of Y?", r"Is (\w+) a son of (\w+)\?", lambda m: f"son_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Is X a child of Y?", r"Is (\w+) a child of (\w+)\?", lambda m: f"child_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Are X, Y, and Z children of W?", r"Are (\w+), (\w+), and (\w+) children of (\w+)\?", lambda m: f"child_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(4))}), child_of({to_prolog_name(m.group(2))}, {to_prolog_name(m.group(4))}), child_of({to_prolog_name(m.group(3))}, {to_prolog_name(m.group(4))})"),
        ("Is X an uncle of Y?", r"Is (\w+) an uncle of (\w+)\?", lambda m: f"uncle_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Is X an aunt of Y?", r"Is (\w+) an aunt of (\w+)\?", lambda m: f"aunt_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
        ("Who are the siblings of X?", r"Who are the siblings of (\w+)\?", lambda m: f"sibling_of(X, {to_prolog_name(m.group(1))})"),
        ("Who are the sisters of X?", r"Who are the sisters of (\w+)\?", lambda m: f"sister_of(X, {to_prolog_name(m.group(1))})"),
        ("Who are the brothers of X?", r"Who are the brothers of (\w+)\?", lambda m: f"brother_of(X, {to_prolog_name(m.group(1))})"),
        ("Who is the mother of X?", r"Who is the mother of (\w+)\?", lambda m: f"mother_of(X, {to_prolog_name(m.group(1))})"),
        ("Who is the father of X?", r"Who is the father of (\w+)\?", lambda m: f"father_of(X, {to_prolog_name(m.group(1))})"),
        ("Who are the parents of X?", r"Who are the parents of (\w+)\?", lambda m: f"parent_of(X, {to_prolog_name(m.group(1))})"),
        ("Who are the daughters of X?", r"Who are the daughters of (\w+)\?", lambda m: f"daughter_of(X, {to_prolog_name(m.group(1))})"),
        ("Who are the sons of X?", r"Who are the sons of (\w+)\?", lambda m: f"son_of(X, {to_prolog_name(m.group(1))})"),
        ("Who are the children of X?", r"Who are the children of (\w+)\?", lambda m: f"child_of(X, {to_prolog_name(m.group(1))})"),
        ("Are X and Y relatives?", r"Are (\w+) and (\w+) relatives\?", lambda m: f"relative_of({to_prolog_name(m.group(1))}, {to_prolog_name(m.group(2))})"),
    ]

    try:
        for _, pattern, func in question_patterns:
            match = re.fullmatch(pattern, question.strip(), re.IGNORECASE) # To check if input matches the pattern
            if match:
                query = func(match)
                
                from pyswip import Prolog as SWIProlog 
                prolog = SWIProlog()
                prolog.consult("relationships.pl")

                if "X" in query: # For questions that ask for specific names
                    results = list(prolog.query(query))
                    if results:
                        xs = set(str(r["X"]) for r in results if "X" in r)
                        if xs:
                            return f"Answers: {', '.join(xs)}"
                        else:
                            return "No."
                    else:
                        return "No."
                else:
                    results = list(prolog.query(query))
                    if results:
                        return "Yes."
                    else:
                        return "No."
        return f"[Unrecognized statement]: {question}"
    except Exception as e:
        return f"[Error executing query: {str(e)}]"

def parse_input(user_input):
    """Parse user input to determine if it's a statement or question and translate to Prolog."""
    if user_input.endswith("?"):
        return query_prolog(user_input)
    else:
        return add_fact_to_prolog(user_input)
    
# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Main landing page with app description and options"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/load-knowledge", response_class=HTMLResponse)
def load_knowledge(request: Request):
    """Load knowledge base from last chat"""
    # TODO: Implement loading previous knowledge base
    return templates.TemplateResponse("chat.html", {"request": request, "mode": "load"})

@app.get("/new-chat", response_class=HTMLResponse)
def new_chat(request: Request):
    """Create a new chat session"""
    # TODO: Initialize new chat session
    return templates.TemplateResponse("chat.html", {"request": request, "mode": "new"})

@app.get("/exit", response_class=HTMLResponse)
def exit_program(request: Request):
    """Exit the program"""
    return templates.TemplateResponse("exit.html", {"request": request})

@app.post("/chat", response_class=HTMLResponse)
def process_chat(request: Request, message: str = Form(...)):
    """Process chat messages and translate to Prolog statement/query."""
    user_input = message
    response = parse_input(user_input) # Parse the input and get Prolog response
    return templates.TemplateResponse("chat.html", {"request": request, "user_input": user_input, "response": response})

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=3000, reload=True)
