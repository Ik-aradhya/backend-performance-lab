from concurrent.futures import ThreadPoolExecutor
import asyncio
import requests
import time 
import httpx
from fastapi import FastAPI
block_seconds=0.3
app=FastAPI()

@app.get("/blocked")
async def blacked_handler():
    time.sleep(block_seconds)
    return {"mode":"blocked"}

@app.get("/fix")
async def fixed():
    await asyncio.to_thread(time.sleep,block_seconds )
    return {"mode":"threadpool-offload"}


@app.on_event("startup")
async def setup_thread_pool():
    loop = asyncio.get_running_loop()

    pool = ThreadPoolExecutor(max_workers=50)

    loop.set_default_executor(pool)

@app.get("/external")
async def external_service():
    await asyncio.sleep(0.3)
    return {"status": "done"}

@app.get("/async-http")
async def async_http():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://127.0.0.1:8000/external")
        return response.json()