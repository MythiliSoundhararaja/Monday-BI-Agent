import asyncio
from app.monday_client import monday_client
from app.config import get_settings

async def debug_monday_data():
    settings = get_settings()

    print("=" * 60)
    print("WORK ORDERS BOARD:")
    print("=" * 60)
    work_orders = await monday_client.fetch_work_orders(settings.WORK_ORDERS_BOARD_ID)
    print(f"Found {len(work_orders)} work orders")
    for item in work_orders[:3]:  # First 3 items
        print(f"  Item: {item.get('name')} → {item}")

    print()
    print("=" * 60)
    print("DEALS BOARD:")
    print("=" * 60)
    deals = await monday_client.fetch_deals(settings.DEALS_BOARD_ID)
    print(f"Found {len(deals)} deals")
    for item in deals[:3]:
        print(f"  Item: {item.get('name')} → {item}")

asyncio.run(debug_monday_data())
