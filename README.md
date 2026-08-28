# FORGEMIND

A self-improving AI agent that reads its own code, learns from external sources,
and iteratively forges itself into something better.

## What It Does

1. **Analyzes** its own source code for weaknesses
2. **Researches** how state-of-the-art AI systems are built (web access)
3. **Plans** improvements using LLM reasoning
4. **Applies** changes via function calling
5. **Tests** — runs test suite to verify changes
6. **Commits** if tests pass, **rolls back** if they fail
7. **Remembers** what worked and what didn't

## Architecture

```
forgemind/
├── core/           # Brain — LLM reasoning, decision loop
│   ├── agent.py    # Main self-improvement loop
│   ├── llm.py      # LLM interface (GPT-4o)
│   └── planner.py  # Planning & task decomposition
├── web/            # Eyes — internet access
│   ├── search.py   # Web search (DuckDuckGo)
│   ├── fetcher.py  # Page fetching & parsing
│   └── learner.py  # Learn from external code/repos
├── tools/          # Hands — code manipulation
│   ├── reader.py   # Read & analyze code (AST)
│   ├── writer.py   # Write/patch code files
│   ├── runner.py   # Run builds & tests
│   └── git_ops.py  # Git operations (checkpoint/rollback)
├── memory/         # Memory — learning storage
│   ├── store.py    # Persistent JSON memory
│   └── metrics.py  # Quality tracking
├── tests/          # Test suite (must stay green)
│   └── test_smoke.py
├── config.yaml     # Configuration
├── main.py         # Entry point
└── requirements.txt
```

## Usage

```bash
# Install
pip install -r requirements.txt

# Set API key
export OPENAI_API_KEY="sk-..."

# Run one improvement cycle
python main.py

# Research techniques first, then improve
python main.py --research

# Run 5 cycles
python main.py --loop 5

# Check status
python main.py --status
```

## Safety

- Git versioning every change
- Test gate: changes must not break existing tests
- Max iterations per cycle (configurable)
- Auto-rollback on regression
- Max consecutive failures before stop
- Human approval mode available

## Philosophy

Every iteration is a strike of the hammer. The forge doesn't cool down —
it gets hotter, sharper, better. The mind forges itself.

<p align="center">⚒️ FORGEMIND — The mind that forges itself ⚒️</p>
