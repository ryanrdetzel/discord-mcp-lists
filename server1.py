# server.py
from fastmcp import FastMCP

mcp = FastMCP("Demo 🚀")


@mcp.tool()
def create_list(channel_id: str, list_name: str) -> str:
    """Creates a new list for a channel"""
    # Do magic
    return f"{list_name} created in channel {channel_id}"


if __name__ == "__main__":
    # mcp.run()
    mcp.run(transport="sse", host="127.0.0.1", port=8001)
