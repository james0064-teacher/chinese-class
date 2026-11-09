"""
AI 公司：四部門（行政、教學、人事、輔導），所有員工都是 Claude agent。

流程：
  老闆（你）下指令 → 行政部的分派 AI 判斷交給哪個部門
  → 該部門的 AI 員工執行 → 結果寫進部門紀錄

安裝：pip install anthropic
設定：export ANTHROPIC_API_KEY=你的金鑰
沒有金鑰時會自動用「模擬模式」跑，方便先測架構。
"""
import json
import os

WORKER_MODEL = "claude-sonnet-5-5"   # 一般員工
ROUTER_MODEL = "claude-haiku-5-5"    # 分派任務用，便宜快速

try:
    import anthropic
    CLIENT = anthropic.Anthropic() if os.getenv("ANTHROPIC_API_KEY") else None
except ImportError:
    CLIENT = None


def ask_claude(system, messages, model=WORKER_MODEL, max_tokens=1000):
    if CLIENT is None:  # 模擬模式
        last = messages[-1]["content"]
        if "只回 JSON" in system:
            return json.dumps({"dept": "教學", "reason": "模擬分派"}, ensure_ascii=False)
        return f"（模擬回覆）已處理：{last[:30]}"
    resp = CLIENT.messages.create(
        model=model, max_tokens=max_tokens, system=system, messages=messages
    )
    return "".join(b.text for b in resp.content if b.type == "text")


def parse_json(raw):
    """容忍模型用 ```json ... ``` 包住回覆的情況。"""
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        text = text.removeprefix("json").strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end + 1]
    return json.loads(text)


class AIEmployee:
    def __init__(self, name, role, duties, model=WORKER_MODEL):
        self.name, self.role, self.model = name, role, model
        self.system = (
            f"你是「{name}」，職位是{role}。職責：{duties}\n"
            "用繁體中文回覆，簡潔、具體、可執行。不確定的事要說明並提出需要的資訊。"
        )
        self.history = []  # 員工自己的工作記憶

    def work(self, task):
        self.history.append({"role": "user", "content": task})
        try:
            reply = ask_claude(self.system, self.history[-10:], self.model)
        except Exception:
            self.history.pop()  # 呼叫失敗時移除，避免 user/assistant 交替錯亂
            raise
        self.history.append({"role": "assistant", "content": reply})
        return reply


class Department:
    def __init__(self, name, mission):
        self.name, self.mission = name, mission
        self.staff, self.log = [], []
        self._next = 0  # 輪流分派用

    def add(self, emp):
        self.staff.append(emp)

    def handle(self, task):
        if not self.staff:
            return f"{self.name}部目前沒有員工"
        emp = self.staff[self._next % len(self.staff)]  # 輪流交給部門員工
        self._next += 1
        result = emp.work(task)
        self.log.append({"task": task, "by": emp.name, "result": result})
        return result


class AICompany:
    def __init__(self, name):
        self.name = name
        self.depts = {
            "行政": Department("行政", "預算、公文、排程、跨部門協調"),
            "教學": Department("教學", "課程設計、教材、學習單、課表"),
            "人事": Department("人事", "職位設計、招募、考核、員工角色設定"),
            "輔導": Department("輔導", "個案分析、輔導策略、紀錄、親師溝通"),
        }

    def route(self, task):
        """行政部的分派 AI 決定任務歸屬"""
        menu = "\n".join(f"- {k}：{d.mission}" for k, d in self.depts.items())
        system = f"你是任務分派員。部門如下：\n{menu}\n只回 JSON：{{\"dept\": 部門名, \"reason\": 一句理由}}"
        raw = ask_claude(system, [{"role": "user", "content": task}], ROUTER_MODEL, 200)
        try:
            data = parse_json(raw)
            return data["dept"] if data.get("dept") in self.depts else "行政"
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
            return "行政"

    def hire(self, dept, name, role, duties):
        if dept not in self.depts:
            raise ValueError(f"沒有「{dept}」這個部門，可用：{'、'.join(self.depts)}")
        self.depts[dept].add(AIEmployee(name, role, duties))

    def order(self, task, dept=None):
        if dept is not None and dept not in self.depts:
            raise ValueError(f"沒有「{dept}」這個部門，可用：{'、'.join(self.depts)}")
        dept = dept or self.route(task)
        print(f"\n▶ 指令：{task}\n  分派至：{dept}部")
        result = self.depts[dept].handle(task)
        print(f"  回覆：{result}")
        return result

    def save_logs(self, path="company_log.json"):
        """把各部門紀錄存成 JSON 檔"""
        data = {name: d.log for name, d in self.depts.items()}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path


if __name__ == "__main__":
    co = AICompany("允文教")
    co.hire("行政", "行政AI-甲", "行政主任", "管理預算、撰寫公文、安排會議")
    co.hire("教學", "教學AI-乙", "課程設計師", "依學生程度設計差異化教材與學習單")
    co.hire("人事", "人事AI-丙", "人事專員", "設計新職位與 AI 員工的角色說明")
    co.hire("輔導", "輔導AI-丁", "輔導員", "依個案需求提出輔導策略並寫紀錄")

    co.order("幫我設計一份二年級的加法補救學習單大綱")
    co.order("寫一則通知家長下週親師座談的公文", dept="行政")
    co.order("小明上課容易分心，請提出三個課堂支持策略", dept="輔導")
