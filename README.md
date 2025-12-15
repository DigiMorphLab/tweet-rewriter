# AI Tweet Rewriter (Web3 Edition)

这是一个基于 AI 的推文批量改写工具，专为 Web3 领域设计。它能够根据输入的原文和改写意图，自动匹配不同的“人设” (Personas)，生成去“AI味”的自然语言推文。

## 功能特点

*   **意图注入**：支持自定义改写意图（如：FUD、喊单、纯分享、交互党抱怨等）。
*   **多视角生成**：内置 20 种 Web3 典型人设（如 Degen、Airdrop Farmer、Tech Skeptic 等），每次随机抽取不同人设进行改写。
*   **去 AI 味质检**：内置 "Quality Gate" 环节，自动检测并重写过于生硬或包含营销禁词的内容。
*   **Web 可视化界面**：基于 Streamlit 的图形化操作界面。
*   **双模型策略**：支持分别为“生成”和“质检”环节配置不同的 LLM（如用 GPT-4 生成，用 Claude 3.5 Sonnet 质检）。
*   **多厂商支持**：支持 OpenAI 和 Anthropic (Claude)。

## 项目结构

```
.
├── src/
│   ├── app.py           # Streamlit Web App 入口
│   ├── main.py          # CLI 入口
│   ├── workflow.py      # 核心工作流逻辑
│   ├── prompts.py       # Prompt 模板管理
│   └── personas.json    # 20种人设数据库
├── requirements.txt     # 依赖项
└── README.md            # 说明文档
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行 Web 界面 (推荐)

```bash
streamlit run src/app.py
```

运行后，浏览器将自动打开 `http://localhost:8501`。

在 Web 界面中，你可以：
1.  在左侧边栏配置 OpenAI / Anthropic 的 API Key。
2.  分别为 **Drafting (生成)** 和 **Quality Gate (质检)** 选择不同的模型。
3.  管理（新增/删除）人设库。
4.  输入原文和意图，点击运行并实时查看每一步的执行日志。

### 3. 运行命令行工具 (CLI)

如果你更喜欢命令行操作：

```bash
python src/main.py --text "原文..." --intent "意图..." --count 3
```

*(注意：CLI 模式目前仅支持环境变量中的 OpenAI Key)*

## 工作流原理

1.  **Fact Extraction**: 提取原文核心事实，分析用户意图。
2.  **Persona Match**: 随机抽取 N 个不同的人设。
3.  **Drafting**: 根据人设和事实生成初稿。
4.  **Quality Gate**: 严苛的自我审查，剔除“AI味”词汇（如 "Unlock potential", "Revolutionize" 等），必要时强制重写。
