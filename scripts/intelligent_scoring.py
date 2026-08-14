"""
智能风险评分系统（V4.0）
8 维度 1-5 分制：与工作流雷达图、意见书风险总览共用同一套分制。
评分标尺、跨阶段严重程度下限规则见 SKILL.md「风险评分」节。
"""

from typing import Dict, List, Optional
import re


class RiskScoringSystem:
    """风险评分系统 — 8 维度 1-5 分制 + 条款级评分 + 六维度综合"""

    # 8 维度（与 review_config.RADAR_DIMENSIONS 对齐，顺序固定）
    DIMENSIONS = [
        "合同效力与合规性", "价款与支付", "交付与验收", "违约责任",
        "知识产权与保密", "合同解除与终止", "争议解决", "主体授权与担保",
    ]

    # 8 维度权重（合计 1.00）
    DIMENSION_WEIGHTS = {
        "合同效力与合规性": 0.25, "价款与支付": 0.15, "交付与验收": 0.15,
        "违约责任": 0.20, "知识产权与保密": 0.05, "合同解除与终止": 0.10,
        "争议解决": 0.05, "主体授权与担保": 0.05,
    }

    # 评分标尺（1-5，5 为最高风险）
    SCORE_SCALE = {
        1: "条款完整且对我方有利",
        2: "基本完整，轻微不利",
        3: "约定不明或存在风险点",
        4: "明显不利或重要条款缺失",
        5: "效力风险或可能直接导致重大损失",
    }

    def __init__(self):
        self.level_scores = {
            '致命风险': 100, '重要风险': 70, '一般风险': 40, '轻微瑕疵': 10
        }

    # ============ 8 维度 1-5 分制（主路径） ============

    def calculate_dimension_weighted_score(self, radar_data: Dict[str, float]) -> Dict:
        """
        基于 8 维度 1-5 分雷达数据计算加权综合评分。

        Args:
            radar_data: {维度名: 1-5 分}，缺省维度按 1 分计

        Returns:
            comprehensive_score (1-5 加权均值), risk_grade (四级评定),
            dimension_scores (各维度原始分 + 等级标签), 最高风险维度
        """
        dim_scores = {}
        weighted_sum = 0.0
        total_weight = 0.0

        for dim in self.DIMENSIONS:
            score = radar_data.get(dim, 1.0)
            score = max(1.0, min(5.0, float(score)))
            weight = self.DIMENSION_WEIGHTS.get(dim, 0.05)
            dim_scores[dim] = {
                "score": score,
                "label": self._dimension_label(score),
            }
            weighted_sum += score * weight
            total_weight += weight

        # 雷达数据可能含 8 维度之外的键，一并计入（权重取默认 0.05）
        for dim, score in radar_data.items():
            if dim not in dim_scores:
                score = max(1.0, min(5.0, float(score)))
                dim_scores[dim] = {"score": score, "label": self._dimension_label(score)}
                weighted_sum += score * 0.05
                total_weight += 0.05

        comprehensive = weighted_sum / total_weight if total_weight > 0 else 1.0

        highest_dim = max(dim_scores, key=lambda d: dim_scores[d]["score"]) if dim_scores else ""
        return {
            "comprehensive_score": round(comprehensive, 2),   # 1-5 分制
            "risk_grade": self._grade(comprehensive),          # 四级综合评定
            "dimension_scores": dim_scores,
            "highest_risk_dimension": highest_dim,
            "highest_score": dim_scores[highest_dim]["score"] if highest_dim else 1.0,
            "deep_review_required": any(d["score"] >= 4 for d in dim_scores.values()),
        }

    @staticmethod
    def _dimension_label(score: float) -> str:
        """维度分值 → 等级标签（雷达图标注用）"""
        if score >= 4:
            return "严重"
        if score >= 3:
            return "关注"
        if score >= 2:
            return "一般"
        return "良好"

    @staticmethod
    def _grade(avg: float) -> str:
        """综合四级评定（1-5 分制）"""
        if avg >= 4:
            return "极高风险"
        if avg >= 3:
            return "高风险"
        if avg >= 2:
            return "中风险"
        return "低风险"

    def apply_severity_floor(self,
                             initial_scores: Dict[str, float],
                             final_scores: Dict[str, float],
                             downgrade_reasons: Optional[Dict[str, str]] = None) -> Dict:
        """
        跨阶段严重程度下限校验：下游阶段不得无声降级上游评级。

        Args:
            initial_scores: 上游阶段（Step 1 初评）各维度分值
            final_scores: 下游阶段（Step 6 逐条审核后）各维度分值
            downgrade_reasons: 降级理由 {维度: 理由}，无理由的降级视为违规

        Returns:
            {passed, violations: [{dimension, from, to, reason}], adjusted_scores}
        """
        reasons = downgrade_reasons or {}
        violations = []
        adjusted = dict(final_scores)

        for dim, init_score in initial_scores.items():
            final_score = final_scores.get(dim, 1.0)
            if final_score < init_score:
                reason = reasons.get(dim, "").strip()
                if not reason:
                    violations.append({
                        "dimension": dim,
                        "from": init_score,
                        "to": final_score,
                        "reason": "",
                        "action": "已恢复上游评级（无降级理由）",
                    })
                    adjusted[dim] = init_score  # 无声降级 → 恢复上游分值
                else:
                    violations.append({
                        "dimension": dim,
                        "from": init_score,
                        "to": final_score,
                        "reason": reason,
                        "action": "降级已记录理由",
                    })

        return {
            "passed": not any(v["reason"] == "" for v in violations),
            "violations": violations,
            "adjusted_scores": adjusted,
        }

    def generate_radar_chart_data(self, radar_data: Dict[str, float]) -> Dict:
        """生成雷达图结构化数据（docx 图表与 HTML 报告共用）"""
        labels = [d for d in self.DIMENSIONS if d in radar_data] + \
                 [d for d in radar_data if d not in self.DIMENSIONS]
        data = [radar_data.get(d, 1.0) for d in labels]
        return {
            "labels": labels,
            "datasets": [{"label": "风险评分", "data": data}],
            "max": 5,
            "risk_levels": {d: self._dimension_label(radar_data.get(d, 1.0)) for d in labels},
        }

    # ============ 条款级评分 ============

    def calculate_clause_risk_score(self,
                                    clause_text: str,
                                    clause_type: str,
                                    contract_type: str) -> Dict:
        """
        计算单个条款的风险评分

        Args:
            clause_text: 条款文本
            clause_type: 条款类型
            contract_type: 合同类型

        Returns:
            条款评分结果
        """
        score = 0
        issues = []

        # 检查0: 占位符空白（硬性规则——必备条款留空不得判合规）
        if self._is_placeholder(clause_text):
            score += 50
            issues.append('条款内容为占位符/空白，必备条款缺失实质约定')

        # 检查1: 明确性
        if self._is_vague(clause_text):
            score += 30
            issues.append('条款表述模糊,缺乏明确标准')

        # 检查2: 完整性
        if not self._has_key_elements(clause_text, clause_type):
            score += 40
            issues.append('条款缺少关键要素')

        # 检查3: 平衡性
        if not self._is_balanced(clause_text):
            score += 20
            issues.append('权利义务不平衡')

        # 检查4: 可执行性
        if not self._is_executable(clause_text):
            score += 25
            issues.append('缺乏可操作性')

        # 确定风险等级
        if score >= 80:
            level = '致命风险'
        elif score >= 50:
            level = '重要风险'
        elif score >= 20:
            level = '一般风险'
        else:
            level = '轻微瑕疵'

        return {
            'score': score,
            'level': level,
            'issues': issues,
            'suggestion': self._generate_clause_suggestion(clause_type, issues)
        }

    @staticmethod
    def _is_placeholder(text: str) -> bool:
        """检测占位符空白（必备条款留空）"""
        stripped = text.strip()
        placeholder_patterns = [
            r'_{3,}',                    # 空白线 ____
            r'【\s*】',                   # 空书名号占位
            r'\[\s*(待填|待定|待确认|待补充)\s*\]',
            r'（\s*(待填|待定|待确认|待补充)\s*）',
            r'详见附件(?!.*[。；])',      # 裸"详见附件"无后续约定
            r'^\s*(待填|待定|待确认|待补充|N/?A|TBD)\s*$',
        ]
        return any(re.search(p, stripped) for p in placeholder_patterns)

    def _is_vague(self, text: str) -> bool:
        """检查是否模糊"""
        vague_patterns = ['合理', '尽快', '适当', '相关', '等']
        return any(pattern in text for pattern in vague_patterns)

    def _has_key_elements(self, text: str, clause_type: str) -> bool:
        """检查是否包含关键要素"""
        key_elements = {
            '标的': ['名称', '规格', '数量'],
            '价款': ['金额', '币种', '支付方式'],
            '履行': ['时间', '地点', '方式'],
            '违约责任': ['违约金', '赔偿', '计算方式']
        }

        required = key_elements.get(clause_type, [])
        found = sum(1 for elem in required if elem in text)

        return found >= len(required) / 2  # 至少包含一半要素

    def _is_balanced(self, text: str) -> bool:
        """检查是否平衡"""
        # 简化检查: 是否同时约束双方
        has_party_a = '甲方' in text
        has_party_b = '乙方' in text
        return has_party_a and has_party_b

    def _is_executable(self, text: str) -> bool:
        """检查是否可执行"""
        # 检查是否有具体的时间、金额、标准
        has_time = bool(re.search(r'\d+[年月天周小时]', text))
        has_amount = bool(re.search(r'\d+[元万元]', text))
        has_standard = '标准' in text or '规格' in text

        return has_time or has_amount or has_standard

    def _generate_clause_suggestion(self, clause_type: str, issues: List[str]) -> str:
        """生成条款建议"""
        suggestions = {
            '标的': '建议明确标的物的名称、规格、数量、质量标准等关键信息',
            '价款': '建议明确金额、币种、支付时间、支付方式等',
            '履行': '建议明确履行时间、地点、方式、验收标准等',
            '违约责任': '建议明确违约情形、违约金计算方式、赔偿范围等'
        }

        base = suggestions.get(clause_type, '建议完善条款内容')

        if '占位符' in str(issues):
            base = '条款留空，必须在签署前填写完整；' + base
        if '模糊' in str(issues):
            base += '，避免使用模糊表述'
        if '不平衡' in str(issues):
            base += '，注意权利义务对等'

        return base

    # ============ 六维度综合 ============

    def calculate_six_dimension_composite(self, risks_with_dimensions):
        """汇总所有风险的六维度评价"""
        composite = {dim: {"count": 0, "highest_severity": "轻微瑕疵"}
                     for dim in ["风险定性", "风险敞口", "发生概率", "可规避性", "商业权衡", "紧迫性"]}
        sev_order = {"致命风险": 4, "重要风险": 3, "一般风险": 2, "轻微瑕疵": 1}
        for risk in risks_with_dimensions:
            six_dim = risk.get("six_dimensions", {})
            severity = risk.get("risk_type", "一般风险")
            for dim in composite:
                if dim in six_dim:
                    composite[dim]["count"] += 1
                    if sev_order.get(severity, 0) > sev_order.get(composite[dim]["highest_severity"], 0):
                        composite[dim]["highest_severity"] = severity
        return composite


