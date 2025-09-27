# Frontline AI Worker – Project Documentation

## 1. Project Overview  

**Project Name:** Frontline AI Worker  

**Objective:**  
To provide an intelligent, agentic AI system that serves as a comprehensive frontline worker across three major industries—**Healthcare** and **Event Management**.  

The system leverages multiple autonomous agents to handle user interactions, assess needs, retrieve relevant information, and manage data entry. By combining agentic workflows, retrieval-augmented generation (RAG), and multi-channel processing tools (MCP), the platform delivers efficient, context-aware support.  

---

## 2. Key Components  

### 2.1 Triage Agent  
Acts as the entry point for all user interactions.  

**Responsibilities:**  
- Assess user queries.  
- Direct requests to the appropriate frontline industry agent.  
- Ensure efficient routing and accurate handoff between users and specialized agents.  

### 2.2 Frontline Industry Agents  
Each agent specializes in a domain while sharing a unified workflow:  

#### Healthcare Frontline Agent  
- Asks basic qualifying questions to collect essential details.  
- Uses Tavely MCP to search for medical guidelines, resources, and healthcare information.  
- Stores validated information in RAG for contextual reuse.  
- Supports appointment preparation and patient triage.  

#### Event Planner Frontline Agent  
- Assists in scheduling, vendor coordination, and resource lookup for events.  
- Uses MCP to fetch relevant event-related resources.  
- Leverages RAG for storing templates, checklists, and past event data.  

### 2.3 Form Filler Agent  
Connected to all main agents to automate data entry.  

**Responsibilities:**  
- Populate standardized forms with user-provided and retrieved data.  
- Ensure consistency across workflows.  
- Act as a central utility to streamline processes in medical and event management workflows.  

### 2.4 Degraded Mode  
We will handle the degraded mode through prompting or custom logic.  

---

## 3. Technical Framework  

### 3.1 Core Technologies  
- **OpenAI SDK** – Primary framework for building the agentic workflow.  
- **Gemini API Key** – Connects to Google’s AI models for enhanced reasoning.  
- **Tavely MCP** – Search and discovery tool integrated with all agents.  
- **RAG (Retrieval-Augmented Generation)** – Storage and knowledge retrieval for past queries and contextual learning.  

### 3.2 Agentic Workflow  
1. User query enters through the **Triage Agent**.  
2. Triage Agent collects input → routes request to the relevant Frontline Agent.  
3. Frontline Agent uses **Tavely MCP** to fetch information.  
4. Relevant findings stored in **RAG** for context enrichment.  
5. **Form Filler Agent** populates structured data forms.  
6. Final response delivered to the user with industry-specific precision.  

---

## 4. Benefits & Real-World Feasibility  

- **Scalability** – Easily extendable to additional industries.  
- **Autonomy** – Agents work independently yet collaborate through orchestration.  
- **Efficiency** – Reduces manual effort for frontline workers.  
- **Consistency** – Standardized form-filling ensures accuracy.  
- **Feasibility** – Uses established SDKs and APIs, minimizing complexity in integration.  

---

## 5. Conclusion  
The Frontline AI Worker project presents a modular, intelligent solution that combines autonomous agents, workflow orchestration, and retrieval-augmented knowledge systems to improve frontline operations in healthcare and event management.
