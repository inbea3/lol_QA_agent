# LOL-Game-Agent
## 基于 RAG 混合检索与双 MCP 的英雄联盟智能助手
> Lightweight LoL Assistant Agent Based on Hybrid RAG & Dual MCP Service

**技术栈**：Python | Neon PostgreSQL | BM25 + 向量混合检索（RRF）| OpenAI 兼容 LLM | MCP

**核心定位**：依托云端数据库搭建英雄联盟领域专属RAG知识库，结合**两类成熟线上MCP标准化工具调用**，实现游戏知识问答、对局时间推算、实时资讯检索、阵容策略分析一体化轻量化智能Agent，数据云端持久化存储。

---

## 项目简介
本项目面向英雄联盟玩家日常咨询、上分策略、对局时间决策、实时资讯查询等实际需求，搭建领域专属智能游戏助手。
采用**Neon云PostgreSQL数据库**维护两套可联动的知识数据：**第一套**按条存储纯 Markdown 原文（一篇文档一条记录）；**第二套**存储面向 RAG 的语义分块与向量。检索命中分块后，可通过关联字段直接回溯完整 MD 原文，兼顾可读维护与向量召回；
接入**两类全网成熟开源MCP线上服务**，零开发成本开箱即用：
1. **时间计算类MCP**：专注时序换算、倒计时推算，适配游戏内各类时间节点计算
2. **全网百科检索类MCP**：负责实时资讯、外网版本改动、赛事动态等本地知识库缺失内容补全

智能Agent可自主完成意图路由分流：静态游戏知识走云端RAG检索；游戏时间时序需求调用**时间MCP**；本地知识库无覆盖的实时资讯、外网玩法调用**百科检索MCP**，最终整合多源信息输出完整精准回答。项目轻量化易部署。

---

## 功能特性
- ✅ 云端双套存储联动：Neon 分别持久化多条 MD 原文与 RAG 向量分块，通过文档 ID 双向关联，支持增量更新与数据导出
- ✅ 全维度游戏知识RAG检索：英雄技能、连招打法、装备合成、符文搭配、游戏机制问答
- ✅ 英雄对位克制、兵线运营、野区资源规划等静态实战攻略智能召回
- ✅ **时序计算MCP能力**：野怪/小龙/先锋/大龙刷新倒计时、对局时长统计、技能CD换算、游戏阶段时序判断
- ✅ **全网百科检索MCP能力**：最新赛事资讯、选手动态、外服版本改动、外网主流打法、拓展英雄背景故事
- ✅ Agent智能路由调度：自动区分静态知识、时间计算、实时资讯三类需求，自主选择调用链路
- ✅ BM25 + 向量混合检索（RRF 融合），兼顾关键词匹配与语义相似
- ✅ 本地运行日志（`logs/agent.log`）
- ✅ 轻量化架构，无 Hugging Face、无 LangChain 重依赖
- ✅ 无自建服务成本，直接调用线上成熟MCP接口，简化部署流程

---

## 核心技术架构
### 1. RAG知识库云端实现方案
#### 数据库选型
- **云端数据库**：Neon Serverless PostgreSQL
- **存储策略**：双表分离、外键联动——MD 原文与 RAG 向量各存一套，互不混写，检索时可一键回溯全文

#### 双套数据说明
| 套别 | 存储对象 | 用途 |
|------|----------|------|
| **第一套** | 纯 Markdown 原文，一篇一条 | 知识库维护、导出、全文展示、人工校对 |
| **第二套** | 语义分块 + 512 维向量 | RAG 相似度检索、上下文召回 |
| **联动方式** | `document_id` 外键 | 向量命中分块 → 关联取回对应 MD 全文，保证回答上下文完整 |

#### RAG核心技术栈
- 入库：`inbox/` 放 MD → `import_md.py` 写入 MD 库 → `vectorize_md.py` 分块入库
- 文本分块：`rag/chunking.py` 递归分隔符分块
- 向量：本地哈希向量（512 维，`scikit-learn`，无需外网模型）
- 检索：**混合检索**（默认 `RETRIEVAL_BACKEND=hybrid`）
  - BM25 路：关键词相关性（`rank-bm25`）
  - 向量路：pgvector 余弦相似度（本地哈希向量，无需 Hugging Face）
  - 融合：RRF（Reciprocal Rank Fusion）合并两路 Top 结果
- 结果回填：按 `document_id` 从 MD 库取回完整原文

