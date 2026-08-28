"""Planner — decomposes goals into actionable steps."""

import json


SYSTEM_PROMPT = """You are the planning module of Forgemind — a self-improving AI agent.
Your job is to analyze the current state of the codebase and create a prioritized plan for improvement.

Rules:
1. Each step must be concrete and actionable
2. Prioritize: bug fixes > test coverage > performance > new features > refactoring
3. Never plan changes that could break existing functionality
4. Include a verification method for each step
5. Maximum 5 steps per cycle

Output format: JSON array of steps, each with:
- "action": what to do
- "target": which file/module
- "reason": why this improvement
- "risk": "low" | "medium" | "high"
- "verify": how to verify it worked"""


class Planner:
    """Planner class responsible for creating improvement plans based on codebase analysis."""
    def __init__(self, llm):
        """Initialize the Planner with a language model.

        Args:
            llm: A language model instance used for generating improvement plans.
        """
        self.llm = llm

    def create_plan(self, codebase_info: dict, weaknesses: list, memory_summary: str) -> list:
        """Analyze codebase and create improvement plan."""
        user_msg = f"""Current codebase structure:
{json.dumps(codebase_info, indent=2)[:3000]}

Detected weaknesses:
{json.dumps(weaknesses[:10], indent=2)[:2000]}

Memory summary:
{memory_summary}

Create an improvement plan. Focus on the highest-impact, lowest-risk changes first."""

        response = self.llm.chat_simple(SYSTEM_PROMPT, user_msg)

        # Parse JSON from response
        try:
            # Find JSON array in response
            start = response.find("[")
            end = response.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass

        return [{"action": "manual_review", "reason": "Planning failed", "risk": "low"}]
