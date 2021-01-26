from backend import s3
from werkzeug.utils import secure_filename

from typing import List

from fastapi import FastAPI, File, UploadFile, HTTPException, Request

from fastapi.responses import HTMLResponse, StreamingResponse
import logging, re

app = FastAPI()


@app.post("/uploadfile/")
async def create_upload_files(files: List[UploadFile] = File(...)):
    file = files[0]
    client = s3.get_s3_client()
    await s3.upload_file_to_s3(client, file)
    # return {"file_name": file.filename}
    return StreamingResponse(i for i in s3.upload_result)
    # return {"filenames": [file.filename for file in files]}

@app.get("/")
async def main():
    content = get_home_page()
    return HTMLResponse(content=content)

@app.get("/response")
async def get_response():
    StreamingResponse( i for i in s3.upload_result)

@app.get("/stream/{video_name}")
async def stream_video(video_name: str, request: Request):


    # from backend import settings
    storage = s3.get_s3_client()
    media_stream = s3.get_video_object(key=video_name)
    # media_stream = storage.get_object(Bucket=settings.BUCKET_NAME, Key="test_video.mp4")

    full_content = media_stream['ContentLength']
    headers = {
        "Accept-Ranges": "bytes",
    }
    print(request.headers)

    range_header = request.headers.get('Range', None)

    if range_header:
        byte_start, byte_end, length = get_byte_range(range_header)
        if byte_end:
            media_stream = s3.get_video_object( key="test_video.mp4", range=f'bytes={byte_start}-{byte_end}')
            end = byte_start + length - 1
            headers['Content-Range'] = f'bytes {byte_start}-{end}/{full_content}'
            headers['Accept-Ranges'] = 'bytes'
            headers['Content-Transfer-Encoding'] = 'binary'
            headers['Connection'] = 'Keep-Alive'
            headers['Content-Type'] = media_stream['ContentType']
            if byte_end == 1:
                headers['Content-Length'] = '1'
            else:
                headers['Content-Length'] = str(media_stream['ContentLength'])

            return StreamingResponse(
                media_stream['Body'].iter_chunks(),
                headers=headers,
                status_code=206,
            )
    # print(range_header, "No byte end")
    headers['Content-Type'] = media_stream['ContentType']
    headers['Content-Length'] = str(media_stream['ContentLength'])
    return StreamingResponse(media_stream['Body'].iter_chunks(), headers=headers, status_code=200)

    # return HTMLResponse(content=html_content)


def get_byte_range(range_header: str):

    range_header = re.search('(\d+)-(\d*)', range_header).groups()
    byte1, byte2, length = 0, None, 0
    if range_header[0]:
        byte1 = int(range_header[0])
    if range_header[1]:
        byte2 = int(range_header[1])
        length = byte2 + 1 - byte1

    return byte1, byte2, length


def get_home_page():

    return """
<body>
<form action="/uploadfile/" enctype="multipart/form-data" method="post">
<input name="files" type="file" multiple>
<input type="submit">
</form>

<div id="progress_wrapper" class="d-none">
  <label id="progress_status"></label>
  <div class="progress mb-3">
    <div id="progress" class="progress-bar" role="progressbar" aria-valuenow="25" aria-valuemin="0" aria-valuemax="100"></div>
  </div>
</div>

<div id="alert_wrapper"></div>
</body>
    """
