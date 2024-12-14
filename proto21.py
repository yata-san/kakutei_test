import streamlit as st
import pandas as pd
import datetime
import os
import json
import urllib.parse
import requests
from dotenv import load_dotenv
import googlemaps

# Initialize app and session state if necessary
if 'responses' not in st.session_state:
    st.session_state['responses'] = []
if 'final_schedule' not in st.session_state:
    st.session_state['final_schedule'] = None
if 'response_files' not in st.session_state:
    st.session_state['response_files'] = []
if 'participant_link' not in st.session_state:
    st.session_state['participant_link'] = None
if 'dates' not in st.session_state:
    st.session_state['dates'] = []

st.title("🎉 飲み会日程調整アプリ 🍻")

# Get query parameters
query_params = st.query_params
page = query_params.get("page", ["admin"])[0]

# クエリパラメータから日程を取得
dates_param = st.query_params.get("dates", [None])[0]
if dates_param:
    try:
        st.write("Raw dates_param:", dates_param)  # デバッグ用

        # 空でない場合にデコードと解析を試みる
        if dates_param.strip():
            decoded_param = urllib.parse.unquote(dates_param)
            st.write("Decoded dates_param:", decoded_param)  # デバッグ用

            # デコード後の値が有効なJSONかチェック
            if decoded_param and decoded_param != "null":
                st.session_state['dates'] = json.loads(decoded_param)
                st.write("Parsed dates:", st.session_state['dates'])  # デバッグ用
            else:
                # JSONが無効な場合
                st.error("日程情報が無効です。幹事に連絡してください。")
                st.session_state['dates'] = []
        else:
            st.error("日程情報が空です。幹事に連絡してください。")
            st.session_state['dates'] = []

    except (json.JSONDecodeError, TypeError, UnicodeDecodeError) as e:
        # JSON解析に失敗した場合のエラーハンドリング
        st.error(f"日程の解析に失敗しました。幹事に連絡してください。エラー: {e}")
        st.write("Error details:", str(e))  # デバッグ用
        st.session_state['dates'] = []

if page == "admin":
    st.header("幹事ページ")

    # 1. 日程範囲を選択
    date_range = st.date_input(
        "飲み会の日程範囲を選択してください",
        [datetime.date.today(), datetime.date.today() + datetime.timedelta(days=7)],
        min_value=datetime.date.today(),
    )

    # 2. 回答期限を設定
    deadline = st.date_input(
        "回答期限を設定してください", datetime.date.today() + datetime.timedelta(days=3)
    )

    # 3. コメントを入力
    comment = st.text_area("参加者へのコメント")

    # 4. 登録ボタンを押すとリンク生成
    if st.button("リンクを発行"):
        unique_id = str(datetime.datetime.now().timestamp()).replace(".", "")
        st.session_state['dates'] = [str(date_range[0] + datetime.timedelta(days=i)) for i in range((date_range[1] - date_range[0]).days + 1)]
        dates_json = json.dumps(st.session_state['dates'])
        encoded_dates = urllib.parse.quote(dates_json)
        participant_link = f"?page=participant&id={unique_id}&dates={encoded_dates}"
        st.session_state['participant_link'] = participant_link

        # 絶対URLの生成
        base_url = f"http://{st.get_option('server.address')}:{st.get_option('server.port')}"
        participant_link = f"{base_url}/?page=participant&id={unique_id}&dates={encoded_dates}"

        st.session_state['participant_link'] = participant_link

        # 参加者用リンクの表示
        st.markdown(f"### 参加者用リンクをコピーして共有してください：")
        st.markdown(f"[参加者ページリンク]({participant_link})")
        st.success("参加者用リンクが生成されました！")

    # 確定した日程を表示
    if st.session_state['final_schedule']:
        st.markdown("### 確定した日程")
        st.markdown(f"<h3 style='color: green;'>🌟 最適日程: {st.session_state['final_schedule']['最適日程']} 🌟</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: blue;'>スコア: {st.session_state['final_schedule']['スコア']} 点</p>", unsafe_allow_html=True)
        st.balloons()

    # 案内メールの定型文生成
        st.markdown("### 案内メール定型文")
        default_email = (
            f"件名: ［確定］飲み会日程のお知らせ\n\n"
            f"皆様\n\n"
            f"お応えいただき、感謝します！\n"
            f"AIによるスコア計算の結果，下記の日程に決定！\n\n"
            f"［最適日程］\n"
            f"{st.session_state['final_schedule']['最適日程']}\n\n"
            f"ぜひご参加！\n\n"
            f"幹事より"
        )
        email_text = st.text_area("案内メール文を編集", value=default_email, height=200)
        if st.button("メール定型文をコピー"):
            st.write("メール定型文をコピー！")

    elif page == "participant":
        st.header("参加者ページ")

