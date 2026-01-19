"""
智能风险评分系统
V1.2: 多维度风险评估与评分
"""

from typing import Dict, List
import re


class RiskScoringSystem:
    """风险评分系统"""

    def __init__(self):
        """初始化评分系统"""
        # 风险权重配置
        self.weight_config = {
            'commercial_risk': 0.3,      # 商业风险权重
            'legal_risk': 0.4,          # 法律风险权重
            'practical_risk': 0.3       # 实务风险权重
        }

        # 风险等级评分映射
        self.level_scores = {
            '致命风险': 100,
            '重要风险': 70,
            '一般风险': 40,
            '轻微瑕疵': 10
        }

    def calculate_comprehensive_risk_score(self,
                                           commercial_analysis: Dict,
                                           legal_analysis: Dict,
                                           practical_analysis: Dict) -> Dict:
        """
        计算综合风险评分

        Args:
            commercial_analysis: 商业维度分析结果
            legal_analysis: 法律维度分析结果
            practical_analysis: 实务维度分析结果

        Returns:
            综合评分报告
        """
        # 计算各维度评分
        commercial_score = self._calculate_dimension_score(commercial_analysis)
        legal_score = self._calculate_dimension_score(legal_analysis)
        practical_score = self._calculate_dimension_score(practical_analysis)

        # 加权综合评分
        comprehensive_score = (
            commercial_score * self.weight_config['commercial_risk'] +
            legal_score * self.weight_config['legal_risk'] +
            practical_score * self.weight_config['practical_risk']
        )

        # 确定风险等级
        risk_level = self._determine_risk_level(comprehensive_score)

        # 生成建议
        recommendations = self._generate_recommendations(
            commercial_analysis, legal_analysis, practical_analysis
        )

        return {
            'comprehensive_score': round(comprehensive_score, 2),
            'risk_level': risk_level,
            'dimension_scores': {
                'commercial': round(commercial_score, 2),
                'legal': round(legal_score, 2),
                'practical': round(practical_score, 2)
            },
            'risk_distribution': self._analyze_risk_distribution(
                commercial_analysis, legal_analysis, practical_analysis
            ),
            'recommendations': recommendations,
            'key_risks': self._identify_key_risks(
                commercial_analysis, legal_analysis, practical_analysis
            )
        }

    def _calculate_dimension_score(self, analysis: Dict) -> float:
        """计算单维度评分"""
        base_score = 50.0  # 基础分

        # 根据风险数量调整评分
        risks = analysis.get('risks', [])
        for risk in risks:
            level = risk.get('level', '一般风险')
            score = self.level_scores.get(level, 40)
            base_score += score * 0.3

        # 根据发现数量调整评分(发现多说明审核仔细)
        findings = len(analysis.get('findings', []))
        base_score -= findings * 2

        # 限制评分范围 0-100
        return max(0, min(100, base_score))

    def _determine_risk_level(self, score: float) -> str:
        """根据评分确定风险等级"""
        if score >= 80:
            return '高风险'
        elif score >= 60:
            return '中等风险'
        elif score >= 40:
            return '低风险'
        else:
            return '极低风险'

    def _analyze_risk_distribution(self, *analyses: Dict) -> Dict:
        """分析风险分布"""
        distribution = {
            '致命风险': 0,
            '重要风险': 0,
            '一般风险': 0,
            '轻微瑕疵': 0
        }

        for analysis in analyses:
            for risk in analysis.get('risks', []):
                level = risk.get('level', '一般风险')
                if level in distribution:
                    distribution[level] += 1

        return distribution

    def _identify_key_risks(self, *analyses: Dict) -> List[Dict]:
        """识别关键风险(致命+重要)"""
        key_risks = []

        for analysis in analyses:
            for risk in analysis.get('risks', []):
                level = risk.get('level', '')
                if level in ['致命风险', '重要风险']:
                    key_risks.append({
                        'dimension': analysis.get('dimension', '未知'),
                        'type': risk.get('risk_type', '未知'),
                        'description': risk.get('description', ''),
                        'level': level,
                        'suggestion': risk.get('suggestion', '')
                    })

        # 按风险等级排序
        key_risks.sort(key=lambda x: self.level_scores.get(x['level'], 0), reverse=True)

        return key_risks

    def _generate_recommendations(self, *analyses: Dict) -> List[str]:
        """生成综合建议"""
        recommendations = []

        for analysis in analyses:
            dimension = analysis.get('dimension', '')
            rating = analysis.get('rating', '')

            # 根据维度和评级生成建议
            if dimension == '商业维度':
                if rating in ['较差', '差']:
                    recommendations.append(
                        f"⚠️ {dimension}: 商业风险较高,建议重新评估交易结构"
                    )
                elif rating == '中等':
                    recommendations.append(
                        f"ℹ️ {dimension}: 建议关注商业条款的合理性"
                    )

            elif dimension == '法律维度':
                fatal_risks = [r for r in analysis.get('risks', []) if r.get('level') == '致命风险']
                if fatal_risks:
                    recommendations.append(
                        f"🚨 {dimension}: 发现{len(fatal_risks)}个致命风险,必须修改"
                    )

            elif dimension == '实务维度':
                vague_terms = any('模糊' in r.get('description', '') for r in analysis.get('risks', []))
                if vague_terms:
                    recommendations.append(
                        f"💡 {dimension}: 建议明确模糊表述,提高可执行性"
                    )

        return recommendations

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

        if '模糊' in str(issues):
            base += '，避免使用模糊表述'
        if '不平衡' in str(issues):
            base += '，注意权利义务对等'

        return base


if __name__ == '__main__':
    # 测试代码
    print("=== 智能风险评分系统测试 ===\n")

    scorer = RiskScoringSystem()

    # 模拟分析结果
    commercial = {
        'dimension': '商业维度',
        'rating': '中等',
        'risks': [
            {'level': '重要风险', 'risk_type': '市场地位', 'description': '处于弱势'}
        ],
        'findings': [{'category': '主体', 'content': 'A公司'}]
    }

    legal = {
        'dimension': '法律维度',
        'rating': '良好',
        'risks': [
            {'level': '致命风险', 'risk_type': '条款缺失', 'description': '缺少验收条款'}
        ],
        'findings': []
    }

    practical = {
        'dimension': '实务维度',
        'rating': '良好',
        'risks': [
            {'level': '一般风险', 'risk_type': '模糊表述', 'description': '使用"合理时间"'}
        ],
        'findings': []
    }

    # 测试综合评分
    print("=== 综合风险评分 ===")
    result = scorer.calculate_comprehensive_risk_score(commercial, legal, practical)
    print(f"综合评分: {result['comprehensive_score']}")
    print(f"风险等级: {result['risk_level']}")
    print(f"\n各维度评分:")
    for dim, score in result['dimension_scores'].items():
        print(f"  {dim}: {score}")
    print(f"\n风险分布:")
    for level, count in result['risk_distribution'].items():
        print(f"  {level}: {count}个")
    print(f"\n关键风险:")
    for risk in result['key_risks']:
        print(f"  - [{risk['level']}] {risk['type']}: {risk['description']}")
    print(f"\n建议:")
    for rec in result['recommendations']:
        print(f"  {rec}")

    # 测试条款评分
    print("\n\n=== 条款风险评分 ===")
    clause_result = scorer.calculate_clause_risk_score(
        "甲方应尽快交付产品。",
        '履行',
        '买卖合同'
    )
    print(f"条款评分: {clause_result['score']}")
    print(f"风险等级: {clause_result['level']}")
    print(f"问题: {clause_result['issues']}")
    print(f"建议: {clause_result['suggestion']}")
