import os
import json
import urllib.request
import sys
import subprocess
from uagents import Agent, Context, Model

try:
    import hyperon
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "hyperon", "openai", "uagents"])
    import hyperon

class RestaurantInfo(Model):
    name: str
    genre: str
    location: str
    target: str
    usp: str
    issue: str
    language: str = "Japanese"
    custom_image_url: str = ""
    bridge_url: str = ""

class CreativePayload(Model):
    campaign_id: str
    restaurant_name: str
    ad_copy: str
    image_url: str
    bridge_url: str
    iteration: int = 1

AD_DEPLOYMENT_ADDRESS = "agent1qw4umx64uk5vsk73un499l4gfgyydp5kygwlfpyw2m37e5en0ypju9lwmsf"

agent = Agent(
    name="creative-studio",
    seed="creative_studio_agentverse_seed_2026"
)

# 業態別フォールバック画像
GENRE_IMAGES = {
    "tonkatsu": "https://images.unsplash.com/photo-1596797038530-2c107229654b?w=1024",
    "sushi": "https://images.unsplash.com/photo-1617196034796-73dfa7b1fd56?w=1024",
    "general": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=1024"
}

@agent.on_message(model=RestaurantInfo)
async def handle_strategy(ctx: Context, sender: str, msg: RestaurantInfo):
    ctx.logger.info(f"🎨【Agent 2 受信】店舗名: {msg.name} / 業態: {msg.genre} / USP: {msg.usp}")

    # 業態判定
    is_tonkatsu = any(k in (msg.name + msg.genre + msg.usp).lower() for k in ["tonkatsu", "とんかつ", "カツ", "pork", "kobuta"])
    image_url = msg.custom_image_url or (GENRE_IMAGES["tonkatsu"] if is_tonkatsu else GENRE_IMAGES["general"])

    openai_key = os.getenv("OPENAI_API_KEY", "").strip().strip('"').strip("'")
    ctx.logger.info(f"🔑 OpenAI API Key 検出状況: {'設定あり (文字数: ' + str(len(openai_key)) + ')' if openai_key else '未設定'}")

    if openai_key and not msg.custom_image_url:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            dalle_prompt = (
                f"Award-winning professional commercial food photography for '{msg.name}'. "
                f"Authentic Japanese {msg.genre} featuring {msg.usp}. "
                "Crispy golden-brown raw panko crust, thick juicy pork cross section, authentic tableware, warm cinematic spotlight, 8k food advertisement."
            )
            ctx.logger.info(f"🤖 DALL-E 3 プロンプト送信中: {dalle_prompt}")
            
            img_res = client.images.generate(
                model="dall-e-3",
                prompt=dalle_prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            image_url = img_res.data[0].url
            ctx.logger.info(f"🎉 DALL-E 3 画像生成成功！ URL: {image_url}")
        except Exception as e:
            ctx.logger.error(f"❌ DALL-E 3 エラー詳細: {type(e).__name__} - {e}")

    dynamic_ad_copy = (
        f"🔥 **Experience the Ultimate Crispy Perfection at {msg.name}!**\n\n"
        f"Beyond sushi — discover authentic Japanese {msg.genre} in {msg.location}! "
        f"Featuring our signature {msg.usp}, fried to golden perfection with artisanal fresh panko breadcrumbs.\n\n"
        f"Juicy, crispy, and unforgettable. Taste the difference today!\n"
        f"#{msg.name.replace(' ','')} #AuthenticTonkatsu #SeattleEats #Foodie"
    )

    out_payload = CreativePayload(
        campaign_id=f"CAMP-{msg.name[:3].upper()}-2026",
        restaurant_name=msg.name,
        ad_copy=dynamic_ad_copy,
        image_url=image_url,
        bridge_url=msg.bridge_url,
        iteration=1
    )
    await ctx.send(AD_DEPLOYMENT_ADDRESS, out_payload)
    ctx.logger.info(f"✅ Agent 3 へ確定データ送信完了。")

if __name__ == "__main__":
    agent.run()
