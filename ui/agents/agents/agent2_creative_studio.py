import os
import json
import urllib.request
from uagents import Agent, Context, Model

CREATIVE_STUDIO_ADDRESS = "agent1qgj6hguesylmq0kswl3mgdt6h7e9h3caa99n972c4vx0frtha7hqzfggukz"

agent = Agent(
    name="gourmet-growth-ai",
    seed="gourmet_growth_ai_agentverse_seed_2026"
)

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

@agent.on_message(model=RestaurantInfo)
async def handle_strategy(ctx: Context, sender: str, msg: RestaurantInfo):
    ctx.logger.info(f"📊【Agent 1 受信】{msg.name} ({msg.location}, {msg.genre}) の自律市場分析を開始...")

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip().strip('"').strip("'")
    
    # デフォルトの推論インサイト（AI分析の指針に基づくフォールバック）
    dynamic_analysis = {
        "positioning": f"プレミアムなダイニング街({msg.location})において、{msg.usp}を武器に高い客単価と高いエンゲージメントを両立するポジション。",
        "competitors": f"近隣の同ジャンル（{msg.genre}）のトップブランドと比較し、ストーリー性と独自性で差別化。",
        "reviews_summary": "「素材の圧倒的なクオリティ」「洗練された空間」への称賛が多い一方、「予約システムの利便性や初回アクセスへの配慮」に改善の余地あり。",
        "improvements": "1. 週末のプレミアム枠を価値化するエンタメ型予約（ドロップデート）の導入\n2. 視覚的シズル感を伝えるリール動画主導の認知拡大"
    }

    # ハードコードされた分析の「指針」をベースに、入力情報からAIがダイナミックに分析を拡張
    if gemini_key:
        try:
            analysis_prompt = f"""
You are the Chief Strategy & Market Intelligence Agent for high-end restaurants.
Based on the following restaurant input data, generate a deep strategic market analysis.
- Restaurant Name: {msg.name}
- Genre: {msg.genre}
- Location: {msg.location}
- Target: {msg.target}
- USP: {msg.usp}
- Additional Context: {msg.issue}

Provide a JSON response with exactly these keys:
- "positioning": Market positioning and local area characteristics in {msg.location}.
- "competitors": Benchmark analysis against local top-tier competitors.
- "reviews_summary": Simulated Yelp & Google reviews summary (positives and minor pain points).
- "improvements": 2 concrete, highly strategic marketing improvements tailored to this restaurant.
Keep the response strictly in Japanese.
"""
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={gemini_key}"
            headers = {"Content-Type": "application/json"}
            payload = {"contents": [{"parts": [{"text": analysis_prompt}]}]}

            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=15) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                candidates = res_data.get("candidates", [])
                if candidates:
                    text_res = candidates[0].get("content", {}).get("parts", [])[0].get("text", "")
                    # JSON部分の抽出
                    cleaned_json = text_res.replace("```json", "").replace("```", "").strip()
                    parsed = json.loads(cleaned_json)
                    dynamic_analysis.update(parsed)
                    ctx.logger.info("🎉 Agent 1 による入力情報ベースの動的市場分析・レビュー推論が完了しました！")
        except Exception as e:
            ctx.logger.warning(f"⚠️ Gemini 分析フォールバック適用: {e}")

    # 分析結果を issue / メッセージデータに結合して下流（Agent 2 ➔ 4 ➔ UI）へ引き渡し
    analysis_package = json.dumps(dynamic_analysis, ensure_ascii=False)
    msg.issue += f"\n[NFM_AI_ANALYSIS_PACKAGE]: {analysis_package}"

    # Agent 2 へ転送
    try:
        await ctx.send(CREATIVE_STUDIO_ADDRESS, msg)
        ctx.logger.info("✅ Agent 2 (Creative Studio) へ戦略分析データを送信完了。")
    except Exception as e:
        ctx.logger.error(f"❌ 転送エラー: {e}")

if __name__ == "__main__":
    agent.run()
