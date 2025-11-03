"""
Webhook 事件处理服务。

本模块包含处理飞书 Webhook 事件的业务逻辑，集成 Coze AI 服务。
"""

import json
import logging
import time
from typing import Any, Dict, Optional

from .coze_service import coze_service
from .feishu_service import feishu_service

logger = logging.getLogger(__name__)

# 简单的事件去重缓存（避免飞书重试或循环导致重复回复）
_processed_events: dict[str, float] = {}
_EVENT_TTL_SECONDS = 600  # 10 分钟


def _is_duplicate_event(event_id: str) -> bool:
    """检查事件是否已处理并清理过期记录。"""
    now = time.time()

    # 清理过期的事件记录
    expired = [eid for eid, ts in _processed_events.items() if ts + _EVENT_TTL_SECONDS < now]
    for eid in expired:
        _processed_events.pop(eid, None)

    if not event_id:
        return False

    if event_id in _processed_events:
        return True

    _processed_events[event_id] = now
    return False


def extract_message_content(event: Dict[str, Any]) -> Optional[str]:
    """
    从飞书事件中提取消息内容。

    Args:
        event: 飞书 Webhook 事件数据

    Returns:
        str: 提取的消息内容，如果无法提取则返回 None
    """
    try:
        # 获取事件数据
        event_data = event.get("event", {})
        message = event_data.get("message", {})

        # 提取消息内容
        content = message.get("content", "")
        if isinstance(content, str):
            try:
                # 尝试解析 JSON 格式的内容
                content_data = json.loads(content)
                return content_data.get("text", "")
            except json.JSONDecodeError:
                # 如果不是 JSON 格式，直接返回内容
                return content

        return None
    except Exception as e:
        logger.warning(f"提取消息内容失败: {e}")
        return None


def extract_user_info(event: Dict[str, Any]) -> Dict[str, str]:
    """
    从飞书事件中提取用户信息。

    Args:
        event: 飞书 Webhook 事件数据

    Returns:
        Dict[str, str]: 用户信息字典
    """
    try:
        event_data = event.get("event", {})
        sender = event_data.get("sender", {})

        return {
            "user_id": sender.get("sender_id", {}).get("user_id", ""),
            "open_id": sender.get("sender_id", {}).get("open_id", ""),
            "union_id": sender.get("sender_id", {}).get("union_id", ""),
        }
    except Exception as e:
        logger.warning(f"提取用户信息失败: {e}")
        return {}


def extract_sender_type(event: Dict[str, Any]) -> str:
    """提取发送者类型（user/app/bot 等）。"""
    try:
        return event.get("event", {}).get("sender", {}).get("sender_type", "")
    except Exception:
        return ""


def extract_message_meta(event: Dict[str, Any]) -> Dict[str, str]:
    """
    从事件中提取消息元信息（message_id, chat_id）。

    Args:
        event: 飞书 Webhook 事件数据

    Returns:
        Dict[str, str]: 包含 message_id 和 chat_id 的字典
    """
    try:
        event_data = event.get("event", {})
        message = event_data.get("message", {})
        return {
            "message_id": message.get("message_id", ""),
            "chat_id": message.get("chat_id", ""),
        }
    except Exception:
        return {"message_id": "", "chat_id": ""}


def normalize_ai_text(content: Optional[str]) -> str:
    """
    规范化 AI 输出，仅返回第一句话。

    - 如果内容是 JSON 串并包含 `output` 字段，则使用该字段
    - 使用常见句子分隔符提取第一句
    - 去除多余空白
    """
    text = (content or "").strip()
    if not text:
        return ""

    # 如果是 JSON 字符串，尝试取 output
    if text.startswith("{"):
        try:
            data = json.loads(text)
            if isinstance(data, dict) and "output" in data and isinstance(data["output"], str):
                text = data["output"].strip()
        except json.JSONDecodeError:
            pass

    # 依据常见分隔符截取第一句话
    separators = ["。", "！", "？", "!", "?", "\n"]
    first_end = len(text)
    for sep in separators:
        idx = text.find(sep)
        if idx != -1:
            first_end = min(first_end, idx + (0 if sep == "\n" else 1))
    first_sentence = text[:first_end].strip()
    return first_sentence or text


