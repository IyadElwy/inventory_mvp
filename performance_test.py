"""
Simple performance test for Inventory API.
Tests throughput requirement: 100 requests/second.
"""
import time
import asyncio
import httpx
from statistics import mean, median

BASE_URL = "http://localhost:8000"


async def make_request(client: httpx.AsyncClient, product_id: str):
    """Make a single API request and measure response time"""
    start = time.time()
    try:
        response = await client.get(f"{BASE_URL}/v1/inventory/{product_id}")
        duration = time.time() - start
        return {
            "success": response.status_code == 200 or response.status_code == 404,
            "status": response.status_code,
            "duration": duration
        }
    except Exception as e:
        duration = time.time() - start
        return {"success": False, "status": 0, "duration": duration, "error": str(e)}


async def run_performance_test(num_requests: int = 1000, concurrency: int = 10):
    """
    Run performance test with specified parameters.

    Args:
        num_requests: Total number of requests to make
        concurrency: Number of concurrent requests
    """
    print(f"Running performance test: {num_requests} requests, {concurrency} concurrent")
    print(f"Target: 100 req/sec")
    print("-" * 60)

    results = []
    start_time = time.time()

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Create batches of concurrent requests
        for batch_start in range(0, num_requests, concurrency):
            batch_end = min(batch_start + concurrency, num_requests)
            batch_size = batch_end - batch_start

            # Create tasks for this batch
            tasks = [
                make_request(client, f"PROD-{i:03d}")
                for i in range(batch_start, batch_end)
            ]

            # Execute batch concurrently
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

            # Progress indicator
            if (batch_end % 100) == 0:
                print(f"Progress: {batch_end}/{num_requests} requests completed")

    total_duration = time.time() - start_time

    # Calculate statistics
    successful_requests = [r for r in results if r["success"]]
    failed_requests = [r for r in results if not r["success"]]
    durations = [r["duration"] for r in results]

    throughput = len(results) / total_duration
    avg_response_time = mean(durations) * 1000  # Convert to ms
    median_response_time = median(durations) * 1000
    p95_response_time = sorted(durations)[int(len(durations) * 0.95)] * 1000
    p99_response_time = sorted(durations)[int(len(durations) * 0.99)] * 1000

    # Print results
    print("\n" + "=" * 60)
    print("PERFORMANCE TEST RESULTS")
    print("=" * 60)
    print(f"Total Requests:       {len(results)}")
    print(f"Successful:           {len(successful_requests)} ({len(successful_requests)/len(results)*100:.1f}%)")
    print(f"Failed:               {len(failed_requests)} ({len(failed_requests)/len(results)*100:.1f}%)")
    print(f"Total Duration:       {total_duration:.2f}s")
    print(f"Throughput:           {throughput:.1f} req/sec")
    print(f"\nResponse Times:")
    print(f"  Average:            {avg_response_time:.2f}ms")
    print(f"  Median:             {median_response_time:.2f}ms")
    print(f"  95th percentile:    {p95_response_time:.2f}ms")
    print(f"  99th percentile:    {p99_response_time:.2f}ms")
    print("=" * 60)

    # Check requirements
    print("\nREQUIREMENTS CHECK:")
    throughput_met = throughput >= 100
    p95_met = p95_response_time < 100

    print(f"  Throughput ≥ 100 req/sec:     {'✓ PASS' if throughput_met else '✗ FAIL'} ({throughput:.1f} req/sec)")
    print(f"  P95 response time < 100ms:    {'✓ PASS' if p95_met else '✗ FAIL'} ({p95_response_time:.2f}ms)")

    if throughput_met and p95_met:
        print("\n✓ All performance requirements met!")
        return 0
    else:
        print("\n✗ Some performance requirements not met")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(run_performance_test(num_requests=1000, concurrency=10))
    sys.exit(exit_code)
