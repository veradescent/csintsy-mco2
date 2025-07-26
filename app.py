from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os

app = FastAPI()

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
    """Process chat messages (to be implemented with PROLOG backend)"""
    user_input = message
    # TODO: Process with PROLOG backend
    return templates.TemplateResponse("chat.html", {"request": request, "user_input": user_input, "response": "Feature coming soon!"})

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=3000, reload=True)
