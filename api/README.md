# xmind2cases API 文档

## 快速开始

### 启动服务

```bash
# 开发环境
uvicorn api.main:app --reload

# 生产环境
uvicorn api.main:app --host 0.0.0.0 --workers 4
```

### 访问文档

启动后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 概述

FastAPI 异步 REST API，用于 XMind 到测试用例的转换和管理。

## 技术栈

- **FastAPI** 0.115+
- **SQLAlchemy** 2.0 (async)
- **Pydantic** v2

## 端点列表

### 健康检查

#### GET /health
检查服务健康状态

**响应:**
```json
{
  "status": "healthy",
  "timestamp": "2026-03-03T12:00:00Z"
}
```

#### GET /health/database
检查数据库连接

**响应:**
```json
{
  "status": "healthy",
  "connection": "ok"
}
```

### 记录管理

#### GET /api/v1/records
获取记录列表

**查询参数:**
- `skip`: 跳过记录数（默认 0）
- `limit`: 返回记录数（默认 20）

**响应:** RecordResponse[]

#### POST /api/v1/records
上传 XMind 文件并创建记录

**请求体:** multipart/form-data
- `file`: XMind 文件

**响应:** RecordResponse

#### GET /api/v1/records/{id}
获取记录详情

**参数:**
- `id`: 记录 ID

**响应:** RecordDetail

## 开发

### 运行测试

```bash
pytest tests/api/ -v
```

### 代码格式化

```bash
ruff format api/
ruff check api/
```
