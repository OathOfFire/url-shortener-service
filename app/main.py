import secrets  #for generating random codes
import string  #letters and digits for codes

from fastapi import FastAPI, HTTPException  #Proper error handling
from fastapi.responses import RedirectResponse  #sends browser to another address
from pydantic import BaseModel, HttpUrl  #checks incoming data using FastAPI

app = FastAPI(title="URL Shortener")     #shows on /docs page

urls: dict[str, str] = {}   #dictionary storage mapping short codes to original URLs
                            #dict[str, str] means the keys and values are both strings
                            #Upgrade to SQlite later as data disappears when the server restarts

ALPHABET = string.ascii_letters + string.digits # 62 characers upper + lower + digits (26+26+10=62)




class ShortenRequest(BaseModel):
    url: HttpUrl #checks that incoming URl is real and valid, 422 error is not valid

#6 random char form ALPHABET into one string
#secrets > random as it is more secure and less predictable, but slower
#while loop handles collisions, if it already exists, try again
# 62^6 possible combinations, 56 billion, so collisions are unlikely, but just in case
def generate_code(length: int = 6) -> str:
    while True:
        code = "".join(secrets.choice(ALPHABET) for _ in range(length))
        if code not in urls:
            return code

#ping from browser to check if server is running, returns 200 OK and JSON {"status": "ok"}
@app.get("/health")
def health():
    return {"status": "ok"}

#post creates something new, so 201 Created is the correct status code
@app.post("/shorten", status_code=201)
def shorten(body: ShortenRequest):       #parameter to trigger validation
    code = generate_code()
    urls[code] = str(body.url)           #Coverts Pydantic's URL object into plain text string for storage
    return {"code": code, "short_path": f"/{code}", "url": urls[code]}

#turns the dicitonary into a list of objects, each with a code and url, so it can be returned as JSON
@app.get("/urls")
def list_urls():
    return [{"code": c, "url": u} for c, u in urls.items()]

#{code} is a path parameter anything after the / gets passed as code
@app.get("/{code}")
def redirect(code: str):
    if code not in urls:
        #unkown code, return 404 Not Found error with a message
        raise HTTPException(status_code=404, detail="Code not found")
    return RedirectResponse(urls[code])

#delete removes a code from the dictionary, 204 means sucess nothing to send back, 404 if code not found
@app.delete("/{code}", status_code=204)
def delete(code: str):
    if code not in urls:
        raise HTTPException(status_code=404, detail="Code not found")
    del urls[code]