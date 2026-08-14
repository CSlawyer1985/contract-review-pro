"""
HTML 可视化报告生成器（V4.0 新增）

生成单文件离线 HTML 审核报告（增强呈现件，不替代 docx 三件套）：
- Chart.js 内联（assets/chart.umd.min.js），断网可开
- 8 维雷达（1-5 分制）、按风险类型的等级分布热力图、条款对比卡、
  风险等级筛选器、综合评定徽章、谈判策略三层标签
- 模板：assets/report_template.html，数据经 {{占位符}} 注入
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

LEVEL_MAP = {"致命风险": "critical", "重要风险": "major",
             "一般风险": "minor", "轻微瑕疵": "trivial"}
GRADE_COLOR = {"极高风险": "#c00000", "高风险": "#c5500b",
               "中风险": "#2e74b5", "低风险": "#64748b"}


class HtmlReportGenerator:
    """渲染 assets/report_template.html 为单文件 HTML 报告"""

    def __init__(self, template_path: Optional[str] = None):
        base = Path(__file__).resolve().parent.parent / "assets"
        self.template_path = Path(template_path) if template_path else base / "report_template.html"
        self.chart_js_path = base / "chart.umd.min.js"

    def generate(self, contract_name: str, analysis_result: Dict, risk_report: Dict,
                 scoring: Optional[Dict] = None, user_context: Optional[Dict] = None,
                 output_dir: Optional[str] = None) -> str:
        """生成 HTML 报告，返回输出路径"""
        scoring = scoring or risk_report.get("scoring", {})
        user_context = user_context or {}
        out_dir = Path(output_dir) if output_dir else Path.cwd()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{contract_name}-审核报告.html"

        template = self.template_path.read_text(encoding="utf-8")
        chart_js = self.chart_js_path.read_text(encoding="utf-8") \
            if self.chart_js_path.exists() else "/* Chart.js missing: assets/chart.umd.min.js */"

        radar_data = risk_report.get("radar_data", {})
        risks_flat = self._flatten_risks(risk_report)

        payload = {
            "{{REPORT_TITLE}}": f"{contract_name} — 合同审核报告",
            "{{CHART_JS_INLINE}}": chart_js,
            "{{CONTRACT_INFO}}": self._js({
                "type": analysis_result.get("identified_type", "未识别"),
                "parties": user_context.get("parties", user_context.get("party", "待确认")),
                "stance": user_context.get("stance", user_context.get("party", "未声明")),
                "review_date": datetime.now().strftime("%Y年%m月%d日"),
            }),
            "{{RADAR_DATA}}": self._js({
                "labels": list(radar_data.keys()),
                "scores": [radar_data[d] for d in radar_data],
                "benchmark": None,
            }),
            "{{RISK_ITEMS}}": self._js(risks_flat),
            "{{COMPARISON_ITEMS}}": self._js(self._comparisons(risks_flat)),
            "{{NEGOTIATION_STRATEGY}}": self._js(self._strategy(user_context)),
            "{{SCORE_CARD}}": self._js(self._score_card(scoring, risk_report)),
            "{{LAW_REFERENCES}}": self._js(self._law_refs(risks_flat)),
            "{{HEATMAP_DATA}}": self._js(self._heatmap(risk_report)),
        }

        html = template
        for key, value in payload.items():
            html = html.replace(key, value)

        out_path.write_text(html, encoding="utf-8")
        print(f"HTML 审核报告已生成: {out_path}")
        return str(out_path)

    # ------------------------------------------------------------------

    @staticmethod
    def _js(obj) -> str:
        """JSON 序列化并防止 </script> 提前闭合"""
        return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")

    @staticmethod
    def _flatten_risks(risk_report: Dict) -> List[Dict]:
        items = []
        for level, mapped in LEVEL_MAP.items():
            for risk in risk_report.get("risks_by_level", {}).get(level, []):
                items.append({
                    "level": mapped,
                    "title": risk.get("description", "")[:40],
                    "description": risk.get("description", ""),
                    "original": risk.get("original_text", "")[:200],
                    "suggestion": risk.get("suggestion", "")[:200],
                    "law_ref": risk.get("legal_basis", ""),
                    "label": risk.get("risk_label", ""),
                    "location": risk.get("location", ""),
                })
        return items

    @staticmethod
    def _comparisons(risks: List[Dict]) -> List[Dict]:
        return [
            {"title": r["title"], "clause_ref": r.get("location", ""),
             "original": r["original"], "suggested": r["suggestion"],
             "reason": r.get("law_ref", "")}
            for r in risks if r.get("original") and r.get("suggestion")
        ]

    @staticmethod
    def _strategy(user_context: Dict) -> Dict:
        nego = user_context.get("negotiation_points") or {}
        items = []
        for t in nego.get("must_win", []):
            items.append({"tactic": t, "priority": "must", "detail": "", "fallback": ""})
        for t in nego.get("should_win", []):
            items.append({"tactic": t, "priority": "should", "detail": "", "fallback": ""})
        for t in nego.get("nice_to_have", []):
            items.append({"tactic": t, "priority": "could", "detail": "", "fallback": ""})
        return {"overview": nego.get("overview", ""), "items": items}

    @staticmethod
    def _score_card(scoring: Dict, risk_report: Dict) -> Dict:
        grade = scoring.get("risk_grade") or "未评定"
        return {
            "overall_grade": grade,
            "overall_score": scoring.get("comprehensive_score", "—"),
            "grade_color": GRADE_COLOR.get(grade, "#64748b"),
        }

    @staticmethod
    def _law_refs(risks: List[Dict]) -> List[Dict]:
        seen, refs = set(), []
        for r in risks:
            basis = (r.get("law_ref") or "").strip()
            if basis and basis not in seen:
                seen.add(basis)
                refs.append({"law": basis, "article": "", "content": ""})
        return refs

    @staticmethod
    def _heatmap(risk_report: Dict) -> Dict:
        """按风险类型标签分行，展示各等级分布"""
        rows: Dict[str, Dict[str, int]] = {}
        for level, mapped in LEVEL_MAP.items():
            for risk in risk_report.get("risks_by_level", {}).get(level, []):
                label = risk.get("risk_label") or "其他"
                row = rows.setdefault(label, {"critical": 0, "major": 0, "minor": 0, "none": 0})
                if mapped in ("critical", "major", "minor"):
                    row[mapped] += 1
        if not rows:
            rows["全文"] = {"critical": 0, "major": 0, "minor": 0, "none": 1}
        return {"sections": list(rows.keys()), "data": list(rows.values())}


if __name__ == "__main__":
    gen = HtmlReportGenerator()
    demo_risk = {
        "radar_data": {"合同效力与合规性": 2, "价款与支付": 4, "交付与验收": 3, "违约责任": 5,
                       "知识产权与保密": 1, "合同解除与终止": 3, "争议解决": 2, "主体授权与担保": 4},
        "risks_by_level": {
            "致命风险": [{"description": "违约金无上限且按日千分之五计算", "location": "第8条",
                           "risk_label": "违约责任", "original_text": "违约方每日按千分之五支付违约金",
                           "suggestion": "设置违约金上限（不超过合同总价款20%）",
                           "legal_basis": "《民法典》第585条"}],
            "重要风险": [{"description": "验收标准不明确", "location": "第5条", "risk_label": "交付与验收",
                           "original_text": "按行业标准验收", "suggestion": "明确具体验收标准和异议期",
                           "legal_basis": "《民法典》第620条"}],
            "一般风险": [{"description": "送达地址未确认", "location": "第12条", "risk_label": "争议解决",
                           "original_text": "", "suggestion": "补充送达确认条款", "legal_basis": ""}],
            "轻微瑕疵": [],
        },
    }
    out = gen.generate(
        "测试买卖合同",
        {"identified_type": "买卖合同"},
        demo_risk,
        scoring={"risk_grade": "高风险", "comprehensive_score": 3.2},
        user_context={"party": "甲方（买受人）",
                      "negotiation_points": {"must_win": ["违约金上限≤总价20%"],
                                              "should_win": ["明确验收标准与异议期"],
                                              "nice_to_have": ["送达确认条款"]}},
        output_dir=".",
    )
    print("OK:", out)
