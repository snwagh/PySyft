# stdlib
import json
import lzma
import os
import sys

# third party
from fastapi import Body
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from loguru import logger
from typing_extensions import Annotated

# relative
from .models import ResponseModel
from .veilid_core import VeilidConnectionSingleton
from .veilid_core import app_call
from .veilid_core import app_message
from .veilid_core import generate_dht_key
from .veilid_core import healthcheck
from .veilid_core import retrieve_dht_key

# Logging Configuration
log_level = os.getenv("APP_LOG_LEVEL", "INFO").upper()
logger.remove()
logger.add(sys.stderr, colorize=True, level=log_level)

app = FastAPI(title="Veilid")
veilid_conn = VeilidConnectionSingleton()


@app.get("/", response_model=ResponseModel)
async def read_root() -> ResponseModel:
    return ResponseModel(message="Veilid has started")


@app.get("/healthcheck", response_model=ResponseModel)
async def healthcheck_endpoint() -> ResponseModel:
    res = await healthcheck()
    if res:
        return ResponseModel(message="OK")
    else:
        return ResponseModel(message="FAIL")


@app.post("/generate_dht_key", response_model=ResponseModel)
async def generate_dht_key_endpoint() -> ResponseModel:
    try:
        res = await generate_dht_key()
        return ResponseModel(message=res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate DHT key: {e}")


@app.get("/retrieve_dht_key", response_model=ResponseModel)
async def retrieve_dht_key_endpoint() -> ResponseModel:
    try:
        res = await retrieve_dht_key()
        return ResponseModel(message=res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/app_message", response_model=ResponseModel)
async def app_message_endpoint(
    request: Request, dht_key: Annotated[str, Body()], message: Annotated[bytes, Body()]
) -> ResponseModel:
    try:
        res = await app_message(dht_key=dht_key, message=message)
        return ResponseModel(message=res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/app_call")
async def app_call_endpoint(
    request: Request, dht_key: Annotated[str, Body()], message: Annotated[bytes, Body()]
) -> dict[str, str]:
    return await app_call(dht_key=dht_key, message=message)


@app.api_route("/proxy", methods=["GET", "POST", "PUT"])
async def proxy(request: Request) -> dict[str, str]:
    logger.info("Proxying request")
    request_data = await request.json()
    logger.info(f"Request URL: {request_data}")
    dht_key = request_data.get("dht_key")
    request_data.pop("dht_key")
    logger.info(f"Request URL: {request_data}")
    message = json.dumps(request_data).encode()
    logger.info(f"Final Message: {message!r}")
    res = await app_call(dht_key=dht_key, message=message)
    logger.info(f"Response: {res}")
    decompressed_res = lzma.decompress(res)
    return Response(decompressed_res, media_type="application/octet-stream")


@app.on_event("startup")
async def startup_event() -> None:
    try:
        await veilid_conn.initialize_connection()
    except Exception as e:
        logger.exception(f"Failed to connect to Veilid: {e}")
        raise e


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await veilid_conn.release_connection()
