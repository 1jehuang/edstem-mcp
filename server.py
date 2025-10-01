#!/usr/bin/env python3
"""
Ed Stem MCP Server

Provides MCP tools for interacting with Ed Discussion platform.
"""

import os
import sys
import json
from typing import Any
from mcp.server import Server
from mcp.types import Tool, TextContent, Resource, EmbeddedResource
import mcp.types as types
from edapi import EdAPI

# Initialize Ed API client
ed_client = None

def init_ed_client():
    """Initialize Ed API client with token from environment."""
    global ed_client
    if ed_client is None:
        token = os.getenv('ED_API_TOKEN')
        if not token:
            raise ValueError("ED_API_TOKEN environment variable not set")

        ed_client = EdAPI(api_token=token)
        ed_client.login()
    return ed_client

# Initialize MCP server
server = Server("edstem")

@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available Ed resources."""
    return [
        Resource(
            uri="edstem://user",
            name="Current User Info",
            description="Information about the authenticated user and their courses",
            mimeType="application/json"
        )
    ]

@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read an Ed resource."""
    client = init_ed_client()

    if uri == "edstem://user":
        user_info = client.get_user_info()
        return json.dumps(user_info, indent=2)

    raise ValueError(f"Unknown resource: {uri}")

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available Ed tools."""
    return [
        Tool(
            name="get_user_info",
            description="Get information about the authenticated user and their enrolled courses",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="list_threads",
            description="List threads in a course. Returns threads with their metadata.",
            inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {
                        "type": "number",
                        "description": "The course ID to list threads from"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of threads to return (default: 30)",
                        "default": 30
                    },
                    "sort": {
                        "type": "string",
                        "description": "Sort order: 'new', 'top', 'trending' (default: 'new')",
                        "enum": ["new", "top", "trending"],
                        "default": "new"
                    },
                    "filter": {
                        "type": "string",
                        "description": "Filter: 'unresolved', 'unanswered', 'following', 'mine' (optional)",
                        "enum": ["unresolved", "unanswered", "following", "mine"]
                    }
                },
                "required": ["course_id"]
            }
        ),
        Tool(
            name="get_thread",
            description="Get detailed information about a specific thread, including all comments",
            inputSchema={
                "type": "object",
                "properties": {
                    "thread_id": {
                        "type": "number",
                        "description": "The thread ID to retrieve"
                    }
                },
                "required": ["thread_id"]
            }
        ),
        Tool(
            name="post_thread",
            description="Create a new thread in a course",
            inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {
                        "type": "number",
                        "description": "The course ID to post to"
                    },
                    "title": {
                        "type": "string",
                        "description": "Thread title"
                    },
                    "content": {
                        "type": "string",
                        "description": "Thread content (plain text or HTML)"
                    },
                    "category": {
                        "type": "string",
                        "description": "Thread category (optional)"
                    },
                    "subcategory": {
                        "type": "string",
                        "description": "Thread subcategory (optional)"
                    },
                    "is_private": {
                        "type": "boolean",
                        "description": "Whether the thread is private (visible only to staff)",
                        "default": False
                    },
                    "is_anonymous": {
                        "type": "boolean",
                        "description": "Whether to post anonymously",
                        "default": False
                    }
                },
                "required": ["course_id", "title", "content"]
            }
        ),
        Tool(
            name="edit_thread",
            description="Edit an existing thread",
            inputSchema={
                "type": "object",
                "properties": {
                    "thread_id": {
                        "type": "number",
                        "description": "The thread ID to edit"
                    },
                    "title": {
                        "type": "string",
                        "description": "New thread title (optional)"
                    },
                    "content": {
                        "type": "string",
                        "description": "New thread content (optional)"
                    },
                    "category": {
                        "type": "string",
                        "description": "New category (optional)"
                    }
                },
                "required": ["thread_id"]
            }
        ),
        Tool(
            name="list_users",
            description="List users enrolled in a course",
            inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {
                        "type": "number",
                        "description": "The course ID"
                    },
                    "filter": {
                        "type": "string",
                        "description": "Filter by role: 'student', 'staff', 'tutor' (optional)"
                    }
                },
                "required": ["course_id"]
            }
        ),
        Tool(
            name="search_threads",
            description="Search for threads in a course by keywords",
            inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {
                        "type": "number",
                        "description": "The course ID to search in"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of results (default: 20)",
                        "default": 20
                    }
                },
                "required": ["course_id", "query"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    client = init_ed_client()

    try:
        if name == "get_user_info":
            result = client.get_user_info()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "list_threads":
            course_id = arguments["course_id"]
            limit = arguments.get("limit", 30)
            sort = arguments.get("sort", "new")
            filter_type = arguments.get("filter")

            result = client.list_threads(
                course_id=course_id,
                limit=limit,
                sort=sort,
                filter=filter_type
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_thread":
            thread_id = arguments["thread_id"]
            result = client.get_thread(thread_id)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "post_thread":
            result = client.post_thread(
                course_id=arguments["course_id"],
                title=arguments["title"],
                content=arguments["content"],
                category=arguments.get("category"),
                subcategory=arguments.get("subcategory"),
                is_private=arguments.get("is_private", False),
                is_anonymous=arguments.get("is_anonymous", False)
            )
            return [TextContent(type="text", text=f"Thread created successfully: {json.dumps(result, indent=2)}")]

        elif name == "edit_thread":
            thread_id = arguments["thread_id"]
            updates = {k: v for k, v in arguments.items() if k != "thread_id" and v is not None}
            result = client.edit_thread(thread_id, **updates)
            return [TextContent(type="text", text=f"Thread updated successfully: {json.dumps(result, indent=2)}")]

        elif name == "list_users":
            course_id = arguments["course_id"]
            filter_type = arguments.get("filter")
            result = client.list_users(course_id, role=filter_type)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "search_threads":
            # EdAPI doesn't have direct search, so we'll list and filter
            course_id = arguments["course_id"]
            query = arguments["query"].lower()
            limit = arguments.get("limit", 20)

            threads = client.list_threads(course_id, limit=100)

            # Filter threads by query
            matching = []
            for thread in threads.get("threads", []):
                title = thread.get("title", "").lower()
                if query in title:
                    matching.append(thread)
                    if len(matching) >= limit:
                        break

            return [TextContent(type="text", text=json.dumps({"threads": matching}, indent=2))]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    """Main entry point for the server."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
