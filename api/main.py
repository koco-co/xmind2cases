# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.config import settings
from api.routes import health, records
from api.core.exceptions import Xmind2CasesError
from fastapi.responses import JSONResponse
from fastapi import Request


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/docs" if settings.DOCS_ENABLED else None,
    redoc_url="/redoc" if settings.DOCS_ENABLED else None,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health.router)
app.include_router(records.router, prefix=settings.API_V1_PREFIX)


# 全局异常处理器
@app.exception_handler(Xmind2CasesError)
async def xmind2cases_exception_handler(request: Request, exc: Xmind2CasesError):
    """处理所有自定义异常"""
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": type(exc).__name__,
                "message": exc.message,
                "detail": exc.detail,
            }
        },
    )


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    from pathlib import Path

    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path("data").mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG
    )
