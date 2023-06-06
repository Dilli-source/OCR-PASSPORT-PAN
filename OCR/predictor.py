# This is the file that implements a flask server to do inferences. It's the file that you will modify to
# implement the scoring for your own algorithm.

from __future__ import print_function
import os
from fastapi import FastAPI,Response,Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import warnings
import boto3
from PP_PN_Read import s3_dowloader_fn
warnings.filterwarnings("ignore", message=r"Passing", category=FutureWarning)

# The fastapi app for serving predictions
app = FastAPI()


@app.get("/ping")
async def ping():
    """Determine if the container is working and healthy. In this sample container, we declare
    it healthy if we can load the model successfully."""
    try:
        status = 200
    except Exception as e:
        print("error", e)
    return Response(content='\n', status_code=200, media_type='application/json')


@app.post("/invocations")
async def transformation(request:Request):
    """function will respond to  POST request
    if the request's content is in application/json then returns the suitable response else sends back an error"""
    content_type = request.headers.get("content-type", None)
    print(request)
    if content_type == 'application/json':
        data = await request.json()
        trail_id = data['trail_id']
        s3_url = data['s3_url']
        id_type=data['id_type']
        if trail_id:
            result=s3_dowloader_fn(trail_id,s3_url,id_type)
            json_compatible_item_data = jsonable_encoder(result)
            response_data = JSONResponse(content=json_compatible_item_data,status_code=200)

        else :
            response_data = Response(content='The \'trail_id\' key is not found ', status_code=415, media_type='text/plain')

    else:
        response_data = Response(content='This predictor accepts only json data', status_code=415, media_type='text/plain')

    return response_data


