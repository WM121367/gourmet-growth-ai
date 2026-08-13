import sys
import subprocess

# hyperon が未インストールの場合は動的に pip install を実行
try:
    import hyperon
except ImportError:
    print("hyperon が見つかりません。動的にインストールを開始します...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "hyperon", "openai", "uagents"])
    import hyperon
    print("hyperon の動的インストールが完了しました！")

from hyperon import MeTTa
# ---------------------------------------------------------
# 以下、既存の agent.py の処理（import os, Agent, Context など）

import os
from openai import OpenAI
from uagents import Agent, Context, Model
from hyperon import MeTTa  # ★ MeTTa エンジンのインポート

class RestaurantInfo(Model):
    name: str
    genre: str
    location: str
    target: str
    usp: str
    issue: str
    language: str
    custom_image_url: str
    bridge_url: str

class CreativePayload(Model):
    restaurant_name: str
    ad_copy: str
    image_prompt: str
    image_url: str
    bridge_url: str

AD_DEPLOYMENT_ADDRESS = "agent1qw4umx64uk5vsk73un499l4gfgyydp5kygwlfpyw2m37e5en0ypju9lwmsf"

agent = Agent(
    name="creative-studio",
    seed="creative_studio_agentverse_seed_2026"
)

# -------------------------------------------------------------
# ★ MeTTa によるルール検証関数の定義
# -------------------------------------------------------------
def verify_marketing_rules(discount_rate: float) -> tuple[bool, str]:
    """
    MeTTa (Atomspace) を用いて、店舗のガードレールルールを検証する
    """
    metta = MeTTa()
    
    # MeTTa スクリプト: 割引率が 0.15 (15%) 以下であるかを論理評価
    metta_script = f"""
    (= (check-discount $rate)
       (if (<= $rate 0.15)
           "APPROVED"
           "REJECTED: Exceeds 15% Maximum Discount Rule"))
    
    !(check-discount {discount_rate})
    """
    
    result = metta.run(metta_script)
    result_str = str(result)
    
    if "APPROVED" in result_str:
        return True, "APPROVED"
    else:
        return False, "REJECTED: 割引率が上限(15%)を超過しています"

# -------------------------------------------------------------

@agent.on_message(model=RestaurantInfo)
async def handle_strategy(ctx: Context, sender: str, msg: RestaurantInfo):
    ctx.logger.info(f"【Agent 2 受信】{msg.name} の処理を開始します...")
    
    # 1. 画像生成ロジック (既存通り)
    if msg.custom_image_url:
        image_url = msg.custom_image_url
        dalle_prompt = "Custom uploaded image used"
        ctx.logger.info("顧客指定画像を使用します。")
    else:
        api_key = os.getenv("OPENAI_API_KEY")
        image_url = "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=1024&auto=format&fit=crop"
        dalle_prompt = f"Professional food photography of signature dishes for {msg.name}"
        
        if api_key:
            try:
                client = OpenAI(api_key=api_key.strip())
                img_response = client.images.generate(
                    model="dall-e-3",
                    prompt=dalle_prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1
                )
                image_url = img_response.data[0].url
                ctx.logger.info("DALL-E 3 画像生成成功！")
            except Exception as e:
                ctx.logger.warning(f"DALL-E 3 スキップ (デフォルト画像へ切り替え): {e}")

    # 2. オファー率の定義（例: 20%オフの提案が発生したと仮定）
    proposed_discount = 0.20 
    
    # 3. ★ MeTTa による監査実行 ★
    is_valid, reason = verify_marketing_rules(proposed_discount)
    
    if not is_valid:
        ctx.logger.warning(f"⚠️ 【MeTTa 監査判定】 違反検知: {reason}")
        ctx.logger.info(" MeTTaの判定に従い、割引率を上限の 15% に安全補正します。")
        final_discount = 0.15
    else:
        ctx.logger.info("【MeTTa 監査判定】 承認 (APPROVED)")
        final_discount = proposed_discount

    # 監査済みの安全な数値でコピーを生成
    ad_copy = f"✨ Special Dining at {msg.name}! Experience our {msg.usp}. Book today & get {int(final_discount*100)}% OFF!"

    payload = CreativePayload(
        restaurant_name=msg.name,
        ad_copy=ad_copy,
        image_prompt=dalle_prompt,
        image_url=image_url,
        bridge_url=msg.bridge_url
    )
    
    await ctx.send(AD_DEPLOYMENT_ADDRESS, payload)
    ctx.logger.info("Agent 3 (Ad Deployment) へ送信完了。")

if __name__ == "__main__":
    agent.run()
