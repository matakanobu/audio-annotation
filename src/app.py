from dataclasses import dataclass
from enum import Enum
import streamlit as st
from streamlit.logger import get_logger
import json

logger = get_logger(__name__)


class Status(str, Enum):
    INCOMPLETE = "incomplete"
    COMPLETE = "complete"


class FilterStatus(str, Enum):
    ALL = "all"
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
        entry["status"] = Status(entry["status"])  # Convert string to Status Enum
        data.append(Record(**entry))
    return data


# JSONLデータを書き込む関数
def save_data(jsonl_file_path, data):
    with open(jsonl_file_path, "w", encoding="utf-8") as f:
        for entry in data:
            entry_dict = entry.__dict__.copy()
            entry_dict["status"] = entry_dict[
                "status"
            ].value  # Convert Status Enum to string
            f.write(json.dumps(entry_dict, ensure_ascii=False) + "\n")


def filter_data_by_status(data: list[Record], status: FilterStatus) -> list[Record]:
    if status == FilterStatus.ALL:
        return data
    else:
        return [item for item in data if item.status == Status(status.value)]


st.title("Audio Transcription Tool")

if "data" not in st.session_state:
    st.session_state.data = None

# JSONLファイルのアップロード
uploaded_file = st.file_uploader("Upload JSONL file", type="jsonl")

if uploaded_file is not None:
    # データの読み込み
    if st.session_state.data is None:
        st.session_state.data = load_data(uploaded_file)
        logger.info(f"Loaded {len(st.session_state.data)} records")

    # 全体の件数と"complete"の件数を表示
    total_count_placeholder = st.empty()
    complete_count_placeholder = st.empty()
    total_count_placeholder.write(f"Total records: {len(st.session_state.data)}")
    complete_count_placeholder.write(
        f"Complete records: {sum(1 for item in st.session_state.data if item.status == Status.COMPLETE)}"
    )

    # ステータスでフィルタ
    status_filter = st.selectbox("Filter by status", [item for item in FilterStatus])

    filtered_data = filter_data_by_status(
        st.session_state.data, FilterStatus(status_filter)
    )
    logger.info(f"Filtered {len(filtered_data)} records")

    # 現在のインデックスを保持する変数
    if "current_index" not in st.session_state:
        st.session_state.current_index = 0

    # 前後のデータに移動するボタン
    if st.button("Previous") and st.session_state.current_index > 0:
        logger.info("Previous button clicked")
        st.session_state.current_index -= 1

    if st.button("Next") and st.session_state.current_index < len(filtered_data) - 1:
        logger.info("Next button clicked")
        st.session_state.current_index += 1

    audio_placeholder = st.empty()
    text_area_placeholder = st.empty()

    if len(filtered_data) > 0:
        audio_placeholder.audio(filtered_data[st.session_state.current_index].wav)
        new_text = text_area_placeholder.text_area(
            "Text", value=filtered_data[st.session_state.current_index].txt
        )

    # テキストの更新
    if st.button("Update Text"):
        filtered_data[st.session_state.current_index].txt = new_text
        filtered_data[st.session_state.current_index].status = Status.COMPLETE

        # 全体のデータを更新
        st.session_state.data[
            filtered_data.index(filtered_data[st.session_state.current_index])
        ] = filtered_data[st.session_state.current_index]

        save_data(uploaded_file.name, st.session_state.data)  # 更新されたデータを保存

        # 全体の件数と"complete"の件数を再計算して表示
        total_count = len(st.session_state.data)
        complete_count = sum(
            1 for item in st.session_state.data if item.status == Status.COMPLETE
        )
        total_count_placeholder.write(f"Total records: {total_count}")
        complete_count_placeholder.write(f"Complete records: {complete_count}")

        # filtered_dataを更新
        filtered_data = filter_data_by_status(
            st.session_state.data, FilterStatus(status_filter)
        )

        if len(filtered_data) > 0:
            st.session_state.current_index = 0
            audio_placeholder.audio(filtered_data[st.session_state.current_index].wav)
            new_text = text_area_placeholder.text_area(
                "Text", value=filtered_data[st.session_state.current_index].txt
            )
        else:
            audio_placeholder.empty()
            text_area_placeholder.empty()

        st.success("Text updated and file saved!")


else:
    st.write("Please upload a JSONL file.")
