import cv2
import base64
import asyncio
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO

app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

camera = None
generic_model = YOLO("yolov8n.pt")  # Default object detection
currency_model = YOLO("best.pt")  # Custom trained model
detection_memory = {}  # {label: (last_seen_time, direction)}

@app.websocket("/ws/cam")
async def webcam_feed(websocket: WebSocket):
    global camera, detection_memory
    await websocket.accept()
    try:
        camera = cv2.VideoCapture(0)
        query_params = dict(pair.split('=') for pair in websocket.url.query.split('&')) if websocket.url.query else {}
        model_type = query_params.get("model", "generic")  # Default to generic if not specified

        while True:
            ret, frame = camera.read()
            if not ret:
                break

            # Select model
            model = currency_model if model_type == "currency" else generic_model
            results = model(frame, verbose=False)[0]
            detection = None
            frame_h, frame_w = frame.shape[:2]

            # Draw grid lines for direction (optional, especially for currency)
            cv2.line(frame, (frame_w // 3, 0), (frame_w // 3, frame_h), (0, 255, 255), 2)
            cv2.line(frame, (2 * frame_w // 3, 0), (2 * frame_w // 3, frame_h), (0, 255, 255), 2)

            for box in results.boxes:
                cls_id = int(box.cls[0])
                label = model.names[cls_id]
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                x_center = (x1 + x2) / 2

                direction = "left" if x_center < frame_w / 3 else "right" if x_center > 2 * frame_w / 3 else "ahead"

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    frame,
                    f"{label} ({direction})",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )

                now = time.time()
                if label in detection_memory:
                    last_seen, last_dir = detection_memory[label]
                    if direction == last_dir and now - last_seen >= 2:
                        detection = f"{label} on {direction}"
                        detection_memory[label] = (now, direction)
                else:
                    detection_memory[label] = (now, direction)

            _, buffer = cv2.imencode(".jpg", frame)
            frame_b64 = base64.b64encode(buffer).decode("utf-8")

            payload = {"frame": frame_b64, "detection": detection}
            await websocket.send_json(payload)

            await asyncio.sleep(0.03)  # ~30 fps

    except WebSocketDisconnect:
        print("🔌 Client disconnected cleanly")
    except Exception as e:
        print("⚠️ Error:", e)
    finally:
        if camera and camera.isOpened():
            camera.release()
            camera = None
        cv2.destroyAllWindows()
        if not websocket.client_state.name == "DISCONNECTED":
            await websocket.close()
        print("✅ Camera released, socket closed")

# import cv2
# import base64
# import asyncio
# import time
# from fastapi import FastAPI, WebSocket, WebSocketDisconnect
# from fastapi.middleware.cors import CORSMiddleware
# from ultralytics import YOLO  # pip install ultralytics

# app = FastAPI()

# # Allow frontend requests
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# camera = None
# model = YOLO("yolov8n.pt")  # COCO pre-trained tiny model for speed

# detection_memory = {}  # {label: (last_seen_time, direction)}

# @app.websocket("/ws/cam")
# async def webcam_feed(websocket: WebSocket):
#     global camera, detection_memory
#     await websocket.accept()

#     try:
#         camera = cv2.VideoCapture(0)
#         while True:
#             ret, frame = camera.read()
#             if not ret:
#                 break

#             # Run YOLO inference
#             results = model(frame, verbose=False)[0]
#             detection = None
#             frame_h, frame_w = frame.shape[:2]

#             # Draw grid lines (divide into 3 equal vertical sections)
#             cv2.line(frame, (frame_w // 3, 0), (frame_w // 3, frame_h), (0, 255, 255), 2)
#             cv2.line(frame, (2 * frame_w // 3, 0), (2 * frame_w // 3, frame_h), (0, 255, 255), 2)

#             for box in results.boxes:
#                 cls_id = int(box.cls[0])
#                 label = model.names[cls_id]
#                 x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
#                 x_center = (x1 + x2) / 2

#                 # Decide direction
#                 if x_center < frame_w / 3:
#                     direction = "left"
#                 elif x_center > 2 * frame_w / 3:
#                     direction = "right"
#                 else:
#                     direction = "ahead"

#                 # Draw bounding box + label
#                 cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
#                 cv2.putText(
#                     frame,
#                     f"{label} ({direction})",
#                     (x1, y1 - 10),
#                     cv2.FONT_HERSHEY_SIMPLEX,
#                     0.6,
#                     (0, 255, 0),
#                     2,
#                 )

#                 # Track detection persistence
#                 now = time.time()
#                 if label in detection_memory:
#                     last_seen, last_dir = detection_memory[label]
#                     if direction == last_dir and now - last_seen >= 2:
#                         detection = f"{label} on {direction}"
#                         detection_memory[label] = (now, direction)
#                 else:
#                     detection_memory[label] = (now, direction)

#             # Encode annotated frame
#             _, buffer = cv2.imencode(".jpg", frame)
#             frame_b64 = base64.b64encode(buffer).decode("utf-8")

#             # Send frame + detection
#             payload = {"frame": frame_b64, "detection": detection}
#             await websocket.send_json(payload)

#             await asyncio.sleep(0.03)  # ~30 fps

#     except WebSocketDisconnect:
#         print("🔌 Client disconnected cleanly")
#     except Exception as e:
#         print("⚠️ Error:", e)
#     finally:
#         if camera and camera.isOpened():
#             camera.release()
#             camera = None
#         cv2.destroyAllWindows()
#         if not websocket.client_state.name == "DISCONNECTED":
#             await websocket.close()
#         print("✅ Camera released, socket closed")
