# 数据库模块详解

本文档面向刚接触数据库编程的新手，详细介绍这个项目的数据库连接和 Schema 提取功能。

---

## 数据库来源

本项目是一个**金融科技（Fintech）数据分析业务**，聚焦于**小企业贷款（Small Business Loan）** 场景。

数据库中的所有数据来源于真实的小企业贷款业务，**在保持数据分布性质不变的前提下，已经去除所有敏感信息并进行了脱敏混淆**。因此可以放心用于开发、测试与教学，不会泄露任何客户隐私或商业机密。

数据文件托管在 GitHub Release。

**本地 SQLite 数据库路径：** `tmp/data.sqlite`

**下载/更新数据库：**

```bash
# 下载数据库文件（如果已存在则跳过）
.venv/bin/python scripts/01-database-operations/s01_download_sqlite_file.py

# 强制重新下载（覆盖旧文件）
# 修改 db_helper.py 中的 force=True，或直接删除 tmp/data.sqlite 后重新运行
```

**相关文件：**
- `labor_ward_ai/tests/db_helper.py` — 数据库下载工具函数
- `scripts/01-database-operations/s01_download_sqlite_file.py` — 下载脚本入口

数据源 URL：`https://github.com/michaelwangyc/hospital_maternity_operation_agent-project/releases/download/0.0.0/hospital_maternity_operation_agent.sqlite`

---

## 数据库业务模型

数据库名为 `smb_analytics_data`，围绕"贷款全生命周期"建模，主要包含以下表：

| 表名 | 含义 |
|------|------|
| `industry` | 行业字典（含基线违约率） |
| `loan_officer` | 信贷员（贷款专员） |
| `loan_status` | 贷款状态字典（如审批中、已放款、已逾期等） |
| `risk_grade` | 风险等级（含信用分区间、利率、隐含违约率） |
| `customer` | 小企业客户（行业、地区、营收、员工数、信用分等） |
| `application` | 贷款申请单 |
| `loan` | 已批准的贷款（金额、利率、期限、当前余额等） |
| `default_event` | 违约事件（违约日期、损失金额、是否有早期预警等） |
| `payment` | 实际还款记录 |
| `repayment_schedule` | 计划还款表 |

完整 Schema 见：`data/database-exploration/database-schema.txt`。

---

## 为什么 AI Agent 需要了解数据库结构？

AI Agent 的核心能力之一是**根据用户问题自动生成 SQL 查询**。

比如用户问："哪些贷款已经逾期违约了？"

Agent 需要知道：
- 违约信息在哪个表？（`default_event` 表）
- 怎么关联到具体客户？（`default_event.loan_id` → `loan.customer_id` → `customer`）
- 表名和字段名是什么？

**这些信息就是数据库的 Schema（结构）。**

所以我们需要：
1. **连接数据库** — 才能读取数据
2. **提取 Schema** — 告诉 AI 数据库长什么样
3. **执行查询** — 把 AI 生成的 SQL 跑起来

---

## 第一部分：数据库连接 (one_02_db.py)

### 两个数据库引擎

这个项目支持两种数据库：

| 数据库 | 用途 | 属性名 |
|--------|------|--------|
| SQLite | 本地开发用，数据存在文件里 | `local_sqlite_engine` |
| PostgreSQL | 远程生产用，云端数据库 | `remote_postgres_engine` |

```python
# labor_ward_ai/one/one_02_db.py

class DbMixin:
    @cached_property
    def local_sqlite_engine(self) -> sa.Engine:
        """本地 SQLite 数据库"""
        return sa.create_engine(f"sqlite:///{path_enum.path_sqlite_db}")

    @cached_property
    def remote_postgres_engine(self) -> sa.Engine:
        """远程 PostgreSQL 数据库"""
        url = sa.URL.create(
            drivername="postgresql+psycopg2",
            username=self.config.db_user,
            password=self.config.db_pass,
            host=self.config.db_host,
            port=self.config.db_port,
            database=self.config.db_name,
        )
        return sa.create_engine(url)
```

### 什么是 Engine？

