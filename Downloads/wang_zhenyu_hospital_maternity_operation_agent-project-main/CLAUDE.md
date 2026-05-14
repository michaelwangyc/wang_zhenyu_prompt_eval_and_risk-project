## Code Architecture

### Entry Point

```python
from labor_ward_ai.api import one  # Main singleton instance
```

### Directory Structure

```
labor_ward_ai/
├── api.py
├── paths.py
├── runtime.py
├── constants.py
├── sql_utils.py
├── ai_sdk_adapter.py
│
├── config/
│   └── conf_00_def.py
│
├── one/
│   ├── one_00_main.py
│   ├── one_01_config.py
│   ├── one_02_db.py
│   ├── one_03_boto3.py
│   ├── one_04_agent.py
│   └── api.py
│
├── prompts/
│   └── bi-agent-system-prompt.md
│
└── db_schema/
```

### When to Modify Each File

**Root Level Modules:**

| File | What It Does | When to Modify |
|------|--------------|----------------|
| `api.py` | Re-exports `one` singleton | Rarely. Only if you need to expose additional top-level imports. |
| `paths.py` | Defines all file/directory paths as `PathEnum` | When adding new files (prompts, data files, output paths). Add path here first, then use `path_enum.your_new_path` everywhere. |
| `runtime.py` | Detects runtime environment (local vs vercel) | When adding a new deployment target (e.g., AWS Lambda). Add new enum value and detection logic. |
| `constants.py` | Enums and constants | When adding new enum types or magic values that need to be shared across modules. |
| `sql_utils.py` | Pure functions for SQL execution and formatting | When changing how SQL results are formatted or adding new query validation rules. |
| `ai_sdk_adapter.py` | Converts Vercel AI SDK format <-> Bedrock format | When frontend message format changes or when switching to a different LLM provider. |

**config/ Directory:**

| File | What It Does | When to Modify |
|------|--------------|----------------|
| `conf_00_def.py` | Config dataclass with env vars, credentials, settings | When adding new environment variables (add field + load in `new_in_local_runtime()` and `new_in_vercel_runtime()`). |

**one/ Directory (Main Class + Mixins):**

| File | What It Does | When to Modify |
|------|--------------|----------------|
| `one_00_main.py` | Defines `One` class that inherits all mixins; creates `one` singleton | When adding a new mixin (import it and add to inheritance list). |
| `one_01_config.py` | `ConfigMixin`: provides `self.config` | Rarely. Config loading logic is in `conf_00_def.py`. |
| `one_02_db.py` | `DbMixin`: provides `self.engine`, `self.local_sqlite_engine`, `self.remote_postgres_engine` | When adding new database connections or changing engine selection logic. |
| `one_03_boto3.py` | `Boto3Mixin`: provides `self.boto_ses`, `self.bedrock_runtime_client()` | When adding new AWS service clients (S3, DynamoDB, etc.). |
| `one_04_agent.py` | `AgentMixin`: provides `self.agent` and all `@tool` methods | **Most common edit.** When adding/modifying agent tools. Add `@tool` method here, then register in `self.agent`'s `tools=[]` list. |
| `api.py` | Exports `one = One()` singleton | Rarely. Only touched when restructuring exports. |

**prompts/ Directory:**

| File | What It Does | When to Modify |
|------|--------------|----------------|
| `bi-agent-system-prompt.md` | System prompt for the BI agent | When changing agent behavior, adding tool usage instructions, or updating workflow guidelines. |

**db_schema/ Directory:**

| File | What It Does | When to Modify |
|------|--------------|----------------|
| (multiple files) | Extracts and encodes database schema in LLM-optimized format | When changing schema representation format or adding support for new database types. |

### Class Hierarchy

