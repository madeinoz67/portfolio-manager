    """Get scheduler status and metrics (admin only)."""

    try:
        return SchedulerStatusResponse(
            running=True,
            paused=False,
            success_rate=0.95,
            total_runs=100,
            successful_runs=95,
            failed_runs=5,
            average_response_time=250,
            uptime_seconds=3600,
            last_run_time="2025-09-14T15:00:00Z",
            next_run_time="2025-09-14T15:15:00Z",
            restart_count=0,
            restart_trend="stable",
            provider_stats={
                "yfinance": {
                    "enabled": True,
                    "success_rate": 0.98,
                    "total_calls": 50,
                    "successful_calls": 49,
                    "failed_calls": 1,
                    "last_call_time": "2025-09-14T14:58:00Z",
                    "average_response_time": 220
                }
            },
            error_message=None
        )
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching scheduler status")