# AI 公司（多部門 Claude agent）

四個部門：行政、教學、人事、輔導，每位員工都是一個 Claude agent。

```
老闆下指令 → 分派 AI（Haiku）判斷部門 → 部門員工（Sonnet）執行 → 寫進部門紀錄
```

## 使用

```bash
pip install anthropic
export ANTHROPIC_API_KEY=你的金鑰   # 不設定則以「模擬模式」執行
python ai_company/ai_company.py
```

## 擴充

```python
co = AICompany("允文教")
co.hire("教學", "教學AI-戊", "國語科教師", "設計閱讀理解題組")  # 同部門多位員工會輪流接案
co.order("出五題三年級閱讀測驗")             # 自動分派
co.order("排下週會議時間", dept="行政")       # 指定部門
co.save_logs("company_log.json")              # 匯出各部門紀錄
```
