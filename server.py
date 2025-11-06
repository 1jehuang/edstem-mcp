#!/usr/bin/env python3
"""
Ed Stem MCP Server

Provides MCP tools for interacting with Ed Discussion platform.
"""

import os
import sys
import json
import logging
from typing import Any
from mcp.server import Server
from mcp.types import Tool, TextContent, Resource, EmbeddedResource
import mcp.types as types
from edapi import EdAPI
from edapi.types import EdAuthError, EdError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/edstem-mcp.log'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger('edstem-mcp')

# Initialize Ed API client
ed_client = None

def init_ed_client():
    """Initialize Ed API client with token from environment."""
    global ed_client
    if ed_client is None:
        logger.info("Initializing Ed API client")
        token = os.getenv('ED_API_TOKEN')
        if not token:
            logger.error("ED_API_TOKEN environment variable not set")
            raise ValueError("ED_API_TOKEN environment variable not set")

        # EdAPI loads token from environment automatically
        ed_client = EdAPI()
        # Token should already be loaded, but verify
        if ed_client.api_token is None:
            ed_client.api_token = token
        logger.info("Ed API client initialized successfully")
    return ed_client

# Initialize MCP server
server = Server("edstem")

def _apply_thread_filter(threads: list, filter_type: str) -> list:
    """Apply client-side filtering to threads.

    Args:
        threads: List of thread objects
        filter_type: One of 'unresolved', 'unanswered', 'mine', 'following'

    Returns:
        Filtered list of threads
    """
    logger.debug(f"Applying filter: {filter_type}")

    if filter_type == "unresolved":
        return [t for t in threads if not t.get("is_resolved", False)]
    elif filter_type == "unanswered":
        return [t for t in threads if not t.get("is_answered", False)]
    elif filter_type == "mine":
        # Get current user ID from client
        try:
            user_info = ed_client.get_user_info()
            user_id = user_info["user"]["id"]
            return [t for t in threads if t.get("user", {}).get("id") == user_id]
        except Exception as e:
            logger.error(f"Failed to get user ID for 'mine' filter: {e}")
            return threads
    elif filter_type == "following":
        return [t for t in threads if t.get("is_following", False)]
    else:
        logger.warning(f"Unknown filter type: {filter_type}")
        return threads

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
                    "offset": {
                        "type": "number",
                        "description": "Offset for pagination (default: 0)",
                        "default": 0
                    },
                    "sort": {
                        "type": "string",
                        "description": "Sort order: 'new', 'top', 'trending' (default: 'new')",
                        "enum": ["new", "top", "trending"],
                        "default": "new"
                    },
                    "filter": {
                        "type": "string",
                        "description": "Filter threads: 'unresolved' (not resolved), 'unanswered' (no answers), 'mine' (created by you), 'following' (you're following)",
                        "enum": ["unresolved", "unanswered", "mine", "following"]
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
    logger.info(f"Tool call: {name} with arguments: {arguments}")

    try:
        client = init_ed_client()

        if name == "get_user_info":
            result = client.get_user_info()
            # Summarize to avoid token limit - just show user and course list
            summary = {
                "user": result.get("user", {}),
                "courses": [
                    {
                        "id": c["course"]["id"],
                        "code": c["course"].get("code"),
                        "name": c["course"].get("name"),
                        "role": c.get("role")
                    }
                    for c in result.get("courses", [])
                ]
            }
            logger.info(f"Retrieved user info for {summary['user'].get('name')}")
            return [TextContent(type="text", text=json.dumps(summary, indent=2))]

        elif name == "list_threads":
            course_id = arguments["course_id"]
            limit = arguments.get("limit", 30)
            offset = arguments.get("offset", 0)
            sort = arguments.get("sort", "new")
            filter_type = arguments.get("filter")

            logger.info(f"Listing threads for course {course_id} (limit={limit}, offset={offset}, sort={sort}, filter={filter_type})")

            # Get threads from API
            threads = client.list_threads(
                course_id,
                limit=limit,
                offset=offset,
                sort=sort
            )

            # Apply client-side filtering if specified
            if filter_type:
                threads = _apply_thread_filter(threads, filter_type)

            # Standardize output format
            result = {
                "threads": threads,
                "count": len(threads),
                "limit": limit,
                "offset": offset
            }

            logger.info(f"Retrieved {len(threads)} threads")
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_thread":
            thread_id = arguments["thread_id"]
            logger.info(f"Getting thread {thread_id}")
            result = client.get_thread(thread_id)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "post_thread":
            from edapi.types import PostThreadParams

            # Build proper PostThreadParams dict
            params: PostThreadParams = {
                "type": "post",
                "title": arguments["title"],
                "content": arguments["content"],
                "is_private": arguments.get("is_private", False),
                "is_anonymous": arguments.get("is_anonymous", False)
            }

            if arguments.get("category"):
                params["category"] = arguments["category"]
            if arguments.get("subcategory"):
                params["subcategory"] = arguments["subcategory"]

            course_id = arguments["course_id"]
            logger.info(f"Creating thread in course {course_id}: {arguments['title']}")

            result = client.post_thread(course_id, params)
            logger.info(f"Thread created successfully: {result.get('id')}")
            return [TextContent(type="text", text=f"Thread created successfully:\n{json.dumps(result, indent=2)}")]

        elif name == "edit_thread":
            from edapi.types import EditThreadParams

            thread_id = arguments["thread_id"]

            # Build proper EditThreadParams dict
            params: EditThreadParams = {}
            if arguments.get("title"):
                params["title"] = arguments["title"]
            if arguments.get("content"):
                params["content"] = arguments["content"]
            if arguments.get("category"):
                params["category"] = arguments["category"]

            logger.info(f"Editing thread {thread_id}")
            result = client.edit_thread(thread_id, params)
            logger.info(f"Thread {thread_id} updated successfully")
            return [TextContent(type="text", text=f"Thread updated successfully:\n{json.dumps(result, indent=2)}")]

        elif name == "list_users":
            course_id = arguments["course_id"]
            logger.info(f"Listing users for course {course_id}")
            result = client.list_users(course_id)
            logger.info(f"Retrieved {len(result)} users")
            return [TextContent(type="text", text=json.dumps({"users": result, "count": len(result)}, indent=2))]

        elif name == "search_threads":
            # EdAPI doesn't have direct search, so we'll list and filter
            course_id = arguments["course_id"]
            query = arguments["query"].lower()
            limit = arguments.get("limit", 20)

            logger.info(f"Searching threads in course {course_id} for query: {query}")

            threads = client.list_threads(course_id, limit=100)

            # Filter threads by query in title and content
            matching = []
            for thread in threads:
                title = thread.get("title", "").lower()
                content = thread.get("content", "").lower()
                if query in title or query in content:
                    matching.append(thread)
                    if len(matching) >= limit:
                        break

            logger.info(f"Found {len(matching)} matching threads")
            return [TextContent(type="text", text=json.dumps({"threads": matching, "count": len(matching), "query": arguments["query"]}, indent=2))]

        else:
            logger.error(f"Unknown tool: {name}")
            raise ValueError(f"Unknown tool: {name}")

    except EdAuthError as e:
        error_msg = f"Authentication error: {str(e)}"
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]

    except EdError as e:
        error_msg = f"Ed API error: {str(e)}"
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]

    except ValueError as e:
        error_msg = f"Invalid input: {str(e)}"
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]

    except KeyError as e:
        error_msg = f"Missing required parameter: {str(e)}"
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]

    except Exception as e:
        error_msg = f"Unexpected error: {type(e).__name__}: {str(e)}"
        logger.exception(error_msg)
        return [TextContent(type="text", text=error_msg)]

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
