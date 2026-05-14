# 数据库同步详解

本文档面向刚接触数据库的新手，解释为什么需要数据库同步，以及这个项目是怎么实现的。

---

## 为什么需要数据库同步？

这个项目有两个数据库：

| 数据库 | 类型 | 位置 | 用途 |
|--------|------|------|------|
| 本地数据库 | SQLite | `tmp/data.sqlite` | 开发时的原始数据 |
| 远程数据库 | PostgreSQL (NeonDB) | 云端 | Agent 实际使用的数据库 |

**为什么要两个？**

1. **本地 SQLite** — 数据存在文件里，方便下载、分享、版本控制。不需要安装数据库服务器，本地开发非常方便。

2. **远程 PostgreSQL** — 生产环境用的真实数据库，支持多用户并发访问，AI Agent 连接的就是它。

**问题来了：** 数据在本地 SQLite 里，怎么让远程 PostgreSQL 也有相同的数据？

**答案：同步（Sync）。** 把本地 SQLite 的数据"搬"到远程 PostgreSQL。

---

## 什么时候需要同步？

### 场景 1：首次部署

你刚把项目部署到 Vercel，远程数据库是空的。需要同步本地数据上去。

### 场景 2：测试后重置

你在 Chat 界面测试了很多操作：
- 转移了几个患者
- 创建了一堆警报
- 安排了几个手术

数据已经"乱了"，想恢复到初始状态。

### 场景 3：本地数据更新

你更新了本地 SQLite 的数据（比如添加了新患者），需要同步到远程。

**同步的本质：用本地数据覆盖远程数据。** 本地是"真理来源"（Source of Truth），远程是它的副本。

---

## 同步的挑战

把数据从 SQLite 搬到 PostgreSQL，听起来简单，实际上有几个坑：

### 挑战 1：表之间有依赖关系（外键）

外键（Foreign Key）是表之间的"引用"关系：

```
patient（患者）
    ↓ 被引用
admission（入院记录）— 通过 patient_id 引用 patient
    ↓ 被引用
bed（床位）— 通过 current_admission_id 引用 admission
```

如果先插入 `bed`，但 `admission` 还不存在，外键约束会报错："你引用的记录不存在！"

**解决：按依赖顺序插入。** 先插入被引用的表（patient），再插入引用它的表（admission），最后插入引用 admission 的表（bed）。

### 挑战 2：循环依赖

```
admission.current_bed_id → 引用 → bed.bed_id
bed.current_admission_id → 引用 → admission.admission_id
```

`admission` 引用 `bed`，`bed` 又引用 `admission`。谁先插入都会报错。

**解决：分两步走。**

1. 先插入 admission（`current_bed_id` 临时设为 NULL）
2. 再插入 bed（此时 admission 已存在，可以引用）
3. 最后更新 admission.current_bed_id（此时 bed 也存在了）

### 挑战 3：数据类型不同

SQLite 和 PostgreSQL 的数据类型表示方式不同：

| 数据 | SQLite | PostgreSQL |
|------|--------|------------|
| 布尔值 | `INTEGER` (0/1) | `BOOLEAN` (true/false) |
| 时间 | `DATETIME` (字符串) | `TIMESTAMP` (专用类型) |
| 字符串 | `VARCHAR(50)` | `TEXT` (PostgreSQL 推荐) |

**解决：类型转换。** 代码检测原始类型，转换成目标数据库兼容的类型。

---

## 代码实现：db_sync.py

同步逻辑在 `labor_ward_ai/tests/db_sync.py`。

### 插入顺序

根据外键依赖关系手动排列：

```python
TABLE_INSERT_ORDER = [
    # 独立表（没有外键依赖）
    "patient",
    "provider",
    "room",
    # 依赖 patient
    "ob_profile",
    # 依赖 provider
    "shift",
    # 依赖 patient, ob_profile, provider
    # 注意：current_bed_id 是循环依赖，稍后处理
    "admission",
    # 依赖 room, admission
    "bed",
    # 依赖 admission
    "labor_progress",
    "vital_sign",
    # 依赖 admission, provider, room
    "medical_order",
    # 依赖 admission, provider
    "alert",
]
```

**删除顺序是插入顺序的反向**——先删除依赖别人的表，再删除被依赖的表。

### 同步函数

```python
def sync_sqlite_to_postgres(
    local_engine: sa.Engine,
    remote_engine: sa.Engine,
    verbose: bool = True,
) -> dict:
```

**7 个步骤：**

#### 步骤 1：反射本地数据库结构

```python
local_metadata = sa.MetaData()
local_metadata.reflect(bind=local_engine)
```

反射（Reflect）是让 SQLAlchemy 自动读取数据库的表结构——表名、列名、列类型、主键、外键等。

#### 步骤 2：读取所有本地数据

```python
for table_name in TABLE_INSERT_ORDER:
    result = conn.execute(sa.text(f"SELECT * FROM {table_name}"))
    rows = result.fetchall()
    local_data[table_name] = {"columns": ..., "rows": ...}
```

把每个表的数据都读到内存里，存成字典结构，方便后续处理。

#### 步骤 3：删除远程数据库的所有表

```python
for table_name in reversed(TABLE_INSERT_ORDER):
    conn.execute(sa.text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
```

`CASCADE` 表示级联删除依赖它的东西。按**反向顺序**删除，避免外键约束报错。

#### 步骤 4：在远程数据库创建表（类型转换）

