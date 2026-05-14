# 配置管理详解

本文档面向刚接触项目开发的新手，解释"配置管理"是什么、为什么需要它、以及这个项目是怎么做的。

---

## 什么是配置？为什么要"管理"它？

**配置（Configuration）** 是程序运行时需要知道的一些信息，但这些信息**不应该写死在代码里**。

**常见的配置例子：**

| 配置项 | 说明 | 为什么不能写在代码里 |
|--------|------|----------------------|
| 数据库密码 | 连接数据库用 | 写在代码里会被所有人在 GitHub 上看到 |
| AWS 密钥 | 调用 AWS 服务 | 泄露后别人可以用你的账号花钱 |
| API 端点地址 | 本地用 localhost，线上用真实域名 | 不同环境需要不同的值 |

**问题来了：** 如果不写在代码里，那写在哪里？

答案：**环境变量** 和 **配置文件**。

---

## 两种运行环境

这个项目在两种环境下运行：

| 环境 | 说明 | 配置来源 |
|------|------|----------|
| **本地开发** (Local) | 你的电脑上运行 | `.env` 文件 + `~/.aws/credentials` |
| **Vercel 部署** (Vercel) | 云服务器上运行 | Vercel Dashboard 的环境变量设置 |

**关键问题：** 同一份代码，怎么知道自己在哪个环境里，该读哪里的配置？

---

## 运行时检测：runtime.py

首先，我们需要知道代码"跑在哪里"。这是 `runtime.py` 的工作：

```python
# labor_ward_ai/runtime.py

class Runtime:
    def is_local(self) -> bool:
        # 如果不是 Vercel，就是本地
        return self.name == "LOCAL"

    def is_vercel(self) -> bool:
        # Vercel 会自动设置 VERCEL=1 环境变量
        return os.environ.get("VERCEL") == "1"

# 单例，全局使用
runtime = Runtime()
```

**怎么判断？**

Vercel 的服务器会自动设置一个环境变量 `VERCEL=1`。如果这个变量存在且值是 `"1"`，说明代码跑在 Vercel 上；否则就是本地。

**使用方式：**

```python
from labor_ward_ai.runtime import runtime

if runtime.is_local():
    print("我在本地电脑上")
elif runtime.is_vercel():
    print("我在 Vercel 云服务器上")
```

---

## 配置类：conf_00_def.py

知道了"在哪里"，下一步是"读什么配置"。这是 `Config` 类的工作。

### Config 类的结构

```python
# labor_ward_ai/config/conf_00_def.py

@dataclasses.dataclass
class Config:
    # AWS 相关
    aws_region: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    model_id: str | None = "us.amazon.nova-micro-v1:0"

    # 数据库相关
    db_host: str | None = None
    db_port: int | None = None
    db_user: str | None = None
    db_pass: str | None = None
    db_name: str | None = None
```

这个类就是一个"配置容器"，把所有配置项都集中在一起。

### 两个工厂函数

**关键来了：** 两种环境读配置的方式不同，所以有两个"工厂函数"：

#### new_in_local_runtime() — 本地环境

```python
@classmethod
def new_in_local_runtime(cls):
    """本地开发环境"""
    from dotenv import load_dotenv
    load_dotenv()  # 从 .env 文件读取环境变量

    return cls(
        aws_region="us-east-1",
        # AWS 密钥不传 → 使用 ~/.aws/credentials 里的默认凭证
        db_host=os.environ["DB_HOST"],
        db_port=int(os.environ["DB_PORT"]),
        db_user=os.environ["DB_USER"],
        db_pass=os.environ["DB_PASS"],
        db_name=os.environ["DB_NAME"],
    )
```

**本地特点：**
- 用 `load_dotenv()` 从 `.env` 文件读取变量
- AWS 凭证**不显式传入**（`aws_access_key_id` 和 `aws_secret_access_key` 保持 `None`），这样 boto3 会自动去找 `~/.aws/credentials` 文件

