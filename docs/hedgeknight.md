I'd like to try a more complex target project called Hedgeknight.

This is inspired by https://github.com/chrisworsey55/atlas-gic
and
https://github.com/karpathy/autoresearch

I'd like to have Shmocky iteratively improve an agentic system for financial research and trading, broadly based on the above ideas (e.g Darwinian selection where weights are prompts and Sharpe ratio is the loss function).

The main points are "mutable prompt surface" for the agents that is iteratively improved e.g. GEPA like https://github.com/gepa-ai/gepa or https://dspy.ai/tutorials/gepa_ai_program/ there's also things like https://github.com/SakanaAI/ShinkaEvolve which are interesting.

I'd have Shmocky manage the development, testing and evaluation of the system e.g. creating agents, creating tools for agents e.g. backtest tooling, databases. It can then analyse data and iteratively improve things. To be clear, Hedgeknight agents and the Hedgeknight code is completely independent from Shmocky. Shmocky is just the developer. I plan to create more traditional "light weight" agents in the Hedgeknight system to execute functions. I'll likely use OpenRouter to provide model access. In summary, I want Schmocky to evolve the system, not be the system.

For the actual hedgeknight v1, I’d keep the “team” much simpler than ATLAS-style 25-agent debate. ATLAS describes prompt evolution from market feedback and agent creation when gaps are detected, which is directionally right, but my intuition points toward a simpler starting point: one editable task repo, strong memory/performance tracking, explicit evaluation, and only a few role-specialized subagents at first. I also don't want to get too hung up on backtesting. It's useful to a point, but I'd really like the system to be mostly learning from live data and paper trading as soon as possible.

Things to consider:
There are a bunch of API keys for things. I'm currently keeping them in a .env in hedgeknight root.
e.g.
#.env.example
OPENROUTER_API_KEY=
FMP_API_KEY=
MASSIVE_API_KEY=
FRED_API_KEY=
SEC_API_USER_AGENT=

We need at least a financial info database so we don't keep hitting API's (both speed and cost of data - I want to stay on free tier as long as possible). Possibly DuckDB for nice polars integration?

Might want something like graphiti for temporal knowledge graphs?

I think tight contracts between the Hedgeknight agents are going to be important. Possibly something like Pydanticai is a good fit here?
