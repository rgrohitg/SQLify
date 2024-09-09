#main.py
from fastapi import FastAPI,Request
from app.api.routes import router as api_router
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
app = FastAPI()
# Load Cube.js semantic documents at startup
# load_cube_semantic_docs()
templates = Jinja2Templates(directory="templates")

app.include_router(api_router)


@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
