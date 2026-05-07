"""
招生組業務管理工具 - 每日自動更新腳本
由 GitHub Actions 執行（每天台灣時間 08:00）

讀取來源：
  1. Gmail - 本月含截止日期的業務相關郵件
  2. Google Drive「簡章重要時程」資料夾 - 圖片檔名中的關鍵字

輸出：todos.json（由 GitHub Actions 推回 repository）
"""

import os, re, json, base64, datetime, sys

# ── Google API ──────────────────────────────────────────
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES_GMAIL  = ["https://www.googleapis.com/auth/gmail.readonly"]
SCOPES_DRIVE  = ["https://www.googleapis.com/auth/drive.readonly"]

def get_service(token_json_str, scopes, api, version):
    """從環境變數中的 JSON 字串建立 Google API 服務"""
    import tempfile, pathlib
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    tmp.write(token_json_str)
    tmp.close()
    creds = Credentials.from_authorized_user_file(tmp.name, scopes)
    pathlib.Path(tmp.name).unlink()
    return build(api, version, credentials=creds)

# ── 業務清單（用來比對 Email）──────────────────────────
TASKS = [
    {"id":"t01","cat":"A","name":"特殊選才","persons":["劉玉萍"],
     "keywords":["特殊選才","特才"]},
    {"id":"t02","cat":"A","name":"申請入學","persons":["余艾璇"],
     "keywords":["申請入學","書審","流失率","書面審查"]},
    {"id":"t03","cat":"A","name":"繁星推薦","persons":["余艾璇"],
     "keywords":["繁星"]},
    {"id":"t04","cat":"A","name":"分發入學","persons":["余艾璇"],
     "keywords":["分發入學","聯合分發"]},
    {"id":"t05","cat":"A","name":"暑假轉學考","persons":["趙沛滋"],
     "keywords":["暑轉","轉學考","轉學生招生"]},
    {"id":"t07","cat":"A","name":"音樂系單獨招生","persons":["余艾璇"],
     "keywords":["音樂系","獨招"]},
    {"id":"t08","cat":"A","name":"運動績優單獨招生","persons":["余艾璇"],
     "keywords":["運動績優"]},
    {"id":"t09","cat":"A","name":"四技二專特殊選才","persons":["余艾璇"],
     "keywords":["四技","二專","技職"]},
    {"id":"t11","cat":"B","name":"院系所增設調整及招生總量提報","persons":["王于心"],
     "keywords":["總量提報","招生總量","增設","系所調整"]},
    {"id":"t12","cat":"C","name":"碩博士班甄試","persons":["王于心"],
     "keywords":["碩士班甄試","博士班甄試","研究所甄試","甄試入學"]},
    {"id":"t13","cat":"C","name":"碩博士班考試","persons":["王于心"],
     "keywords":["碩士班考試","博士班考試","研究所考試"]},
    {"id":"t14","cat":"D","name":"外國學生招生","persons":["劉玉萍"],
     "keywords":["外國學生","外國生","境外學生申請"]},
    {"id":"t15","cat":"D","name":"僑港澳招生","persons":["劉玉萍"],
     "keywords":["海外聯招","僑生","港澳","聯招會"]},
    {"id":"t16","cat":"D","name":"陸生招生","persons":["劉玉萍"],
     "keywords":["陸生","陸聯會","大陸地區"]},
    {"id":"t17","cat":"E","name":"身障甄試試務（北四區）","persons":["趙沛滋","劉玉萍"],
     "keywords":["身心障礙","身障甄試","身障生","北四區"]},
    {"id":"t18","cat":"F","name":"招生專業化計畫","persons":["劉育志","高佳嵐","張禧恕","王意涵"],
     "keywords":["招生專業化","工作小組","評量尺規","書審系統"]},
    {"id":"t19","cat":"G","name":"至高中宣傳","persons":["劉玉萍","趙沛滋"],
     "keywords":["高中宣傳","前進高中","校園參訪","宣傳活動","校外加班"]},
    {"id":"t23","cat":"G","name":"高中生電子報製作","persons":["陳佳妤","王意涵"],
     "keywords":["電子報","高中生電子報"]},
    {"id":"t24","cat":"G","name":"校園記者招募與管理","persons":["陳佳妤"],
     "keywords":["校園記者","記者招募"]},
    {"id":"t25","cat":"G","name":"網路廣告行銷與管理","persons":["陳佳妤"],
     "keywords":["廣告","行銷","採購案","標價"]},
    {"id":"t26","cat":"G","name":"院系所招生活動經費補助","persons":["趙沛滋"],
     "keywords":["招生活動","經費補助","活動補助"]},
    {"id":"t27","cat":"H","name":"ISMS資訊安全管理制度","persons":["王意涵"],
     "keywords":["ISMS","資訊安全","資安窗口"]},
    {"id":"t28","cat":"H","name":"個資保護管理制度（PIMS）","persons":["王意涵"],
     "keywords":["PIMS","個資保護","個人資料"]},
    {"id":"t29","cat":"H","name":"自衛消防編組訓練","persons":["王意涵"],
     "keywords":["消防編組","消防訓練","自衛消防"]},
    {"id":"t30","cat":"H","name":"內部控制自行評估","persons":["王意涵"],
     "keywords":["內部控制","內控","自行評估"]},
    {"id":"t31","cat":"H","name":"風險管理評估","persons":["王意涵"],
     "keywords":["風險管理","風險評估","風險處理"]},
    {"id":"t32","cat":"H","name":"職場不法侵害預防評估","persons":["王意涵"],
     "keywords":["不法侵害","職場暴力","潛在暴力"]},
    {"id":"t33","cat":"H","name":"校務資料庫填報","persons":["余艾璇","趙沛滋"],
     "keywords":["校務資料庫","校庫","資訊公開"]},
    {"id":"t27b","cat":"H","name":"資安教育訓練","persons":["王意涵"],
     "keywords":["資安宣導","資安教育訓練","社交工程","線上測驗"]},
    {"id":"t34","cat":"I","name":"經文不利生人數填報","persons":["余艾璇"],
     "keywords":["經濟文化不利","弱勢","經文不利"]},
    {"id":"t37","cat":"I","name":"深耕經費管理","persons":["趙沛滋"],
     "keywords":["高教深耕","深耕計畫","深耕經費"]},
    {"id":"t38","cat":"J","name":"工讀生管理","persons":["張禧恕"],
     "keywords":["工讀生"]},
    {"id":"t39","cat":"J","name":"各類法規校閱與更新","persons":["劉育志"],
     "keywords":["法規","校閱","分層負責明細表"]},
    {"id":"t40","cat":"J","name":"各類工作報告","persons":["劉育志","張禧恕"],
     "keywords":["行政會議","執行情形","工作報告","主管會報","座談會"]},
    {"id":"t41","cat":"J","name":"校務評鑑自我改善計畫","persons":["劉育志"],
     "keywords":["校務評鑑","自我改善","評鑑報告"]},
    {"id":"t43","cat":"J","name":"中長程計畫","persons":["劉育志"],
     "keywords":["中長程計畫"]},
    {"id":"t44","cat":"K","name":"財物複盤作業","persons":["余艾璇"],
     "keywords":["財物複盤","複盤","財產盤點"]},
    {"id":"t45","cat":"K","name":"年度校務基金預算書與績效報告","persons":["王于心"],
     "keywords":["校務基金","預算書","績效報告","預算總說明"]},
    {"id":"t46","cat":"K","name":"資通訊經費預算表填報","persons":["王于心"],
     "keywords":["資通訊","電腦預算","設備汰換"]},
]