**Engine（引擎）** 是 SQLAlchemy 的核心概念，它代表**与数据库的连接**。

**类比理解：**

把 Engine 想象成**电话线**：
- 你（Python 代码）想和数据库通话
- Engine 是连接你和数据库的那条线
- 有了 Engine，你就能发送 SQL 命令、接收查询结果

### engine 属性：自动选择

```python
@cached_property
def engine(self) -> sa.Engine:
    """根据环境自动选择数据库"""
    if runtime.is_local():
        return self.remote_postgres_engine  # 本地也用远程数据库
    else:
        raise NotImplementedError()
```

**注意：** 当前代码本地环境也使用远程 PostgreSQL。这是因为我们希望本地和生产环境使用相同的脱敏后数据。

### 懒加载 (@cached_property)

注意所有 engine 都用了 `@cached_property`：

- **第一次访问** `one.engine` → 创建数据库连接
- **后续访问** → 直接返回已有连接

这样避免了每次使用都重新连接数据库（连接是昂贵操作）。

---

## 第二部分：Schema 提取 (db_schema 模块)

AI Agent 需要知道数据库的结构才能写 SQL。但原始的数据库元数据太复杂、太长，直接给 AI 会：
- 浪费 token（花更多钱）
- 超出上下文长度限制
- AI 理解起来困难

所以我们需要**提取并压缩** Schema 信息。

### 三层架构：Model → Extractor → Encoder

```
数据库
  ↓
Extractor（提取器）
  ↓
Model（数据模型）
  ↓
Encoder（编码器）
  ↓
LLM 友好的紧凑字符串
```

让我们按顺序看每一层。

---

### 第一层：Model（数据模型）— model.py

**作用：** 定义用来**存放** Schema 信息的数据结构。

```python
# labor_ward_ai/db_schema/model.py

class ColumnInfo(BaseColumnInfo):
    """列信息"""
    name: str              # 列名，如 "customer_id"
    fullname: str          # 完整名，如 "loan.customer_id"
    type: str              # 原始类型，如 "VARCHAR(50)"
    llm_type: LLMTypeEnum  # 简化类型，如 "STR"
    primary_key: bool      # 是否是主键
    nullable: bool         # 是否可为空
    foreign_keys: list     # 外键列表

class TableInfo(BaseTableInfo):
    """表信息"""
    name: str              # 表名
    columns: list[ColumnInfo]  # 所有列
    primary_key: list[str]     # 主键列名列表
    foreign_keys: list         # 外键列表

class SchemaInfo(BaseSchemaInfo):
    """Schema 信息（一个 schema 包含多个表）"""
    name: str
    tables: list[TableInfo]

class DatabaseInfo(BaseDatabaseInfo):
    """数据库信息（一个数据库包含多个 schema）"""
    name: str
    db_type: DbTypeEnum    # SQLite / PostgreSQL / ...
    schemas: list[SchemaInfo]
```

**层级关系：**

```
DatabaseInfo
  └── SchemaInfo（可能有多个）
        └── TableInfo（可能有多个）
              └── ColumnInfo（可能有多个）
```

**为什么用 Pydantic？**

这些类都继承自 Pydantic 的 BaseModel，好处是：
- 自动类型验证
- IDE 自动补全
- 可以轻松转成 JSON

---

### 第二层：Extractor（提取器）— extractor.py

**作用：** 从真实数据库中**读取**元数据，填充到 Model 里。

#### 核心流程

```
SQLAlchemy MetaData.reflect()
       ↓
遍历每个表 → new_table_info()
       ↓
遍历每个列 → new_column_info()
       ↓
返回填充好的 Model 对象
```

#### 关键函数

**1. sqlalchemy_type_to_llm_type() — 类型简化**

数据库有几十种数据类型（VARCHAR、TEXT、BIGINT、DECIMAL...），但对 AI 来说，只需要知道"这是字符串"还是"这是金额"。

