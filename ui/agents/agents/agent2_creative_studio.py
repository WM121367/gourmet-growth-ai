import os
from uagents import Agent, Context, Model
from pydantic import BaseModel
from openai import OpenAI

class StrategyPayload(BaseModel):
    restaurant_name: str
    sender_agent: str
    strategy_report: str

class CreativePayload(BaseModel):
    restaurant_name: str
    ad_copy: str
    image_prompt: str

AD_DEPLOYMENT_ADDRESS = "agent1qw4umx64uk5vsk73un499l4gfgyydp5kygwlfpyw2m37e5en0ypju9lwmsf"

agent = Agent(name="creative-studio", seed="creative_studio_agentverse_seed_2026")

@agent.on_message(model=StrategyPayload)
async def handle_strategy(ctx: Context, sender: str, msg: StrategyPayload):
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    
    prompt = f"店舗: {msg.restaurant_name}\n戦略: {msg.strategy_report}\n\nInstagram広告テキストとDALL-E 3用英語プロンプトを生成してください。"
    res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
    
    payload = CreativePayload(
        restaurant_name=msg.restaurant_name,
        ad_copy=res.choices[0].message.content,
        image_prompt=f"Professional food photo for {msg.restaurant_name}"
    )
    await ctx.send(AD_DEPLOYMENT_ADDRESS, payload)

if __name__ == "__main__":
    agent.run()