elif page == "participant":
    st.header("参加者ページ")
    # クエリパラメータから日程を取得
    dates_param = st.query_params.get("dates", [None])[0]
    if dates_param:
        try:
            st.write("Raw dates_param:", dates_param)  # デバッグ用

            if dates_param.strip():
                decoded_param = urllib.parse.unquote(dates_param)
                st.write("Decoded dates_param:", decoded_param)  # デバッグ用

                st.session_state['dates'] = json.loads(decoded_param.encode('utf-8').decode('utf-8'))
                st.write("Parsed dates:", st.session_state['dates'])  # デバッグ用
            else:
                st.error("日程情報が空です。幹事に連絡してください。")
                st.session_state['dates'] = []
        except (json.JSONDecodeError, TypeError, UnicodeDecodeError) as e:
            st.error(f"日程の解析に失敗しました。幹事に連絡してください。エラー: {e}")
            st.write("Error details:", str(e))  # デバッグ用
            st.session_state['dates'] = []

    # 1. 役職を選択
    role = st.selectbox(
        "あなたの役職を選択",
        ["一般", "リーダークラス", "部長クラス", "本部長クラス", "社長クラス"],
    )

     #2. ジャンルを選択
    genre_code_list = {
    "和食":"G004",
    "洋食" : "G005",
    "イタリアン・フレンチ" : "G006",
    "中華" : "G007",
    "焼肉" : "G008",
    "韓国料理" : "G017",
    "アジア・エスニック料理" : "G009",
    }

    st.write("行きたいお店のジャンルを選んでください")
    selected_genre = st.selectbox(
        f"ジャンルを選択 ", 
        genre_code_list,  
        key=f"genre"  
            )

    # 3. 日程ごとに希望を回答
    st.write("日程ごとに以下の希望をチェック！")
    options = ["絶対行ける", "たぶん行ける", "未定", "たぶん行けない", "絶対行けない"]

    date_responses = {}
    if st.session_state['dates']:
        for date in st.session_state['dates']:
            st.write(f"**{date}**")
            choice = st.radio(f"選択肢 ({date})", options, key=f"{date}_response")
            date_responses[str(date)] = choice
    else:
        st.error("日程が設定されていません！幹事に連絡！")

    # 4. 回答完了ボタン
    if st.button("回答を送信"):
        if date_responses:
            response = {
                "役職": role,
                **date_responses,
                "ジャンル":selected_genre
            }
            # 保存先ディレクトリ
            responses_dir = "responses"
            if not os.path.exists(responses_dir):
                os.makedirs(responses_dir)

            filename = os.path.join(responses_dir, f"response_{datetime.datetime.now().timestamp()}.csv")
            pd.DataFrame([response]).to_csv(filename, index=False)
            st.success("回答が送信！")
        else:
            st.error("日程が選択！回答送信不可！")

# 回答期限後にCSVを連結して最適日程計算
if page == "admin" and st.button("最適日程計算"):
    # 役職に対応する重み付け
    weights = {
        "一般": 1,
        "リーダークラス": 2,
        "部長クラス": 3,
        "本部長クラス": 4,
        "社長クラス": 5
    }

    # CSVファイル連結
    all_responses = pd.DataFrame()
    responses_dir = "responses"
    if os.path.exists(responses_dir):
        files = os.listdir(responses_dir)
        for file in files:
            file_path = os.path.join(responses_dir, file)
            all_responses = pd.concat([all_responses, pd.read_csv(file_path)], ignore_index=True)

    # 日程スコア計算
    scores = {date: 0 for date in st.session_state['dates']}
    for _, response in all_responses.iterrows():
        role_weight = weights[response["役職"]]
        selected_genre = response["ジャンル"] 
        for date in st.session_state['dates']:
            if str(date) in response:
                choice = response[str(date)]
                if response["役職"] in ["本部長クラス", "社長クラス"] and choice == "絶対行ける":
                    scores[date] += 2 * role_weight
                elif response["役職"] == "部長クラス" and choice in ["絶対行ける", "たぶん行ける"]:
                    scores[date] += 1 * role_weight
                elif response["役職"] not in ["本部長クラス", "社長クラス", "部長クラス"]:
                    if choice == "絶対行ける":
                        scores[date] += 2 * role_weight
                    elif choice == "たぶん行ける":
                        scores[date] += 1 * role_weight

                # ジャンルのスコアを更新
                if selected_genre not in genre_scores[date]:
                    genre_scores[date][selected_genre] = 0
                if choice in ["絶対行ける", "たぶん行ける"]:
                    genre_scores[date][selected_genre] += 1 * role_weight

    # 最適日程とジャンルの計算
    best_date = max(scores, key=scores.get)
    best_genre = max(genre_scores[best_date], key=genre_scores[best_date].get)
    st.session_state['final_schedule'] = {"最適日程": best_date, "スコア": scores[best_date], "ジャンル":best_genre}

    st.markdown(f"<h2 style='color: red;'>🎉 最適な飲み会の日程が確定！ 🎉</h2>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='color: green;'>🌟 最適日程: {best_date} 🌟</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: blue;'>スコア: {scores[best_date]} 点</p>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='color: green;'>🌟 ジャンル: {best_genre} 🌟</h3>", unsafe_allow_html=True)
    st.balloons()

