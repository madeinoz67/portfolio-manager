"""
Pydantic schemas for adapter metrics and monitoring.

Defines response schemas for metrics collection, performance monitoring,
cost tracking, and system health reporting.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class MetricsPeriod(str, Enum):
    """Time periods for metrics aggregation."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class MetricsAggregation(str, Enum):
    """Aggregation methods for metrics."""
    SUM = "sum"
    AVERAGE = "average"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    PERCENTILE_95 = "p95"
    PERCENTILE_99 = "p99"


class AlertLevel(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class CostTrackingStatus(str, Enum):
    """Cost tracking status levels."""
    OK = "ok"
    WARNING = "warning"
    BUDGET_EXCEEDED = "budget_exceeded"
    LIMIT_REACHED = "limit_reached"


class CurrentMetrics(BaseModel):
    """Current real-time metrics for an adapter."""
    adapter_id: str = Field(..., description="Adapter configuration ID")
    provider_name: str = Field(..., description="Provider type")
    is_healthy: bool = Field(..., description="Current health status")
    is_active: bool = Field(..., description="Whether adapter is active")
    last_check: datetime = Field(..., description="Last metrics update timestamp")

    # Request metrics
    total_requests: int = Field(default=0, ge=0, description="Total requests made")
    successful_requests: int = Field(default=0, ge=0, description="Successful requests")
    failed_requests: int = Field(default=0, ge=0, description="Failed requests")
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Success rate (0.0 to 1.0)")

    # Performance metrics
    avg_latency_ms: float = Field(default=0.0, ge=0.0, description="Average response time in ms")
    min_latency_ms: float = Field(default=0.0, ge=0.0, description="Minimum response time in ms")
    max_latency_ms: float = Field(default=0.0, ge=0.0, description="Maximum response time in ms")
    p95_latency_ms: float = Field(default=0.0, ge=0.0, description="95th percentile latency in ms")

    # Rate limiting
    requests_per_minute: float = Field(default=0.0, ge=0.0, description="Current requests per minute")
    rate_limit_remaining: Optional[int] = Field(None, description="Remaining rate limit quota")
    rate_limit_reset_time: Optional[datetime] = Field(None, description="Rate limit reset timestamp")

    # Error tracking
    error_count_24h: int = Field(default=0, ge=0, description="Errors in last 24 hours")
    last_error: Optional[str] = Field(None, description="Last error message")
    last_error_time: Optional[datetime] = Field(None, description="Last error timestamp")

    # Circuit breaker
    circuit_breaker_state: str = Field(default="closed", description="Circuit breaker state")
    circuit_breaker_failure_count: int = Field(default=0, ge=0, description="Current failure count")
    circuit_breaker_next_attempt: Optional[datetime] = Field(None, description="Next attempt time if open")


class CostMetrics(BaseModel):
    """Cost tracking metrics for an adapter."""
    # Daily costs
    daily_cost: Decimal = Field(default=Decimal('0.00'), description="Cost today")
    daily_budget: Optional[Decimal] = Field(None, description="Daily budget limit")
    daily_budget_used_percent: float = Field(default=0.0, ge=0.0, description="Daily budget usage percentage")

    # Monthly costs
    monthly_cost: Decimal = Field(default=Decimal('0.00'), description="Cost this month")
    monthly_budget: Optional[Decimal] = Field(None, description="Monthly budget limit")
    monthly_budget_used_percent: float = Field(default=0.0, ge=0.0, description="Monthly budget usage percentage")

    # Cost efficiency
    cost_per_request: Decimal = Field(default=Decimal('0.00'), description="Average cost per request")
    cost_per_successful_request: Decimal = Field(default=Decimal('0.00'), description="Cost per successful request")

    # Budget status
    budget_status: CostTrackingStatus = Field(default=CostTrackingStatus.OK, description="Budget status")
    budget_remaining_daily: Optional[Decimal] = Field(None, description="Remaining daily budget")
    budget_remaining_monthly: Optional[Decimal] = Field(None, description="Remaining monthly budget")

    # Alerts
    cost_alerts: List[str] = Field(default_factory=list, description="Active cost alerts")

    # Projections
    projected_daily_cost: Optional[Decimal] = Field(None, description="Projected daily cost")
    projected_monthly_cost: Optional[Decimal] = Field(None, description="Projected monthly cost")


class HistoricalDataPoint(BaseModel):
    """Historical metrics data point."""
    timestamp: datetime = Field(..., description="Data point timestamp")
    period: MetricsPeriod = Field(..., description="Aggregation period")

    # Request metrics
    request_count: int = Field(default=0, ge=0, description="Number of requests")
    success_count: int = Field(default=0, ge=0, description="Number of successful requests")
    error_count: int = Field(default=0, ge=0, description="Number of failed requests")
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Success rate")

    # Performance metrics
    avg_latency_ms: float = Field(default=0.0, ge=0.0, description="Average latency")
    p95_latency_ms: float = Field(default=0.0, ge=0.0, description="95th percentile latency")

    # Cost metrics (optional)
    total_cost: Optional[Decimal] = Field(None, description="Total cost for period")
    cost_per_request: Optional[Decimal] = Field(None, description="Cost per request")


class MetricsAlert(BaseModel):
    """Metrics-based alert."""
    id: str = Field(..., description="Alert identifier")
    adapter_id: str = Field(..., description="Related adapter ID")
    alert_type: str = Field(..., description="Type of alert")
    level: AlertLevel = Field(..., description="Alert severity level")
    message: str = Field(..., description="Alert message")
    threshold_value: Optional[float] = Field(None, description="Threshold that was breached")
    current_value: Optional[float] = Field(None, description="Current metric value")
    created_at: datetime = Field(..., description="Alert creation time")
    acknowledged: bool = Field(default=False, description="Whether alert is acknowledged")
    acknowledged_by: Optional[str] = Field(None, description="User who acknowledged alert")
    acknowledged_at: Optional[datetime] = Field(None, description="Acknowledgment timestamp")


class AdapterMetricsResponse(BaseModel):
    """Complete metrics response for an adapter."""
    adapter_id: str = Field(..., description="Adapter configuration ID")
    provider_name: str = Field(..., description="Provider type")
    current_metrics: CurrentMetrics = Field(..., description="Current real-time metrics")
    cost_metrics: Optional[CostMetrics] = Field(None, description="Cost tracking metrics")
    historical_data: Optional[List[HistoricalDataPoint]] = Field(None, description="Historical metrics")
    active_alerts: List[MetricsAlert] = Field(default_factory=list, description="Active alerts")
    last_updated: datetime = Field(..., description="Last metrics update")


class SystemMetricsSummary(BaseModel):
    """System-wide metrics summary."""
    total_adapters: int = Field(..., ge=0, description="Total configured adapters")
    active_adapters: int = Field(..., ge=0, description="Currently active adapters")
    healthy_adapters: int = Field(..., ge=0, description="Healthy adapters")

    # Aggregate request metrics
    total_requests_24h: int = Field(default=0, ge=0, description="Total requests in 24 hours")
    successful_requests_24h: int = Field(default=0, ge=0, description="Successful requests in 24 hours")
    system_success_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall success rate")

    # Performance
    system_avg_latency_ms: float = Field(default=0.0, ge=0.0, description="System average latency")

    # Cost summary
    total_daily_cost: Decimal = Field(default=Decimal('0.00'), description="Total daily cost")
    total_monthly_cost: Decimal = Field(default=Decimal('0.00'), description="Total monthly cost")

    # Alerts
    active_alerts_count: int = Field(default=0, ge=0, description="Number of active alerts")
    critical_alerts_count: int = Field(default=0, ge=0, description="Number of critical alerts")

    last_updated: datetime = Field(..., description="Last update timestamp")


class ProviderComparisonMetrics(BaseModel):
    """Comparison metrics between providers."""
    provider_name: str = Field(..., description="Provider type")
    adapter_count: int = Field(..., ge=0, description="Number of configured adapters")

    # Performance comparison
    avg_success_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Average success rate")
    avg_latency_ms: float = Field(default=0.0, ge=0.0, description="Average latency")
    reliability_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Reliability score")

    # Cost comparison
    total_cost: Decimal = Field(default=Decimal('0.00'), description="Total cost")
    cost_efficiency: float = Field(default=0.0, ge=0.0, description="Cost efficiency score")

    # Usage comparison
    request_volume: int = Field(default=0, ge=0, description="Request volume")
    market_share: float = Field(default=0.0, ge=0.0, le=1.0, description="Market share percentage")


class MetricsFilterRequest(BaseModel):
    """Request schema for filtering metrics."""
    start_date: Optional[date] = Field(None, description="Start date for metrics")
    end_date: Optional[date] = Field(None, description="End date for metrics")
    period: MetricsPeriod = Field(default=MetricsPeriod.DAILY, description="Aggregation period")
    provider_names: Optional[List[str]] = Field(None, description="Filter by provider types")
    include_cost_data: bool = Field(default=False, description="Include cost metrics")
    include_alerts: bool = Field(default=False, description="Include alert data")
    aggregation: MetricsAggregation = Field(default=MetricsAggregation.AVERAGE, description="Aggregation method")


class MetricsExportRequest(BaseModel):
    """Request schema for metrics export."""
    adapter_ids: Optional[List[str]] = Field(None, description="Specific adapters to export")
    start_date: date = Field(..., description="Export start date")
    end_date: date = Field(..., description="Export end date")
    period: MetricsPeriod = Field(default=MetricsPeriod.DAILY, description="Export granularity")
    include_cost_data: bool = Field(default=True, description="Include cost information")
    include_raw_data: bool = Field(default=False, description="Include raw data points")
    format: str = Field(default="csv", description="Export format (csv, json, xlsx)")


class MetricsExportResponse(BaseModel):
    """Response schema for metrics export."""
    export_id: str = Field(..., description="Export job identifier")
    status: str = Field(..., description="Export status")
    download_url: Optional[str] = Field(None, description="Download URL when ready")
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")
    record_count: Optional[int] = Field(None, description="Number of records exported")
    created_at: datetime = Field(..., description="Export creation time")
    expires_at: Optional[datetime] = Field(None, description="Download link expiration")


class CostProjection(BaseModel):
    """Cost projection for budget planning."""
    period: str = Field(..., description="Projection period (daily, weekly, monthly)")
    projected_cost: Decimal = Field(..., description="Projected cost amount")
    confidence_level: float = Field(..., ge=0.0, le=1.0, description="Projection confidence")
    trend: str = Field(..., description="Cost trend (increasing, decreasing, stable)")
    factors: List[str] = Field(default_factory=list, description="Factors affecting projection")
    recommendation: Optional[str] = Field(None, description="Cost optimization recommendation")


class PerformanceBenchmark(BaseModel):
    """Performance benchmark data."""
    metric_name: str = Field(..., description="Metric being benchmarked")
    current_value: float = Field(..., description="Current metric value")
    benchmark_value: float = Field(..., description="Benchmark/target value")
    performance_ratio: float = Field(..., description="Current/benchmark ratio")
    status: str = Field(..., description="Performance status (above, below, meeting)")
    improvement_suggestion: Optional[str] = Field(None, description="Improvement suggestion")


class AdapterRecommendation(BaseModel):
    """Optimization recommendation for adapters."""
    adapter_id: str = Field(..., description="Target adapter ID")
    recommendation_type: str = Field(..., description="Type of recommendation")
    priority: str = Field(..., description="Recommendation priority (low, medium, high)")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed recommendation")
    expected_benefit: Optional[str] = Field(None, description="Expected benefit")
    implementation_effort: Optional[str] = Field(None, description="Implementation effort level")
    risk_level: str = Field(default="low", description="Risk level of implementing")


class SystemHealthResponse(BaseModel):
    """System health overview response."""
    overall_status: str = Field(..., description="Overall system health status")
    system_metrics: SystemMetricsSummary = Field(..., description="System-wide metrics")
    provider_comparison: List[ProviderComparisonMetrics] = Field(
        default_factory=list, description="Provider performance comparison"
    )
    cost_projections: List[CostProjection] = Field(
        default_factory=list, description="Cost projections"
    )
    performance_benchmarks: List[PerformanceBenchmark] = Field(
        default_factory=list, description="Performance benchmarks"
    )
    recommendations: List[AdapterRecommendation] = Field(
        default_factory=list, description="Optimization recommendations"
    )
    critical_issues: List[str] = Field(default_factory=list, description="Critical issues requiring attention")
    last_updated: datetime = Field(..., description="Health data timestamp")


class MetricsConfigurationResponse(BaseModel):
    """Metrics system configuration."""
    collection_interval_seconds: int = Field(..., description="Metrics collection interval")
    retention_days: int = Field(..., description="Metrics retention period")
    aggregation_periods: List[MetricsPeriod] = Field(..., description="Available aggregation periods")
    available_metrics: List[str] = Field(..., description="Available metric types")
    cost_tracking_enabled: bool = Field(..., description="Whether cost tracking is enabled")
    alerting_enabled: bool = Field(..., description="Whether alerting is enabled")
    export_formats: List[str] = Field(..., description="Supported export formats")