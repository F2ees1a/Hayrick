"""
农田草垛视觉识别系统 - FastAPI后端
"""

import os
import io
import base64
import uuid
import sys
from typing import List

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import torch


# =========================
# 模型路径
# =========================
MODEL_PATH = r"C:\Users\shadow\.minimax-agent\projects\best.pt"
YOLOV5_PATH = r"C:\Users\shadow\PycharmProjects\Hayrick\yolov5"


model = None
model_loaded = False


# =========================
# 加载模型
# =========================
def load_model():
    global model, model_loaded

    try:
        print("正在加载YOLOv5模型...")

        if YOLOV5_PATH not in sys.path:
            sys.path.insert(0, YOLOV5_PATH)

        model = torch.hub.load(
            YOLOV5_PATH,
            "custom",
            path=MODEL_PATH,
            source="local"
        )

        model.conf = 0.25
        model_loaded = True

        print("模型加载成功")

    except Exception as e:
        print("模型加载失败:", e)
        model_loaded = False


# =========================
# FastAPI
# =========================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    load_model()


# =========================
# 健康检查
# =========================
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "model_loaded": model_loaded
    }


# =========================
# 图片处理
# =========================
def process_image(image: Image.Image, conf):

    if image.mode != "RGB":
        image = image.convert("RGB")

    model.conf = conf

    results = model(image)

    detections = []

    if len(results.xyxy[0]) > 0:
        for *box, confidence, cls in results.xyxy[0]:

            detections.append({
                "bbox": [float(x) for x in box],
                "confidence": float(confidence),
                "class": int(cls)
            })

    results.render()

    img = results.ims[0]

    buffer = io.BytesIO()
    Image.fromarray(img).save(buffer, format="JPEG")

    base64_img = base64.b64encode(buffer.getvalue()).decode()

    return base64_img, detections


# =========================
# 检测接口
# =========================
@app.post("/api/detect")
async def detect(
    files: List[UploadFile] = File(...),
    confidence: float = Form(0.25)
):

    if not model_loaded:
        raise HTTPException(500, "模型未加载")

    results_data = []

    for file in files:

        content = await file.read()

        image = Image.open(io.BytesIO(content))

        image_id = uuid.uuid4().hex[:8]

        processed_image, detections = process_image(image, confidence)

        results_data.append({
            "image_id": image_id,
            "original_filename": file.filename,
            "detected": len(detections) > 0,
            "detections": len(detections),
            "confidence": max([d["confidence"] for d in detections], default=0),
            "bbox": [d["bbox"] for d in detections],
            "processed_image": processed_image
        })

    return {
        "success": True,
        "message": "检测完成",
        "results": results_data
    }


# =========================
# 启动
# =========================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)