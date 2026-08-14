"""
修订方式路由模块（V4.0）
修订动作 5 分类：replace / insert / delete / comment / report-only
兼容字段 method：track_changes（replace/insert/delete）| comment | report_only
"""
import csv
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class RevisionDecision:
    """修订方式决策结果"""
    method: str   # "track_changes" | "comment" | "report_only"（向后兼容）
    reasoning: str
    override_allowed: bool = True
    action: str = "comment"  # "replace" | "insert" | "delete" | "comment" | "report-only"


# action → method 映射（兼容旧调用方）
ACTION_TO_METHOD = {
    "replace": "track_changes",
    "insert": "track_changes",
    "delete": "track_changes",
    "comment": "comment",
    "report-only": "report_only",
}


class RevisionRouter:
    """修订方式路由器 — 5 分类动作 + 决策树 + 4 问自检"""

    # 文本类问题 → replace（错别字等）
    TYPO_PATTERNS = [
        '错别字/笔误', '标点错误', '日期格式错误', '法律名称过时',
        '银行名称或公司名称错误', '文字与格式'
    ]

    # 前后不一致/明显不利且可直接改写 → replace
    REPLACE_PATTERNS = [
        '前后不一致', '表述冲突', '引用错误', '编号错误'
    ]

    # 常用条款缺失 → insert（默认 Track Changes 补充）
    AUTO_INSERT_CLAUSES = [
        '实现债权费用条款缺失', '送达确认条款缺失', '签章生效条款不完整',
        '声明与保证条款缺失', '限制收款方式条款缺失', '反商业贿赂条款缺失',
        '独立关系声明缺失', '一人公司补充条款缺失'
    ]

    # 重复冗余 → delete
    DELETE_PATTERNS = [
        '重复表述', '冗余条款', '重复约定', '多余条款'
    ]

    # 商业判断/多方案 → comment
    COMMENT_ISSUES = [
        '条款矛盾或文本不一致', '验收标准重构', '违约金数额调整',
        '知识产权归属重大调整', '付款比例调整', '默示同意条款修改',
        '事实待核实', '多方案需客户选择'
    ]

    # 整体观察 → report-only（仅意见书）
    REPORT_ONLY_PATTERNS = [
        '整体框架观察', '交易结构提示', '商业环境提示', '行业惯例提示'
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

    def _decide(self, action: str, reasoning: str, override_allowed: bool = True) -> RevisionDecision:
        return RevisionDecision(
            method=ACTION_TO_METHOD[action],
            reasoning=reasoning,
            override_allowed=override_allowed,
            action=action,
        )

    def determine_revision_method(self, issue_type: str, clause_context: Optional[Dict] = None,
                                  client_config=None) -> RevisionDecision:
        """
        根据问题类型和上下文确定修订动作（5 分类）

        Args:
            issue_type: 问题类型（对齐路由表中的 issue_type）
            clause_context: 条款上下文（可选）
            client_config: 客户配置（可选，用于覆盖默认路由）

        Returns:
            RevisionDecision（action 为 5 分类之一，method 为兼容字段）
        """
        # 1. 查询路由表（含 action 列）
        for rule in self.routing_table:
            if rule['issue_type'] == issue_type:
                action = rule.get('action') or (
                    'insert' if '缺失' in issue_type or '不完整' in issue_type
                    else 'replace' if rule['default_method'] == 'track_changes'
                    else 'comment')
                return self._decide(
                    action,
                    f"路由表规则: {issue_type} → {action}",
                    rule.get('auto_applicable', 'True') == 'True'
                )

        # 2. 模式匹配
        if any(p in issue_type for p in self.REPORT_ONLY_PATTERNS):
            return self._decide("report-only", "整体观察/框架提示 → 仅写入意见书", False)
        if any(p in issue_type for p in self.TYPO_PATTERNS):
            return self._decide("replace", "文本类问题 → Track Changes 替换")
        if any(p in issue_type for p in self.DELETE_PATTERNS):
            return self._decide("delete", "重复冗余 → Track Changes 删除")
        if any(p in issue_type for p in self.REPLACE_PATTERNS):
            return self._decide("replace", "不一致/错误 → Track Changes 替换")
        if any(p in issue_type for p in self.AUTO_INSERT_CLAUSES):
            return self._decide("insert", "常用条款缺失 → Track Changes 插入补充")
        if any(p in issue_type for p in self.COMMENT_ISSUES):
            return self._decide("comment", "涉及商业判断或多方案 → Comments", False)

        # 3. 运行 4 问自检
        return self._self_check_4_questions(issue_type, clause_context)

    def _self_check_4_questions(self, issue_type: str, clause_context: Optional[Dict] = None) -> RevisionDecision:
        """4 问自检清单"""
        # Q1: 我能替客户直接改吗？
        if clause_context and clause_context.get('auto_fixable'):
            return self._decide("replace", "Q1: 可直接修改 → replace")

        # Q2: 涉及商业判断吗？
        commercial_keywords = ['价款', '付款', '价格', '金额', '补偿', '违约金', '赔偿',
                               '验收标准', '知识产权归属', '回购', '优先']
        if any(kw in issue_type for kw in commercial_keywords):
            return self._decide("comment", "Q2: 涉及商业判断 → Comments", False)

        # Q3: 对方大概率会接受吗？
        if any(kw in issue_type for kw in ['缺失', '不完整', '未约定']):
            return self._decide("insert", "Q3: 缺失补充对方大概率接受 → insert（需告知客户）")
        if any(kw in issue_type for kw in ['笔误', '格式', '错别字']):
            return self._decide("replace", "Q3: 文本修正对方大概率接受 → replace")

        # Q4: 有多个合理方案吗？
        multi_option_keywords = ['调整', '重构', '选择', '方案']
        if any(kw in issue_type for kw in multi_option_keywords):
            return self._decide("comment", "Q4: 多方案 → Comments，列出方案", False)

        # 默认保守：Comments
        return self._decide("comment", "默认保守策略 → Comments，待客户确认", False)

    def get_default_routing(self) -> Dict[str, str]:
        """获取常用条款默认路由表（8 条 insert）"""
        return {clause: "insert" for clause in self.AUTO_INSERT_CLAUSES}

    def validate_routing_decisions(self, decisions: List[Dict]) -> List[str]:
        """
        违规自检：应 Track Changes（insert/replace/delete）却降级为 Comments 的情况

        Args:
            decisions: [{issue_type: str, method: str 或 action: str}, ...]

        Returns:
            违规列表（空列表表示无违规）
        """
        violations = []
        for d in decisions:
            issue = d.get('issue_type', '')
            actual = d.get('action') or d.get('method', '')
            # 应 insert 的常用条款被降级
            if any(c in issue for c in self.AUTO_INSERT_CLAUSES) and actual in ('comment', 'comments'):
                violations.append(f"路由错误: '{issue}' 应 insert（Track Changes），实际为 Comments")
            # 文本类问题被降级
            if any(p in issue for p in self.TYPO_PATTERNS) and actual in ('comment', 'comments'):
                violations.append(f"路由错误: '{issue}' 应 replace（Track Changes），实际为 Comments")
        return violations

    def is_auto_insert_clause(self, issue_type: str) -> bool:
        """检查是否为可自动插入的常用条款"""
        return any(clause in issue_type for clause in self.AUTO_INSERT_CLAUSES)


if __name__ == '__main__':
    router = RevisionRouter(str(Path(__file__).parent.parent / "data"))

    test_cases = [
        "错别字/笔误",
        "实现债权费用条款缺失",
        "重复表述",
        "违约金数额调整",
        "整体框架观察",
        "条款矛盾或文本不一致",
        "事实待核实",
        "未知问题类型-付款节点",
    ]
    for tc in test_cases:
        d = router.determine_revision_method(tc)
        print(f"  {tc}: action={d.action} method={d.method} ({d.reasoning})")

    print(f"\n违规自检: {router.validate_routing_decisions([{'issue_type': '送达确认条款缺失', 'method': 'comment'}])}")
