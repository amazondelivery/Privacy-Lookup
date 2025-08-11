from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path
from security import setup_security
import re

app = FastAPI(
    title="Privacy Lookup",
    description="Privacy Lookup",
    version="1.0.0",
    docs_url=None,
    redoc_url=None
)

setup_security(app)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Serve main page
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/guide/{domain}")
async def check_guide_exists(domain: str):
    domain = sanitize_domain(domain)
    guide_path = Path(f"guides/{domain}/{domain}.txt")

    if guide_path.exists() and guide_path.is_file():
        return {"exists": True, "url": f"/guide/{domain}"}
    else:
        return {"exists": False}

@app.get("/guide/{domain}", response_class=HTMLResponse)
async def get_guide(request: Request, domain: str):
    domain = sanitize_domain(domain)
    guide_path = Path(f"guides/{domain}/{domain}.txt")  # Fixed path

    if guide_path.exists() and guide_path.is_file():
        with open(guide_path, 'r', encoding="utf-8") as file:
            guide_content = file.read()
        parsed_guide = parse_guide_text(guide_content)

        return templates.TemplateResponse("guide.html", {
            "request": request,
            "domain": domain,
            "guide": parsed_guide
        })
    else:
        raise HTTPException(status_code=404, detail="Guide not found")

def sanitize_domain(domain: str) -> str:
    domain = domain.lower().strip()
    domain = re.sub(r'^https?://', '', domain)
    domain = re.sub(r'^www\.', '', domain)
    domain = domain.rstrip('/')

    # Prevent path traversal attempts
    if '/' in domain or '\\' in domain:
        raise HTTPException(status_code=400, detail="Invalid domain format")
    
    if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', domain):
        raise HTTPException(status_code=400, detail="Invalid domain format")
    
    return domain

def parse_guide_text(content: str) -> dict:
    """Parse structured text file into guide data"""
    lines = content.strip().split('\n')
    
    guide = {
        'title': '',
        'last_updated': '',
        'desktop_steps': [],
        'mobile_steps': []
    }
    
    current_section = None
    current_step = None
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('TITLE:'):
            guide['title'] = line.replace('TITLE:', '').strip()
        elif line.startswith('UPDATED:'):
            guide['last_updated'] = line.replace('UPDATED:', '').strip()
        elif line == 'DESKTOP:':
            current_section = 'desktop'
        elif line == 'MOBILE:':
            current_section = 'mobile'
        elif line.startswith('STEP:'):
            if current_step:
                # Save previous step
                if current_section == 'desktop':
                    guide['desktop_steps'].append(current_step)
                elif current_section == 'mobile':
                    guide['mobile_steps'].append(current_step)
            
            # Start new step
            current_step = {
                'instruction': line.replace('STEP:', '').strip(),
                'image': '',
                'note': ''
            }
        elif line.startswith('IMAGE:'):
            if current_step:
                current_step['image'] = line.replace('IMAGE:', '').strip()
        elif line.startswith('NOTE:'):
            if current_step:
                current_step['note'] = line.replace('NOTE:', '').strip()
    
    # Don't forget the last step
    if current_step:
        if current_section == 'desktop':
            guide['desktop_steps'].append(current_step)
        elif current_section == 'mobile':
            guide['mobile_steps'].append(current_step)
    
    return guide

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)