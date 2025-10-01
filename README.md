# Ed Stem MCP Server

Model Context Protocol (MCP) server for Ed Discussion platform integration.

## Features

This MCP server provides Claude Code with tools to interact with Ed Stem:

- **Get user info**: View your enrolled courses
- **List threads**: Browse course discussions with filters (unresolved, unanswered, etc.)
- **Get thread**: Read full thread with all comments
- **Post thread**: Create new discussion threads
- **Edit thread**: Update existing threads
- **Search threads**: Find threads by keywords
- **List users**: View course enrollment

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd edstem-mcp
```

2. Create virtual environment and install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Get your Ed API token:
   - Go to https://edstem.org/us/settings/api-tokens
   - Create a new token
   - Copy the token value

4. Create `.env` file:
```bash
cp .env.example .env
# Edit .env and add your token
```

## Configuration

Add to your Claude Code MCP settings file:

**Linux/Mac**: `~/.claude_code/mcp_settings.json`

```json
{
  "mcpServers": {
    "edstem": {
      "command": "/home/jeremy/edstem-mcp/venv/bin/python",
      "args": ["/home/jeremy/edstem-mcp/server.py"],
      "env": {
        "ED_API_TOKEN": "your_token_here"
      }
    }
  }
}
```

Replace `/home/jeremy` with your actual home directory path, and add your actual token.

## Usage Examples

Once configured, you can use natural language in Claude Code:

- "List recent threads in my CSE 421 course"
- "Show me unanswered questions in course 12345"
- "Create a thread asking about the homework deadline"
- "Search for threads about dynamic programming"
- "Get details for thread #6789"

## Available Tools

### `get_user_info`
Get information about authenticated user and enrolled courses.

### `list_threads`
List threads in a course with optional filtering.
- **Parameters**: `course_id`, `limit`, `sort` (new/top/trending), `filter` (unresolved/unanswered/following/mine)

### `get_thread`
Get detailed thread information including all comments.
- **Parameters**: `thread_id`

### `post_thread`
Create a new thread.
- **Parameters**: `course_id`, `title`, `content`, `category`, `subcategory`, `is_private`, `is_anonymous`

### `edit_thread`
Edit an existing thread.
- **Parameters**: `thread_id`, `title`, `content`, `category`

### `search_threads`
Search for threads by keyword.
- **Parameters**: `course_id`, `query`, `limit`

### `list_users`
List users enrolled in a course.
- **Parameters**: `course_id`, `filter` (student/staff/tutor)

## Resources

The server exposes:
- `edstem://user` - Current user information and courses

## Security Notes

- **Treat your API token as a password** - anyone with it can access your Ed account
- Never commit `.env` or tokens to version control
- The Ed API is in beta and may change without notice

## License

MIT

## Credits

Uses the unofficial [edapi](https://github.com/smartspot2/edapi) library for Ed Stem API access.
