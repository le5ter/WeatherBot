import asyncio
import aiohttp
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

url = "https://api.gismeteo.net/v2/weather/current/5026/"
#5026, 4368
headers = {
    "X-Gismeteo-Token": f'{os.getenv("API_TOKEN")}',
    "Accept-Encoding": "gzip"
}


async def main():
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as response:
            json_body = await response.json()
            print(json_body)


if __name__ == '__main__':
    asyncio.run(main())