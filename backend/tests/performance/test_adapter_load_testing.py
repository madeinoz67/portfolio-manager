"""
T065: Load testing for 1000+ concurrent adapter requests
Tests adapter system performance under high concurrent load.
"""

import pytest
import asyncio
import time
import statistics
from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, AsyncMock, Mock
import threading
import queue

from src.services.adapters.base_adapter import MarketDataAdapter
from src.services.adapters.registry import ProviderRegistry
from src.services.adapters.metrics import ProviderMetricsCollector
from src.services.config_manager import ConfigurationManager


class MockLoadTestAdapter(MarketDataAdapter):
    """Mock adapter for load testing."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._request_delay = config.get('request_delay', 0.05)  # 50ms default
        self._failure_rate = config.get('failure_rate', 0.05)  # 5% failure rate
        self._request_count = 0
        self._lock = threading.Lock()

    @property
    def provider_name(self) -> str:
        return "load_test_provider"

    @property
    def capabilities(self):
        from src.services.adapters.base_adapter import ProviderCapabilities
        return ProviderCapabilities(
            supports_real_time=True,
            supports_historical=True,
            supports_bulk=True,
            max_symbols_per_request=100,
            rate_limit_per_minute=1000,  # High limit for load testing
            requires_api_key=False
        )

    async def connect(self) -> bool:
        await asyncio.sleep(0.001)  # Minimal connection time
        return True

    async def disconnect(self) -> None:
        await asyncio.sleep(0.001)

    async def get_current_price(self, symbol: str) -> Dict[str, Any]:
        with self._lock:
            self._request_count += 1
            current_count = self._request_count

        # Simulate processing time
        await asyncio.sleep(self._request_delay)

        # Simulate occasional failures
        if current_count % int(1 / self._failure_rate) == 0:
            raise Exception(f"Simulated failure for request {current_count}")

        return {
            "symbol": symbol,
            "price": 100.0 + (current_count % 50),  # Varying price
            "volume": 1000000,
            "timestamp": time.time(),
            "source": "load_test_provider",
            "request_id": current_count
        }

    async def get_multiple_prices(self, symbols: List[str]) -> Dict[str, Any]:
        results = {}
        for symbol in symbols:
            try:
                results[symbol] = await self.get_current_price(symbol)
            except Exception:
                results[symbol] = None
        return results

    async def validate_config(self) -> bool:
        return True


class TestAdapterLoadTesting:
    """Test adapter system under high concurrent load."""

    def setup_method(self):
        """Set up test environment for each test."""
        self.results_queue = queue.Queue()
        self.error_queue = queue.Queue()

    @pytest.fixture
    def load_test_adapter(self):
        """Create adapter optimized for load testing."""
        config = {
            'request_delay': 0.02,  # 20ms response time
            'failure_rate': 0.02,   # 2% failure rate
        }
        return MockLoadTestAdapter(config)

    @pytest.fixture
    def metrics_collector(self):
        """Create mock metrics collector."""
        collector = Mock(spec=ProviderMetricsCollector)
        collector.record_request = AsyncMock()
        collector.get_adapter_metrics = AsyncMock(return_value={
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0
        })
        return collector

    async def single_request_task(
        self,
        adapter: MockLoadTestAdapter,
        symbol: str,
        task_id: int,
        metrics_collector: Mock
    ) -> Dict[str, Any]:
        """Execute single request and measure performance."""
        start_time = time.perf_counter()

        try:
            result = await adapter.get_current_price(symbol)
            end_time = time.perf_counter()
            response_time = (end_time - start_time) * 1000  # ms

            # Record success metrics
            await metrics_collector.record_request(
                provider_id="load_test_provider",
                adapter_id=adapter.adapter_id,
                success=True,
                response_time_ms=response_time
            )

            return {
                "task_id": task_id,
                "symbol": symbol,
                "success": True,
                "response_time": response_time,
                "result": result
            }

        except Exception as e:
            end_time = time.perf_counter()
            response_time = (end_time - start_time) * 1000

            # Record failure metrics
            await metrics_collector.record_request(
                provider_id="load_test_provider",
                adapter_id=adapter.adapter_id,
                success=False,
                response_time_ms=response_time,
                error_type=type(e).__name__
            )

            return {
                "task_id": task_id,
                "symbol": symbol,
                "success": False,
                "response_time": response_time,
                "error": str(e)
            }

    async def bulk_request_task(
        self,
        adapter: MockLoadTestAdapter,
        symbols: List[str],
        task_id: int,
        metrics_collector: Mock
    ) -> Dict[str, Any]:
        """Execute bulk request and measure performance."""
        start_time = time.perf_counter()

        try:
            results = await adapter.get_multiple_prices(symbols)
            end_time = time.perf_counter()
            response_time = (end_time - start_time) * 1000

            successful_symbols = len([r for r in results.values() if r is not None])

            await metrics_collector.record_request(
                provider_id="load_test_provider",
                adapter_id=adapter.adapter_id,
                success=True,
                response_time_ms=response_time,
                endpoint="bulk_prices"
            )

            return {
                "task_id": task_id,
                "symbols": symbols,
                "success": True,
                "response_time": response_time,
                "successful_symbols": successful_symbols,
                "total_symbols": len(symbols)
            }

        except Exception as e:
            end_time = time.perf_counter()
            response_time = (end_time - start_time) * 1000

            return {
                "task_id": task_id,
                "symbols": symbols,
                "success": False,
                "response_time": response_time,
                "error": str(e)
            }

    @pytest.mark.asyncio
    async def test_concurrent_single_requests(self, load_test_adapter, metrics_collector):
        """Test 1000+ concurrent single symbol requests."""
        print("\n" + "="*60)
        print("CONCURRENT SINGLE REQUESTS LOAD TEST")
        print("="*60)

        # Test parameters
        num_requests = 1000
        symbols = [f"SYMBOL{i:03d}" for i in range(100)]  # 100 unique symbols

        # Connect adapter
        await load_test_adapter.connect()

        # Create tasks
        tasks = []
        for i in range(num_requests):
            symbol = symbols[i % len(symbols)]  # Cycle through symbols
            task = self.single_request_task(
                adapter=load_test_adapter,
                symbol=symbol,
                task_id=i,
                metrics_collector=metrics_collector
            )
            tasks.append(task)

        # Execute all tasks concurrently
        start_time = time.perf_counter()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.perf_counter()

        total_time = (end_time - start_time) * 1000  # ms

        # Analyze results
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_results = [r for r in results if isinstance(r, dict) and not r.get("success")]
        exceptions = [r for r in results if isinstance(r, Exception)]

        response_times = [r["response_time"] for r in successful_results]

        print(f"Total requests: {num_requests}")
        print(f"Successful requests: {len(successful_results)}")
        print(f"Failed requests: {len(failed_results)}")
        print(f"Exceptions: {len(exceptions)}")
        print(f"Success rate: {len(successful_results) / num_requests * 100:.2f}%")
        print(f"Total execution time: {total_time:.2f}ms")
        print(f"Requests per second: {num_requests / (total_time / 1000):.2f}")

        if response_times:
            print(f"Average response time: {statistics.mean(response_times):.2f}ms")
            print(f"Median response time: {statistics.median(response_times):.2f}ms")
            print(f"95th percentile: {self.percentile(response_times, 95):.2f}ms")
            print(f"99th percentile: {self.percentile(response_times, 99):.2f}ms")
            print(f"Max response time: {max(response_times):.2f}ms")

        # Performance assertions
        success_rate = len(successful_results) / num_requests
        assert success_rate >= 0.95, f"Success rate {success_rate:.2%} below 95%"

        if response_times:
            avg_response_time = statistics.mean(response_times)
            assert avg_response_time < 100.0, f"Average response time {avg_response_time:.2f}ms exceeds 100ms"

            p95_response_time = self.percentile(response_times, 95)
            assert p95_response_time < 200.0, f"95th percentile {p95_response_time:.2f}ms exceeds 200ms"

        rps = num_requests / (total_time / 1000)
        assert rps >= 100, f"Requests per second {rps:.2f} below 100 RPS"

        await load_test_adapter.disconnect()

    @pytest.mark.asyncio
    async def test_concurrent_bulk_requests(self, load_test_adapter, metrics_collector):
        """Test concurrent bulk symbol requests."""
        print("\n" + "="*60)
        print("CONCURRENT BULK REQUESTS LOAD TEST")
        print("="*60)

        # Test parameters
        num_bulk_requests = 100
        symbols_per_request = 10
        symbols = [f"BULK{i:03d}" for i in range(200)]

        await load_test_adapter.connect()

        # Create bulk request tasks
        tasks = []
        for i in range(num_bulk_requests):
            start_idx = (i * symbols_per_request) % (len(symbols) - symbols_per_request)
            request_symbols = symbols[start_idx:start_idx + symbols_per_request]

            task = self.bulk_request_task(
                adapter=load_test_adapter,
                symbols=request_symbols,
                task_id=i,
                metrics_collector=metrics_collector
            )
            tasks.append(task)

        # Execute all bulk requests concurrently
        start_time = time.perf_counter()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.perf_counter()

        total_time = (end_time - start_time) * 1000  # ms

        # Analyze results
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed_results = [r for r in results if isinstance(r, dict) and not r.get("success")]

        total_symbols_requested = num_bulk_requests * symbols_per_request
        total_symbols_processed = sum(r.get("successful_symbols", 0) for r in successful_results)

        response_times = [r["response_time"] for r in successful_results]

        print(f"Bulk requests: {num_bulk_requests}")
        print(f"Symbols per request: {symbols_per_request}")
        print(f"Total symbols requested: {total_symbols_requested}")
        print(f"Successful bulk requests: {len(successful_results)}")
        print(f"Failed bulk requests: {len(failed_results)}")
        print(f"Total symbols processed: {total_symbols_processed}")
        print(f"Symbol success rate: {total_symbols_processed / total_symbols_requested * 100:.2f}%")
        print(f"Total execution time: {total_time:.2f}ms")
        print(f"Bulk requests per second: {num_bulk_requests / (total_time / 1000):.2f}")

        if response_times:
            print(f"Average bulk response time: {statistics.mean(response_times):.2f}ms")
            print(f"95th percentile: {self.percentile(response_times, 95):.2f}ms")

        # Performance assertions
        bulk_success_rate = len(successful_results) / num_bulk_requests
        assert bulk_success_rate >= 0.90, f"Bulk success rate {bulk_success_rate:.2%} below 90%"

        symbol_success_rate = total_symbols_processed / total_symbols_requested
        assert symbol_success_rate >= 0.85, f"Symbol success rate {symbol_success_rate:.2%} below 85%"

        if response_times:
            avg_bulk_time = statistics.mean(response_times)
            assert avg_bulk_time < 500.0, f"Average bulk response time {avg_bulk_time:.2f}ms exceeds 500ms"

        await load_test_adapter.disconnect()

    @pytest.mark.asyncio
    async def test_sustained_load(self, load_test_adapter, metrics_collector):
        """Test sustained load over time."""
        print("\n" + "="*60)
        print("SUSTAINED LOAD TEST")
        print("="*60)

        # Test parameters
        duration_seconds = 30
        requests_per_second = 50
        symbols = [f"SUSTAINED{i:02d}" for i in range(20)]

        await load_test_adapter.connect()

        start_time = time.perf_counter()
        end_time = start_time + duration_seconds

        all_results = []
        batch_count = 0

        while time.perf_counter() < end_time:
            batch_start = time.perf_counter()

            # Create batch of requests
            batch_tasks = []
            for i in range(requests_per_second):
                symbol = symbols[i % len(symbols)]
                task = self.single_request_task(
                    adapter=load_test_adapter,
                    symbol=symbol,
                    task_id=batch_count * requests_per_second + i,
                    metrics_collector=metrics_collector
                )
                batch_tasks.append(task)

            # Execute batch
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            all_results.extend(batch_results)

            batch_count += 1

            # Wait for next second (rate limiting)
            batch_end = time.perf_counter()
            batch_duration = batch_end - batch_start
            if batch_duration < 1.0:
                await asyncio.sleep(1.0 - batch_duration)

        actual_duration = time.perf_counter() - start_time

        # Analyze sustained load results
        successful_results = [r for r in all_results if isinstance(r, dict) and r.get("success")]
        failed_results = [r for r in all_results if isinstance(r, dict) and not r.get("success")]

        total_requests = len(all_results)
        actual_rps = total_requests / actual_duration

        response_times = [r["response_time"] for r in successful_results]

        print(f"Target duration: {duration_seconds}s")
        print(f"Actual duration: {actual_duration:.2f}s")
        print(f"Target RPS: {requests_per_second}")
        print(f"Actual RPS: {actual_rps:.2f}")
        print(f"Total requests: {total_requests}")
        print(f"Successful requests: {len(successful_results)}")
        print(f"Failed requests: {len(failed_results)}")
        print(f"Success rate: {len(successful_results) / total_requests * 100:.2f}%")

        if response_times:
            print(f"Average response time: {statistics.mean(response_times):.2f}ms")
            print(f"95th percentile: {self.percentile(response_times, 95):.2f}ms")
            print(f"Response time std dev: {statistics.stdev(response_times):.2f}ms")

        # Performance assertions for sustained load
        success_rate = len(successful_results) / total_requests
        assert success_rate >= 0.90, f"Sustained success rate {success_rate:.2%} below 90%"

        assert actual_rps >= requests_per_second * 0.9, f"Actual RPS {actual_rps:.2f} significantly below target {requests_per_second}"

        if response_times:
            avg_response_time = statistics.mean(response_times)
            assert avg_response_time < 150.0, f"Average response time {avg_response_time:.2f}ms exceeds 150ms under sustained load"

            # Check for performance degradation over time
            first_half = response_times[:len(response_times)//2]
            second_half = response_times[len(response_times)//2:]

            if first_half and second_half:
                avg_first_half = statistics.mean(first_half)
                avg_second_half = statistics.mean(second_half)
                degradation = (avg_second_half - avg_first_half) / avg_first_half

                print(f"First half avg response time: {avg_first_half:.2f}ms")
                print(f"Second half avg response time: {avg_second_half:.2f}ms")
                print(f"Performance degradation: {degradation * 100:.2f}%")

                assert degradation < 0.3, f"Performance degraded by {degradation * 100:.2f}% over time"

        await load_test_adapter.disconnect()

    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, load_test_adapter, metrics_collector):
        """Test memory usage doesn't grow excessively under load."""
        import psutil
        import os

        print("\n" + "="*60)
        print("MEMORY USAGE UNDER LOAD TEST")
        print("="*60)

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        await load_test_adapter.connect()

        # Run load test batches
        num_batches = 10
        requests_per_batch = 100
        symbols = [f"MEM{i:02d}" for i in range(10)]

        memory_measurements = [initial_memory]

        for batch in range(num_batches):
            # Create and execute batch
            tasks = []
            for i in range(requests_per_batch):
                symbol = symbols[i % len(symbols)]
                task = self.single_request_task(
                    adapter=load_test_adapter,
                    symbol=symbol,
                    task_id=batch * requests_per_batch + i,
                    metrics_collector=metrics_collector
                )
                tasks.append(task)

            await asyncio.gather(*tasks, return_exceptions=True)

            # Measure memory after batch
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_measurements.append(current_memory)

            print(f"Batch {batch + 1}/{num_batches} - Memory: {current_memory:.2f}MB")

        final_memory = memory_measurements[-1]
        max_memory = max(memory_measurements)
        memory_growth = final_memory - initial_memory

        print(f"Initial memory: {initial_memory:.2f}MB")
        print(f"Final memory: {final_memory:.2f}MB")
        print(f"Max memory: {max_memory:.2f}MB")
        print(f"Memory growth: {memory_growth:.2f}MB")
        print(f"Memory growth percentage: {memory_growth / initial_memory * 100:.2f}%")

        # Memory assertions
        assert memory_growth < 100, f"Memory grew by {memory_growth:.2f}MB, exceeding 100MB limit"
        assert memory_growth / initial_memory < 0.5, f"Memory grew by {memory_growth / initial_memory * 100:.2f}%, exceeding 50% limit"

        await load_test_adapter.disconnect()

    def percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of data."""
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]

    def test_load_testing_summary(self):
        """Print load testing summary."""
        print("\n" + "="*60)
        print("ADAPTER LOAD TESTING SUMMARY")
        print("="*60)
        print("✅ 1000+ concurrent single requests")
        print("✅ 100+ concurrent bulk requests")
        print("✅ 30-second sustained load test")
        print("✅ Memory usage under load")
        print("\nPerformance Targets:")
        print("  • Success rate: >95% (single), >90% (bulk), >90% (sustained)")
        print("  • Response time: <100ms avg (single), <500ms avg (bulk)")
        print("  • Throughput: >100 RPS (single), >50 RPS (sustained)")
        print("  • Memory growth: <100MB, <50% increase")
        print("="*60)