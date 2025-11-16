# 📋 MLX-LM Session Management Design v0.2.8

**Version:** 0.2.8
**Feature:** Session History & Resume
**Status:** Design Phase
**Date:** 2025-01-16

---

## 🎯 概要

セッション履歴の保存・復元機能を実装し、ユーザーが過去の会話を再開できるようにする。

### 主要機能
- セッションの自動保存（終了時・5分ごと）
- 過去のセッション復元 (`/resume`)
- 手動保存 (`/save`)
- セッション管理 (`/session`)
- セッションの名前変更・削除

---

## 🗂️ データ構造

### セッションデータ（JSON形式）

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-01-15T14:30:00",
  "updated_at": "2025-01-15T15:45:00",
  "session_name": "",
  "model_name": "mlx-community/Qwen2.5-7B-Instruct-4bit",
  "settings": {
    "max_tokens": 2048,
    "stream_mode": "all",
    "chat_mode": "auto",
    "history_mode": "on",
    "time_limit": 0,
    "reasoning": null
  },
  "history": [
    ["user message 1", "assistant response 1"],
    ["user message 2", "assistant response 2"]
  ],
  "message_count": 2,
  "archived": false
}
```

### フィールド説明

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `session_id` | string | UUID形式のセッション識別子 |
| `created_at` | string | セッション作成日時（ISO 8601形式） |
| `updated_at` | string | 最終更新日時（ISO 8601形式） |
| `session_name` | string | セッション名（デフォルトは空文字列） |
| `model_name` | string | 使用モデル名 |
| `settings` | object | セッション設定 |
| `history` | array | 会話履歴（[user, assistant]のタプル配列） |
| `message_count` | number | 会話数 |
| `archived` | boolean | アーカイブ状態（Phase 4で使用） |

---

## 📁 ディレクトリ構造

```
mlxlm_data/
├── config.json                    # 既存：ユーザー設定
├── history.json                   # 既存：プロンプト履歴
└── sessions/                      # 新規：セッション保存フォルダ
    ├── active_session.json        # 現在のアクティブセッション
    ├── 550e8400-e29b-41d4-a716-446655440000.json
    ├── 660f9511-f30c-52e5-b827-557766551111.json
    └── ...
```

### ファイル管理方針

- **active_session.json**: 現在進行中のセッション（常に上書き）
- **{session_id}.json**: 保存済みセッション（終了時・手動保存時に作成）
- セッション数は無制限（将来的に設定で制限可能）

---

## 🎮 コマンド仕様

### 1. `/resume` - セッション復元（クイックアクセス）

**説明:**
過去のセッション一覧を表示し、選択したセッションを復元する。`/session`メニューをスキップする直接アクセスコマンド。

**UI例:**
```
📂 Saved Sessions (10 sessions found)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 1. 2 hours ago | 5 messages
    [No name] "Explain async/await in Python..."

 2. Yesterday 10:22 | 12 messages | "Debugging Session"
    "Why is my API call failing? I'm getting..."

 3. 2 days ago | 8 messages | "React Hooks研究"
    "useEffectとuseLayoutEffectの違いを教えて..."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 0. Cancel

Select session (0-3) or use ↑↓ + Enter: _
```

**表示内容（1セッション2行）:**
- **1行目**: 番号、相対時間、メッセージ数、セッション名（あれば）
- **2行目**: 冒頭の会話（60文字でトリミング）

**選択方法:**
- 数字入力 + Enter
- 矢印キー（↑↓）+ Enter（prompt-toolkit使用）

**動作フロー:**
1. セッション一覧を`updated_at`降順で取得
2. 一覧表示（相対時間形式）
3. ユーザーが選択
4. **現在のセッションを自動保存**
5. 選択したセッションを復元
6. `history`, `settings`, `session_id`, `session_name`を置き換え
7. 成功メッセージ表示

**成功メッセージ:**
```
💾 Current session saved
📂 Loading session...
✅ Session restored: "Debugging Session" (12 messages)
```

---

### 2. `/save` - 手動保存

**説明:**
現在のセッションを即座に保存する。

**UI例:**
```
💾 Session saved: 550e8400-e29b-41d4-a716-446655440000
   5 messages, last updated: 2025-01-15 15:45
