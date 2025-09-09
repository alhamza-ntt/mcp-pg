import re
from typing import Any
from fastmcp.server.openapi import OpenAPITool
from fastmcp.tools.tool_transform import ArgTransformConfig, ToolTransformConfig
from fastmcp import FastMCP

def remove_links(text: str) -> str:
    # Replace markdown links text with just 'text'
    return re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

def get_arg_transform_config(parameters: dict[str, Any]) -> dict[str, ArgTransformConfig]:
    properties = parameters["properties"]
    transform_args = {}
    for key, value in properties.items():
        description = value.get("description")
        if description:
            transform_args[key] = ArgTransformConfig(description=remove_links(description))
    return transform_args

def get_tags(tool: OpenAPITool) -> set[str]:
    return set([tool._route.method, tool._route.path[1:]])

def get_tool_transform_config(tool: OpenAPITool) -> ToolTransformConfig:
    return ToolTransformConfig(description=remove_links(tool.description), arguments=get_arg_transform_config(tool.parameters), tags=get_tags(tool))

async def perform_tool_transformation(mcp_server: FastMCP) -> None:
    for tool_name in await mcp_server.get_tools():
        tool = await mcp_server.get_tool(tool_name)
        mcp_server.add_tool_transformation(tool_name, get_tool_transform_config(tool))