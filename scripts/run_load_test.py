import asyncio
import time
from httpx import AsyncClient, ASGITransport
from services.api.main import app

CONCURRENCY = 20
TOTAL_REQUESTS = 100


async def worker(client: AsyncClient, latencies: list, errors: list):
    for _ in range(TOTAL_REQUESTS // CONCURRENCY):
        t0 = time.time()
        try:
            res = await client.get("/api/v1/health")
            elapsed = (time.time() - t0) * 1000
            if res.status_code == 200:
                latencies.append(elapsed)
            else:
                errors.append(res.status_code)
        except Exception as e:
            errors.append(str(e))


async def run_benchmark():
    print(f"🚀 Starting TrustCounsel AI Concurrency Load Test ({TOTAL_REQUESTS} requests, {CONCURRENCY} concurrent workers)...")
    latencies = []
    errors = []

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        start_time = time.time()
        tasks = [worker(client, latencies, errors) for _ in range(CONCURRENCY)]
        await asyncio.gather(*tasks)
        total_time = time.time() - start_time

    if not latencies:
        print("❌ All requests failed.")
        return

    latencies.sort()
    p50 = latencies[int(len(latencies) * 0.50)]
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]
    rps = len(latencies) / total_time

    print("\n📊 Benchmark Results:")
    print(f"  • Total Completed: {len(latencies)}")
    print(f"  • Total Errors:    {len(errors)} (Error Rate: {len(errors)/TOTAL_REQUESTS*100:.2f}%)")
    print(f"  • Throughput:      {rps:.1f} req/sec")
    print(f"  • P50 Latency:     {p50:.2f} ms")
    print(f"  • P95 Latency:     {p95:.2f} ms")
    print(f"  • P99 Latency:     {p99:.2f} ms")
    print(f"  • Total Duration:  {total_time:.2f} s")

    assert len(errors) == 0, "Benchmark failed: error rate > 0%"
    assert p95 < 200.0, "Benchmark failed: P95 latency > 200ms"
    print("\n✅ All performance SLAs met!")


if __name__ == "__main__":
    asyncio.run(run_benchmark())
