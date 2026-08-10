import os
from uagents import Agent, Context, Model
from pydantic import BaseModel
from openai import OpenAI

class RestaurantInfo(BaseModel):
    name: str
    genre: str
    location: str
    target: str
    usp: str
    issue: str

class StrategyPayload(BaseModel):
    restaurant_name: str
    sender_agent: str
    strategy_report: str

CREATIVE_STUDIO_ADDRESS = "agent1qgj6hguesylmq0kswl3mgdt6h7e9h3caa99n972c4vx0frtha7hqzfggukz"

agent = Agent(name="gourmet-growth-ai", seed="gourmet_growth_ai_agentverse_seed_2026")

@agent.on_message(model=RestaurantInfo)
async def handle_info(ctx: Context, sender: str, msg: RestaurantInfo):
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    
    prompt = f"店名: {msg.name}\nジャンル: {msg.genre}\nターゲット: {msg.target}\n課題: {msg.issue}\n\n上記店舗の市場分析と施策を立案してください。"
    res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
    
    payload = StrategyPayload(restaurant_name=msg.name, sender_agent=agent.address, strategy_report=res.choices[0].message.content)
    await ctx.send(CREATIVE_STUDIO_ADDRESS, payload)

if __name__ == "__main__":
    agent.run()