#開催地、予算の設定

if page == "admin" :
# 1. 開催地を選択
    place = st.text_input("開催地を入れてください", placeholder="place", max_chars=10)
    st.session_state['place'] = place
    if st.session_state.get("is_admin", False) and st.button("経度緯度を算出"):
        load_dotenv()
        API_KEY_G = os.getenv("API_KEY_G")
        gmaps = googlemaps.Client(key=API_KEY_G)

        geocode_result = gmaps.geocode(place)

        if geocode_result:
            latlng = geocode_result[0]['geometry']['location']
            address = geocode_result[0]['formatted_address']
            lat = latlng['lat']
            lng = latlng['lng']

        st.session_state['lat'] = lat
        st.session_state['lng'] = lng 
    
    #検索範囲の選択
    range_code_list = {
        "300m":"1",
        "500m" : "2",
        "1000m" : "3",
        "2000m" : "4",
        "3000m" : "5"
        }

    selected_range = st.selectbox(
        f"検索範囲を選択してください ",  # ラベル
        range_code_list,  # ジャンルのリスト
        key=f"range"  # 一意のキー
        )
    st.session_state['selected_range'] = selected_range 

# 2. 予算を選択
    budget_code_list = {
        "3001～4000円":"B003",
        "4001～5000円" : "B008",
        "5001～7000円" : "B004",
        "7001～10000円" : "B005",
        "10001～15000円" : "B006",
        "15001～20000円" : "B012",
        "20001～30000円" : "B013",
        }

    selected_budget = st.selectbox(
        f"予算を選択してください ",  # ラベル
        budget_code_list,  # ジャンルのリスト
        key=f"budget"  # 一意のキー
        )
    st.session_state['selected_budget'] = selected_budget 

#お店を選ぶ
if page == "admin" and st.button("お店リストを出す"):
    # ジャンルがsession_stateに存在することを確認
    if 'final_schedule' not in st.session_state or 'ジャンル' not in st.session_state['final_schedule']:
        st.error("最適日程が計算されていません。最適日程を計算してからお店を選んでください。")
    else:
        best_genre = st.session_state['final_schedule']['ジャンル']
        st.write(f"予算: {selected_budget}")
        
        genre_code_list = {
            "和食":"G004",
            "洋食" : "G005",
            "イタリアン・フレンチ" : "G006",
            "中華" : "G007",
            "焼肉" : "G008",
            "韓国料理" : "G017",
            "アジア・エスニック料理" : "G009",
            }

        if best_genre in genre_code_list:
            best_genre_code = genre_code_list[best_genre]

        budget_code_list = {
            "3001～4000円":"B003",
            "4001～5000円" : "B008",
            "5001～7000円" : "B004",
            "7001～10000円" : "B005",
            "10001～15000円" : "B006",
            "15001～20000円" : "B012",
            "20001～30000円" : "B013",
            }

        if selected_budget in budget_code_list:
            selected_budget_code = budget_code_list[selected_budget]

        range_code_list = {
            "300m":"1",
            "500m" : "2",
            "1000m" : "3",
            "2000m" : "4",
            "3000m" : "5"
            }

        if selected_range in range_code_list:
            selected_range_code = range_code_list[selected_range]


        REQUEST_URL = "http://webservice.recruit.co.jp/hotpepper/gourmet/v1/"

        load_dotenv()
        API_KEY = os.getenv("API_KEY")

        #lat:緯度、lng:経度、ソート（おすすめ順）、数
        params = {
            "format": "json",
            "lat":st.session_state['lat'],
            "lng":st.session_state['lng'],
            "range":selected_range_code,
            "genre": best_genre_code,
            "budget": selected_budget_code,
            "count":15,
            "order":4,
            "key": API_KEY
            }

        res = requests.get(REQUEST_URL, params)
        result = res.json()

        df = pd.DataFrame()

        for i in range(0, len(result["results"]["shop"])):

           info = result["results"]["shop"][i]

           if "urls" in info and isinstance(info["urls"], dict):
                info.update(info["urls"])  
                del info["urls"]     

           temp_df = pd.DataFrame(info, index=[i])

           df = pd.concat([df, temp_df], ignore_index=True)
        
        df["url"] = df["pc"].apply(lambda x: f"[リンクはこちら]({x})")

        st.write(df[["name", "catch", "access", "pc"]])

