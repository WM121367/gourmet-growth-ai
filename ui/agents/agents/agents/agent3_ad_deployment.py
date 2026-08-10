from uagents import Agent, Context, Model
from pydantic import BaseModel

class CreativePayload(BaseModel):
    restaurant_name: str
    ad_copy: str
    image_prompt: str

class DeploymentPayload(BaseModel):
    restaurant_name: str
    campaign_id: str
    status: str

ANALYTICS_MONITOR_ADDRESS = "agent1q0uajwauh4a3hwejc45lmsfv7c7zd2qzjzhg05n0y8a3635v5djtckz7tds"

agent = Agent(name="ad-deployment", seed="ad_deployment_agentverse_seed_2026")

@agent.on_message(model=CreativePayload)
async def handle_creative(ctx: Context, sender: str, msg: CreativePayload):
    ctx.logger.info(f"[{msg.restaurant_name}] 広告配信タスクを実行中...")
    
    # Meta Ads API / Instagram Graph API 連携シミュレーション
    campaign_id = f"CAMP-{msg.restaurant_name[:3].upper()}-2026"
    
    payload = DeploymentPayload(
        restaurant_name=msg.restaurant_name,
        campaign_id=campaign_id,
        status="ACTIVE"
    )
    ctx.logger.info(f"キャンペーン {campaign_id} を出稿しました。Analytics Agent へ引き継ぎます。")
    await ctx.send(ANALYTICS_MONITOR_ADDRESS, payload)

if __name__ == "__main__":
    agent.run()
