# main.py
import os
import asyncio
from dotenv import load_dotenv, find_dotenv
import traceback
from agents import Agent, Runner, set_tracing_disabled, OpenAIChatCompletionsModel, AsyncOpenAI, handoff, RunContextWrapper, TResponseInputItem, function_tool
from agents.mcp import MCPServerStdio
import os
from datetime import datetime, date
from google.oauth2 import service_account
from googleapiclient.discovery import build
import asyncio
from dotenv import load_dotenv, find_dotenv
import traceback
from agents import Agent, Runner, set_tracing_disabled, OpenAIChatCompletionsModel, AsyncOpenAI, function_tool


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
    # ----------------- Google Sheets Setup -----------------
    SERVICE_ACCOUNT_FILE = "gcp_key.json"  # Path to your service account JSON file
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )

    service = build("sheets", "v4", credentials=creds)
    spreadsheets = service.spreadsheets()
    load_dotenv(find_dotenv())
    print("Environment variables loaded.")

    # ----------------- Helper Function -----------------
    def _normalize(val):
        """Turn None/empty -> 'NONE', datetime/date -> ISO string, else str(val)."""
        if val is None:
            return "NONE"
        if isinstance(val, str) and val.strip() == "":
            return "NONE"
        if isinstance(val, datetime):
            return val.date().isoformat()
        if isinstance(val, date):
            return val.isoformat()
        return str(val)

    # ----------------- Core Sheets Function -----------------
    @function_tool
    def append_event_to_sheet(
        spreadsheet_id: str,
        sheet_range: str,
        user_name=None,
        num_guests=None,
        planner_name=None,
        company_contact=None,
        location=None,
        theme=None,
        date_value=None,
        budget=None,
    ):
        """Append an event row to a Google Sheet (agent-facing)."""

        sheet_name = sheet_range.split("!")[0] if "!" in sheet_range else sheet_range

        headers = [
            "User Name",
            "No. of Guests",
            "Event Planner Name",
            "Company Contact Details",
            "Location",
            "Theme",
            "Date",
            "Budget",
        ]

        row = [
            _normalize(user_name),
            _normalize(num_guests),
            _normalize(planner_name),
            _normalize(company_contact),
            _normalize(location),
            _normalize(theme),
            _normalize(date_value),
            _normalize(budget),
        ]

        # Add headers if not present
        header_range = f"{sheet_name}!A1:H1"
        get_resp = spreadsheets.values().get(
            spreadsheetId=spreadsheet_id, range=header_range
        ).execute()

        existing = get_resp.get("values", [])
        if not existing:
            spreadsheets.values().append(
                spreadsheetId=spreadsheet_id,
                range=sheet_name,
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body={"values": [headers]},
            ).execute()

        # Append the row
        return spreadsheets.values().append(
            spreadsheetId=spreadsheet_id,
            range=sheet_name,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": [row]},
        ).execute()


    google_sheet_agent = Agent(
        name="Google Sheets Agent",
        instructions=(
            """You are an agent that helps users add event details to a Google Sheet.
           # Analyze the user data type and categorize in event and health hospitality.
           Always call the tool 'append_event_to_sheet' with the correct arguments.
           In Event related data you do:
               - You will be given user_name, num_guests, planner_name, company_contact,
               -location, theme, date_value, budget, spreadsheet_id, and sheet_range.
               - If any detail is missing, insert NONE in that field.
                - sheet_range=Sheet1 when data is related to an event. 
            In Health hospitality related data you do:
               - You will be given patient_name, disease, location, hospital_name, doctor_name,
               - Use sheet_range=Sheet2 when data is related to health hospitality.
            spreadsheet_id=1824ucSfO7zuOqHYqFrgYorjjHZQFY749rbFfZxohZz4,
            Sheet1 and Sheet2 already exist in the spreadsheet.
            - Always return the response: Event added to sheet successfully.
           
            """
        ),
        model=model,
        tools=[append_event_to_sheet],
    )

    event_planner_agent = Agent(
        name="Event Planner Agent",
        instructions="""# Use Tavily's MCP Stdio tools (search, extract, map, crawl) 
        via remote server to find venues, vendors, and manage event details, contact details.
        You will search at least Five event planners details which should be include:
        Event Planner Names,	Contact Details, 	Location,	Theme,	Date, and 	Budget
        Provide the 5 event planners details in a structured format to user. When User select one event planner then perform action using tool.
        Use Handoffs to google_sheet_agent to append the event details to Google Sheets, only after user selection and if user not want to add any information related to like he/she not select the budget then insert "NONE" in that field.
        
        """,
        model=model,
        mcp_servers=[tavily_stdio],
        handoffs=[google_sheet_agent]
    )
    health_care_agent = Agent(
        name="Health Care Agent",
        instructions="""# Use MCP Stdio tools (search, extract, map, crawl) 
        #  via remote server to find hospital and doctor details based on patient's disease and location.
        Your task is to ask some question like patient name, disease, location (where he/she live)
        and on this basis search the hospital details Use Tavily's stdio MCP tools (search, extract, map, crawl) and search minimum five hospital details at the same city that the provided location which should include:
        Hospital name,	Doctor Name (related to that disease),	Hospital Contact Details,
        And ask patient to select one of them and provide the details in structured format.
        After user selection, use Handoffs to google_sheet_agent to append the health care details to Google Sheets, only after user selection and if user not want to add any information related to like he/she not select the budget then insert "NONE" in that field.""",
        model=model,
        mcp_servers=[tavily_stdio],
        handoffs = [google_sheet_agent]
    )
    def event_handoffs(ctx: RunContextWrapper):
      print("Checking handoff conditions... to Event Planner Agent")
      
    def health_handoffs(ctx: RunContextWrapper):
      print("Checking handoff conditions... to Health Care Agent")
     
    triage_agent = Agent(
        name="Triage Agent",
        instructions="""You are a "Triage expert" assistant.
        Analyze the user's query then categorize it as either related to event planning or healthcare.
        If it is related to event planning, handoff to the event_planner_agent.
        If it is related to healthcare, handoff to the health_care_agent.
       
        Act as a friendly and professional receptionist.
        If the query in not related to event planning or healthcare, then Ask them I will not entertain you in your query and specify the reason.
        """,
        model=model,
        handoffs=[handoff(event_planner_agent, on_handoff=event_handoffs), handoff(health_care_agent, on_handoff=health_handoffs)],
    )
    # google_sheet_agent.handoffs(triage_agent)
    print("Agent initialized.")
    conversation: list[TResponseInputItem] = []  # store conversation history
    last_agent1 = triage_agent
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
#Search the hospital for lungs disease in lahore and provide the doctors with specialization and contact details.