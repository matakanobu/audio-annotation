from dataclasses import dataclass
from enum import Enum
import streamlit as st
import json


class Status(Enum):
    INCOMPLETE = "incomplete"
    COMPLETE = "complete"


@dataclass
class Record:
    wav: str
    txt: str
    status: Status
    invalid_audio: bool


# JSONLデータを読み込む関数
def load_data(jsonl_file):
    data: list[Record] = []
    for line in jsonl_file:
        entry = json.loads(line)
        entry['status'] = Status(entry['status'])  # Convert string to Status Enum
        data.append(Record(**entry))
    return data


# JSONLデータを書き込む関数
def save_data(jsonl_file_path, data):
    with open(jsonl_file_path, 'w', encoding='utf-8') as f:
        for entry in data:
            entry_dict = entry.__dict__.copy()
            entry_dict['status'] = entry_dict['status'].value  # Convert Status Enum to string
            f.write(json.dumps(entry_dict, ensure_ascii=False) + "\n")


st.title("Audio Transcription Tool")

# JSONLファイルのアップロード
uploaded_file = st.file_uploader("Upload JSONL file", type="jsonl")

if uploaded_file is not None:
    # データの読み込み
    data = load_data(uploaded_file)

    # 全体の件数と"complete"の件数を表示
    total_count = len(data)
    complete_count = sum(1 for item in data if item.status == Status.COMPLETE)
    total_count_placeholder = st.empty()
    complete_count_placeholder = st.empty()
    total_count_placeholder.write(f"Total records: {total_count}")
    complete_count_placeholder.write(f"Complete records: {complete_count}")

    # ステータスでフィルタ
    status_filter = st.selectbox("Filter by status", ["all", Status.INCOMPLETE.value, Status.COMPLETE.value])

    if status_filter != "all":
        filtered_data = [item for item in data if item.status.value == status_filter]
    else:
        filtered_data = data

    # データの一覧を表示
    st.write("Select an audio file from the list:")
    options = [f"{i}: {item.txt}" for i, item in enumerate(filtered_data)]
    index = st.selectbox("Index", [None] + list(range(len(filtered_data))),
                         format_func=lambda x: "Select an option" if x is None else options[x])

    # 選択された音声ファイルとテキストのみを表示および編集
    if index is not None:
        # 音声の再生, 倍速再生, テキストの編集
        audio_path = filtered_data[index].wav
        text = filtered_data[index].txt

        st.audio(audio_path)
        new_text = st.text_area("Text", value=text)

        # テキストの更新
        if st.button("Update Text"):
            filtered_data[index].txt = new_text
            filtered_data[index].status = Status.COMPLETE

            # 全体のデータを更新
            data[filtered_data.index(filtered_data[index])] = filtered_data[index]

            save_data(uploaded_file.name, data)  # 更新されたデータを保存

            # 全体の件数と"complete"の件数を再計算して表示
            total_count = len(data)
            complete_count = sum(1 for item in data if item.status == Status.COMPLETE)
            total_count_placeholder.write(f"Total records: {total_count}")
            complete_count_placeholder.write(f"Complete records: {complete_count}")

            st.success("Text updated and file saved!")

else:
    st.write("Please upload a JSONL file.")