#### new_in_vercel_runtime() — Vercel 环境

```python
@classmethod
def new_in_vercel_runtime(cls):
    """Vercel 云环境"""
    return cls(
        aws_region="us-east-1",
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],      # 必须显式传入
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        db_host=os.environ["DB_HOST"],
        db_port=int(os.environ["DB_PORT"]),
        db_user=os.environ["DB_USER"],
        db_pass=os.environ["DB_PASS"],
        db_name=os.environ["DB_NAME"],
    )
```

**Vercel 特点：**
- 直接从 `os.environ` 读取（Vercel Dashboard 配置的环境变量会自动注入）
- AWS 凭证**必须显式传入**（Vercel 服务器上没有 `~/.aws/credentials` 文件）

### new() — 自动选择

```python
@classmethod
def new(cls):
    """自动检测环境，返回对应的配置"""
    if runtime.is_local():
        return cls.new_in_local_runtime()
    elif runtime.is_vercel():
        return cls.new_in_vercel_runtime()
    else:
        raise RuntimeError("未知环境")
```

**这是核心设计：** 调用 `Config.new()` 会自动检测环境，返回正确的配置。使用代码完全不需要关心"现在是本地还是 Vercel"。

---

## 本地的 .env 文件

本地开发时，配置写在项目根目录的 `.env` 文件里。

### .env 文件结构

```bash
# .env 文件示例（只展示结构，不展示真实值）

# 数据库配置
DB_HOST=ep-xxx-pooler.us-east-1.aws.neon.tech
DB_PORT=5432
DB_USER=your_username
DB_PASS=your_password
DB_NAME=neondb

# AWS 配置（本地一般不需要，因为用 ~/.aws/credentials）
# AWS_ACCESS_KEY_ID=...
# AWS_SECRET_ACCESS_KEY=...
```

### 重要：.env 绝对不能进 Git！

`.env` 文件包含**敏感信息**（数据库密码、API 密钥等），如果上传到 GitHub：

- 全世界都能看到你的密码
- 恶意用户可以登录你的数据库
- 可以用你的 AWS 账号消费

**所以我们在 `.gitignore` 里明确忽略它：**

```gitignore
# .gitignore
.env
.envrc
```

**验证方法：**

```bash
# 检查 .env 是否被 git 跟踪
git status

# 如果 .env 没出现在列表里，说明它被正确忽略了
```

### 团队协作怎么办？

既然 `.env` 不进 Git，新加入的团队成员怎么知道要填什么？

常见做法是提供一个 `.env.example` 文件（这个**可以**进 Git）：

```bash
# .env.example（可以进 Git，只有变量名，没有值）
DB_HOST=
DB_PORT=
DB_USER=
DB_PASS=
DB_NAME=
```

新成员复制这个文件，然后填入自己的值：

```bash
cp .env.example .env
# 编辑 .env，填入真实值
```

---

## 配置的懒加载单例：one_01_config.py

配置创建后应该**全局只有一份**（单例），而且**只在需要时才创建**（懒加载）。

这个项目用 `ConfigMixin` 实现：

```python
# labor_ward_ai/one/one_01_config.py

from functools import cached_property
from ..config.conf_00_def import Config

class ConfigMixin:
    @cached_property
    def config(self) -> Config:
        """返回缓存的配置实例"""
        return Config.new()
```

### cached_property 是什么？

`@cached_property` 是 Python 的一个装饰器，效果是：

- **第一次访问** `self.config` → 调用 `Config.new()` 创建配置，并缓存结果
- **后续访问** `self.config` → 直接返回缓存的结果，不再调用 `Config.new()`

**好处：**

1. **懒加载**：程序启动时不创建配置，只有第一次用到时才创建
2. **单例**：无论访问多少次，都是同一个配置对象
3. **性能**：避免重复读取 `.env` 文件和环境变量

### Mixin 是什么？

