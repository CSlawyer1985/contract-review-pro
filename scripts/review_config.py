"""
审核配置模块
根据用户选择配置审核深度
"""

from typing import Dict, List, Optional


class ReviewConfig:
    """审核配置"""

    DEPTH_LEVELS = {
        'quick': {
            'name': '快速审核',
            'time_estimate': '5-10分钟',
            'focus': '核心条款和重大风险',
            'check_categories': ['致命风险', '重要风险'],
            'clauses_to_review': ['标的', '价款', '违约责任', '解除条款'],
            'detail_level': '简略'
        },
        'standard': {
            'name': '标准审核',
            'time_estimate': '30-60分钟',
            'focus': '全面审核主要条款',
            'check_categories': ['致命风险', '重要风险', '一般风险'],
            'clauses_to_review': ['标的', '数量质量', '价款', '履行', '违约责任',
                                 '解除终止', '不可抗力', '担保保险', '争议解决'],
            'detail_level': '标准'
        },
        'deep': {
            'name': '深度审核',
            'time_estimate': '1-2小时',
            'focus': '逐条审核所有条款',
            'check_categories': ['致命风险', '重要风险', '一般风险', '轻微瑕疵'],
            'clauses_to_review': 'all',  # 审核所有条款
            'detail_level': '详细'
        }
    }

    def __init__(self, depth: str = 'standard'):
        """
        初始化审核配置

        Args:
            depth: 审核深度 ('quick' | 'standard' | 'deep')
        """
        if depth not in self.DEPTH_LEVELS:
            raise ValueError(f"无效的审核深度: {depth}，必须是 'quick', 'standard', 或 'deep'")

        self.depth = depth
        self.config = self.DEPTH_LEVELS[depth]

    def get_review_scope(self) -> Dict:
        """获取审核范围"""
        return self.config

    def should_check_clause(self, clause_type: str) -> bool:
        """
        判断是否需要审核某类条款

        Args:
            clause_type: 条款类型（如 '标的', '价款' 等）

        Returns:
            是否需要审核该条款
        """
        if self.config['clauses_to_review'] == 'all':
            return True

        # 模糊匹配：如果条款类型包含在审核列表中
        for target_clause in self.config['clauses_to_review']:
            if target_clause in clause_type or clause_type in target_clause:
                return True

        return False

    def should_report_risk(self, risk_level: str) -> bool:
        """
        判断是否需要报告某级风险

        Args:
            risk_level: 风险等级（'致命风险', '重要风险', '一般风险', '轻微瑕疵'）

        Returns:
            是否需要报告该风险
        """
        return risk_level in self.config['check_categories']

    def get_detail_level(self) -> str:
        """获取详细程度"""
        return self.config['detail_level']

    def __repr__(self) -> str:
        return f"ReviewConfig(depth={self.depth}, name={self.config['name']})"


if __name__ == '__main__':
    # 测试代码
    print("=== 审核配置模块测试 ===\n")

    # 测试三种审核深度
    for depth in ['quick', 'standard', 'deep']:
        config = ReviewConfig(depth)
        print(f"{config}")
        print(f"  关注: {config.config['focus']}")
        print(f"  检查风险等级: {config.config['check_categories']}")
        print(f"  审核条款: {config.config['clauses_to_review']}")
        print(f"  详细程度: {config.config['detail_level']}")
        print()

    # 测试条款审核判断
    print("=== 条款审核判断测试 ===\n")
    quick_config = ReviewConfig('quick')
    print(f"快速审核 - 是否审核'标的'条款: {quick_config.should_check_clause('标的')}")
    print(f"快速审核 - 是否审核'保密'条款: {quick_config.should_check_clause('保密')}")

    standard_config = ReviewConfig('standard')
    print(f"标准审核 - 是否审核'标的'条款: {standard_config.should_check_clause('标的')}")
    print(f"标准审核 - 是否审核'保密'条款: {standard_config.should_check_clause('保密')}")

    deep_config = ReviewConfig('deep')
    print(f"深度审核 - 是否审核'标的'条款: {deep_config.should_check_clause('标的')}")
    print(f"深度审核 - 是否审核'保密'条款: {deep_config.should_check_clause('保密')}")

    # 测试风险报告判断
    print("\n=== 风险报告判断测试 ===\n")
    print(f"快速审核 - 是否报告'致命风险': {quick_config.should_report_risk('致命风险')}")
    print(f"快速审核 - 是否报告'一般风险': {quick_config.should_report_risk('一般风险')}")

    print(f"标准审核 - 是否报告'致命风险': {standard_config.should_report_risk('致命风险')}")
    print(f"标准审核 - 是否报告'一般风险': {standard_config.should_report_risk('一般风险')}")

    print(f"深度审核 - 是否报告'致命风险': {deep_config.should_report_risk('致命风险')}")
    print(f"深度审核 - 是否报告'轻微瑕疵': {deep_config.should_report_risk('轻微瑕疵')}")
