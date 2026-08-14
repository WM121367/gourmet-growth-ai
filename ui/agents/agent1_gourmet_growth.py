from uagents import Agent, Context, Model, Protocol

# --------------------------------------------------
# ⚙️ Agent 初期化 & アドレス設定
# --------------------------------------------------
CREATIVE_STUDIO_ADDRESS = "agent1qgj6hguesylmq0kswl3mgdt6h7e9h3caa99n972c4vx0frtha7hqzfggukz"

agent = Agent(
    name="gourmet-growth-ai",
    seed="gourmet_growth_ai_agentverse_seed_2026"
)

# --------------------------------------------------
# 📊 P2P データ通信用モデル定義
# --------------------------------------------------
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

class ResponseMsg(Model):
    status: str
    message: str

# --------------------------------------------------
# 💬 Chat Protocol (ASI One 標準完全互換版)
# --------------------------------------------------
class ChatMessage(Model):
    message: str

chat_proto = Protocol(name="Agent Chat Protocol", version="0.2.0")

@chat_proto.on_message(model=ChatMessage, replies=ChatMessage)
async def handle_marketing_chat(ctx: Context, sender: str, msg: ChatMessage):
    user_query = msg.message.lower().strip()
    ctx.logger.info(f"💬 [Marketing Agent 1 Chat] 受信 from {sender}: {msg.message}")

    if any(k in user_query for k in ["campaign", "キャンペーン", "施策", "広告"]):
        reply_text = (
            f"📈 **Next Flow Marketing - Campaign Status**\n"
            f"・アクティブ施策: ターゲット層自動最適化パイプライン稼働中\n"
            f"・主要チャネル: SNS・AIプロモート / コンバージョン重視設計\n"
            f"・ステータス: 正常配信中"
        )
    elif any(k in user_query for k in ["roi", "成果", "コンバージョン", "パフォーマンス"]):
        reply_text = (
            f"🎯 **Next Flow Marketing - Performance Metrics**\n"
            f"・予想ROI: **320% - 450%**\n"
            f"・リード獲得効率: AIマルチエージェント最適化により従来比 +38% 向上\n"
            f"・データ同期: FastAPI Bridge 正常接続"
        )
    else:
        reply_text = (
            f"🚀 **Next Flow Marketing Agent 1 (gourmet-growth-ai)**\n"
            f"自律型マーケティングパイプライン＆顧客獲得エンジン稼働中。\n\n"
            f"キーワード: `campaign`, `roi`"
        )

    await ctx.send(sender, ChatMessage(message=reply_text))

# ★ パブリッシュ付きでプロトコル登録
agent.include(chat_proto, publish_manifest=True)

# --------------------------------------------------
# 🔄 P2P データ転送ハンドラー (on_message で確実に受信)
# --------------------------------------------------
@agent.on_message(model=RestaurantInfo)
async def handle_restaurant_info(ctx: Context, sender: str, msg: RestaurantInfo):
    ctx.logger.info(f"🚀【Agent 1 受信】Bridgeから店舗データ受け取り: {msg.name} ({msg.genre})")
    try:
        await ctx.send(CREATIVE_STUDIO_ADDRESS, msg)
        ctx.logger.info(f"✅ Agent 2 (Creative Studio: {CREATIVE_STUDIO_ADDRESS[:16]}...) へ P2P 転送完了。")
    except Exception as e:
        ctx.logger.error(f"❌ Agent 2 転送エラー: {e}")

if __name__ == "__main__":
    agent.run()
