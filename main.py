# main.py
import os
import asyncio
from dotenv import load_dotenv, find_dotenv
import traceback
from agents import Agent, Runner, set_tracing_disabled, OpenAIChatCompletionsModel, AsyncOpenAI, handoff, RunContextWrapper, TResponseInputItem
from agents.mcp import MCPServerStdio

set_tracing_disabled(disabled=True)
load_dotenv(find_dotenv())
print("Environment variables loaded.")

async def main():
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

    if not GEMINI_API_KEY or not TAVILY_API_KEY:
        print("Missing GEMINI_API_KEY or TAVILY_API_KEY in env.")
        return

    client = AsyncOpenAI(
        api_key=GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )
    model = OpenAIChatCompletionsModel(
        model="gemini-2.0-flash",
        openai_client=client
    )

    # Use mcp-remote bridge to remote Tavily MCP via stdio
    tavily_stdio = MCPServerStdio(
        params={    
                "command": "npx",
               "args": [
                        "-y",
                        "mcp-remote",
                        f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"
                    ]
                },
        name="tavily-remote-stdio",
        cache_tools_list=True,
        client_session_timeout_seconds=2000
    )

    try:
        await tavily_stdio.connect()
        print("Connected via mcp-remote to Tavily MCP server.")
    except Exception as e:
        print("Error connecting via mcp-remote:", e)
        traceback.print_exc()
        return 

    event_planner_agent = Agent(
        name="Event Planner Agent",
        instructions="""Act as an expert event planner. ## Use Tavily's MCP tools (search, extract, map, crawl) 
        via remote server to find venues, vendors, and manage event details, contact details, years of experience in the event 
        management. You will provide Five event planners details which should be include: 1.Event Planner Company Name, 2.Location, 3.Contact Details, 4. Menu (Optional if you fd on websites) .
        # When You get the Some Detals of Event the lways use the Tvily MCP ool to search the Event planner and to provide
        the details to user.""",
        model=model,
        mcp_servers=[tavily_stdio]
    )
    health_care_agent = Agent(
        name="Health Care Agent",
        instructions="""Use Tavily's MCP tools (search, extract, map, crawl) via remote server to search the hospital
        doctors with loction and specialization and provide the contact details.""",
        model=model,
        mcp_servers=[tavily_stdio]
    )
    def event_handoffs(ctx: RunContextWrapper):
      print("Checking handoff conditions... to Event Planner Agent")
      
    def health_handoffs(ctx: RunContextWrapper):
      print("Checking handoff conditions... to Health Care Agent")
     
    agent = Agent(
        name="Triage Agent",
        instructions="""You are a "Triage expert" assistant.The goal is to determine whether the user needs 
        event planning assistance or healthcare information and route them to the appropriate specialized agent.  
        ### CRITICAL RULE (Must be followed at all times)
        Your ONLY function is to classify the user's query as either **'Event Planning'** or **'Healthcare'**.
        If the query is about ANY other topic (e.g., history, technology, travel, cooking, personal opinion), you MUST politely but firmly refuse to engage with the question. Do not attempt to use general knowledge.
        ### Refusal Protocol
        For any out-of-scope query, you MUST use this exact response template: 
        "I am a specialized triage agent for healthcare and event management. I can only assist with classifying queries related to those two topics. Please rephrase your question."
        ### Role & Behavior
        - Greet the user warmly and explain you’ll ask a few questions to understand their needs and then fnd the best 
        hospital o clinic for them.
        """,
        model=model,
        handoffs=[handoff(event_planner_agent, on_handoff=event_handoffs), handoff(health_care_agent, on_handoff=health_handoffs)],
    )
    print("Agent initialized.")
    conversation: list[TResponseInputItem] = []  # store conversation history
    last_agent1 = agent
    try:
        while True:
            user_query = input("Enter your query (or 'exit' to quit): ")
            if user_query.lower() == 'exit':
                break

            conversation.append({"content": user_query, "role": "user"})
            result = await Runner.run(last_agent1, conversation)
            print("Final Result:", result.final_output)
            last_agent1 = result.last_agent
            conversation = result.to_input_list()  # keep updated history
    finally:
        await tavily_stdio.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
#Search the hospital for lungs disease in lahore and provide the doctors with specialization and contact details. 