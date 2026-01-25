from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.base_agent import BaseAgent
from google.adk.events import Event, EventActions
from typing import AsyncGenerator

class CheckStatusAndEscalate(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        feedback = ctx.session.state.get("feedback", "valid")
        should_stop = (feedback == "valid")
        yield Event(author=self.name, actions=EventActions(escalate=should_stop))