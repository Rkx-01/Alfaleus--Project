import httpx
import asyncio

async def trigger_sync():
    url = "https://alfaleus-project.onrender.com/api/v1/test"
    print(f"📡 Triggering news sync at {url}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            if response.status_code == 200:
                print("✅ Success! The backend has started fetching news.")
                print("⏳ Please wait about 60 seconds for the AI to process the news...")
            else:
                print(f"❌ Failed. Status code: {response.status_code}")
                print(f"Details: {response.text}")
    except Exception as e:
        print(f"❌ Error connecting to backend: {e}")

if __name__ == "__main__":
    asyncio.run(trigger_sync())
