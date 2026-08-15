from uagents import Agent, Context, Model

# ★ Agent 2 と完全同一にした CreativePayload
class CreativePayload(Model):
    campaign_id: str
    restaurant_name: str
    ad_copy: str
    image_url: str
    bridge_url: str
    iteration: int = 1

# ★ Agent 4 と完全同一にした DeploymentPayload
class DeploymentPayload(Model):
    campaign_id: str
    restaurant_name: str
    status: str
    image_url: str
    ad_copy: str
    bridge_url: str

ANALYTICS_MONITOR_ADDRESS = "agent1q0uajwauh4a3hwejc45lmsfv7c7zd2qzjzhg05n0y8a3635v5djtckz7tds"

agent = Agent(
    name="ad-deployment",
    seed="ad_deployment_agentverse_seed_2026"
)

@agent.on_message(model=CreativePayload)
async def handle_creative(ctx: Context, sender: str, msg: CreativePayload):
    ctx.logger.info(f"【Agent 3 受信】[{msg.restaurant_name}] クリエイティブ受け取り完了。(Bridge URL: {msg.bridge_url})")

    payload = DeploymentPayload(
        campaign_id=msg.campaign_id,
        restaurant_name=msg.restaurant_name,
        status="ACTIVE",
        image_url=msg.image_url,
        ad_copy=msg.ad_copy,
        bridge_url=msg.bridge_url
    )

    await ctx.send(ANALYTICS_MONITOR_ADDRESS, payload)
    ctx.logger.info("✅ Agent 4 (analytics-monitor) へ DeploymentPayload 送信完了。")

if __name__ == "__main__":
    agent.run()
