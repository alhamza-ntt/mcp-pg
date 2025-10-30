import asyncio
from fastmcp import Client
import random


azclinet = "https://pg-aib-afgmech7ccdqdedh.canadacentral-01.azurewebsites.net/"
sapclinet = "https://mcp-api.cfapps.us10-001.hana.ondemand.com"
local = "http://localhost:8000"


async def main():
    async with Client(f"{local}/mcp") as client:
        
        tools = await client.list_tools()
        
        print("Generated Tools:")
        print(len(tools))
        for tool in tools:
            print(f"- {tool.name} ")

if __name__ == "__main__":
    asyncio.run(main())