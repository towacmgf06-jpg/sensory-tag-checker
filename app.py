import os
import streamlit as st
from PIL import Image
import google.generativeai as genai

st.set_page_config(page_title="感覚過敏向け 衣服ストレスチェッカー", page_icon="🏷️", layout="centered")

st.title("🏷️ 衣服ストレス・不快度チェッカー")
st.caption("テキスタイル科学に基づく感覚過敏向けタグ・縫製判定アプリ")

# --- サイドバー：個人設定 ---
st.sidebar.header("⚙️ 過敏度プロファイル設定")
p_tag = st.sidebar.slider("🏷️ タグ角・エッジ過敏度", 0.5, 3.0, 1.0, 0.1)
p_seam = st.sidebar.slider("🧵 縫い代・糸摩擦過敏度", 0.5, 3.0, 1.0, 0.1)
p_fiber = st.sidebar.slider("🧶 化繊・チクチク過敏度", 0.5, 3.0, 1.0, 0.1)

zone_options = {
    "腕・すね (低感受性: 1.0)": 1.0,
    "背中・胸 (中感受性: 1.2)": 1.2,
    "ウエスト・足首 (高感受性: 1.5)": 1.5,
    "首筋・脇腹・鼠蹊部 (超高感受性: 2.0)": 2.0
}
selected_zone_name = st.sidebar.selectbox("📍 接触部位", list(zone_options.keys()), index=3)
w_z = zone_options[selected_zone_name]

# --- メイン画面 ---
st.subheader("1. タグまたは服の裏側を撮影")
uploaded_file = st.camera_input("カメラで撮影") or st.file_uploader("または画像をアップロード", type=["jpg", "jpeg", "png"])

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.sidebar.text_input("🔑 Gemini API Key を入力", type="password")

if uploaded_file and api_key:
    image = Image.open(uploaded_file)
    st.image(image, caption="解析対象画像", use_container_width=True)

    if st.button("🔍 不快度スコアを解析する", type="primary"):
        with st.spinner("AIが素材・タグ仕様・縫製を多面的に解析中..."):
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-1.5-flash")

                prompt = f"""
                あなたはテキスタイル科学と感覚過敏（触覚過敏）の専門家です。
                提供された衣服のタグ・縫製画像を解析し、以下の4大評価軸に基づいて数値を抽出・判定してください。

                【評価軸スコア基準 (0〜4点)】
                1. タグ仕様 (S_T): 0(タグレス)〜4(角の硬いナイロンタグ)
                2. 縫製仕様 (S_S): 0(シームレス)〜4(硬いロックミシン)
                3. 繊維組成 (S_F): 0(綿100%)〜4(ウール/麻/アクリル)

                【現在のユーザー設定】
                - 部位重み (W_Z): {w_z}
                - タグ過敏バイアス: {p_tag}, 縫製過敏バイアス: {p_seam}, 繊維過敏バイアス: {p_fiber}

                【計算モデル】
                総合不快度 = W_Z * ((0.45 * S_T * {p_tag}) + (0.35 * S_S * {p_seam}) + (0.20 * S_F * {p_fiber}))
                ※0〜100点スケールに換算。

                【出力フォーマット】
                ■ 総合不快度スコア: [〇点 / 100点]
                ■ 判定ランク: [🟢 セーフ (0〜20点) / 🟡 軽度注意 (21〜50点) / 🟠 要警戒 (51〜75点) / 🔴 高トリガー (76〜100点)]
                ■ 読み取り内訳:
                  - 繊維組成: [素材%と評価点]
                  - タグ仕様: [種類と評価点]
                  - 縫製仕様: [縫い目と評価点]
                ■ リスク要因とアドバイス: [簡潔な解説と対策]
                """

                response = model.generate_content([prompt, image])
                st.success("解析が完了しました！")
                st.markdown(response.text)

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
elif not api_key:
    st.info("👈 左側のサイドバーに先ほどコピーした Gemini API Key を貼り付けてください。")
