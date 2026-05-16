---
title: ContentBlitz
emoji: ✍️
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
---
# ✍️ ContentBlitz — AI Content Marketing Assistant

ContentBlitz is a multi-agent AI-powered content marketing assistant that helps creators produce research-backed blogs, LinkedIn posts, and images through natural conversation. Built with LangGraph, Google Gemini, Tavily, and DALL-E.

> ⚠️ This project is for educational purposes as part of the Applied Agentic AI for SWEs capstone program.

---

## Architecture Overview

ContentBlitz uses a multi-agent architecture orchestrated by LangGraph. An LLM-based router classifies each user query and dispatches it to one or more specialized agents that execute sequentially with context passing.

```
User Query
    │
    ▼
┌──────────────────┐
│   LLM Router     │  Classifies → one or more agents
│  (Gemini Flash)  │
└────────┬─────────┘
         │ sorted by priority
    ┌────┴────┬──────────┬──────────┬──────────┐
    ▼         ▼          ▼          ▼          ▼
┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐
│Research││Strategy││  Blog  ││LinkedIn││ Image  │
│ Agent  ││ Agent  ││ Writer ││ Writer ││ Agent  │
└───┬────┘└────────┘└───┬────┘└────────┘└───┬────┘
    │                    │                    │
 Tavily             Tavily               DALL-E /
 Search             Search              GPT Image
```

### Multi-Agent Sequential Chaining

When a query requires multiple agents, they execute in priority order with context accumulation:

1. **Research Agent** (priority 1) — gathers data from the web
2. **Content Strategist** (priority 2) — plans content approach
3. **Blog Writer** (priority 3) — writes SEO-optimized posts using research
4. **LinkedIn Writer** (priority 4) — creates social posts using research
5. **Image Agent** (priority 5) — generates visuals based on content

Each agent receives the user's message **plus** accumulated output from all previous agents, enabling the Blog Writer to use real research data and the Image Agent to create visuals matching the blog content.

### Agents

| Agent | Purpose | Tools |
|-------|---------|-------|
| **Deep Research** | Web research with source attribution | Tavily search (with time filtering) |
| **SEO Blog Writer** | Long-form SEO-optimized blog posts | Tavily search for topic research |
| **LinkedIn Writer** | Engaging professional social posts | None (prompt-driven) |
| **Image Generator** | AI-powered visuals for content | DALL-E / GPT Image |
| **Content Strategist** | Content planning and calendars | None (prompt-driven) |

---

## Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| LLM | Google Gemini 2.5 Flash | Free tier, fast, good for content generation |
| Orchestration | LangGraph | State graph with priority-based multi-agent chaining |
| Research | Tavily AI | 1000 free searches/month, built for AI agents, returns clean content |
| Image Generation | OpenAI GPT Image | High quality marketing visuals |
| UI | Streamlit | Rapid prototyping, chat components, free cloud hosting |
| Config | PyYAML + python-dotenv | Clean separation of settings and secrets |

### Why Tavily over SERP API?

- **Built for AI agents** — returns pre-extracted content ready for LLM consumption
- **10x more free searches** — 1000/month vs 100/month
- **Better content extraction** — visits pages and extracts relevant content, not just snippets
- **Time filtering** — `days` parameter restricts to recent results when needed
- **Fallback logic** — if time-filtered search returns nothing, automatically retries without filter

---

## Setup Instructions

### Prerequisites