```

**動作:**
- `active_session.json`を読み込み
- `{session_id}.json`として保存
- `updated_at`を現在時刻に更新
- クラッシュ対策・手動バックアップ用

---

### 3. `/session` - セッション管理メニュー

**説明:**
セッション関連の全機能にアクセスできる総合メニュー。

**UI例:**
```
📊 Session Management
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Sessions:     47 sessions
Storage Used:       12.4 MB
Oldest Session:     2024-12-15 (32 days ago)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 1. Resume Session
 2. Rename Current Session
 3. Delete Sessions
 4. Auto-save Settings
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 0. Back

Select option (0-4): _
```

#### **サブメニュー詳細**

##### **1. Resume Session**
- `/resume`と同じUI・動作
- セッション一覧 → 選択 → 復元

##### **2. Rename Current Session**
```
Current session name: [No name]
Enter new name (or leave blank): Debugging Session_
✅ Session renamed to "Debugging Session"
```

**仕様:**
- 既存の名前を表示（空なら`[No name]`）
- 入力欄は空白でスタート（`default=""`）
- 空白で確定 → 名前をクリア
- 文字列入力 → その名前に変更

##### **3. Delete Sessions**
```
📂 Select Sessions to Delete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 [ ] 1. 2 hours ago | 5 messages
 [x] 2. Yesterday 10:22 | 12 messages | "Debugging Session"
 [ ] 3. 2 days ago | 8 messages

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Space: Toggle  |  Enter: Confirm  |  0: Cancel

Delete 1 session? (y/n): y_
🗑️  Deleted 1 session
```

**仕様:**
- チェックボックス式（複数選択可能）
- スペースキーでトグル
- Enterで確定 → 確認プロンプト
- 削除後、ファイルを物理削除

##### **4. Auto-save Settings**
```
⚙️  Auto-save Settings
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current: Enabled (every 5 minutes)

 1. Enable (5 minutes interval)
 2. Enable (10 minutes interval)
 3. Disable
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 0. Back

Select option (0-3): _
```

**仕様:**
- 5分 / 10分 / 無効から選択
- `config.json`の`sessions.auto_save_interval`を更新
- 変更は即座に反映

---

## ⏱️ 自動保存の仕組み

### 保存タイミング

| タイミング | 説明 | 実装場所 |
|-----------|------|---------|
| プログラム終了時 | `/exit`, `/quit`, `/bye`実行時 | `run.py` |
| Ctrl+D | EOFError捕捉時 | `run.py` |
| 5分ごと | 自動保存タイマー | `run.py`のメインループ |
| 手動保存 | `/save`実行時 | `run_save.py` |
| セッション移動時 | `/resume`でセッション切り替え前 | `run_resume.py` |

### 実装方法

**run.pyのメインループ内:**
```python
import time

# セッションIDを起動時に生成
session_id = create_session_id()
session_name = ""
last_auto_save = time.time()
auto_save_interval = 300  # 5分 = 300秒（設定から読み込み）

while True:
    # 5分ごとに自動保存チェック
    if time.time() - last_auto_save >= auto_save_interval:
        session_data = build_session_data(
            history, model_name, settings, session_id, session_name
        )
        save_session(session_data)
        last_auto_save = time.time()
        # 静かに保存（ユーザーに通知しない）

    # 通常の入力処理
    user_input = session.prompt(...)

    # /exit, /quit, /bye 時
    if user_input.lower() in ['/exit', '/quit', '/bye']:
        session_data = build_session_data(...)
        save_session(session_data)
        print("💾 Session saved")
        break
```

**Ctrl+D対応:**
```python
except EOFError:  # Ctrl+D
    session_data = build_session_data(...)
    save_session(session_data)
    print("\n💾 Session saved")
    print("👋 Goodbye!")
    break
```

---

## 🎨 UI/UX詳細

### 相対時間表示

**実装:**
```python
from datetime import datetime, timedelta

