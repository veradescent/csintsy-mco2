import json
import os
import shutil
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional
import re
from pyswip import Prolog

# Import parser functions from the new parser module
from parser import parse_input, cleanup_impossible_relationships

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Global variable to track current chat session
current_chat_session = None

def create_chat_session():
    """Create a new chat session with its own folder and knowledge base."""
    global current_chat_session
    
    # Create timestamp for unique folder name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    chat_folder = f"chats/chat_{timestamp}"
    
    # Create the chat folder
    os.makedirs(chat_folder, exist_ok=True)
    
    # Copy the base relationships.pl to the chat folder
    chat_kb_file = os.path.join(chat_folder, "relationships.pl")
    if os.path.exists("relationships.pl"):
        shutil.copy2("relationships.pl", chat_kb_file)
    else:
        # Create a basic relationships.pl file if it doesn't exist
        with open(chat_kb_file, "w") as f:
            f.write("% Family Relationship Rules\n\n")
            f.write("% Basic parent-child relationship\n")
            f.write("father_of(X, Y) :- parent_of(X, Y), male(X), X \\= Y.\n")
            f.write("mother_of(X, Y) :- parent_of(X, Y), female(X), X \\= Y.\n")
            f.write("child_of(Y, X) :- parent_of(X, Y), X \\= Y.\n")
            f.write("son_of(Y, X) :- child_of(Y, X), male(Y).\n")
            f.write("daughter_of(Y, X) :- child_of(Y, X), female(Y).\n")
            f.write("sibling_of(X, Y) :- parent_of(Z, X), parent_of(Z, Y), X \\= Y, Z \\= X, Z \\= Y.\n")
            f.write("brother_of(X, Y) :- sibling_of(X, Y), male(X).\n")
            f.write("sister_of(X, Y) :- sibling_of(X, Y), female(X).\n")
            f.write("grandparent_of(X, Y) :- parent_of(X, Z), parent_of(Z, Y), X \\= Y.\n")
            f.write("grandmother_of(X, Y) :- grandparent_of(X, Y), female(X).\n")
            f.write("grandfather_of(X, Y) :- grandparent_of(X, Y), male(X).\n")
            f.write("grandchild_of(Y, X) :- grandparent_of(X, Y), X \\= Y.\n")
            f.write("granddaughter_of(Y, X) :- grandchild_of(Y, X), female(Y).\n")
            f.write("grandson_of(Y, X) :- grandchild_of(Y, X), male(Y).\n")
            f.write("uncle_of(X, Y) :- brother_of(X, Z), parent_of(Z, Y), X \\= Y.\n")
            f.write("aunt_of(X, Y) :- sister_of(X, Z), parent_of(Z, Y), X \\= Y.\n")
            f.write("niece_of(Y, X) :- female(Y), (uncle_of(X, Y); aunt_of(X, Y)), X \\= Y.\n")
            f.write("nephew_of(Y, X) :- male(Y), (uncle_of(X, Y); aunt_of(X, Y)), X \\= Y.\n")
            f.write("cousin_of(X, Y) :- parent_of(Z1, X), parent_of(Z2, Y), sibling_of(Z1, Z2), X \\= Y.\n")
            f.write("half_sibling_of(X, Y) :- parent_of(Z, X), parent_of(Z, Y), X \\= Y, parent_of(W1, X), parent_of(W2, Y), W1 \\= W2, W1 \\= Z, W2 \\= Z.\n")
            f.write("half_brother_of(X, Y) :- half_sibling_of(X, Y), male(X).\n")
            f.write("half_sister_of(X, Y) :- half_sibling_of(X, Y), female(X).\n")
            f.write("relative(X, Y) :- parent_of(X, Y); parent_of(Y, X); child_of(X, Y); child_of(Y, X); sibling_of(X, Y); sibling_of(Y, X); grandparent_of(X, Y); grandparent_of(Y, X); uncle_of(X, Y); uncle_of(Y, X); aunt_of(X, Y); aunt_of(Y, X); cousin_of(X, Y); cousin_of(Y, X); half_sibling_of(X, Y); half_sibling_of(Y, X).\n")
            f.write("ancestor_of(X, Y) :- parent_of(X, Y).\n")
            f.write("ancestor_of(X, Y) :- parent_of(X, Z), parent_of(Z, Y), X \\= Y.\n")
            f.write("ancestor_of(X, Y) :- parent_of(X, Z1), parent_of(Z1, Z2), parent_of(Z2, Y), X \\= Y, Z1 \\= Y.\n")
    
    # Create empty chat history file
    chat_history_file = os.path.join(chat_folder, "chat_history.json")
    with open(chat_history_file, "w") as f:
        json.dump([], f)
    
    current_chat_session = {
        "folder": chat_folder,
        "kb_file": chat_kb_file,
        "history_file": chat_history_file,
        "timestamp": timestamp
    }
    
    return current_chat_session