- Python 3.13+
- API keys for:
  - [Google AI Studio](https://aistudio.google.com/apikey) (Gemini — free)
  - [Tavily](https://app.tavily.com) (research — free tier)
  - [OpenAI](https://platform.openai.com/api-keys) (DALL-E — ~$0.04/image)

### Installation

```bash
git clone https://github.com/DhanarajuV/contentblitz.git
cd contentblitz

python3.13 -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate          # Windows

pip install -r requirements.txt
```

### Configuration

1. Create a `.env` file in the project root:

```
GOOGLE_API_KEY=your_gemini_key
TAVILY_API_KEY=your_tavily_key
OPENAI_API_KEY=your_openai_key
```

2. Configuration is in `config/development.yaml`:

```yaml
llm:
  model: "gemini-2.5-flash"
  temperature: 0.7

research:
  provider: "tavily"
  max_results: 5

image:
  provider: "gpt-image-1"
  size: "1024x1024"
  quality: "medium"

app:
  name: "ContentBlitz"
  description: "AI-powered content marketing assistant"
```

### Run the Application

```bash
streamlit run src/web_app/app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Usage Examples

### Chat Tab (Primary Interface)

| What You Type | Agents Triggered | What Happens |
|--------------|-----------------|-------------|
| "Research the top AI trends in marketing" | Research | Web search → structured summary with sources |
| "Write an SEO blog post about remote work productivity" | Blog | Research + SEO-optimized 800-1500 word post |
| "Write a LinkedIn post about prompt engineering" | LinkedIn | Engaging post with hook, body, CTA, hashtags |
| "Create an image for my blog about cloud computing" | Image | DALL-E generates optimized visual |
| "Create a content strategy for my SaaS startup" | Strategy | Content plan with formats, angles, schedule |
| "Research AI trends and write a blog and LinkedIn post" | Research, Blog, LinkedIn | Full pipeline with context chaining |
| "Create a complete blog with images about sustainability" | Blog, Image | Blog with [IMAGE] markers + generated visuals |

### Content Editor Tab

- Shows the latest generated content (final agent output only)
- Editable text area for human refinement
- `[IMAGE: description]` markers auto-replaced with markdown image references
- Export as Markdown

### Images Tab

- Gallery of all generated images
- Most recent first

### Multi-Turn Conversations

```
User: "Write a LinkedIn post about AI in healthcare"
Agent: [generates post]
User: "Make the hook more provocative"
Agent: [regenerates with stronger hook — remembers context]
User: "Now create a blog version of this"
Agent: [writes blog using the LinkedIn post as context]
```

---

## API Documentation

### Core Function

```python
from src.workflow.graph import chat

response, agents_used, updated_history = chat(
    user_message="Write a blog about AI",
    chat_history=[]
)
# response: str — combined agent outputs
# agents_used: str — comma-separated agent names
# updated_history: list — pass back for multi-turn
```

### Router

```python
from src.workflow.router import route_query

agent_types = route_query("Research AI and write a blog")
# Returns: ["research", "blog"]
```

### Individual Agents

```python
from src.agents.research_agent import ResearchAgent

agent = ResearchAgent()
response, history = agent.run("Latest trends in content marketing")
```

### Integration Clients

```python
from src.integrations.tavily_client import search
from src.integrations.image_client import generate_image

# Research
results = search("AI marketing trends", max_results=5, days=30)

# Image generation
result = generate_image("Modern blog header about AI, blue gradient, minimalist")
# Returns: {"local_path": "generated_images/image_12345.png", "revised_prompt": "..."}
```

---

## Project Structure

```
contentblitz/
├── src/
│   ├── agents/
│   │   ├── base_agent.py          # Base class — LLM, tool loop (max 5 iterations), memory
│   │   ├── research_agent.py      # Deep web research with Tavily
│   │   ├── blog_writer.py         # SEO-optimized blog posts
│   │   ├── linkedin_writer.py     # Professional social posts
│   │   ├── image_agent.py         # AI image generation with prompt optimization
│   │   └── content_strategist.py  # Content planning and strategy
│   ├── core/
│   │   └── config.py              # YAML config loader
│   ├── integrations/
│   │   ├── tavily_client.py       # Tavily search with fallback logic
│   │   └── image_client.py        # OpenAI image generation (URL + b64 support)
│   ├── web_app/
│   │   └── app.py                 # Streamlit UI (chat + editor + images)
│   ├── utils/
│   └── workflow/
│       ├── router.py              # LLM-based multi-intent query classifier
│       └── graph.py               # LangGraph state graph with priority chaining
├── tests/                         # 54 tests, 86% coverage
├── config/
│   └── development.yaml           # Application configuration
├── generated_images/              # DALL-E output (gitignored)
├── .env                           # API keys (gitignored)
├── .coveragerc
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Testing

### Run all tests

```bash
python -m pytest tests/ -v
```

### Run with coverage

```bash
python -m pytest tests/ --cov=src --cov-report=term
```

### Test summary

- **54 tests** covering router, workflow, agents, integrations, and config
- **86% coverage** (excluding Streamlit UI)
- Tests use mocks for LLM and API calls — no API keys needed to run tests

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Multi-intent routing | Router returns list of agents | Complex queries like "research + blog + image" handled in one request |
| Priority-based execution | Research → Strategy → Blog → LinkedIn → Image | Data-gathering agents run first so content agents have context |
| Context accumulation | Each agent sees previous agents' output | Blog writer uses real research; image agent matches blog content |
| Tool loop (max 5) | Agent retries tool calls up to 5 times | Handles LLM wanting to refine searches without infinite loops |
| Tavily fallback | Retry without `days` filter if no results | Niche topics may not have recent coverage |
| Image markers | Blog outputs `[IMAGE: description]` | Human-in-the-loop: user approves before image generation |

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'src'"

```bash
echo "$(pwd)" > venv/lib/python3.13/site-packages/contentblitz.pth
```

### "TAVILY_API_KEY not found"

Verify `.env` exists with `TAVILY_API_KEY=tvly-xxxxx`. Restart the app after changes.

### "Model not found" for image generation

Check available models:
```bash
python -c "
from openai import OpenAI; from dotenv import load_dotenv; import os; load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
for m in client.models.list():
    if 'image' in m.id.lower(): print(m.id)
"
```
Update `config/development.yaml` with a valid model name.

### Research returns old/irrelevant results

The `days` parameter filters by recency. If your query needs recent info, include time words like "latest", "recent", "this month" — the LLM will pass `days=30` to the search tool.

### Empty responses from agents

Usually means the LLM made multiple tool calls. The tool loop (max 5 iterations) handles this. If still empty, check that Tavily returns results for your query:
```bash
python -c "from src.integrations.tavily_client import search; print(search('your query'))"
```

### Image generation fails

- Verify OpenAI API key has credits loaded
- Check the model name in config matches available models
- DALL-E/GPT-Image costs ~$0.04-0.08 per image

---

## Deployment

### Streamlit Community Cloud

1. Push to public GitHub repo
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. New app → select repo → main file: `src/web_app/app.py`
4. Add secrets: `GOOGLE_API_KEY`, `TAVILY_API_KEY`, `OPENAI_API_KEY`
5. Deploy

### Local

```bash
source venv/bin/activate
streamlit run src/web_app/app.py
```

---

## Cost Estimate

| Component | Cost | When |
|-----------|------|------|
| Gemini 2.5 Flash | Free | Every query |
| Tavily search | Free (1000/month) | Research queries |
| GPT Image generation | ~$0.04/image | Image requests only |

**Typical query cost**: $0 (text only) to $0.05 (with image). Total project development: ~$3-6.

---

## Future Enhancements

- CMS integration (WordPress, Medium direct publishing)
- Brand voice training from sample content
- Content performance prediction
- Multi-language content generation
- Video script and podcast content generation
- Social media scheduling integration (Buffer, Hootsuite)