`ConfigMixin` 是一个 **Mixin 类**，用来给其他类"混入"功能。

在这个项目里，有一个核心的 `One` 类，它通过继承多个 Mixin 获得各种能力：

```python
class One(ConfigMixin, DbMixin, Boto3Mixin, AgentMixin):
    pass
```

这样 `One` 类就有了 `.config` 属性。

---

## 使用配置

配置系统设计好了，使用起来非常简单：

```python
from labor_ward_ai.api import one

# 通过 one 单例访问配置
print(one.config.aws_region)    # us-east-1
print(one.config.db_host)       # 你的数据库地址
print(one.config.model_id)      # us.amazon.nova-micro-v1:0
```

**不需要关心环境：** 代码不需要写 `if runtime.is_local(): ...`。`Config.new()` 已经帮你处理好了。

**不需要关心单例：** 无论访问多少次 `one.config`，都是同一个对象，`@cached_property` 保证了这一点。

---

## 添加新配置项

如果需要添加新的配置项，只需要三步：

### 1. 在 Config 类里添加字段

```python
@dataclasses.dataclass
class Config:
    # ... 现有字段 ...
    my_new_setting: str | None = None  # 新字段
```

### 2. 在两个工厂函数里设置值

```python
@classmethod
def new_in_local_runtime(cls):
    return cls(
        # ... 现有配置 ...
        my_new_setting=os.environ.get("MY_NEW_SETTING", "default_value"),
    )

@classmethod
def new_in_vercel_runtime(cls):
    return cls(
        # ... 现有配置 ...
        my_new_setting=os.environ["MY_NEW_SETTING"],
    )
```

### 3. 在代码里使用

```python
from labor_ward_ai.config import config

print(config.my_new_setting)
```

**就这么简单。** 不需要在代码的其他地方加任何环境判断。

---

## 为什么这样设计？

这种设计叫 **Config Pattern**（配置模式），好处是：

| 好处 | 说明 |
|------|------|
| **一处复杂，处处简单** | 环境判断只在 `Config.new()` 里做一次，其他代码不需要关心 |
| **易于扩展** | 加新配置只改一个文件，不用到处加 `if` 判断 |
| **方便测试** | 测试时可以直接创建 `Config(db_host="test", ...)` 不用管环境 |
| **自文档化** | 看 Config 类的字段就知道有哪些可配置项 |

**反面教材（不要这样做）：**

```python
# ❌ 到处写环境判断 — 难维护
def connect_db():
    if runtime.is_local():
        host = os.environ["DB_HOST"]
    else:
        host = os.environ["DB_HOST"]  # 其实一样，但散落各处难以追踪

# ✅ 正确做法 — 只用 config
def connect_db():
    host = config.db_host  # 简单清晰
```

---

## 总结

| 组件 | 文件 | 作用 |
|------|------|------|
| `Runtime` | `runtime.py` | 检测当前是本地还是 Vercel |
| `Config` 类 | `config/conf_00_def.py` | 存放所有配置项 |
| `new_in_local_runtime()` | `config/conf_00_def.py` | 创建本地环境配置 |
| `new_in_vercel_runtime()` | `config/conf_00_def.py` | 创建 Vercel 环境配置 |
| `ConfigMixin` | `one/one_01_config.py` | 懒加载 + 单例，提供 `one.config` |
| `.env` 文件 | 项目根目录 | 本地开发的配置来源（**不进 Git**） |
| Vercel Dashboard | 云端 | 生产环境的配置来源 |

**记住这个流程：**

```
代码访问 one.config
    ↓
@cached_property 检查是否已缓存
    ↓
首次访问 → 调用 Config.new()
    ↓
检测 runtime.is_local() 还是 is_vercel()
    ↓
调用对应的 new_in_xxx_runtime()
    ↓
读取环境变量 / .env 文件
    ↓
返回配置好的 Config 实例（并缓存）
    ↓
后续访问 → 直接返回缓存的实例
```