def check_saved_chat_exists():
    """Check if there's a saved chat session available."""
    print("check_saved_chat_exists called")
    
    if not os.path.exists("chats"):
        print("chats directory does not exist")
        return False
    
    # Find the most recent chat folder
    chat_folders = [f for f in os.listdir("chats") if f.startswith("chat_")]
    print(f"Found chat folders: {chat_folders}")
    
    if not chat_folders:
        print("No chat folders found")
        return False
    
    # Sort by timestamp and get the most recent
    chat_folders.sort(reverse=True)
    latest_folder = chat_folders[0]
    chat_folder = os.path.join("chats", latest_folder)
    print(f"Checking folder: {chat_folder}")
    
    # Check if this chat session has been saved (has a saved flag)
    saved_flag_file = os.path.join(chat_folder, "saved.flag")
    print(f"Saved flag exists: {os.path.exists(saved_flag_file)}")
    
    if not os.path.exists(saved_flag_file):
        print("No saved flag found")
        return False
    
    kb_file = os.path.join(chat_folder, "relationships.pl")
    history_file = os.path.join(chat_folder, "chat_history.json")
    
    print(f"KB file exists: {os.path.exists(kb_file)}")
    print(f"History file exists: {os.path.exists(history_file)}")
    
    if not os.path.exists(kb_file) or not os.path.exists(history_file):
        print("Required files missing")
        return False
    
    print("Saved chat exists")
    return True

def load_last_chat_session():
    """Load the most recent saved chat session."""
    global current_chat_session
    
    print("load_last_chat_session called")
    
    if not check_saved_chat_exists():
        print("No saved chat exists")
        return None
    
    # Find the most recent chat folder
    chat_folders = [f for f in os.listdir("chats") if f.startswith("chat_")]
    print(f"Found chat folders: {chat_folders}")
    
    if not chat_folders:
        print("No chat folders found")
        return None
    
    chat_folders.sort(reverse=True)
    latest_folder = chat_folders[0]
    chat_folder = os.path.join("chats", latest_folder)
    print(f"Loading from folder: {chat_folder}")
    
    kb_file = os.path.join(chat_folder, "relationships.pl")
    history_file = os.path.join(chat_folder, "chat_history.json")
    
    print(f"KB file exists: {os.path.exists(kb_file)}")
    print(f"History file exists: {os.path.exists(history_file)}")
    
    current_chat_session = {
        "folder": chat_folder,
        "kb_file": kb_file,
        "history_file": history_file,
        "timestamp": latest_folder.replace("chat_", "")
    }
    
    print(f"Loaded chat session: {current_chat_session}")
    return current_chat_session

def save_chat_session():
    """Mark the current chat session as saved."""
    global current_chat_session
    
    print(f"save_chat_session called. Current session: {current_chat_session}")
    
    if current_chat_session:
        # Check if there's already a saved chat that's different from current
        existing_saved = None
        if os.path.exists("chats"):
            chat_folders = [f for f in os.listdir("chats") if f.startswith("chat_")]
            for folder in chat_folders:
                chat_folder = os.path.join("chats", folder)
                saved_flag_file = os.path.join(chat_folder, "saved.flag")
                if os.path.exists(saved_flag_file) and chat_folder != current_chat_session["folder"]:
                    existing_saved = chat_folder
                    break
        
        # If there's an existing saved chat, delete it first
        if existing_saved:
            print(f"Deleting existing saved chat: {existing_saved}")
            try:
                shutil.rmtree(existing_saved)
                print("Existing saved chat deleted")
            except Exception as e:
                print(f"Error deleting existing saved chat: {e}")
        
        # Mark current session as saved
        saved_flag_file = os.path.join(current_chat_session["folder"], "saved.flag")
        print(f"Creating saved flag file: {saved_flag_file}")
        try:
            with open(saved_flag_file, "w") as f:
                f.write("saved")
            print("Saved flag file created successfully")
            return True
        except Exception as e:
            print(f"Error creating saved flag file: {e}")
            return False
    else:
        print("No current session to save")
        return False

def delete_chat_session():
    """Delete the current chat session folder."""
    global current_chat_session
    
    print(f"Attempting to delete chat session: {current_chat_session}")
    
    if current_chat_session:
        print(f"Current session folder: {current_chat_session['folder']}")
        print(f"Folder exists: {os.path.exists(current_chat_session['folder'])}")
        
        if os.path.exists(current_chat_session["folder"]):
            print(f"Deleting folder: {current_chat_session['folder']}")
            try:
                shutil.rmtree(current_chat_session["folder"])
                print("Chat session deleted successfully")
                current_chat_session = None
                return True
            except Exception as e:
                print(f"Error deleting folder: {e}")
                return False
        else:
            print(f"Folder does not exist: {current_chat_session['folder']}")
            return False
    else:
        print("No current chat session to delete")
        return False

