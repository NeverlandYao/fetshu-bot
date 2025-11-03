"""
飞书开放平台服务。

提供获取租户访问令牌和发送/回复消息的能力。
"""

import json
import logging
import time
from typing import Any, Dict, Optional

from httpx import AsyncClient

from ..core import get_settings

logger = logging.getLogger(__name__)


class FeishuService:
    """飞书服务类。"""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_url = self.settings.FEISHU_API_BASE_URL.rstrip("/")
        self.app_id = self.settings.FEISHU_APP_ID
        self.app_secret = self.settings.FEISHU_APP_SECRET
        self.timeout = self.settings.FEISHU_TIMEOUT
        # 简单的内存令牌缓存
        self._tenant_token: Optional[str] = None
        self._tenant_token_expires_at: float = 0.0

    async def _fetch_tenant_access_token(self) -> Optional[str]:
        """从飞书获取租户访问令牌。"""
        url = f"{self.base_url}/open-apis/auth/v3/tenant_access_token/internal"
        payload = {"app_id": self.app_id, "app_secret": self.app_secret}

        try:
            async with AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=payload)
                data = resp.json()

                if resp.status_code != 200 or data.get("code") != 0:
                    logger.error(
                        f"获取租户令牌失败: status={resp.status_code}, code={data.get('code')}, msg={data.get('msg')}"
                    )
                    return None

                token = data.get("tenant_access_token")
                expire = data.get("expire", 0)
                # 设置过期时间（提前 60 秒刷新）
                self._tenant_token = token
                self._tenant_token_expires_at = time.time() + max(0, int(expire) - 60)
                logger.info("已获取飞书租户访问令牌")
                return token
        except Exception as e:
            logger.error(f"获取租户令牌异常: {e}")
            return None

    async def _get_tenant_access_token(self) -> Optional[str]:
        """获取可用的租户访问令牌，必要时刷新。"""
        if self._tenant_token and time.time() < self._tenant_token_expires_at:
            return self._tenant_token

        if not self.app_id or not self.app_secret:
            logger.error("未配置 FEISHU_APP_ID 或 FEISHU_APP_SECRET")
            return None

        return await self._fetch_tenant_access_token()

    async def reply_to_message(self, message_id: str, text: str) -> Dict[str, Any]:
        """回复指定消息。

        Args:
            message_id: 要回复的消息 ID（来自事件）
            text: 回复的纯文本内容

        Returns:
            Dict: 包含 success 与可选的 error 信息
        """
        token = await self._get_tenant_access_token()
        if not token:
            return {"success": False, "error": "无法获取租户访问令牌"}

        url = f"{self.base_url}/open-apis/im/v1/messages/{message_id}/reply"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        # 飞书要求 content 为 JSON 字符串
        content = json.dumps({"text": text})
        payload = {"content": content, "msg_type": "text"}

        try:
            async with AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, headers=headers, json=payload)
                data = resp.json()

                if resp.status_code != 200 or data.get("code") != 0:
                    logger.error(
                        f"回复消息失败: status={resp.status_code}, code={data.get('code')}, msg={data.get('msg')}"
                    )
                    return {"success": False, "error": data.get("msg")}

                return {"success": True}
        except Exception as e:
            logger.error(f"回复消息异常: {e}")
            return {"success": False, "error": str(e)}

    async def send_message_to_chat(self, chat_id: str, text: str) -> Dict[str, Any]:
        """向指定群聊发送消息。"""
        token = await self._get_tenant_access_token()
        if not token:
            return {"success": False, "error": "无法获取租户访问令牌"}

        url = f"{self.base_url}/open-apis/im/v1/messages?receive_id_type=chat_id"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        content = json.dumps({"text": text})
        payload = {"receive_id": chat_id, "content": content, "msg_type": "text"}

        try:
            async with AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, headers=headers, json=payload)
                data = resp.json()

                if resp.status_code != 200 or data.get("code") != 0:
                    logger.error(
                        f"发送消息失败: status={resp.status_code}, code={data.get('code')}, msg={data.get('msg')}"
                    )
                    return {"success": False, "error": data.get("msg")}

                return {"success": True}
        except Exception as e:
            logger.error(f"发送消息异常: {e}")
            return {"success": False, "error": str(e)}


# 全局服务实例
feishu_service = FeishuService()