def format_relative_time(timestamp_str: str) -> str:
    """
    ISO 8601タイムスタンプを相対時間に変換

    例:
    - "2025-01-15T14:30:00" → "2 hours ago"
    - "2025-01-14T10:00:00" → "Yesterday 10:00"
    """
    timestamp = datetime.fromisoformat(timestamp_str)
    now = datetime.now()
    delta = now - timestamp

    if delta < timedelta(minutes=1):
        return "just now"
    elif delta < timedelta(hours=1):
        minutes = int(delta.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif delta < timedelta(days=1):
        hours = int(delta.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif delta.days == 1:
        return f"Yesterday {timestamp.strftime('%H:%M')}"
    elif delta < timedelta(days=7):
        days = delta.days
        return f"{days} day{'s' if days > 1 else ''} ago"
    else:
        # 1週間以上前は日付表示
        return timestamp.strftime("%Y-%m-%d %H:%M")
```

**表示例:**
```
just now
5 minutes ago
2 hours ago
Yesterday 14:30
3 days ago
2025-01-08 10:00
```

### セッション一覧フォーマット

**実装:**
```python
def format_session_preview(session: dict, index: int) -> str:
    """
    1セッションを2行で整形

    例:
     1. 2 hours ago | 5 messages
        [No name] "Explain async/await in Python..."
    """
    # 1行目
    time_str = format_relative_time(session['updated_at'])
    msg_count = session['message_count']
    name = f' | "{session["session_name"]}"' if session['session_name'] else ''
    line1 = f" {index}. {time_str} | {msg_count} message{'s' if msg_count != 1 else ''}{name}"

    # 2行目（冒頭の会話）
    if session['history']:
        first_message = session['history'][0][0]
        name_prefix = f'[No name] ' if not session['session_name'] else ''
        preview = first_message[:60] + "..." if len(first_message) > 60 else first_message
        line2 = f'    {name_prefix}"{preview}"'
    else:
        line2 = '    (Empty session)'

    return f"{line1}\n{line2}"
```

### セッション選択UI

**prompt-toolkit使用:**
```python
from prompt_toolkit.shortcuts import radiolist_dialog
from prompt_toolkit.styles import Style

def select_session_ui(sessions: list[dict]) -> dict | None:
    """
    セッション選択ダイアログ

    Returns:
        選択されたセッション or None（キャンセル時）
    """
    # 選択肢を作成
    choices = [
        (session, format_session_preview(session, i+1))
        for i, session in enumerate(sessions)
    ]

    # ダイアログ表示
    result = radiolist_dialog(
        title="📂 Saved Sessions",
        text=f"{len(sessions)} session{'s' if len(sessions) != 1 else ''} found\n"
             "Use ↑↓ to navigate, Enter to select, or type number + Enter",
        values=choices,
    ).run()

    return result  # 選択されたsession dict or None
```

### ストレージ情報表示

**実装:**
```python
import os

def get_session_storage_info() -> dict:
    """
    セッション保存フォルダの情報を取得

    Returns:
        {
            'total_sessions': int,
            'storage_mb': float,
            'oldest_date': str
        }
    """
    session_dir = get_mlxlm_data_dir() / "sessions"

    if not session_dir.exists():
        return {'total_sessions': 0, 'storage_mb': 0.0, 'oldest_date': 'N/A'}

    # セッションファイルを取得（active_session.jsonを除く）
    session_files = [
        f for f in session_dir.glob("*.json")
        if f.name != "active_session.json"
    ]

    # 合計サイズを計算
    total_bytes = sum(f.stat().st_size for f in session_files)
    storage_mb = total_bytes / (1024 * 1024)

    # 最古のセッション日時を取得
    oldest_date = "N/A"
    if session_files:
        oldest_session = min(
            session_files,
            key=lambda f: json.loads(f.read_text()).get('created_at', '')
        )
        data = json.loads(oldest_session.read_text())
        oldest_date = format_relative_time(data['created_at'])

    return {
        'total_sessions': len(session_files),
        'storage_mb': round(storage_mb, 1),
        'oldest_date': oldest_date
    }
```

---

## 🔧 実装ファイル構成

```
commands/
├── run.py                    # メインループ（自動保存タイマー追加）
├── run_resume.py             # 新規：/resume処理
├── run_save.py               # 新規：/save処理
├── run_session.py            # 新規：/session メニュー
├── run_utils.py              # 既存
└── settings/
    └── ...

core.py
└── session_utils.py          # 新規：セッションデータの読み書き
```

### 新規ファイルの役割

#### **`core/session_utils.py`** (推定: 150-200行)

**関数一覧:**
```python
def create_session_id() -> str:
    """UUIDでセッションID生成"""
    import uuid
    return str(uuid.uuid4())

def get_sessions_dir() -> Path:
    """セッション保存ディレクトリを取得（存在しなければ作成）"""
    session_dir = get_mlxlm_data_dir() / "sessions"
    session_dir.mkdir(exist_ok=True)
    return session_dir

def build_session_data(
    history: list[tuple[str, str]],
    model_name: str,
    settings: dict,
    session_id: str,
    session_name: str,
    created_at: str | None = None
) -> dict:
    """セッションデータを構築"""
    from datetime import datetime

    now = datetime.now().isoformat()

    return {
        "session_id": session_id,
        "created_at": created_at or now,
        "updated_at": now,
        "session_name": session_name,
        "model_name": model_name,
        "settings": settings,
        "history": history,
        "message_count": len(history),
        "archived": False
    }

def save_session(session_data: dict) -> None:
    """セッションをJSONファイルに保存"""
    session_dir = get_sessions_dir()
    session_id = session_data['session_id']
    filepath = session_dir / f"{session_id}.json"

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)

def load_session(session_id: str) -> dict:
    """セッションIDから復元"""
    session_dir = get_sessions_dir()
    filepath = session_dir / f"{session_id}.json"

    if not filepath.exists():
        raise FileNotFoundError(f"Session not found: {session_id}")

    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def list_sessions(include_archived: bool = False) -> list[dict]:
    """
    全セッションをリスト（updated_at降順）

    Args:
        include_archived: アーカイブ済みセッションも含めるか
    """
    session_dir = get_sessions_dir()

    sessions = []
    for filepath in session_dir.glob("*.json"):
        if filepath.name == "active_session.json":
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            session = json.load(f)

        # アーカイブフィルタ
        if not include_archived and session.get('archived', False):
            continue

        sessions.append(session)

    # updated_at降順でソート
    sessions.sort(key=lambda s: s['updated_at'], reverse=True)

    return sessions

def delete_session(session_id: str) -> None:
    """セッション削除"""
    session_dir = get_sessions_dir()
    filepath = session_dir / f"{session_id}.json"

    if filepath.exists():
        filepath.unlink()

def update_session_name(session_id: str, name: str) -> None:
    """セッション名を更新"""
    session = load_session(session_id)
    session['session_name'] = name
    session['updated_at'] = datetime.now().isoformat()
    save_session(session)

def get_session_storage_info() -> dict:
    """ストレージ情報を取得"""
    # 実装は上記UI/UX詳細セクションを参照
    pass

def format_relative_time(timestamp_str: str) -> str:
    """相対時間表示"""
    # 実装は上記UI/UX詳細セクションを参照
    pass
```

---

#### **`commands/run_resume.py`** (推定: 140-190行)

**関数一覧:**
```python
from core.session_utils import (
    list_sessions, load_session, save_session,
    build_session_data, format_relative_time
)
from .run_utils import _colored

def format_session_preview(session: dict, index: int) -> str:
    """1セッションを2行で整形"""
    # 実装は上記UI/UX詳細セクションを参照
    pass

def select_session_ui(sessions: list[dict]) -> dict | None:
    """セッション選択ダイアログ"""
    # 実装は上記UI/UX詳細セクションを参照
    pass

def handle_resume_command(
    current_history: list[tuple[str, str]],
    current_model: str,
    current_settings: dict,
    current_session_id: str,
    current_session_name: str,
    created_at: str
) -> dict | None:
    """
    セッション復元処理

    Args:
        current_*: 現在のセッション情報（自動保存用）

    Returns:
        選択されたセッションデータ or None（キャンセル時）
    """
    # 1. セッション一覧を取得
    sessions = list_sessions()

    if not sessions:
        print(_colored("📂 No saved sessions found", "warning"))
        return None

    # 2. セッション選択UI表示
    selected_session = select_session_ui(sessions)

    if not selected_session:
        return None  # キャンセル

    # 3. 現在のセッションを自動保存
    print(_colored("💾 Saving current session...", "system"))
    current_session_data = build_session_data(
        current_history,
        current_model,
        current_settings,
        current_session_id,
        current_session_name,
        created_at
    )
    save_session(current_session_data)
    print(_colored("✅ Current session saved", "success"))

    # 4. 選択されたセッションを復元
    print(_colored(f"📂 Loading session...", "system"))

    msg_count = selected_session['message_count']
    name_display = selected_session['session_name'] or '[No name]'
    print(_colored(
        f"✅ Session restored: {name_display} ({msg_count} message{'s' if msg_count != 1 else ''})",
        "success"
    ))

    return selected_session
```

---

#### **`commands/run_save.py`** (推定: 40-60行)

**関数一覧:**
```python
from core.session_utils import save_session, build_session_data
from .run_utils import _colored

def handle_save_command(
    history: list[tuple[str, str]],
    model_name: str,
    settings: dict,
    session_id: str,
    session_name: str,
    created_at: str
) -> None:
    """
    現在のセッションを即座に保存
    """
    session_data = build_session_data(
        history, model_name, settings, session_id, session_name, created_at
    )

    save_session(session_data)

    msg_count = len(history)
    updated_time = session_data['updated_at'][:16].replace('T', ' ')

    print(_colored(f"💾 Session saved: {session_id}", "success"))
    print(_colored(f"   {msg_count} message{'s' if msg_count != 1 else ''}, last updated: {updated_time}", "system"))
```

---

#### **`commands/run_session.py`** (推定: 200-250行)

**関数一覧:**
```python
from core.session_utils import (
    get_session_storage_info, update_session_name,
    delete_session, list_sessions
)
from .run_utils import _colored
from .run_resume import handle_resume_command

def show_session_menu(
    current_history: list[tuple[str, str]],
    current_model: str,
    current_settings: dict,
    current_session_id: str,
    current_session_name: str,
    created_at: str
) -> dict | None:
    """
    セッション管理メニュー

    Returns:
        復元されたセッション（Resume選択時）or None
    """
    while True:
        # ストレージ情報を取得
        info = get_session_storage_info()

        # メニュー表示
        print("\n" + "="*60)
        print(_colored("📊 Session Management", "system"))
        print("="*60)
        print(f"Total Sessions:     {info['total_sessions']} sessions")
        print(f"Storage Used:       {info['storage_mb']} MB")
        print(f"Oldest Session:     {info['oldest_date']}")
        print("="*60)
        print(" 1. Resume Session")
        print(" 2. Rename Current Session")
        print(" 3. Delete Sessions")
        print(" 4. Auto-save Settings")
        print("="*60)
        print(" 0. Back")
        print()

        choice = input(_colored("Select option (0-4): ", "user_prompt")).strip()

        if choice == "1":
            # Resume Session
            restored = handle_resume_command(
                current_history, current_model, current_settings,
                current_session_id, current_session_name, created_at
            )
            if restored:
                return restored  # セッション切り替え

        elif choice == "2":
            # Rename Current Session
            rename_current_session(current_session_id, current_session_name)

        elif choice == "3":
            # Delete Sessions
            delete_sessions_ui()

        elif choice == "4":
            # Auto-save Settings
            edit_autosave_settings()

        elif choice == "0":
            break

        else:
            print(_colored("⚠️  Invalid option", "warning"))

    return None

def rename_current_session(session_id: str, current_name: str) -> str:
    """
    現在のセッション名を変更

    Returns:
        新しいセッション名
    """
    display_name = current_name if current_name else "[No name]"
    print(f"\nCurrent session name: {display_name}")

    from prompt_toolkit import prompt
    new_name = prompt("Enter new name (or leave blank): ", default="").strip()

    # セッションを更新
    update_session_name(session_id, new_name)

    if new_name:
        print(_colored(f"✅ Session renamed to \"{new_name}\"", "success"))
    else:
        print(_colored("✅ Session name cleared", "success"))

    return new_name

def delete_sessions_ui() -> None:
    """
    セッション削除UI（複数選択）
    """
    sessions = list_sessions()

    if not sessions:
        print(_colored("📂 No sessions to delete", "warning"))
        return

    # チェックボックス式UI（prompt-toolkit使用）
    from prompt_toolkit.shortcuts import checkboxlist_dialog

    choices = [
        (session['session_id'], format_session_preview(session, i+1))
        for i, session in enumerate(sessions)
    ]

    selected = checkboxlist_dialog(
        title="🗑️  Delete Sessions",
        text="Select sessions to delete (Space to toggle, Enter to confirm):",
        values=choices,
    ).run()

    if not selected:
        print(_colored("Cancelled", "system"))
        return

    # 確認
    count = len(selected)
    confirm = input(f"Delete {count} session{'s' if count > 1 else ''}? (y/n): ").strip().lower()

    if confirm == 'y':
        for session_id in selected:
            delete_session(session_id)
        print(_colored(f"🗑️  Deleted {count} session{'s' if count > 1 else ''}", "success"))
    else:
        print(_colored("Cancelled", "system"))

def edit_autosave_settings() -> None:
    """
    自動保存設定の変更
    """
    # config.jsonから現在の設定を読み込み
    from core import load_user_config, save_to_config

    config = load_user_config()
    current_interval = config.get('sessions', {}).get('auto_save_interval', 300)

    # 現在の設定表示
    if current_interval == 0:
        status = "Disabled"
    else:
        minutes = current_interval // 60
        status = f"Enabled (every {minutes} minutes)"

    print("\n" + "="*60)
    print(_colored("⚙️  Auto-save Settings", "system"))
    print("="*60)
    print(f"Current: {status}\n")
    print(" 1. Enable (5 minutes interval)")
    print(" 2. Enable (10 minutes interval)")
    print(" 3. Disable")
    print("="*60)
    print(" 0. Back")
    print()

    choice = input(_colored("Select option (0-3): ", "user_prompt")).strip()

    if choice == "1":
        config.setdefault('sessions', {})['auto_save_interval'] = 300
        print(_colored("✅ Auto-save enabled (5 minutes)", "success"))
    elif choice == "2":
        config.setdefault('sessions', {})['auto_save_interval'] = 600
        print(_colored("✅ Auto-save enabled (10 minutes)", "success"))
    elif choice == "3":
        config.setdefault('sessions', {})['auto_save_interval'] = 0
        print(_colored("✅ Auto-save disabled", "success"))
    elif choice == "0":
        return
    else:
        print(_colored("⚠️  Invalid option", "warning"))
        return

    # 設定を保存
    save_to_config('sessions', config.get('sessions', {}))
```

---

#### **`commands/run.py`への変更** (推定: +30行)

**追加箇所:**

1. **インポート:**
```python
from core.session_utils import (
    create_session_id, build_session_data, save_session
)
from .run_resume import handle_resume_command
from .run_save import handle_save_command
from .run_session import show_session_menu
```

2. **セッション初期化（`run_model()`の最初）:**
```python
def run_model(...):
    # セッション管理の初期化
    session_id = create_session_id()
    session_name = ""
    session_created_at = datetime.now().isoformat()

    # 自動保存タイマー
    last_auto_save = time.time()
    auto_save_interval = load_user_config().get('sessions', {}).get('auto_save_interval', 300)

    # 既存の初期化処理...
```

3. **メインループ内（自動保存チェック）:**
```python
while True:
    try:
        # 自動保存チェック
        if auto_save_interval > 0 and time.time() - last_auto_save >= auto_save_interval:
            settings_dict = {
                'max_tokens': max_tokens,
                'stream_mode': stream_mode,
                'chat_mode': chat_mode,
                'history_mode': history_mode,
                'time_limit': time_limit,
                'reasoning': reasoning,
            }
            session_data = build_session_data(
                history, model_name, settings_dict,
                session_id, session_name, session_created_at
            )
            save_session(session_data)
            last_auto_save = time.time()
            # 静かに保存（ユーザーに通知しない）

        # 通常の入力処理
        if session:
            # ...既存のコード...
```

4. **コマンド処理:**
```python
        # /resume コマンド
        if user_input.lower() == "/resume":
            settings_dict = {...}
            restored = handle_resume_command(
                history, model_name, settings_dict,
                session_id, session_name, session_created_at
            )
            if restored:
                # セッションを切り替え
                history = restored['history']
                session_id = restored['session_id']
                session_name = restored['session_name']
                session_created_at = restored['created_at']
                # 設定も復元
                max_tokens = restored['settings']['max_tokens']
                stream_mode = restored['settings']['stream_mode']
                # ...
            continue

        # /save コマンド
        if user_input.lower() == "/save":
            settings_dict = {...}
            handle_save_command(
                history, model_name, settings_dict,
                session_id, session_name, session_created_at
            )
            continue

        # /session コマンド
        if user_input.lower() == "/session":
            settings_dict = {...}
            restored = show_session_menu(
                history, model_name, settings_dict,
                session_id, session_name, session_created_at
            )
            if restored:
                # セッション切り替え処理（/resumeと同じ）
                # ...
            continue
```

5. **終了時の保存:**
```python
        # /exit, /quit, /bye
        if user_input.lower() in ['/exit', '/quit', '/bye']:
            settings_dict = {...}
            session_data = build_session_data(
                history, model_name, settings_dict,
                session_id, session_name, session_created_at
            )
            save_session(session_data)
            print(_colored("💾 Session saved", "success"))
            print(_colored("👋 Goodbye!", "system"))
            break

    except EOFError:  # Ctrl+D
        settings_dict = {...}
        session_data = build_session_data(
            history, model_name, settings_dict,
            session_id, session_name, session_created_at
        )
        save_session(session_data)
        print(_colored("\n💾 Session saved", "success"))
        print(_colored("👋 Goodbye!", "system"))
        break
```

---

## 📝 config.jsonへの追加

```json
{
  "sessions": {
    "auto_save_interval": 300
  }
}
```

**デフォルト値（`core.py`の`default_config`）:**
```python
default_config = {
    # 既存の設定...
    "sessions": {
        "auto_save_interval": 300  # 秒（5分）、0で無効
    }
}
```

---

## 🚀 実装フェーズ

### **Phase 1: v0.2.8リリース（基本機能）**

#### **ステップ1: セッションユーティリティの実装**
- [ ] `core/session_utils.py`作成
- [ ] `create_session_id()`
- [ ] `build_session_data()`
- [ ] `save_session()`
- [ ] `load_session()`
- [ ] `list_sessions()`
- [ ] `delete_session()`
- [ ] `update_session_name()`
- [ ] `get_session_storage_info()`
- [ ] `format_relative_time()`

#### **ステップ2: コマンドハンドラの実装**
- [ ] `commands/run_save.py`作成
  - [ ] `handle_save_command()`
- [ ] `commands/run_resume.py`作成
  - [ ] `format_session_preview()`
  - [ ] `select_session_ui()`
  - [ ] `handle_resume_command()`
- [ ] `commands/run_session.py`作成
  - [ ] `show_session_menu()`
  - [ ] `rename_current_session()`
  - [ ] `delete_sessions_ui()`
  - [ ] `edit_autosave_settings()`

#### **ステップ3: run.pyへの統合**
- [ ] セッション初期化処理追加
- [ ] 自動保存タイマー実装
- [ ] `/resume`コマンド統合
- [ ] `/save`コマンド統合
- [ ] `/session`コマンド統合
- [ ] 終了時の保存処理追加
- [ ] Ctrl+D時の保存処理追加

#### **ステップ4: 設定ファイルの更新**
- [ ] `core.py`のデフォルト設定に`sessions`追加
- [ ] 設定の読み込み・保存テスト

#### **ステップ5: テスト**
- [ ] セッション保存・復元のテスト
- [ ] 自動保存のテスト
- [ ] セッション名変更のテスト
- [ ] セッション削除のテスト
- [ ] エッジケース（空セッション、大量セッションなど）

---

### **Phase 4: 将来の拡張機能**

#### **アーカイブ機能**
- [ ] `archived`フラグの活用
- [ ] アーカイブUI実装（`/session`メニューに追加）
- [ ] アーカイブ解除機能

#### **検索機能**
- [ ] 会話内容の全文検索
- [ ] キーワードハイライト表示
- [ ] 検索結果からセッション復元

#### **エクスポート機能**
- [ ] セッション管理メニューに「Export Session」追加
- [ ] 過去セッションのエクスポート（md/txt/json）
- [ ] アーカイブからもエクスポート可能に

---

## 🎨 ヘルプテキストへの追加

**`commands/run_help.py`の更新:**

```python
help_text = """
📖 MLX-LM Interactive Commands:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/help      Show this help message
/clear     Clear conversation/screen
/status    Show current session status
/export    Export current conversation
/setting   Adjust settings (model, colors, etc.)

Session Management:
/resume    Resume a previous session
/save      Save current session
/session   Session management menu

/exit, /quit, /bye, Ctrl+D
           Save and exit
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
```

---

## 📊 推定コード量

| ファイル | 推定行数 | 説明 |
|---------|---------|------|
| `core/session_utils.py` | 150-200 | セッションデータ操作 |
| `commands/run_resume.py` | 140-190 | `/resume`コマンド |
| `commands/run_save.py` | 40-60 | `/save`コマンド |
| `commands/run_session.py` | 200-250 | `/session`メニュー |
| `commands/run.py`（追加分） | +30 | 統合処理 |
| **合計** | **560-730行** | |

**v0.2.7の実績:**
- 1163行 → 436行（62%削減、727行削減）

**v0.2.8での追加:**
- 約600-700行の新規コード
- ただしモジュール分割されているため、メンテナンス性は高い

---

## ✅ チェックリスト（実装前）

### **設計確認**
- [x] データ構造の定義完了
- [x] ディレクトリ構造の決定
- [x] コマンド仕様の確定
- [x] UI/UX設計完了
- [x] ファイル構成の決定
- [x] Phase分け完了

### **実装準備**
- [ ] `core/session_utils.py`の関数リスト確認
- [ ] `run.py`への統合ポイント確認
- [ ] prompt-toolkitの使用方法確認
- [ ] テストケースの洗い出し

### **ドキュメント**
- [x] 設計書作成完了
- [ ] 実装ガイド作成（このファイルを参照）
- [ ] リリースノート準備（v0.2.8）

---

## 🔗 参考資料

### **関連ファイル**
- `CLAUDE.md`: 開発ワークフロー
- `SESSION_DESIGN_v0.2.8.md`: 本設計書
- `commands/run.py`: メインループ
- `core.py`: コア機能・設定管理

### **外部ライブラリ**
- [prompt-toolkit](https://python-prompt-toolkit.readthedocs.io/): インタラクティブUIライブラリ
  - `radiolist_dialog`: 単一選択ダイアログ
  - `checkboxlist_dialog`: 複数選択ダイアログ
  - `prompt`: 入力プロンプト

---

## 📌 注意事項

1. **セッションIDの一意性**
   - UUID v4を使用することで衝突を回避
   - `create_session_id()`で必ず生成

2. **タイムスタンプのフォーマット**
   - ISO 8601形式（`2025-01-15T14:30:00`）
   - `datetime.now().isoformat()`で生成

3. **エラーハンドリング**
   - セッションファイルが存在しない場合
   - JSONパースエラー
   - ディスク容量不足

4. **後方互換性**
   - 既存の`config.json`との互換性を保つ
   - 設定項目は段階的に追加

5. **パフォーマンス**
   - セッション数が増えても動作速度に影響しないよう配慮
   - 必要に応じてキャッシング検討

---

## 🎉 期待される成果

### **ユーザーメリット**
- ✅ 過去の会話を簡単に再開できる
- ✅ クラッシュしても会話が失われない
- ✅ 複数のプロジェクトを並行管理できる
- ✅ セッション整理が簡単（名前変更・削除）

### **開発メリット**
- ✅ モジュール化されたコード構造
- ✅ テスト可能な設計
- ✅ 将来の拡張に対応しやすい
- ✅ ドキュメント完備

---

**設計書バージョン:** 1.0
**最終更新:** 2025-01-16
**作成者:** Claude (Anthropic)