def get_chat_history():
    """Get the current chat history."""
    global current_chat_session
    
    if not current_chat_session:
        return []
    
    try:
        with open(current_chat_session["history_file"], "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_chat_history(history):
    """Save the chat history to the current session."""
    global current_chat_session
    
    if current_chat_session:
        with open(current_chat_session["history_file"], "w") as f:
            json.dump(history, f)

def get_current_kb_file():
    """Get the current knowledge base file path."""
    global current_chat_session
    
    if current_chat_session:
        return current_chat_session["kb_file"]
    return "relationships.pl"

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Main landing page with app description and options"""
    # Check if there's a saved chat to load
    has_saved_chat = check_saved_chat_exists()
    return templates.TemplateResponse("index.html", {"request": request, "has_saved_chat": has_saved_chat})

@app.get("/new-chat", response_class=RedirectResponse)
def new_chat(request: Request):
    """Start a new chat session"""
    global current_chat_session
    
    # If there's a current session, delete it (user chose not to save)
    if current_chat_session:
        delete_chat_session()
    
    # Create new chat session
    create_chat_session()
    return RedirectResponse(url="/menu-chat")

@app.get("/load-chat", response_class=RedirectResponse)
def load_chat(request: Request):
    """Load the last saved chat session"""
    global current_chat_session
    
    print(f"Load chat request received. Current session: {current_chat_session}")
    
    # Check if current session is already a saved session
    if current_chat_session and os.path.exists(os.path.join(current_chat_session["folder"], "saved.flag")):
        print("Current session is already a saved session, redirecting with mode=load")
        return RedirectResponse(url="/menu-chat?mode=load")
    
    # If there's a current session that's not saved, delete it
    if current_chat_session:
        print("Deleting unsaved current session before loading saved chat")
        delete_chat_session()
    
    # Try to load the last saved chat
    print("Attempting to load last saved chat session")
    session = load_last_chat_session()
    print(f"Load result: {session}")
    
    if session:
        print("Successfully loaded saved chat, redirecting with mode=load")
        return RedirectResponse(url="/menu-chat?mode=load")
    else:
        print("No saved chat found, creating new session")
        # If no saved chat exists, create a new one
        create_chat_session()
        return RedirectResponse(url="/menu-chat")

@app.get("/menu-chat", response_class=HTMLResponse)
def menu_chat(request: Request, mode: Optional[str] = None):
    """Menu-based chat interface"""
    global current_chat_session
    
    # If no current session, create one
    if not current_chat_session:
        create_chat_session()
    
    chat_history = get_chat_history()
    
    return templates.TemplateResponse("menu_chat.html", {
        "request": request, 
        "chat_history": chat_history,
        "mode": mode,
        "has_saved_chat": check_saved_chat_exists(),
        "current_session_folder": current_chat_session["folder"] if current_chat_session else None
    })

@app.post("/menu-chat", response_class=HTMLResponse)
async def process_menu_chat(request: Request, message: str = Form(...), chat_history: Optional[str] = Form(None)):
    """Process menu chat messages"""
    global current_chat_session
    
    if not message.strip():
        return templates.TemplateResponse("menu_chat.html", {"request": request, "chat_history": []})
    
    # Ensure we have a current session
    if not current_chat_session:
        create_chat_session()
    
    # Temporarily set the knowledge base file for the parser
    import parser
    original_kb_file = getattr(parser, 'current_kb_file', 'relationships.pl')
    parser.current_kb_file = get_current_kb_file()
    
    try:
        # Parse and process the message
        response = parse_input(message.strip())
    finally:
        # Restore original knowledge base file
        parser.current_kb_file = original_kb_file
    
    # Parse existing chat history
    try:
        if chat_history:
            history_list = json.loads(chat_history)
        else:
            history_list = []
    except (json.JSONDecodeError, TypeError):
        history_list = []
    
    # Add new messages to history
    history_list.append({"role": "user", "text": message})
    history_list.append({"role": "bot", "text": response})
    
    # Save the updated history
    save_chat_history(history_list)
    
    return templates.TemplateResponse("menu_chat.html", {
        "request": request, 
        "chat_history": history_list,
        "current_session_folder": current_chat_session["folder"] if current_chat_session else None
    })

@app.post("/save-chat")
async def save_chat(request: Request):
    """Save the current chat session"""
    print("Save chat request received")
    success = save_chat_session()
    print(f"Save result: {success}")
    return JSONResponse(content={"success": success})

@app.post("/delete-chat")
async def delete_chat(request: Request):
    """Delete the current chat session"""
    global current_chat_session
    
    # Get the request body
    body = await request.json()
    session_folder = body.get("session_folder", "")
    
    print(f"Delete request received. Session folder: {session_folder}")
    print(f"Current session: {current_chat_session}")
    
    # If we have a session folder from the frontend, use it
    if session_folder and os.path.exists(session_folder):
        print(f"Deleting folder from request: {session_folder}")
        try:
            shutil.rmtree(session_folder)
            current_chat_session = None
            print("Chat session deleted successfully")
            return JSONResponse(content={"success": True})
        except Exception as e:
            print(f"Error deleting folder: {e}")
            return JSONResponse(content={"success": False})
    
    # Fallback to current session
    success = delete_chat_session()
    print(f"Delete chat session result: {success}")
    return JSONResponse(content={"success": success})

@app.get("/exit", response_class=HTMLResponse)
def exit_program(request: Request):
    """Exit page"""
    return templates.TemplateResponse("exit.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
