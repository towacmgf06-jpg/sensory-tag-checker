import os
import json
import streamlit as st
from PIL import Image
import google.generativeai as genai

st.set_page_config(page_title="感覚過敏向け 衣服ストレスチェッカー", page_icon="🏷️", layout="centered")

st.title("🏷️ 衣服ストレス・不快度チェッカー")
st.caption("テキスタイル科学に基づく感覚過敏向けタグ・縫製判定アプリ")

# --- サイドバー: 個人設定 ---
st.sidebar.header("⚙️ 過敏度プロファイル設定")
p_tag = st.sidebar.slider("🏷️ タグ角・エッジ過敏度", 0.5, 3.0, 1.0, 0.1)
p_seam = st.sidebar.slider("🧵 縫い代・糸摩擦過敏度", 0.5, 3.0, 1.0, 0.1)
p_fiber = st.sidebar.slider("🧶 化繊・チクチク過敏度", 0.5, 3.0, 1.0, 0.1)

zone_options = {
    "腕・すね (低感受性: 1.0)": 1.0,
    "背中・胸 (中感受性: 1.2)": 1.2,
    "ウエスト・足首 (高感受性: 1.5)": 1.5,
    "首筋・脇腹・鼠径部 (超高感受性: 2.0)": 2.0
}
selected_zone_name = st.sidebar.selectbox("📍 接触部位", list(zone_options.keys()), index=3)
w_z = zone_options[selected_zone_name]

api_key = os.environ.get("GEMINI_API_KEY") or st.sidebar.text_input("🔑 Gemini API Key を入力", type="password")

# --- メイン画面 ---
st.subheader("1. タグまたは服の裏側を撮影")
uploaded_file = st.camera_input("カメラで撮影") or st.file_uploader("または画像をアップロード", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="解析対象画像", use_container_width=True)

    if st.button("🔍 不快度スコアを解析する", type="primary"):
        if not api_key:
            st.error("左側のサイドバーに Gemini API Key を入力してください。")
        else:
            with st.spinner("AIが素材・タグ仕様・縫製を多角的に解析中..."):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel("gemini-3.6-flash")

                    prompt = """
あなたはテキスタイル科学と感覚過敏の専門家です。
画像から以下の3項目を解析し、0〜4点で評価した結果を必ず以下のJSON形式のみで出力してください。

JSONフォーマット:
{
  "S_T": 0, // タグ仕様 (0:タグレス 〜 4:硬いナイロン)
  "S_S": 0, // 縫製仕様 (0:シームレス 〜 4:硬いロックミシン)
  "S_F": 0, // 繊維組成 (0:綿100% 〜 4:ウール/麻/アクリル)
  "fiber_detail": "読み取った素材情報",
  "tag_detail": "読み取ったタグ情報",
  "seam_detail": "読み取った縫製情報",
  "advice": "具体策・リスク解説"
}
"""
                    response = model.generate_content([prompt, image])
                    # レスポンスからJSONを抽出してパース
                    clean_text = response.text.replace("```json", "").replace("```", "").strip()
                    data = json.loads(clean_text)

                    # Python側で計算処理（0〜100点換算）
                    raw_score = w_z * ((0.45 * data["S_T"] * p_tag) + (0.35 * data["S_S"] * p_seam) + (0.20 * data["S_F"] * p_fiber))
                    # 4点満点基準の最大値補正で100点満点に正規化
                    max_possible = w_z * ((0.45 * 4 * p_tag) + (0.35 * 4 * p_seam) + (0.20 * 4 * p_fiber))
                    final_score = min(100, int((raw_score / max_possible) * 100))

                    # ランク判定
                    if final_score <= 20:
                        rank = "🟢 セーフ"
                    elif final_score <= 50:
                        rank = "🟡 軽度注意"
                    elif final_score <= 75:
                        rank = "🟠 要警戒"
                    else:
                        rank = "🔴 高トリガー"

                    # 結果表示
                    st.success("解析が完了しました！")
                    col1, col2 = st.columns(2)
                    col1.metric("総合不快度スコア", f"{final_score} / 100")
                    col2.metric("判定ランク", rank)

                    st.progress(final_score / 100)

                    st.markdown("### 📋 読み取り内訳")
                    st.write(f"- **繊維組成 ({data['S_F']}点)**: {data['fiber_detail']}")
                    st.write(f"- **タグ仕様 ({data['S_T']}点)**: {data['tag_detail']}")
                    st.write(f"- **縫製仕様 ({data['S_S']}点)**: {data['seam_detail']}")

                    st.markdown("### 💡 アドバイス")
                    st.info(data["advice"])

                except Exception as e:
                    st.error(f"解析中にエラーが発生しました: {e}")
