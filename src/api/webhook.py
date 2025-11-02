"""
飞书 Webhook 端点。

处理来自飞书的 Webhook 事件，包括 URL 验证挑战和消息事件。
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..models import FeishuWebhookEvent, WebhookChallenge, WebhookResponse
from ..services import handle_feishu_event

router = APIRouter()


@router.post("/feishu", response_model=WebhookResponse)
async def feishu_webhook(request: Request) -> JSONResponse:
    """
    飞书 Webhook 端点。

    此端点接收并处理来自飞书的 Webhook 事件。
    它处理两种类型的请求：

    1. URL 验证：注册 Webhook 时，飞书会发送一个挑战值需要回传。
    2. 事件通知：实际的 Webhook 事件（消息、交互等）。

    端点会自动检测请求类型并相应地响应。

    Args:
        request: 包含 Webhook 负载的 FastAPI 请求对象

    Returns:
        JSONResponse: 对于验证请求，返回挑战值。对于事件请求，返回处理状态。

    Example:
        URL 验证：
        ```
        POST / webhook / feishu
        {"challenge": "ajls384kdjx98XX", "token": "xxxxxx", "type": "url_verification"}
        Response: {"challenge": "ajls384kdjx98XX"}
        ```

        事件通知：
        ```
        POST /webhook/feishu
        {
            "schema": "2.0",
            "header": {
                "event_id": "...",
                "event_type": "im.message.receive_v1",
                ...
            },
            "event": {...}
        }
        Response: {"success": true, "message": "..."}
        ```
    """
    # 解析原始 JSON 请求体
    body = await request.json()

    # 检查这是否是 URL 验证挑战
    if "challenge" in body and body.get("type") == "url_verification":
        # 解析为挑战并返回挑战值
        challenge = WebhookChallenge(**body)
        return JSONResponse(content={"challenge": challenge.challenge})

    # 解析为常规 Webhook 事件
    try:
        event = FeishuWebhookEvent(**body)

        # 通过服务层处理事件
        result = await handle_feishu_event(event.model_dump())

        return JSONResponse(
            content=WebhookResponse(
                success=result.get("success", True),
                message=result.get("message", "事件处理成功"),
            ).model_dump()
        )

    except Exception as e:
        # 记录错误（在生产环境中使用适当的日志记录）
        print(f"处理 Webhook 时出错: {e}")

        return JSONResponse(
            status_code=500,
            content=WebhookResponse(
                success=False,
                message=f"处理 Webhook 时出错: {str(e)}",
            ).model_dump(),
        )