#### 数据库核心表结构
```sql
CREATE EXTENSION IF NOT EXISTS vector;

-- 第一套：纯 Markdown 原文（多篇、多条）
CREATE TABLE lol_knowledge_documents (
    id SERIAL PRIMARY KEY,
    doc_title TEXT NOT NULL,           -- 文档标题
    doc_source TEXT,                   -- 来源标签（英雄/装备/机制等）
    markdown_content TEXT NOT NULL,    -- 完整 MD 原文
    is_vectorized SMALLINT NOT NULL DEFAULT 0 CHECK (is_vectorized IN (0, 1)),  -- 0 未向量化 / 1 已向量化
    create_time TIMESTAMP DEFAULT NOW(),
    update_time TIMESTAMP DEFAULT NOW()
);

-- 第二套：RAG 向量分块（与原文表联动）
CREATE TABLE lol_knowledge_chunks (
    id SERIAL PRIMARY KEY,
    document_id INT NOT NULL,              -- 逻辑关联 MD 库主键（跨库无外键）
    chunk_index INT NOT NULL,          -- 文档内分块序号
    chunk_content TEXT NOT NULL,       -- 分块文本
    chunk_embedding vector(512),       -- 本地哈希向量，维度同 EMBEDDING_DIM
    create_time TIMESTAMP DEFAULT NOW(),
    UNIQUE (document_id, chunk_index)
);

CREATE INDEX idx_chunks_document ON lol_knowledge_chunks(document_id);
```

#### RAG完整业务流程
```
import_md.py 从 inbox/ 导入 MD 到 Neon
→ vectorize_md.py 仅处理 is_vectorized = 0 的文档，完成后置 1
→ 分块 + 本地生成中文语义向量
→ 写入 Neon Vector 库（document_id 关联 MD 库主键）
→ 用户提问向量化
→ BM25 + 向量混合检索（RRF）→ document_id 联动取回 MD 全文
→ 拼接提示词送入大模型生成回答
```

### 2. 双 MCP 接入（stdio 子进程）

| MCP | 包名 | 工具 | 用途 |
|-----|------|------|------|
| 时间 | `mcp-server-time` | `get_current_time`、`convert_time` | 当前时间、时区换算 |
| 抓取 | `mcp-server-fetch` | `fetch` | 抓取 Fandom 百科检索页 Markdown |

安装：`pip install mcp-server-time mcp-server-fetch`（已写入 `requirements.txt`）

配置见 `.env` 中 `TIME_MCP_*`、`FETCH_MCP_*`。验证：`python database/test_mcp.py`

**调用逻辑**
1. 静态知识 → 本地 RAG
2. 时间/时区 → `mcp-server-time`
3. 实时/外网 → RAG + `mcp-server-fetch` 抓取百科搜索页

### 3. Agent整体智能调度流程
```
用户游戏问答输入
        ↓
LangGraph智能意图识别
├─ 静态游戏知识查询 → BM25+向量混合检索 + document_id 联动 MD 原文
├─ 游戏时间/倒计时/对局时序需求 → 调用线上时间计算MCP → 输出精准时间推算结果
└─ 实时资讯/版本改动/外网打法需求 → 调用线上百科检索MCP → 补充全网实时内容
        ↓
多源结果整合润色
        ↓
统一格式化回复用户
```

---

## RAG 知识库维护
将 Markdown 放入 `inbox/` 后执行 `import_md.py` 写入 MD 库，再执行 `vectorize_md.py` 同步到 Vector 库。

---

## 环境依赖
```bash
pip install -r requirements.txt
```

---

## 项目目录结构
```
lol_QA_agent/
├── main.py              # 交互入口
├── config/settings.py   # 环境变量与配置
├── inbox/               # 在此目录编写/放置 .md，再执行 import_md.py
├── test_queries.md      # 20 条 RAG/Agent 测试查询
├── database/
│   ├── init_db.py       # 建表 / --check 状态检查
│   ├── import_md.py     # 从 inbox/ 导入 MD 库
│   ├── vectorize_md.py  # 分块 + 向量入库
│   ├── connection.py    # 双库连接
│   ├── schema_md.sql
│   └── schema_vector.sql
├── rag/
│   ├── retriever.py     # 混合检索（RRF）
│   ├── bm25.py
│   ├── embedder.py      # 本地向量
│   └── chunking.py      # 文本分块
├── agent/               # 意图路由 + LLM 回答
├── mcp_tools/           # runner + time_client + wiki_client（stdio MCP）
├── utils/logger.py
├── logs/
├── requirements.txt
└── .env
```

---

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
复制 `.env.example` 为 `.env`，填写两套 Neon 连接信息与 LLM 密钥：
- `MD_*`：第一套，存纯 Markdown 原文
- `VECTOR_*`：第二套，存 RAG 分块与向量
- 两套库通过 `document_id` 逻辑联动（MD 库主键 = 向量库中的 `document_id`）

### 3. 初始化与维护知识库
```bash
python database/init_db.py

# 1. 把写好的 .md 放进 inbox/
# 2. 导入 MD 库（默认同标题会更新，并标记待向量化）
python database/import_md.py

# 仅导入某一个文件
python database/import_md.py 亚索.md

# 3. 分块 + 向量入库
python database/vectorize_md.py
python database/init_db.py --check
```

重新导入已存在的文档会自动更新内容，并将 `is_vectorized` 置为 0，需再运行 `vectorize_md.py`。

### 4. 验证 MCP（可选）
```bash
python database/test_mcp.py
```

### 5. 启动助手
```bash
python main.py
```

---
