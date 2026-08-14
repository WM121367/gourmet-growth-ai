import os
import json
import urllib.request
import sys
import subprocess
from uagents import Agent, Context, Model, Protocol

try:
    import hyperon
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "hyperon", "openai", "uagents"])
    import hyperon

# ==============================================================================
# 1. メッセージモデル定義
# ==============================================================================
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

# ★ ASI:One / DeltaV 標準チャットモデル (text: str)
class Message(Model):
    text: str

class TextResponse(Model):
    text: str

AD_DEPLOYMENT_ADDRESS = "agent1qw4umx64uk5vsk73un499l4gfgyydp5kygwlfpyw2m37e5en0ypju9lwmsf"

agent = Agent(
    name="creative-studio",
    seed="creative_studio_agentverse_seed_2026"
)

# 業態別フォールバック写真
GENRE_IMAGES = {
    "tonkatsu": "https://images.unsplash.com/photo-1596797038530-2c107229654b?w=1024",
    "sushi": "https://images.unsplash.com/photo-1617196034796-73dfa7b1fd56?w=1024",
    "general": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=1024"
}

# ==============================================================================
# 🎨 共通クリエイティブ生成コアロジック
# ==============================================================================
def generate_creative_assets(restaurant_name: str, genre: str, usp: str, location: str, ctx: Context) -> tuple[str, str]:
    is_tonkatsu = any(k in (restaurant_name + genre + usp).lower() for k in ["tonkatsu", "とんかつ", "カツ", "pork", "kobuta"])
    default_img = GENRE_IMAGES["tonkatsu"] if is_tonkatsu else (GENRE_IMAGES["sushi"] if "sushi" in (restaurant_name + genre).lower() else GENRE_IMAGES["general"])
    image_url = default_img

    openai_key = os.getenv("OPENAI_API_KEY", "").strip().strip('"').strip("'")
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            dalle_prompt = (
                f"Award-winning professional commercial food photography for '{restaurant_name}'. "
                f"Authentic Japanese {genre} featuring {usp}. "
                "Crispy golden-brown raw panko crust, thick juicy pork cross section, authentic tableware, warm cinematic spotlight, 8k food advertisement."
            )
            ctx.logger.info(f"🤖 DALL-E 3 起動: {dalle_prompt}")
            img_res = client.images.generate(
                model="dall-e-3",
                prompt=dalle_prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            image_url = img_res.data[0].url
            ctx.logger.info(f"🎉 DALL-E 3 画像生成完了: {image_url}")
        except Exception as e:
            ctx.logger.warning(f"⚠️ DALL-E 3 スキップ (フォールバック使用): {e}")
    else:
        ctx.logger.warning("⚠️ OPENAI_API_KEY が未設定のため、高品質フォールバック画像を使用します。")

    ad_copy = (
        f"🔥 **Experience the Ultimate Crispy Perfection at {restaurant_name}!**\n\n"
        f"Beyond sushi — discover authentic Japanese {genre} in {location}! "
        f"Featuring our signature {usp}, fried to golden perfection with artisanal fresh panko breadcrumbs.\n\n"
        f"Juicy, crispy, and unforgettable. Taste the difference today!\n"
        f"#{restaurant_name.replace(' ','')} #AuthenticTonkatsu #SeattleEats #Foodie"
    )

    return image_url, ad_copy

# ==============================================================================
# ① パイプライン自動受信ハンドラー (Agent 1 ➔ Agent 2)
# ==============================================================================
@agent.on_message(model=RestaurantInfo)
async def handle_strategy(ctx: Context, sender: str, msg: RestaurantInfo):
    ctx.logger.info(f"🎨【Agent 1 受信】店舗名: {msg.name} / 業態: {msg.genre} / USP: {msg.usp}")

    image_url, ad_copy = generate_creative_assets(msg.name, msg.genre, msg.usp, msg.location, ctx)

    out_payload = CreativePayload(
        campaign_id=f"CAMP-{msg.name[:3].upper()}-2026",
        restaurant_name=msg.name,
        ad_copy=ad_copy,
        image_url=image_url,
        bridge_url=msg.bridge_url,
        iteration=1
    )
    await ctx.send(AD_DEPLOYMENT_ADDRESS, out_payload)
    ctx.logger.info(f"✅ Agent 3 へ送信完了 (確定画像URL: {image_url})")

# ==============================================================================
# ② ★ ASI:One / DeltaV 標準チャットハンドラー (人間対話用)
# ==============================================================================
@agent.on_message(model=Message, replies={TextResponse})
async def handle_asi_message(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"💬【ASI:One チャット受信】: {msg.text}")
    
    r_name = "Kobuta and Ookami"
    r_genre = "サクサクジューシーとんかつ Specialty"
    r_usp = "極上ロースとんかつ、特製エビフライ、黄金生パン粉"
    r_loc = "Seattle, WA"

    if "sushi" in msg.text.lower() or "寿司" in msg.text:
        r_name = "Shomon kappo Sushi"
        r_genre = "Fine Seasonal Kappo & Omakase"
        r_usp = "秋の新作おまかせ2コース、松茸、本鮪"

    image_url, ad_copy = generate_creative_assets(r_name, r_genre, r_usp, r_loc, ctx)

    reply_content = (
        f"🍱 【Agent 2: Creative Studio 回答】\n"
        f"店舗: {r_name} ({r_genre})\n\n"
        f"📸 【生成画像 URL】:\n{image_url}\n\n"
        f"✍️ 【Instagram 広告コピー】:\n{ad_copy}"
    )

    await ctx.send(sender, TextResponse(text=reply_content))
    ctx.logger.info("💬 ASI:One へ対話レスポンスを返信完了！")

if __name__ == "__main__":
    agent.run()