```python
# 简化映射示例
VARCHAR(50)  → STR   # 字符串（如 business_name）
TEXT         → STR
INTEGER      → INT   # 整数（如 employee_count、credit_score）
BIGINT       → INT
DECIMAL(10,2)→ DEC   # 金额（如 approved_amount、outstanding_balance）
TIMESTAMP    → TS    # 时间戳
DATE         → DATE  # 日期（如 disbursement_date）
BOOLEAN      → BOOL  # 布尔值（如 is_repeat_customer）
```

**2. new_column_info() — 提取单列信息**

```python
def new_column_info(table, column) -> ColumnInfo:
    return ColumnInfo(
        name=column.name,
        type=str(column.type),           # 原始类型
        llm_type=sqlalchemy_type_to_llm_type(column.type),  # 简化类型
        primary_key=column.primary_key,
        nullable=column.nullable,
        foreign_keys=[...],               # 外键关系
    )
```

**3. new_table_info() — 提取单表信息**

```python
def new_table_info(table) -> TableInfo:
    columns = []
    for column in table.columns:
        columns.append(new_column_info(table, column))

    return TableInfo(
        name=table.name,
        columns=columns,
        primary_key=[col.name for col in table.primary_key.columns],
    )
```

**4. new_schema_info() — 提取整个 Schema**

```python
def new_schema_info(engine, metadata) -> SchemaInfo:
    tables = []
    for table in metadata.sorted_tables:
        tables.append(new_table_info(table))

    return SchemaInfo(tables=tables)
```

---

### 第三层：Encoder（编码器）— encoder.py

**作用：** 把 Model 对象**转换成**紧凑的字符串，供 AI 阅读。

#### 编码格式

这是最终给 AI 看的格式（节选自真实 schema）：

```
sqlite Database smb_analytics_data(
    Schema default(
        Table customer(
            id:int*PK,
            business_name:str*NN,
            tax_id:str*NN,
            industry_id:int*NN*FK->industry.id,
            state:str*NN,
            annual_revenue:dec*NN,
            employee_count:int*NN,
            credit_score:int*NN,
            is_repeat_customer:bool*NN,
        )
        Table loan(
            id:int*PK,
            loan_number:str*NN,
            application_id:int*NN*FK->application.id,
            customer_id:int*NN*FK->customer.id,
            risk_grade_id:int*NN*FK->risk_grade.id,
            approved_amount:dec*NN,
            interest_rate:float*NN,
            outstanding_balance:dec*NN,
        )
    )
)
```

#### 约束缩写

为了节省 token，约束用简短缩写：

| 缩写 | 含义 | 说明 |
|------|------|------|
| `*PK` | Primary Key | 主键 |
| `*UQ` | Unique | 唯一约束 |
| `*NN` | Not Null | 非空约束 |
| `*IDX` | Index | 有索引 |
| `*FK->Table.Column` | Foreign Key | 外键，指向哪个表的哪个列 |

#### 编码函数

**1. encode_column_info() — 编码单列**

```python
def encode_column_info(table_info, column_info) -> str:
    # 例：id:int*PK
    # 例：business_name:str*NN
    # 例：customer_id:int*NN*FK->customer.id

    col_name = column_info.name
    col_type = column_info.llm_type.value
    pk = "*PK" if column_info.name in table_info.primary_key else ""
    nn = "*NN" if not column_info.nullable else ""
    fk = "".join([f"*FK->{fk.name}" for fk in column_info.foreign_keys])

    return f"{col_name}:{col_type}{pk}{nn}{fk}"
```

**2. encode_table_info() — 编码单表**

```python
def encode_table_info(table_info) -> str:
    columns = [encode_column_info(table_info, col) for col in table_info.columns]
    return f"Table {table_info.name}(\n    {',\n    '.join(columns)}\n)"
```

**3. encode_database_info() — 编码整个数据库**

最终调用的是这个函数，它会递归编码所有层级。

---

## 第三部分：两个核心属性

### 1. database_schema_str — 获取 Schema 字符串