if __name__ == '__main__':
    print("=== 智能风险评分系统测试（V4.0 · 8 维度 1-5 分制）===\n")

    scorer = RiskScoringSystem()

    # 测试 8 维度评分
    radar = {
        "合同效力与合规性": 2, "价款与支付": 4, "交付与验收": 3,
        "违约责任": 5, "知识产权与保密": 1, "合同解除与终止": 3,
        "争议解决": 2, "主体授权与担保": 4,
    }
    result = scorer.calculate_dimension_weighted_score(radar)
    print(f"综合评分: {result['comprehensive_score']}/5")
    print(f"综合评定: {result['risk_grade']}")
    print(f"最高风险维度: {result['highest_risk_dimension']} ({result['highest_score']}分)")
    print(f"需律师深度审阅: {'是' if result['deep_review_required'] else '否'}")

    # 测试跨阶段严重程度下限
    print("\n=== 严重程度下限校验 ===")
    initial = {"违约责任": 5, "价款与支付": 4}
    final = {"违约责任": 2, "价款与支付": 4}
    floor = scorer.apply_severity_floor(initial, final, downgrade_reasons={})
    print(f"通过: {floor['passed']}")
    for v in floor["violations"]:
        print(f"  {v['dimension']}: {v['from']}→{v['to']} ({v['action']})")

    # 测试占位符检测
    print("\n=== 条款评分（占位符检测）===")
    r1 = scorer.calculate_clause_risk_score("交付时间：____", '履行', '买卖合同')
    print(f"空白条款: {r1['score']}分 {r1['level']} — {r1['issues']}")
    r2 = scorer.calculate_clause_risk_score("甲方应于2026年3月1日前在甲方仓库交付100台设备。", '履行', '买卖合同')
    print(f"正常条款: {r2['score']}分 {r2['level']}")
