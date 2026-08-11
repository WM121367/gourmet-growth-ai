%%writefile agents/agent2_creative_studio.py
import os
from uagents import Agent, Context, Model
from openai import OpenAI

class StrategyPayload(Model):
    restaurant_name: str
    sender_agent: str
    strategy_report: str

class CreativePayload(Model):
    restaurant_name: str
    ad_copy: str
    image_prompt: str
    image_url: str  # DALL-E 3 で生成した画像URLを追加

# 送信先 Agent 3 (ad-deployment) のアドレス
AD_DEPLOYMENT_ADDRESS = "agent1qw4umx64uk5vsk73un499l4gfgyydp5kygwlfpyw2m37e5en0ypju9lwmsf"

agent = Agent(
    name="creative-studio",
    seed="creative_studio_agentverse_seed_2026"
)

@agent.on_message(model=StrategyPayload)
async def handle_strategy(ctx: Context, sender: str, msg: StrategyPayload):
    ctx.logger.info(f"[{msg.restaurant_name}] の戦略データを受信。広告クリエイティブ＆画像生成を開始します...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        ctx.logger.error("OPENAI_API_KEY が未設定です。AgentVerse Secrets を確認してください。")
        return

    client = OpenAI(api_key=api_key)

    # 1. 広告コピー & DALL-E 3 用英語プロンプトの生成 (GPT-4o-mini)
    copy_prompt = f"""
あなたは外食産業専門の最高クリエイティブディレクターです。
以下の店舗情報と戦略レポートに基づき、Instagram広告用のテキストおよびDALL-E 3画像生成用プロンプトを作成してください。

店舗名: {msg.restaurant_name}
戦略レポート:
{msg.strategy_report}

【出力形式】
[AD_COPY]
Instagram用のキャッチコピー、本文、ハッシュタグ

[IMAGE_PROMPT]
DALL-E 3用プロンプト (英語のみ。シズル感溢れる料理のクローズアップ、シネマティックな照明、高解像度レストラン写真の指定を含める)
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": copy_prompt}],
        temperature=0.7
    )

    generated_text = response.choices[0].message.content

    # テキスト解析 (AD_COPY と IMAGE_PROMPT の分離)
    ad_copy = generated_text
    dalle_prompt = f"Professional food photography of signature dishes for {msg.restaurant_name}, high-end restaurant ambiance, natural lighting, 8k resolution, photorealistic"

    if "[IMAGE_PROMPT]" in generated_text:
        parts = generated_text.split("[IMAGE_PROMPT]")
        ad_copy = parts[0].replace("[AD_COPY]", "").strip()
        dalle_prompt = parts[1].strip()

    # 2. DALL-E 3 API の直接呼び出し
    ctx.logger.info(f"DALL-E 3 API を呼び出して画像を生成中... (Prompt: {dalle_prompt[:60]}...)")
    
    try:
        img_response = client.images.generate(
            model="dall-e-3",
            prompt=dalle_prompt,
            size="1024x1024",  # Instagram 正方形サイズ
            quality="standard",
            n=1
        )
        image_url = img_response.data[0].url
        ctx.logger.info(f"DALL-E 3 画像の生成に成功しました: {image_url}")
    except Exception as e:
        ctx.logger.error(f"DALL-E 3 画像生成エラー: {e}")
        # エラー時のフォールバック用ダミー画像 URL
        image_url = "https://placehold.co/1024x1024/png?text=DALL-E+Generation+Failed"

    # 3. Agent 3 (ad-deployment) へ P2P 送信
    payload = CreativePayload(
        restaurant_name=msg.restaurant_name,
        ad_copy=ad_copy,
        image_prompt=dalle_prompt,
        image_url=image_url
    )

    ctx.logger.info("クリエイティブ生成および画像URLの紐付け完了。Agent 3 へ P2P 送信します...")
    await ctx.send(AD_DEPLOYMENT_ADDRESS, payload)

if __name__ == "__main__":
    agent.run()
