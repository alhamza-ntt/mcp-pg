import asyncio
from fastmcp import Client
import random

async def main():
    async with Client("http://127.0.0.1:8000/mcp/") as client:
        
        rand = random.randint(1, 10)
        tools = await client.list_tools()
        print(tools)
        """
        print("Generated Tools:")
        for tool in tools:
            print(f"- {tool.name}")
        print(tool.description)
       
        print(f"\n\nCalling tool 'get_user_by_id for user {rand}'...")
        user = await client.call_tool("get_user_by_id", {"id": rand})
        print(f"Result:\n{user.data}")


        print(f"\n\nCalling tool 'get_post_by_id for post {rand}'...")
        post = await client.call_tool("get_post_by_id", {"id": rand}) 
        print(f"Result:\n{post.data}")
        """ 
    

if __name__ == "__main__":
    asyncio.run(main())