# 組內人員 Email 清單（用來過濾組內業務郵件）
STAFF_EMAILS = {
    "lyc614@mail.ntue.edu.tw":    "劉育志",
    "gwennie@mail.ntue.edu.tw":   "趙沛滋",
    "clair@mail.ntue.edu.tw":     "劉玉萍",
    "vivian@tea.ntue.edu.tw":     "高佳嵐",
    "yu5831@mail.ntue.edu.tw":    "余艾璇",
    "jyc89@mail.ntue.edu.tw":     "陳佳妤",
    "jmvupk@mail.ntue.edu.tw":   "王于心",
    "wendypig654@mail.ntue.edu.tw": "王意涵",
    "cys@tea.ntue.edu.tw":        "張禧恕",
}

# 噪音關鍵字：含這些字的 Email 直接略過
NOISE_SUBJECTS = [
    "allstaff", "割草", "水運會", "圖書館", "餐廳", "競賽", "轉知",
    "研習", "講座", "招聘", "徵才", "發票", "廠商", "實習表單",
    "新書發表", "外部", "外校", "其他學校",
]

# ── 日期正規表達式 ──────────────────────────────────────
DATE_PATTERNS = [
    # 115/5/13、115年5月13日、5/13、5月13日、05/13
    r'(\d{3})[年/](\d{1,2})[月/](\d{1,2})[日]?',  # 民國年
    r'(\d{4})[年-](\d{1,2})[月-](\d{1,2})[日]?',  # 西元年
    r'(?<!\d)(\d{1,2})[/月](\d{1,2})(?:日|[前截])?\s*(?:前|截止|中午|下班|回覆|擲回|回傳)',
]

