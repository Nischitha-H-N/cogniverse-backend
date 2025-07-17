from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")

if not API_KEY:
    raise ValueError("OPENROUTER_API_KEY not set in environment variables.")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)

agents: List[dict] = []

class Agent(BaseModel):
    name: str
    role: str
    instructions: str

class Query(BaseModel):
    agent_name: str
    question: str

@app.post("/create-agent")
async def create_agent(agent: Agent):
    agent_data = agent.dict()
    agents.append(agent_data)
    return {"message": "Agent created successfully", "data": agent_data}

@app.post("/ask-agent")
async def ask_agent(query: Query):
    agent = next((a for a in agents if a["name"].lower() == query.agent_name.lower()), None)
    if not agent:
        return {"response": f"Agent '{query.agent_name}' not found."}

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = (
        f"You are {agent['name']}, a helpful assistant working as a {agent['role']}. "
        f"{agent['instructions']} "
        f"The user asked: {query.question}. Provide a helpful answer."
    )

    payload = {
        "model": "mistralai/mistral-7b-instruct",  # ✅ Free and working model
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
        res.raise_for_status()
        data = res.json()
        answer = data['choices'][0]['message']['content']
        return {"response": answer}
    except Exception as e:
        print("Error from OpenRouter:", e)
        return {"response": "Failed to get AI response. Check your API key, model ID, or internet."}