async def handle_feishu_event(event: dict[str, Any]) -> dict[str, Any]:
    """
    处理飞书 Webhook 事件。

    这个函数现在集成了 Coze AI 服务，能够：
    - 解析飞书消息事件
    - 提取用户输入内容
    - 调用 Coze AI 获取智能回复
    - 返回处理结果

    Args:
        event: 已解析的飞书 Webhook 事件数据

    Returns:
        dict: 包含处理结果和 AI 响应的字典

    Example:
        >>> result = await handle_feishu_event({"header": {...}, "event": {...}})
        >>> assert result["success"] is True
        >>> assert "ai_response" in result
    """
    # 提取事件元数据
    header = event.get("header", {})
    event_type = header.get("event_type", "unknown")
    event_id = header.get("event_id", "unknown")

    logger.info(f"正在处理飞书事件: type={event_type}, id={event_id}")

    # 去重：避免重复事件或飞书重试导致的二次处理
    if _is_duplicate_event(event_id):
        logger.info(f"检测到重复事件，忽略: id={event_id}")
        return {
            "success": True,
            "event_type": event_type,
            "event_id": event_id,
            "message": "重复事件已忽略",
        }

    # 处理消息接收事件
    if event_type == "im.message.receive_v1":
        # 忽略机器人/应用自身消息，避免自我回复触发循环
        sender_type = extract_sender_type(event)
        if sender_type and sender_type != "user":
            logger.info(f"忽略非用户消息: sender_type={sender_type}")
            return {
                "success": True,
                "event_type": event_type,
                "event_id": event_id,
                "message": "忽略非用户消息",
            }
        # 提取消息内容
        message_content = extract_message_content(event)
        if not message_content:
            logger.warning("无法提取消息内容")
            return {
                "success": False,
                "event_type": event_type,
                "event_id": event_id,
                "error": "无法提取消息内容",
            }

        # 提取用户信息
        user_info = extract_user_info(event)
        logger.info(f"收到用户消息: {message_content[:100]}...")

        try:
            # 调用 Coze AI 服务
            ai_response = await coze_service.chat_with_workflow(
                user_input=message_content, conversation_name="飞书机器人对话"
            )

            if ai_response.success:
                logger.info("Coze AI 响应成功")
                # 回复飞书消息
                meta = extract_message_meta(event)
                reply_text = normalize_ai_text(ai_response.content) or "(无内容)"
                feishu_result = await feishu_service.reply_to_message(
                    message_id=meta.get("message_id", ""),
                    text=reply_text,
                )

                return {
                    "success": True,
                    "event_type": event_type,
                    "event_id": event_id,
                    "message": "消息已处理，AI 响应已生成并已回复",
                    "user_input": message_content,
                    "ai_response": {
                        "content": ai_response.content,
                        "debug_url": ai_response.debug_url,
                        "conversation_id": ai_response.conversation_id,
                    },
                    "feishu_reply": feishu_result,
                    "user_info": user_info,
                }
            else:
                logger.error(f"Coze AI 响应失败: {ai_response.error_message}")
                return {
                    "success": False,
                    "event_type": event_type,
                    "event_id": event_id,
                    "error": f"AI 处理失败: {ai_response.error_message}",
                    "user_input": message_content,
                    "user_info": user_info,
                }

        except Exception as e:
            logger.error(f"处理 AI 响应时发生错误: {e}")
            return {
                "success": False,
                "event_type": event_type,
                "event_id": event_id,
                "error": f"AI 处理异常: {str(e)}",
                "user_input": message_content,
                "user_info": user_info,
            }

    # 处理其他类型的事件
    else:
        logger.info(f"收到非消息事件: {event_type}")
        return {
            "success": True,
            "event_type": event_type,
            "event_id": event_id,
            "message": f"事件类型 {event_type} 已接收，暂不处理",
        }
