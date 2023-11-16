import fastapi


app = fastapi.FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World, this is a fastapi app"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, debug=True)
