from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
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

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Main landing page with app description and options"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/load-knowledge", response_class=RedirectResponse)
def load_knowledge(request: Request):
    """Load knowledge base from last chat"""
    # TODO: Implement loading previous knowledge base
    return RedirectResponse(url="/menu-chat")

@app.get("/menu-chat", response_class=HTMLResponse)
def menu_chat(request: Request):
    """Menu-based chat interface"""
    return templates.TemplateResponse("menu_chat.html", {"request": request})

@app.post("/menu-chat", response_class=HTMLResponse)
async def process_menu_chat(request: Request, message: str = Form(...), chat_history: Optional[str] = Form(None)):
    """Process menu chat messages"""
    if not message.strip():
        return templates.TemplateResponse("menu_chat.html", {"request": request, "chat_history": chat_history or ""})
    
    # Parse and process the message
    response = parse_input(message.strip())
    
    # Build chat history
    if chat_history:
        new_history = f"{chat_history}\n\nUser: {message}\nBot: {response}"
    else:
        new_history = f"User: {message}\nBot: {response}"
    
    return templates.TemplateResponse("menu_chat.html", {"request": request, "chat_history": new_history})

@app.get("/exit", response_class=HTMLResponse)
def exit_program(request: Request):
    """Exit page"""
    return templates.TemplateResponse("exit.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
