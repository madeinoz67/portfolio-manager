"""
Pydantic schemas for audit log API responses.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from src.models.audit_log import AuditEventType


class AuditLogEntry(BaseModel):
    """Schema for individual audit log entry in API responses."""
    id: int
    event_type: str
    event_description: str
    user_id: str
    user_email: Optional[str] = None
    entity_type: str
    entity_id: str
    timestamp: str
    event_metadata: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class AuditLogPagination(BaseModel):
    """Pagination information for audit log responses."""
    current_page: int
    total_pages: int
    total_items: int
    items_per_page: int


class AuditLogFilters(BaseModel):
    """Current filter parameters applied to audit log query."""
    user_id: Optional[str] = None
    event_type: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    search: Optional[str] = None
    sort_by: Optional[str] = None
    sort_order: Optional[str] = None


class AuditLogMetadata(BaseModel):
    """Metadata about the audit log request."""
    request_timestamp: str
    processing_time_ms: int
    total_events_in_system: int


class AuditLogResponse(BaseModel):
    """Complete response for audit log listing."""
    data: List[AuditLogEntry]
    pagination: AuditLogPagination
    filters: AuditLogFilters
    meta: AuditLogMetadata


class AuditLogStats(BaseModel):
    """Statistics about audit logs."""
    total_events: int
    events_today: int
    events_this_week: int
    events_this_month: int
    event_types_breakdown: Dict[str, int]
    user_activity_breakdown: Dict[str, int]
    entity_types_breakdown: Dict[str, int]


class AuditLogStatsResponse(BaseModel):
    """Response for audit log statistics."""
    stats: AuditLogStats
    generated_at: str


class AuditLogExportRequest(BaseModel):
    """Request parameters for audit log export."""
    format: str = Field(..., pattern="^(csv|json)$", description="Export format: csv or json")
    user_id: Optional[str] = None
    event_type: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    search: Optional[str] = None
    include_metadata: bool = True