DEADLINE_TRIGGERS = [
    "前回覆", "前擲回", "前回傳", "截止", "限辦日", "期限",
    "中午前", "下班前", "前惠傳", "前寄回",
]

def parse_deadline(text, now):
    """從文字中抽取最接近的截止日期，回傳 datetime.date 或 None"""
    candidates = []

    # 民國年格式
    for m in re.finditer(r'(\d{3})[年/](\d{1,2})[月/](\d{1,2})[日]?', text):
        y = int(m.group(1)) + 1911
        mo, d = int(m.group(2)), int(m.group(3))
        try:
            candidates.append(datetime.date(y, mo, d))
        except ValueError:
            pass

    # 西元年格式
    for m in re.finditer(r'(\d{4})[年-](\d{1,2})[月-](\d{1,2})', text):
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            candidates.append(datetime.date(y, mo, d))
        except ValueError:
            pass

    # 無年份：M/D 或 M月D日，前後有截止觸發詞
    for m in re.finditer(r'(\d{1,2})[/月](\d{1,2})日?\s*(?:前|截止|中午|下班)?', text):
        mo, d = int(m.group(1)), int(m.group(2))
        try:
            dt = datetime.date(now.year, mo, d)
            # 若已過去超過 60 天，推測是明年
            if (dt - now).days < -60:
                dt = datetime.date(now.year + 1, mo, d)
            candidates.append(dt)
        except ValueError:
            pass

    if not candidates:
        return None

    # 取最接近今天（且不超過 90 天後）的日期
    future = [d for d in candidates if (d - now).days >= -7]
    if future:
        return min(future, key=lambda d: abs((d - now).days))
    return min(candidates, key=lambda d: abs((d - now).days))

def match_task(text):
    """比對文字，回傳最可能對應的業務（或 None）"""
    text_lower = text.lower()
    best, best_score = None, 0
    for task in TASKS:
        score = sum(1 for kw in task["keywords"] if kw in text)
        if score > best_score:
            best, best_score = task, score
    return best if best_score > 0 else None

