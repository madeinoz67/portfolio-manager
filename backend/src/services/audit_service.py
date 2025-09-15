"""
Audit service for capturing and logging all portfolio and transaction events.
Provides comprehensive audit trail for administrative oversight.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.models.audit_log import AuditLog, AuditEventType
from src.models.user import User
from src.models.portfolio import Portfolio
from src.models.transaction import Transaction
from src.utils.datetime_utils import now

logger = logging.getLogger(__name__)


class AuditService:
    """
    Service for creating audit log entries for all portfolio and transaction events.

    Captures comprehensive event information including user context, entity details,
    and additional metadata for administrative oversight and user accountability.
    """

    def __init__(self, db_session: Session):
        """Initialize the audit service with a database session."""
        self.db = db_session

    def create_audit_entry(
        self,
        event_type: AuditEventType,
        event_description: str,
        user_id: str,
        entity_type: str,
        entity_id: str,
        event_metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLog]:
        """
        Create a generic audit log entry.

        Args:
            event_type: Type of event being logged
            event_description: Human-readable description of the event
            user_id: ID of the user who performed the action
            entity_type: Type of entity affected (portfolio, transaction, etc.)
            entity_id: ID of the specific entity affected
            event_metadata: Additional structured data about the event
            ip_address: IP address of the user (if available)
            user_agent: User agent string (if available)

        Returns:
            AuditLog entry if successful, None if failed
        """
        try:
            audit_entry = AuditLog(
                event_type=event_type,
                event_description=event_description,
                user_id=user_id,
                entity_type=entity_type,
                entity_id=entity_id,
                timestamp=now(),
                event_metadata=event_metadata,
                ip_address=ip_address,
                user_agent=user_agent
            )

            self.db.add(audit_entry)
            self.db.flush()  # Get the ID without committing

            logger.info(f"Audit entry created: {event_type.value} for {entity_type} {entity_id} by user {user_id}")
            return audit_entry

        except SQLAlchemyError as e:
            logger.error(f"Failed to create audit entry: {e}")
            # Don't raise - audit logging should not fail the main operation
            return None

    def log_portfolio_created(
        self,
        portfolio: Portfolio,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLog]:
        """Log portfolio creation event."""
        return self.create_audit_entry(
            event_type=AuditEventType.PORTFOLIO_CREATED,
            event_description=f"Portfolio '{portfolio.name}' created",
            user_id=user_id,
            entity_type="portfolio",
            entity_id=str(portfolio.id),
            event_metadata={
                "portfolio_name": portfolio.name,
                "portfolio_description": portfolio.description
            },
            ip_address=ip_address,
            user_agent=user_agent
        )

    def log_portfolio_updated(
        self,
        portfolio: Portfolio,
        user_id: str,
        changes: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLog]:
        """Log portfolio update event."""
        return self.create_audit_entry(
            event_type=AuditEventType.PORTFOLIO_UPDATED,
            event_description=f"Portfolio '{portfolio.name}' updated",
            user_id=user_id,
            entity_type="portfolio",
            entity_id=str(portfolio.id),
            event_metadata={
                "portfolio_name": portfolio.name,
                "changes": changes
            },
            ip_address=ip_address,
            user_agent=user_agent
        )

    def log_portfolio_deleted(
        self,
        portfolio_id: str,
        portfolio_name: str,
        user_id,  # UUID or str
        is_hard_delete: bool = False,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLog]:
        """Log portfolio deletion event."""
        delete_type = "hard deleted" if is_hard_delete else "soft deleted"
        event_type = AuditEventType.PORTFOLIO_HARD_DELETED if is_hard_delete else AuditEventType.PORTFOLIO_SOFT_DELETED

        return self.create_audit_entry(
            event_type=event_type,
            event_description=f"Portfolio '{portfolio_name}' {delete_type}",
            user_id=user_id,
            entity_type="portfolio",
            entity_id=portfolio_id,
            event_metadata={
                "portfolio_name": portfolio_name,
                "is_hard_delete": is_hard_delete
            },
            ip_address=ip_address,
            user_agent=user_agent
        )

    def log_transaction_created(
        self,
        transaction: Transaction,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLog]:
        """Log transaction creation event."""
        return self.create_audit_entry(
            event_type=AuditEventType.TRANSACTION_CREATED,
            event_description=f"Transaction created: {transaction.transaction_type.value} {transaction.symbol}",
            user_id=user_id,
            entity_type="transaction",
            entity_id=str(transaction.id),
            event_metadata={
                "transaction_type": transaction.transaction_type.value,
                "symbol": transaction.symbol,
                "quantity": float(transaction.quantity),
                "price_per_share": float(transaction.price_per_share),
                "portfolio_id": str(transaction.portfolio_id)
            },
            ip_address=ip_address,
            user_agent=user_agent
        )

    def log_transaction_updated(
        self,
        transaction: Transaction,
        user_id: str,
        changes: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLog]:
        """Log transaction update event."""
        return self.create_audit_entry(
            event_type=AuditEventType.TRANSACTION_UPDATED,
            event_description=f"Transaction updated: {transaction.transaction_type.value} {transaction.symbol}",
            user_id=user_id,
            entity_type="transaction",
            entity_id=str(transaction.id),
            event_metadata={
                "transaction_type": transaction.transaction_type.value,
                "symbol": transaction.symbol,
                "changes": changes,
                "portfolio_id": str(transaction.portfolio_id)
            },
            ip_address=ip_address,
            user_agent=user_agent
        )

    def log_transaction_deleted(
        self,
        transaction_id: str,
        transaction_type: str,
        symbol: str,
        user_id: str,
        portfolio_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLog]:
        """Log transaction deletion event."""
        return self.create_audit_entry(
            event_type=AuditEventType.TRANSACTION_DELETED,
            event_description=f"Transaction deleted: {transaction_type} {symbol}",
            user_id=user_id,
            entity_type="transaction",
            entity_id=transaction_id,
            event_metadata={
                "transaction_type": transaction_type,
                "symbol": symbol,
                "portfolio_id": portfolio_id
            },
            ip_address=ip_address,
            user_agent=user_agent
        )

    def log_user_login(
        self,
        user_id,  # UUID or str
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLog]:
        """Log user login event."""
        return self.create_audit_entry(
            event_type=AuditEventType.USER_LOGIN,
            event_description="User logged in",
            user_id=user_id,
            entity_type="user",
            entity_id=str(user_id),
            event_metadata={
                "login_timestamp": now().isoformat()
            },
            ip_address=ip_address,
            user_agent=user_agent
        )

    def log_user_logout(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLog]:
        """Log user logout event."""
        return self.create_audit_entry(
            event_type=AuditEventType.USER_LOGOUT,
            event_description="User logged out",
            user_id=user_id,
            entity_type="user",
            entity_id=user_id,
            event_metadata={
                "logout_timestamp": now().isoformat()
            },
            ip_address=ip_address,
            user_agent=user_agent
        )

    def log_user_created(
        self,
        user_id,  # UUID or str
        email: str,
        first_name: str,
        last_name: str,
        role: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLog]:
        """Log user creation event."""
        return self.create_audit_entry(
            event_type=AuditEventType.USER_CREATED,
            event_description=f"User registered: {email}",
            user_id=user_id,
            entity_type="user",
            entity_id=str(user_id),
            event_metadata={
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
                "registration_timestamp": now().isoformat()
            },
            ip_address=ip_address,
            user_agent=user_agent
        )

    def log_admin_action(
        self,
        action_description: str,
        user_id: str,
        entity_type: str,
        entity_id: str,
        action_metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLog]:
        """Log administrative action event."""
        return self.create_audit_entry(
            event_type=AuditEventType.ADMIN_ACTION_PERFORMED,
            event_description=action_description,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            event_metadata=action_metadata,
            ip_address=ip_address,
            user_agent=user_agent
        )