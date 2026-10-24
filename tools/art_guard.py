"""臨時圖保護（AI／腳本畫的貼圖共用）。
腳本每次寫入 src/main/resources 底下的貼圖時，把內容的 sha1 記在 tools/ai_texture_hashes.json。
下次重跑時，檔案若已存在且內容和紀錄不同（＝使用者用同檔名覆蓋了自己畫的圖），就不再覆蓋，只印出提示。
沒有紀錄的既有檔案也視為使用者的圖，不覆蓋；要強制重畫請先刪掉那個檔案。

用法（腳本在 tools/<子資料夾>/ 底下）：
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import art_guard
    art_guard.save(img, path)        # 取代 img.save(path)
"""
import hashlib, json
from pathlib import Path

P = Path(__file__).resolve().parents[1]
RES = P / "src/main/resources"
STATE = P / "tools/ai_texture_hashes.json"


def _load():
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}


def sha1(path):
    return hashlib.sha1(Path(path).read_bytes()).hexdigest()


def key(path):
    return Path(path).resolve().relative_to(P).as_posix()


def is_ours(path):
    """檔案不存在，或內容仍是腳本上次寫的臨時圖。"""
    path = Path(path)
    return not path.exists() or _load().get(key(path)) == sha1(path)


def save(img, path):
    """寫入貼圖；使用者重畫過的檔案保持原樣。回傳是否有寫入。"""
    path = Path(path)
    if RES not in path.resolve().parents:            # build/ 底下的預覽、暫存檔：直接寫
        img.save(path)
        return True
    if not is_ours(path):
        print(f"  keep (hand-drawn): {key(path)}")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    record(path)
    return True


def record(*paths):
    """把目前的檔案內容登記成臨時圖（之後可被腳本覆蓋）。"""
    state = _load()
    for p in paths:
        state[key(p)] = sha1(p)
    STATE.write_text(json.dumps(dict(sorted(state.items())), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
