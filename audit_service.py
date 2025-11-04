"""
Audit logging service for tracking queries, provider usage, and compliance.
"""

import logging
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from models import AuditLog, ConversationMessage

logger = logging.getLogger(__name__)


class AuditService:
    """Service for audit logging and compliance tracking."""

    def __init__(self, session: Session):
        self.session = session

    def log_query(
        self,
        query_text: str,
        query_type: str,  # chat, bi_bot, embedding
        provider_name: str,
        provider_model: str,
        report_id: Optional[str] = None,
        chunks_used: int = 0,
        processing_time_ms: Optional[float] = None,
        response_length: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """Log a query to audit trail."""
        try:
            audit_log = AuditLog(
                query_text=query_text,
                query_type=query_type,
                provider_name=provider_name,
                provider_model=provider_model,
                report_id=report_id,
                chunks_used=chunks_used,
                processing_time_ms=processing_time_ms,
                response_length=response_length,
                success=success,
                error_message=error_message,
                session_id=session_id,
            )

            self.session.add(audit_log)
            self.session.commit()

            logger.info(
                f"Logged {query_type} query using {provider_name}/{provider_model}"
            )
            return audit_log.id

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error logging query: {e}")
            raise

    def save_conversation_message(
        self,
        session_id: str,
        message_index: int,
        role: str,  # user, assistant
        content: str,
        provider_used: Optional[str] = None,
        model_used: Optional[str] = None,
        chunks_referenced: Optional[List[str]] = None,
    ) -> str:
        """Save a conversation message."""
        try:
            message = ConversationMessage(
                session_id=session_id,
                message_index=message_index,
                role=role,
                content=content,
                provider_used=provider_used,
                model_used=model_used,
                chunks_referenced=json.dumps(chunks_referenced) if chunks_referenced else None,
            )

            self.session.add(message)
            self.session.commit()

            return message.id

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error saving conversation message: {e}")
            raise

    def get_conversation_history(
        self,
        session_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve conversation history."""
        try:
            messages = (
                self.session.query(ConversationMessage)
                .filter(ConversationMessage.session_id == session_id)
                .order_by(ConversationMessage.created_at)
                .limit(limit)
                .all()
            )

            return [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "provider": msg.provider_used,
                    "model": msg.model_used,
                    "timestamp": msg.created_at.isoformat(),
                }
                for msg in messages
            ]

        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            return []

    def get_audit_logs(
        self,
        limit: int = 100,
        query_type: Optional[str] = None,
        provider_name: Optional[str] = None,
        report_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve audit logs with optional filtering."""
        try:
            query = self.session.query(AuditLog)

            if query_type:
                query = query.filter(AuditLog.query_type == query_type)

            if provider_name:
                query = query.filter(AuditLog.provider_name == provider_name)

            if report_id:
                query = query.filter(AuditLog.report_id == report_id)

            logs = (
                query.order_by(AuditLog.created_at.desc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "id": log.id,
                    "query_type": log.query_type,
                    "provider": log.provider_name,
                    "model": log.provider_model,
                    "success": log.success,
                    "processing_time_ms": log.processing_time_ms,
                    "chunks_used": log.chunks_used,
                    "timestamp": log.created_at.isoformat(),
                }
                for log in logs
            ]

        except Exception as e:
            logger.error(f"Error retrieving audit logs: {e}")
            return []

    def get_provider_usage_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get usage statistics by provider."""
        try:
            query = self.session.query(AuditLog)

            if start_date:
                query = query.filter(AuditLog.created_at >= start_date)

            if end_date:
                query = query.filter(AuditLog.created_at <= end_date)

            logs = query.all()

            stats = {}
            for log in logs:
                provider = log.provider_name
                if provider not in stats:
                    stats[provider] = {
                        "queries": 0,
                        "successful": 0,
                        "failed": 0,
                        "total_time_ms": 0,
                        "avg_time_ms": 0,
                    }

                stats[provider]["queries"] += 1
                if log.success:
                    stats[provider]["successful"] += 1
                else:
                    stats[provider]["failed"] += 1

                if log.processing_time_ms:
                    stats[provider]["total_time_ms"] += log.processing_time_ms

            # Calculate averages
            for provider in stats:
                if stats[provider]["queries"] > 0:
                    stats[provider]["avg_time_ms"] = (
                        stats[provider]["total_time_ms"]
                        / stats[provider]["queries"]
                    )

            return stats

        except Exception as e:
            logger.error(f"Error calculating usage stats: {e}")
            return {}

    def delete_old_logs(self, days_to_keep: int = 90) -> int:
        """Delete audit logs older than specified days (for compliance)."""
        try:
            from datetime import timedelta

            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

            deleted_count = (
                self.session.query(AuditLog)
                .filter(AuditLog.created_at < cutoff_date)
                .delete()
            )

            self.session.commit()

            logger.info(
                f"Deleted {deleted_count} audit logs older than {days_to_keep} days"
            )
            return deleted_count

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting old logs: {e}")
            raise