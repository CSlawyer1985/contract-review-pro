"""
修订方式路由模块
决策树 + 4问自检，确定每个审核发现应用 Track Changes 还是 Comments
"""
import csv
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class RevisionDecision:
    """修订方式决策结果"""
    method: str  # "track_changes" | "comment"
    reasoning: str
    override_allowed: bool = True


class RevisionRouter:
    """修订方式路由器 — 编码工作区路由决策树"""

    # 可直接 Track Changes 的问题类型（错别字等）
    TYPO_PATTERNS = [
        '错别字/笔误', '标点错误', '日期格式错误', '法律名称过时',
        '银行名称或公司名称错误', '文字与格式'
    ]

    # 常用条款默认 Track Changes 补充
    AUTO_INSERT_CLAUSES = [
        '实现债权费用条款缺失', '送达确认条款缺失', '签章生效条款不完整',
        '声明与保证条款缺失', '限制收款方式条款缺失', '反商业贿赂条款缺失',
        '独立关系声明缺失', '一人公司补充条款缺失'
    ]

    # Comment 类问题
    COMMENT_ISSUES = [
        '条款矛盾或文本不一致', '验收标准重构', '违约金数额调整',
        '知识产权归属重大调整', '付款比例调整', '默示同意条款修改',
        '事实待核实', '多方案需客户选择'
    ]

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.routing_table = self._load_routing_table()

    def _load_routing_table(self) -> List[Dict]:
        path = self.data_dir / "revision_routing.csv"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return list(csv.DictReader(f))
        return []

    def determine_revision_method(self, issue_type: str, clause_context: Optional[Dict] = None,
                                  client_config=None) -> RevisionDecision:
        """
        根据问题类型和上下文确定修订方式

        Args:
            issue_type: 问题类型（对齐路由表中的 issue_type）
            clause_context: 条款上下文（可选）
            client_config: 客户配置（可选，用于覆盖默认路由）

        Returns:
            RevisionDecision 包含 method 和 reasoning
        """
        # 1. 查询路由表
        for rule in self.routing_table:
            if rule['issue_type'] == issue_type:
                method = rule['default_method']
                # 客户规则可以覆盖
                if client_config and client_config.risk_tolerance == 'aggressive' and method == 'comment':
                    # 激进客户可能希望更多直接修订
                    pass  # 保持原决定
                return RevisionDecision(
                    method=method,
                    reasoning=f"路由表规则: {issue_type} → {method}",
                    override_allowed=rule.get('auto_applicable', 'True') == 'True'
                )

        # 2. 模糊匹配
        if any(p in issue_type for p in self.TYPO_PATTERNS):
            return RevisionDecision(method="track_changes", reasoning="错别字/格式类问题 → Track Changes")
        if any(p in issue_type for p in self.AUTO_INSERT_CLAUSES):
            return RevisionDecision(method="track_changes", reasoning="常用条款缺失 → Track Changes 自动补充")
        if any(p in issue_type for p in self.COMMENT_ISSUES):
            return RevisionDecision(method="comment", reasoning="涉及商业判断或多方案 → Comments")

        # 3. 运行 4 问自检
        return self._self_check_4_questions(issue_type, clause_context)

    def _self_check_4_questions(self, issue_type: str, clause_context: Optional[Dict] = None) -> RevisionDecision:
        """4 问自检清单"""
        # Q1: 我能替客户直接改吗？
        if clause_context and clause_context.get('auto_fixable'):
            return RevisionDecision(method="track_changes", reasoning="Q1: 可直接修改")

        # Q2: 涉及商业判断吗？
        commercial_keywords = ['价款', '付款', '价格', '金额', '补偿', '违约金', '赔偿',
                               '验收标准', '知识产权归属', '回购', '优先']
        if any(kw in issue_type for kw in commercial_keywords):
            return RevisionDecision(method="comment", reasoning="Q2: 涉及商业判断 → Comments")

        # Q3: 对方大概率会接受吗？
        acceptable_patterns = ['缺失', '不完整', '未约定', '笔误', '格式', '错别字']
        if any(kw in issue_type for kw in acceptable_patterns):
            return RevisionDecision(method="track_changes",
                                    reasoning="Q3: 对方大概率接受 → Track Changes（需告知客户）",
                                    override_allowed=True)

        # Q4: 有多个合理方案吗？
        multi_option_keywords = ['调整', '重构', '选择', '方案']
        if any(kw in issue_type for kw in multi_option_keywords):
            return RevisionDecision(method="comment", reasoning="Q4: 多方案 → Comments，列出方案")

        # 默认保守：Comments
        return RevisionDecision(method="comment", reasoning="默认保守策略 → Comments，待客户确认")

    def get_default_routing(self) -> Dict[str, str]:
        """获取常用条款默认路由表（8条 Track Changes 默认补充）"""
        return {clause: "track_changes" for clause in self.AUTO_INSERT_CLAUSES}

    def validate_routing_decisions(self, decisions: List[Dict]) -> List[str]:
        """
        违规自检：检查是否有应 Track Changes 但降级为 Comments 的情况

        Args:
            decisions: [{issue_type: str, method: str}, ...]

        Returns:
            违规列表（空列表表示无违规）
        """
        violations = []
        for d in decisions:
            issue = d.get('issue_type', '')
            method = d.get('method', '')
            # 检查常用条款是否被错误降级
            if any(clause in issue for clause in self.AUTO_INSERT_CLAUSES) and method == 'comment':
                violations.append(f"路由错误: '{issue}' 应使用 Track Changes，实际使用 Comments")
        return violations

    def is_auto_insert_clause(self, issue_type: str) -> bool:
        """检查是否为可自动插入的常用条款"""
        return any(clause in issue_type for clause in self.AUTO_INSERT_CLAUSES)


if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    router = RevisionRouter(str(Path(__file__).parent.parent / "data"))

    test_cases = [
        "错别字/笔误",
        "实现债权费用条款缺失",
        "违约金数额调整",
        "条款矛盾或文本不一致",
        "送达确认条款缺失",
        "事实待核实",
        "未知问题类型-付款节点",
    ]
    for tc in test_cases:
        decision = router.determine_revision_method(tc)
        print(f"  {tc}: {decision.method} ({decision.reasoning})")

    print(f"\n默认路由表: {router.get_default_routing()}")