def is_business_email(subject, sender, snippet):
    """判斷是否為與招生業務相關的郵件"""
    subject_lower = subject.lower()
    combined = (subject + " " + snippet).lower()

    # 明確排除（全校公告且與招生無關）
    noise = ["割草", "水運會", "餐廳問卷", "新書發表",
             "教師徵選", "教師甄選", "新聘專任", "徵才通知",
             "體育用品", "無人機", "電動車"]
    if any(n in subject for n in noise):
        return False

    # 公文系統通知 → 一律保留
    if "公文線上簽核" in subject:
        return True

    # 組內人員寄出的郵件 → 保留
    if any(e in sender for e in STAFF_EMAILS):
        return True

    # 主旨含業務關鍵字 → 保留
    biz_kws = ["招生", "簡章", "甄試", "入學", "報名", "錄取",
               "行政會議", "分層負責", "校務評鑑", "校務基金",
               "特殊選才", "外國學生", "轉學", "資安", "個資",
               "消防", "預算", "提案", "總量", "工作報告"]
    if any(k in combined for k in biz_kws):
        return True

    return False

    # 公文系統通知直接保留
    if "公文線上簽核" in subject or "限辦日" in snippet:
        return True

    # 組內人員寄出的郵件直接保留
    if any(e in sender for e in STAFF_EMAILS):
        return True

    # 收件含組內人員且主旨有業務關鍵字
    business_kws = ["招生", "簡章", "甄試", "入學", "報名", "錄取",
                    "公文", "限辦", "行政會議", "分層負責", "校務",
                    "特殊選才", "申請入學", "轉學", "外國學生",
                    "資安", "個資", "消防", "預算"]
    if any(k in combined for k in business_kws):
        return True

    return False

# 截止日偵測：多組 regex 組合，涵蓋各種中文 Email 格式
import re as _re
_DEADLINE_RE = [
    _re.compile(r'[0-9]{1,2}[月/][0-9]{1,2}.{0,6}(?:前|截止|中午|下班)'),
    _re.compile(r'(?:前|截止|中午|下班).{0,3}[0-9]{1,2}[月/][0-9]{1,2}'),
    _re.compile(r'1[01][0-9][年/][0-9]{1,2}[月/][0-9]{1,2}'),
    _re.compile(r'限辦日'),
]

def has_deadline(subject, snippet):
    combined = subject + " " + snippet
    # 快速關鍵字預篩
    quick = ["前回覆","截止","限辦","前擲回","前回傳","中午前","下班前","前惠傳","請盡速"]
    if not any(k in combined for k in quick):
        return False
    return any(p.search(combined) for p in _DEADLINE_RE)


