"""
审核配置模块
根据用户选择配置审核深度，支持客户规则和工作区配置
"""

import csv
import os
from pathlib import Path
from typing import Dict, List, Optional


class ClientConfig:
    """客户专属配置"""

    def __init__(self, client_name: str = "", associated_entities: List[str] = None,
                 preferred_clauses: Dict[str, str] = None, review_focus: List[str] = None,
                 risk_tolerance: str = "moderate"):
        self.client_name = client_name
        self.associated_entities = associated_entities or []
        self.preferred_clauses = preferred_clauses or {}
        self.review_focus = review_focus or []
        self.risk_tolerance = risk_tolerance  # conservative / moderate / aggressive

    @classmethod
    def load_from_workspace(cls, workspace_path: str, client_name: str) -> Optional["ClientConfig"]:
        """从工作区客户规则文件加载配置，只提取结构化字段，不嵌入原文"""
        client_rules_dir = Path(workspace_path) / ".claude" / "client-rules"
        rule_file = client_rules_dir / f"{client_name}.md"
        if not rule_file.exists():
            return None
        config = cls(client_name=client_name)
        try:
            with open(rule_file, "r", encoding="utf-8") as f:
                content = f.read()
            # 提取关联主体列表
            import re
            entity_match = re.search(r'关联主体[：:]\s*(.+?)(?:\n|$)', content)
            if entity_match:
                config.associated_entities = [e.strip() for e in entity_match.group(1).split('、') if e.strip()]
            # 提取审查重点
            focus_match = re.search(r'重点审查条款[：:]\s*(.+?)(?:\n|$)', content)
            if focus_match:
                config.review_focus = [f.strip() for f in focus_match.group(1).split('、') if f.strip()]
            # 提取风险容忍度
            if '保守' in content:
                config.risk_tolerance = 'conservative'
            elif '激进' in content:
                config.risk_tolerance = 'aggressive'
        except Exception:
            pass
        return config

    def match_entity(self, entity_name: str) -> bool:
        """检查实体名称是否匹配关联主体"""
        return any(e in entity_name or entity_name in e for e in self.associated_entities)


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
            'clauses_to_review': 'all',
            'detail_level': '详细'
        }
    }

    # 8 审查维度
    RADAR_DIMENSIONS = [
        "合同效力与合规性", "价款与支付", "交付与验收", "违约责任",
        "知识产权与保密", "合同解除与终止", "争议解决", "主体授权与担保"
    ]

    # 门禁开关
    GATES = ["gate_validity", "gate_subject", "gate_clause", "gate_consistency", "gate_output"]

    def __init__(self, depth: str = 'standard', client_config: Optional[ClientConfig] = None,
                 workspace_path: Optional[str] = None, author: str = "陈石律师【海泰所】",
                 initials: str = "CS"):
        if depth not in self.DEPTH_LEVELS:
            raise ValueError(f"无效的审核深度: {depth}，必须是 'quick', 'standard', 或 'deep'")
        self.depth = depth
        self.config = self.DEPTH_LEVELS[depth]
        self.client_config = client_config
        self.workspace_path = workspace_path
        self.author = author
        self.initials = initials
        self._risk_labels = None
        self._revision_routing = None

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

    def get_clause_library_path(self) -> Optional[str]:
        """获取条款库路径（优先工作区，降级为 skill 数据）"""
        if self.workspace_path:
            lib = Path(self.workspace_path) / ".claude" / "clauses"
            if lib.exists():
                return str(lib)
        return None

    def load_risk_labels(self, data_dir: str) -> List[Dict]:
        """加载风险标签"""
        if self._risk_labels is None:
            path = Path(data_dir) / "risk_labels.csv"
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    self._risk_labels = list(csv.DictReader(f))
        return self._risk_labels or []

    def load_revision_routing(self, data_dir: str) -> List[Dict]:
        """加载修订方式路由表"""
        if self._revision_routing is None:
            path = Path(data_dir) / "revision_routing.csv"
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    self._revision_routing = list(csv.DictReader(f))
        return self._revision_routing or []

    def is_gate_enabled(self, gate_name: str) -> bool:
        """检查门禁是否启用"""
        return gate_name in self.GATES

    def get_radar_dimensions(self) -> List[str]:
        """获取审查维度列表"""
        return self.RADAR_DIMENSIONS

    def __repr__(self) -> str:
        client = f", client={self.client_config.client_name}" if self.client_config else ""
        return f"ReviewConfig(depth={self.depth}, name={self.config['name']}{client})"


if __name__ == '__main__':
    # 测试代码
    print("=== 审核配置模块测试 ===\n")

    for depth in ['quick', 'standard', 'deep']:
        config = ReviewConfig(depth)
        print(f"{config}")
        print(f"  关注: {config.config['focus']}")
        print(f"  维度: {config.get_radar_dimensions()}")
        print(f"  门禁: {config.GATES}")
        print()

    # 测试客户配置加载
    print("=== 客户配置测试 ===")
    ws = "/Users/CS/Trae/个人工作/合同审核"
    cc = ClientConfig.load_from_workspace(ws, "示例客户")
    if cc:
        print(f"客户: {cc.client_name}")
        print(f"关联主体: {cc.associated_entities}")
        print(f"审查重点: {cc.review_focus}")
    else:
        print("未找到客户规则（预期：示例客户规则存在但敏感信息不入库）")

    # 测试含客户配置的 ReviewConfig
    config = ReviewConfig('standard', client_config=cc, workspace_path=ws)
    print(f"\n{config}")
    print(f"  条款库路径: {config.get_clause_library_path()}")
