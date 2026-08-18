from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI()

# Разрешаем запросы из мобильного приложения
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Хранилище активных WebSocket-подключений: {username: websocket}
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, username: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[username] = websocket

    def disconnect(self, username: str):
        if username in self.active_connections:
            del self.active_connections[username]

    async def send_personal_message(self, message: dict, recipient: str):
        if recipient in self.active_connections:
            await self.active_connections[recipient].send_text(json.dumps(message))

manager = ConnectionManager()

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await manager.connect(username, websocket)
    try:
        while True:
            # Ожидаем сообщение от клиента
            data_str = await websocket.receive_text()
            data = json.loads(data_str)
            
            target = data.get("target")
            msg_type = data.get("type", "chat") # 'chat', 'call-offer', 'call-answer', 'ice-candidate'
            
            # Пересылаем пакет адресату
            payload = {
                "sender": username,
                "type": msg_type,
                "content": data.get("content")
            }
            await manager.send_personal_message(payload, target)
            
    except WebSocketDisconnect:
        manager.disconnect(username)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)