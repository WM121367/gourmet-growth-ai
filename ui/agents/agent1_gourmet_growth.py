import os
import json
import urllib.request
import urllib.error
import sys
import subprocess
from uagents import Agent, Context, Model

# ★ MeTTaの動的インポート
try:
    import hyperon
except ImportError:
    print("hyperon が見つかりません。動的にインストールを開始します...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "hyperon", "openai", "uagents"])
    import hyperon

from hyperon import MeTTa

class DeploymentPayload(Model):
    campaign_id: str
    restaurant_name: str
    status: str
    image_url: str
    ad_copy: str
    bridge_url: str

agent = Agent(
    name="analytics-monitor",
    seed="analytics_monitor_agentverse_seed_2026"
)

SUPPORTED_LANGUAGES = {
    "Japanese": "日本語",
    "English": "English",
    "Traditional Chinese": "繁體中文",
    "Simplified Chinese": "简体中文",
    "Korean": "한국어",
    "Spanish": "Español",
    "Thai": "ไทย",
    "Vietnamese": "Tiếng Việt"
}

# ★ Ayrshare 経由で Instagram に自動投稿する関数
def post_to_instagram_via_ayrshare(caption: str, image_url: str, ctx: Context = None) -> dict:
    ayrshare_key = os.getenv("AYRSHARE_API_KEY", "").strip().strip('"').strip("'")
    
    if not ayrshare_key:
        msg = "⚠️ AYRSHARE_API_KEY が Secrets に設定されていません。"
        if ctx:
            ctx.logger.warning(msg)
        else:
            print(msg)
        return {"status": "error", "message": "Missing API Key"}

    url = "https://app.ayrshare.com/api/post"
    headers = {
        "Authorization": f"Bearer {ayrshare_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "post": caption,
        "platforms": ["instagram"],
        "mediaUrls": [image_url]
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            msg = f"🎉 Instagram への自動投稿が完了しました！: {res_data}"
            if ctx:
                ctx.logger.info(msg)
            else:
                print(msg)
            return res_data
    except Exception as e:
        msg = f"❌ Ayrshare 投稿エラー: {e}"
        if ctx:
            ctx.logger.error(msg)
        else:
            print(msg)
        return {"status": "error", "message": str(e)}

EXCLUDE_KEYWORDS = ["tts", "embedding", "imagen", "aqa", "bison"]

# ★ MeTTa によるアナリティクス・提案内容の検証関数
def audit_analytics_report(analysis_text: str, current_cpa: float) -> str:
    metta = MeTTa()
    metta_script = f"""
    (= (check-cpa-status $cpa)
       (if (> $cpa 10.00)
           "WARNING: CPA Target Exceeded. Prioritize High-Margin Upsell Items."
           "OPTIMAL: CPA Within Target Range."))
    
    !(check-cpa-status {current_cpa})
    """
    result = metta.run(metta_script)
    return analysis_text + f"\n\n[MeTTa Logic Audit]: {str(result)}"

@agent.on_message(model=DeploymentPayload)
async def handle_deployment(ctx: Context, sender: str, msg: DeploymentPayload):
    selected_lang = os.getenv("OUTPUT_LANGUAGE", "Japanese")
    target_lang_label = SUPPORTED_LANGUAGES.get(selected_lang, "日本語")

    ctx.logger.info(f"[{msg.campaign_id}] 多言語推論を開始... (Bridge URL: {msg.bridge_url})")

    raw_gemini_key = os.getenv("GEMINI_API_KEY", "")
    gemini_key = raw_gemini_key.strip().strip('"').strip("'")
    openai_key = os.getenv("OPENAI_API_KEY", "").strip().strip('"').strip("'")

    if gemini_key:
        ctx.logger.info(f"GEMINI_API_KEY 読み込み完了 (有効文字数: {len(gemini_key)}文字)")
    else:
        ctx.logger.warning("GEMINI_API_KEY が Secrets から検出されませんでした。")

    metrics_summary = "CTR: 3.8% (High), CVR: 1.1% (Low), CPA: $14.50 (Target: $10.00)"

    reasoning_prompt = f"""
You are the Chief Analytics Reasoning Agent operating in a global autonomous marketing ecosystem.
Analyze the following marketing campaign input data and generate the output report strictly in {target_lang_label}.

[Input Data]:
- Target Restaurant: {msg.restaurant_name}
- Campaign ID: {msg.campaign_id}
- Creative Image URL: {msg.image_url}
- Performance Metrics: {metrics_summary}

Tasks:
1. Explain logically WHY the click-through rate (CTR) is high while the conversion rate (CVR) is low.
2. Formulate 1 specific improvement instruction for Agent 2 to refine the next ad copy.
"""

    analysis_text = ""

    # 1. Gemini REST API
    if gemini_key:
        active_models = []
        try:
            list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={gemini_key}"
            req_list = urllib.request.Request(list_url, method="GET")
            with urllib.request.urlopen(req_list, timeout=10) as resp:
                models_data = json.loads(resp.read().decode("utf-8"))
                for m in models_data.get("models", []):
                    methods = m.get("supportedGenerationMethods", [])
                    m_name = m.get("name", "").replace("models/", "")
                    if "generateContent" in methods and not any(kw in m_name.lower() for kw in EXCLUDE_KEYWORDS):
                        active_models.append(m_name)
            
            active_models.sort(key=lambda x: ("flash" not in x, "latest" not in x, "pro" not in x))
            ctx.logger.info(f"最適化された Gemini モデル優先リスト: {active_models[:3]}")
        except Exception as e:
            ctx.logger.warning(f"モデルリスト自動取得失敗 (固定デフォルト適用): {e}")
            active_models = ["gemini-flash-latest", "gemini-1.5-flash", "gemini-pro-latest"]

        for model_name in active_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}"
            headers = {"Content-Type": "application/json"}
            payload = {"contents": [{"parts": [{"text": reasoning_prompt}]}]}

            try:
                req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=15) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    candidates = res_data.get("candidates", [])
                    if candidates:
                        analysis_text = candidates[0].get("content", {}).get("parts", [])[0].get("text", "")
                        ctx.logger.info(f"🎉 Gemini REST API ({model_name}) 推論完了！")
                        break
            except Exception as e:
                ctx.logger.warning(f"Gemini API ({model_name}) スキップ: {e}")

    # 2. GPT-4o フォールバック
    if not analysis_text and openai_key:
        ctx.logger.info("GPT-4o フォールバックを開始します...")
        from openai import OpenAI
        try:
            client = OpenAI(api_key=openai_key)
            res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": reasoning_prompt}],
                temperature=0.2
            )
            analysis_text = res.choices[0].message.content
        except Exception as e:
            ctx.logger.error(f"GPT-4o 実行エラー: {e}")

    if not analysis_text:
        analysis_text = f"【自律改善診断 ({target_lang_label})】広告クリック数は良好ですが、予約完了率に課題があります。ランディングページ上の特別オファーとクリエイティブ写真の合致度を高めてください。"

    ctx.logger.info(f"分析完了: {analysis_text[:50]}...")

    # ★ MeTTa による最終レポート監査
    current_cpa = 14.50
    final_analysis_text = audit_analytics_report(analysis_text, current_cpa)
    ctx.logger.info("【MeTTa 監査】アナリティクスレポートの論理検証完了。")

    # ★ Instagram への自動パブリッシュ (Ayrshare 経由)
    if msg.image_url and msg.ad_copy:
        ctx.logger.info("Instagram への自動投稿を開始します...")
        post_to_instagram_via_ayrshare(
            caption=f"{msg.ad_copy}\n\n#NextFlowMarketing #AIAgent",
            image_url=msg.image_url,
            ctx=ctx
        )

    # Bridge サーバーへ送信
    if msg.bridge_url:
        report_payload = {
            "campaign_id": msg.campaign_id,
            "restaurant_name": msg.restaurant_name,
            "analysis_text": final_analysis_text,
            "ad_copy": msg.ad_copy,
            "image_url": msg.image_url
        }
        try:
            target_report_url = f"{msg.bridge_url.rstrip('/')}/report"
            req = urllib.request.Request(
                target_report_url,
                data=json.dumps(report_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                ctx.logger.info("Bridge サーバーへ最終分析レポートを送信完了。")
        except Exception as e:
            ctx.logger.error(f"Bridge 返送エラー: {e}")

if __name__ == "__main__":
    agent.run()