```python
for col in local_table.columns:
    type_str = str(col.type).upper()

    if "DATETIME" in type_str:
        col_type = sa.TIMESTAMP()
    elif "BOOLEAN" in type_str:
        col_type = sa.Boolean()
    elif "VARCHAR" in type_str:
        col_type = sa.Text()  # PostgreSQL 建议用 TEXT
    # ...
```

根据原始类型，转换成 PostgreSQL 兼容的类型。

#### 步骤 5：识别布尔列

```python
for col in local_table.columns:
    if "BOOLEAN" in str(col.type).upper():
        bool_cols.append(col.name)
```

SQLite 用 0/1 存布尔值，PostgreSQL 用 true/false。记录哪些列需要转换。

#### 步骤 6：插入数据（处理循环依赖）

```python
# 插入 admission 时，先把 current_bed_id 设为 NULL
if table_name == "admission":
    for row in rows:
        if row.get("current_bed_id") is not None:
            admission_bed_mappings.append((row["admission_id"], row["current_bed_id"]))
            row["current_bed_id"] = None  # 临时设为 NULL

# 布尔值转换
if table_name in boolean_columns:
    for row in rows:
        for col_name in boolean_columns[table_name]:
            row[col_name] = bool(row[col_name])  # 0/1 → True/False
```

#### 步骤 7：修复循环依赖

```python
for admission_id, bed_id in admission_bed_mappings:
    conn.execute(
        sa.text("UPDATE admission SET current_bed_id = :bed_id WHERE admission_id = :admission_id"),
        {"admission_id": admission_id, "bed_id": bed_id},
    )
```

所有表插入完成后，再更新之前临时设为 NULL 的 `current_bed_id`。

---

## 如何运行同步？

### 方法 1：命令行脚本

```bash
.venv/bin/python scripts/test_sync_data_to_remote_db.py
```

**输出示例：**

```
============================================================
Syncing local SQLite to remote PostgreSQL (NeonDB)
============================================================
Sync sqlite to remote database...
Reflecting local SQLite schema...
Reading data from local SQLite...
  patient: 20 rows
  provider: 15 rows
  room: 12 rows
  ...
Dropping tables in remote PostgreSQL...
Creating tables in remote PostgreSQL...
Inserting data into remote PostgreSQL...
Updating admission.current_bed_id (circular dependency fix)...
  Updated 12 admission records.
Sync completed successfully!
============================================================
```

### 方法 2：在 Python 代码中调用

```python
from labor_ward_ai.tests.db_sync import reset_remote_database

# 重置远程数据库
result = reset_remote_database(verbose=True)

print(result)
# {"success": True, "tables": {"patient": 20, "provider": 15, ...}}
```

### 方法 3：测试 fixture 中自动调用

```python
# 在测试开始前重置数据库
def setup_remote_database():
    reset_remote_database(verbose=False)
```

---

## 幂等性

同步操作是**幂等的**（Idempotent）：

- 运行 1 次 → 远程数据库 = 本地数据库
- 运行 10 次 → 远程数据库 = 本地数据库

每次都是**完全覆盖**（DROP + CREATE + INSERT），所以结果始终一致。

**好处：**
- 出错了？再跑一次就好
- 不确定状态？同步一下就回到已知状态
- 测试搞乱了？重置即可

---

## 完整流程图

```
本地 SQLite (tmp/data.sqlite)
           ↓
       读取所有数据
           ↓
远程 PostgreSQL (NeonDB)
           ↓
   DROP 所有表 (反向顺序)
           ↓
   CREATE 所有表 (类型转换)
           ↓
   INSERT 数据 (正向顺序)
     └── admission.current_bed_id 临时设为 NULL
           ↓
   UPDATE admission.current_bed_id (修复循环依赖)
           ↓
       同步完成！
```

---

## 常见问题

### Q: 同步会丢失远程数据库的修改吗？

**是的。** 同步是"覆盖"操作，远程数据库的所有数据都会被本地数据替换。

这正是我们想要的——用本地的"干净数据"重置远程的"被改乱的数据"。但在生产环境要小心，不要误操作。

### Q: 如果本地数据库文件不存在怎么办？

脚本会报错：

```
FileNotFoundError: Database file not found: tmp/data.sqlite
```

需要先运行 `mise run download-db` 下载数据库文件。

### Q: 同步需要多长时间？

通常几秒钟。数据量不大（几百行），网络延迟是主要因素。

### Q: 可以反向同步吗（PostgreSQL → SQLite）？

当前代码不支持。如果需要，可以类似地实现，但要注意类型转换是反向的（TIMESTAMP → DATETIME，true/false → 1/0）。

### Q: 如果同步中断了怎么办？

因为使用了事务，中断后已完成的操作会回滚，数据库保持之前的状态。再跑一次就行。

---

## 总结

| 概念 | 说明 |
|------|------|
| 为什么同步 | 本地数据（SQLite）需要上传到远程（PostgreSQL） |
| 挑战 | 外键依赖、循环依赖、类型转换 |
| 插入顺序 | 按依赖关系排序，独立表先插入 |
| 循环依赖 | 先设 NULL，最后 UPDATE |
| 类型转换 | SQLite 0/1 → PostgreSQL true/false 等 |
| 幂等性 | 每次同步结果一致，可反复运行 |

**运行命令：**

```bash
.venv/bin/python scripts/test_sync_data_to_remote_db.py
```

**核心用途：**
- 首次部署时初始化数据
- 测试后重置数据库
- 本地数据更新后同步到远程
