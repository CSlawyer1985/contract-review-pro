"""
条款审核模块
审核合同条款并提出修改建议
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional


class ClauseReviewer:
    """条款审核器"""

    def __init__(self, data_dir: str):
        """
        初始化条款审核器

        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = Path(data_dir)
        self.clause_standards = self._load_clause_standards()

    def _load_clause_standards(self) -> pd.DataFrame:
        """加载标准条款数据"""
        file_path = self.data_dir / 'clause_standards.csv'
        return pd.read_csv(file_path, encoding='utf-8')

    def review_clause(self, clause_text: str, clause_type: str, contract_type: str) -> Dict:
        """
        审核单个条款

        Args:
            clause_text: 条款文本
            clause_type: 条款类型
            contract_type: 合同类型

        Returns:
            审核结果
        """
        # 查找标准条款模板
        standards = self.clause_standards[
            self.clause_standards['clause_type'].str.contains(clause_type, case=False, na=False) &
            (self.clause_standards['contract_type'].str.contains(contract_type, case=False, na=False) |
             self.clause_standards['contract_type'] == '通用')
        ]

        issues = []
        suggestions = []

        if not standards.empty:
            standard = standards.iloc[0]

            # 检查关键要素
            key_elements = standard['key_elements'].split('、')
            for element in key_elements:
                if element not in clause_text:
                    issues.append(f"缺少关键要素: {element}")

            # 生成修改建议
            if issues:
                suggestions.append({
                    'issue': '、'.join(issues),
                    'suggestion': f"建议参考标准模板：{standard['standard_template']}",
                    'standard_template': standard['standard_template']
                })

        return {
            'clause_type': clause_type,
            'issues': issues,
            'suggestions': suggestions,
            'has_issues': len(issues) > 0
        }

    def generate_revised_clause(self, original_clause: str, suggestions: List[Dict]) -> str:
        """
        生成修订后的条款

        Args:
            original_clause: 原始条款
            suggestions: 修改建议列表

        Returns:
            修订后的条款
        """
        if not suggestions:
            return original_clause

        # 使用第一个建议的标准模板（简化版）
        if suggestions and 'standard_template' in suggestions[0]:
            return suggestions[0]['standard_template']

        return original_clause