# ── 主邏輯 ──────────────────────────────────────────────
def main():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).date()
    this_month = now.month
    print(f"[{now}] 開始更新 todos.json（{this_month}月）")

    # 讀取環境變數（由 GitHub Actions Secrets 注入）
    gmail_token  = os.environ.get("GMAIL_TOKEN_JSON", "")
    gdrive_token = os.environ.get("GDRIVE_TOKEN_JSON", "")
    folder_id    = os.environ.get("BROCHURE_FOLDER_ID", "1dext3fFM9TIzMjb9wo4YB0xnxADs7qZ3")

    todos = []

    # ── 1. 讀取 Gmail ────────────────────────────────────
    if gmail_token:
        print("  讀取 Gmail...")
        try:
            gmail = get_service(gmail_token, SCOPES_GMAIL, "gmail", "v1")
            after_ts = int(datetime.datetime(now.year, this_month, 1).timestamp())
            result = gmail.users().messages().list(
                userId="me",
                q=f"after:{after_ts} -label:promotions -label:social",
                maxResults=100,
            ).execute()

            msgs = result.get("messages", [])
            print(f"    本月郵件：{len(msgs)} 封")
            seen_tasks = set()

            for msg in msgs:
                detail = gmail.users().messages().get(
                    userId="me", messageId=msg["id"],
                    format="metadata",
                    metadataHeaders=["Subject", "From", "Date"],
                ).execute()
                headers = {h["name"]: h["value"]
                           for h in detail.get("payload", {}).get("headers", [])}
                subject = headers.get("Subject", "")
                sender  = headers.get("From", "").lower()
                snippet = detail.get("snippet", "")

                if not is_business_email(subject, sender, snippet):
                    continue
                if not has_deadline(subject, snippet):
                    continue

                combined = subject + " " + snippet
                task     = match_task(combined)
                deadline = parse_deadline(combined, now)

                if not deadline:
                    continue
                if deadline.month != this_month and (deadline - now).days > 60:
                    continue

                task_id = task["id"] if task else "email_misc"
                key = f"{task_id}_{deadline}"
                if key in seen_tasks:
                    continue
                seen_tasks.add(key)

                todos.append({
                    "task_id":   task_id,
                    "task_name": task["name"] if task else subject[:20],
                    "cat":       task["cat"] if task else "J",
                    "action":    snippet[:80].strip(),
                    "deadline":  deadline.isoformat(),
                    "persons":   task["persons"] if task else ["劉育志"],
                    "source":    "email",
                    "done":      False,
                })
                print(f"    + [{deadline}] {task['name'] if task else subject[:20]}")
        except Exception as e:
            print(f"    [警告] Gmail 讀取失敗：{e}")
    else:
        print("  [略過] GMAIL_TOKEN_JSON 未設定")

    # ── 2. 讀取 Google Drive 簡章資料夾 ─────────────────
    if gdrive_token:
        print("  讀取 Google Drive 簡章資料夾...")
        try:
            drive = get_service(gdrive_token, SCOPES_DRIVE, "drive", "v3")
            result = drive.files().list(
                q=f"'{folder_id}' in parents",
                fields="files(id,name,mimeType,modifiedTime)",
                pageSize=50,
            ).execute()
            files = result.get("files", [])
            print(f"    檔案數：{len(files)}")

            for f in files:
                # 只讀取「名稱中含有本月數字」或「近期修改」的檔案
                fname = f["name"]
                # 從檔名抽取關鍵字
                task = match_task(fname)
                deadline = parse_deadline(fname, now)

                # 若檔名找不到截止日，嘗試讀取圖片 snippet（Drive 有時提供）
                snippet_text = ""
                if not deadline:
                    # 從 Drive 的 contentSnippet 取得（若有）
                    file_detail = drive.files().get(
                        fileId=f["id"],
                        fields="contentSnippet",
                    ).execute()
                    snippet_text = file_detail.get("contentSnippet", "")
                    deadline = parse_deadline(snippet_text, now)

                if not deadline:
                    print(f"    [略過] {fname}（找不到截止日期）")
                    continue
                if deadline.month != this_month and (deadline - now).days > 90:
                    print(f"    [略過] {fname}（截止日 {deadline} 不在本月範圍）")
                    continue

                combined = fname + " " + snippet_text
                task = match_task(combined) or task

                todos.append({
                    "task_id":   task["id"] if task else "brochure_misc",
                    "task_name": task["name"] if task else fname[:20],
                    "cat":       task["cat"] if task else "A",
                    "action":    f"依簡章辦理：{fname}",
                    "deadline":  deadline.isoformat(),
                    "persons":   task["persons"] if task else ["劉育志"],
                    "source":    "brochure",
                    "done":      False,
                })
                print(f"    + [{deadline}] {task['name'] if task else fname[:20]}（來自簡章）")
        except Exception as e:
            print(f"    [警告] Google Drive 讀取失敗：{e}")
    else:
        print("  [略過] GDRIVE_TOKEN_JSON 未設定")

    # ── 3. 去重 + 排序 ───────────────────────────────────
    seen = set()
    unique_todos = []
    for t in sorted(todos, key=lambda x: x["deadline"]):
        key = f"{t['task_id']}_{t['deadline']}"
        if key not in seen:
            seen.add(key)
            unique_todos.append(t)

    # ── 4. 輸出 todos.json ───────────────────────────────
    output = {
        "updated_at": datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=8))
        ).strftime("%Y-%m-%d %H:%M"),
        "month":  this_month,
        "todos":  unique_todos,
    }

    out_path = "todos.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n  ✓ 寫出 {out_path}（共 {len(unique_todos)} 筆）")


if __name__ == "__main__":
    main()