```python
@cached_property
def database_schema_str(self) -> str:
    """获取 LLM 优化格式的数据库 Schema"""
    # 1. 反射元数据
    metadata = sa.MetaData()
    metadata.reflect(bind=self.engine)

    # 2. 提取 Schema 信息
    schema_info = new_schema_info(engine=self.engine, metadata=metadata)
    database_info = new_database_info(
        name="smb_analytics_data",
        db_type=DbTypeEnum.SQLITE,
        schemas=[schema_info],
    )

    # 3. 编码成字符串
    return encode_database_info(database_info)
```

**用途：** AI Agent 调用 `get_database_schema` 工具时，返回这个字符串。AI 看到它就知道数据库有哪些表、哪些列。

### 2. execute_and_print_result — 执行 SQL 并格式化结果

```python
def execute_and_print_result(self, sql: str) -> str:
    """执行 SELECT 查询，返回 Markdown 表格"""
    return execute_and_print_result(engine=self.engine, sql=sql)
```

这个函数做三件事：
1. **验证** SQL 必须是 SELECT 语句（安全检查）
2. **执行** 查询
3. **格式化** 结果为 Markdown 表格

**为什么用 Markdown 表格？**

```markdown
| loan_number | business_name      | approved_amount | outstanding_balance |
|-------------|--------------------|-----------------|--------------------|
| L-2024-0017 | Northwind Supplies | 250000.00       | 187432.55          |
| L-2024-0042 | Acme Logistics     | 120000.00       | 98210.10           |
```

- **Token 效率高**：比 JSON 格式节省约 24% 的 token
- **AI 容易理解**：Markdown 是 AI 训练数据中常见的格式
- **人类也能读**：调试时一目了然

---

## 完整流程图

```
用户问："最近一年违约的贷款总共损失了多少？"
           ↓
AI Agent 调用 get_database_schema 工具
           ↓
one.database_schema_str 被访问
           ↓
SQLAlchemy metadata.reflect() 从数据库读取结构
           ↓
Extractor: new_schema_info() 提取信息
           ↓
Encoder: encode_database_info() 转成紧凑字符串
           ↓
AI 看到 Schema，生成 SQL：
"SELECT SUM(loss_amount) AS total_loss
   FROM default_event
  WHERE default_date >= DATE('now', '-1 year')"
           ↓
AI Agent 调用 execute_sql_query 工具
           ↓
one.execute_and_print_result(sql) 被调用
           ↓
执行 SQL，结果格式化为 Markdown 表格
           ↓
AI 读取结果，生成人类语言回答：
"过去 12 个月共发生 37 起违约，累计损失约 ¥4,820,000。"
```

---

## 测试代码

```python
# tests_python/one/test_one_one_02_db.py

class TestDbMixin:
    def test_database_schema_str(self):
        """测试 Schema 提取"""
        _ = one.database_schema_str
        # 能跑通就说明 Schema 提取成功

    def test_execute_and_print_result(self):
        """测试 SQL 执行"""
        sql = "SELECT 1;"
        _ = one.execute_and_print_result(sql)
        # 能跑通就说明数据库连接和查询都正常
```

运行测试：

```bash
mise run test-python
```

---

## 总结

| 组件 | 文件 | 作用 |
|------|------|------|
| `DbMixin` | `one/one_02_db.py` | 提供数据库连接 |
| `local_sqlite_engine` | 同上 | 本地 SQLite 连接 |
| `remote_postgres_engine` | 同上 | 远程 PostgreSQL 连接 |
| `database_schema_str` | 同上 | 获取 LLM 友好的 Schema 字符串 |
| `execute_and_print_result` | 同上 | 执行 SQL 返回 Markdown 表格 |
| Model | `db_schema/model.py` | 定义 Schema 数据结构 |
| Extractor | `db_schema/extractor.py` | 从数据库提取元数据 |
| Encoder | `db_schema/encoder.py` | 把元数据编码成紧凑字符串 |

**核心思想：**

1. **连接数据库** → Engine
2. **提取结构** → Model + Extractor
3. **压缩给 AI** → Encoder
4. **执行查询** → execute_and_print_result

这套系统让 AI Agent 能够"看懂"小企业贷款数据库，然后自主生成并执行 SQL 查询，回答信贷风险、放款表现、客户画像等业务问题。