```
One (one_00_main.py)
├── ConfigMixin (one_01_config.py)
│   └── self.config -> Config instance (from conf_00_def.py)
│
├── DbMixin (one_02_db.py)
│   ├── self.local_sqlite_engine   -> SQLite (tmp/data.sqlite)
│   ├── self.remote_postgres_engine -> PostgreSQL (NeonDB)
│   ├── self.engine                -> Auto-selects based on runtime
│   ├── self.database_schema_str   -> LLM-optimized schema string
│   └── self.execute_and_print_result(sql) -> Markdown table
│
├── Boto3Mixin (one_03_boto3.py)
│   ├── self.boto_ses              -> boto3.Session
│   └── self.bedrock_runtime_client() -> BedrockRuntimeClient
│
└── AgentMixin (one_04_agent.py)
    ├── self.bedrock_model         -> BedrockModel (strands)
    ├── self.agent                 -> Agent with tools
    └── @tool methods:
        ├── tool_get_database_schema
        ├── tool_execute_sql_query
        └── tool_write_debug_report
```

### Pure Functions vs Bound Methods

| Type | Location | Characteristics |
|------|----------|-----------------|
| **Pure Functions** | `sql_utils.py` | Take `engine` as first param, no class dependency |
| **Bound Methods** | `one/one_*.py` | Use `self.config`, `self.engine`, etc. |

**Pure Functions (sql_utils.py):**
- `format_result(result)` - Format SQL result as Markdown table
- `ensure_valid_select_query(query)` - Validate SELECT statement
- `execute_and_print_result(engine, sql)` - Execute query and return Markdown

### Key Singletons

```python
from labor_ward_ai.api import one           # Main app instance
from labor_ward_ai.paths import path_enum   # All paths
from labor_ward_ai.runtime import runtime   # Runtime detection
```

### Agent Framework

- **Library**: `strands` (Strands Agents SDK)
- **Model**: AWS Bedrock (configurable via `config.model_id`)
- **Tools**: Defined with `@tool` decorator in `one_04_agent.py`
- **System Prompt**: `labor_ward_ai/prompts/bi-agent-system-prompt.md`

---

## Development Setup

**Package Managers:**
- Python: uv (via mise)
- Node.js: pnpm (via mise)

**Core Configuration Files:**
- `mise.toml` - Project tasks and tool versions (Python 3.12, Node 24, uv, pnpm)
- `pyproject.toml` - Python dependencies and project metadata
- `package.json` - Node.js dependencies
- `.venv/` - Python virtual environment directory
- `node_modules/` - Node.js dependencies directory

**Environment Variables (.env):**
```bash
DB_HOST=ep-xxx-pooler.us-east-1.aws.neon.tech
DB_PORT=5432
DB_USER=neondb_owner
DB_PASS=your_password
DB_NAME=neondb
```

---

## Tests

**Python Tests:**
- Location: `tests_python/`
- Runner: pytest
- Command: `mise run test-python`

**Test File Mapping:**
```
tests_python/
├── config/
│   └── test_config_conf_00_def.py  # Tests for Config class
├── one/
│   ├── test_one_one_00_main.py     # Tests for One class
│   ├── test_one_one_01_config.py   # Tests for ConfigMixin
│   └── test_one_one_02_db.py       # Tests for DbMixin
├── test_api.py                     # Tests for api.py
├── test_write_operations.py        # Tests for write operations
└── test_utils.py                   # Tests for utilities
```

**Node.js Tests:**
- Location: `tests_node/`
- Runner: Node's built-in test module
- Command: `mise run test-node`

---

## Available Tasks

- `mise run venv-create` - Create Python virtual environment
- `mise run venv-remove` - Remove virtual environment
- `mise run inst-python-deps` - Install Python dependencies
- `mise run inst-node-deps` - Install Node.js dependencies
- `mise run inst` - Install all dependencies (Python + Node.js)
- `mise run test-python` - Run Python tests
- `mise run test-node` - Run Node.js tests
- `mise run test` - Run all tests (Python + Node.js)
- `mise run export` - Export Python requirements to requirements.txt
- `mise run dev` - Start all development servers (Next.js + FastAPI, auto-kills old instances first)
- `mise run kill` - Kill all running development servers

---

## Database

**Schema Reference:**
- `data/database-exploration/database-schema.txt` - Database schema (read only when needed)

**Run SQL Locally:**
```bash
.venv/bin/python scripts/test_run_sql_locally_cli.py --sql "SELECT * FROM table_name LIMIT 5"
```

**Print LLM-Optimized Schema:**
```bash
.venv/bin/python scripts/test_print_database_schema.py
```
