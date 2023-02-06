from fastapi.responses import JSONResponse, Response
from typing import Union
from Dao.Model import UserModel, ConfigModel


class ResponseBuild:
    @staticmethod
    def success(*, code: int = 200, message: str = "操作成功~",
                data: Union[list, dict, str, UserModel, ConfigModel]) -> Response:
        return JSONResponse(
            status_code=code,
            content={
                "code": code,
                "message": message,
                "data": data,
            }
        )

    @staticmethod
    def fail(*, data: str = None, message: str = "操作失败~", code: int = 200) -> Response:
        return JSONResponse(
            status_code=code,
            content={
                'code': code,
                'message': message,
                'data': data,
            }
        )
