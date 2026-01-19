"""
三观四步法深度分析模块
V1.2: 集成三观四步法和三维审查法
"""

from typing import Dict, List
import re


class SanguanAnalysis:
    """三观四步法分析器"""

    def __init__(self):
        """初始化三观分析器"""
        pass

    def analyze_commercial_dimension(self, contract_text: str, user_context: Dict) -> Dict:
        """
        商业维度分析

        核心问题: 这笔交易从商业上是否合理?

        分析要点:
        1. 理解交易本质
        2. 识别商业风险
        3. 评估交易条款的商业合理性
        """
        analysis = {
            'dimension': '商业维度',
            'rating': '中等',  # 优秀/良好/中等/较差/差
            'findings': [],
            'risks': [],
            'suggestions': []
        }

        # 提取商业要素
        parties = self._extract_parties(contract_text)
        price_terms = self._extract_price_terms(contract_text)
        delivery_terms = self._extract_delivery_terms(contract_text)

        # 分析1: 交易本质
        if parties:
            analysis['findings'].append({
                'category': '交易主体',
                'content': f'识别到交易主体: {", ".join(parties)}',
                'significance': '重要'
            })

        # 分析2: 商业合理性
        if user_context.get('position') == '弱势':
            analysis['risks'].append({
                'risk_type': '商业风险',
                'description': '用户处于弱势地位,可能面临不对等条款',
                'level': '重要风险',
                'suggestion': '重点关注权利义务平衡性,必要时要求调整'
            })

        # 分析3: 价格合理性
        if price_terms:
            analysis['findings'].append({
                'category': '价格条款',
                'content': f'价格条款: {price_terms}',
                'significance': '关键'
            })

        # 分析4: 关注点
        focus = user_context.get('focus', '')
        if focus:
            analysis['suggestions'].append({
                'aspect': '用户关注点',
                'content': f'用户关注: {focus},审核时应重点审查相关条款'
            })

        return analysis

    def analyze_legal_dimension(self, contract_text: str, contract_type: str) -> Dict:
        """
        法律维度分析

        核心问题: 从法律上是否有效、完整?

        分析要点:
        1. 合法性审查
        2. 有效性审查
        3. 权利义务平衡性
        """
        analysis = {
            'dimension': '法律维度',
            'rating': '良好',
            'findings': [],
            'risks': [],
            'suggestions': []
        }

        # 检查1: 合同类型合法性
        analysis['findings'].append({
            'category': '合同类型',
            'content': f'识别为: {contract_type}',
            'significance': '基础'
        })

        # 检查2: 必要条款
        essential_clauses = self._check_essential_clauses(contract_text, contract_type)
        if essential_clauses['missing']:
            analysis['risks'].append({
                'risk_type': '致命风险',
                'description': f'缺少必要条款: {", ".join(essential_clauses["missing"])}',
                'level': '致命风险',
                'suggestion': '必须补充,否则合同可能无法履行或产生争议'
            })

        # 检查3: 权利义务平衡
        balance_score = self._assess_balance(contract_text)
        if balance_score < 0.3:
            analysis['risks'].append({
                'risk_type': '重要风险',
                'description': '权利义务严重不平衡',
                'level': '重要风险',
                'suggestion': '建议调整违约责任、解除权等条款,增强平衡性'
            })

        # 检查4: 免责条款
        exemption_clauses = self._find_exemption_clauses(contract_text)
        if exemption_clauses:
            analysis['findings'].append({
                'category': '免责条款',
                'content': f'发现{len(exemption_clauses)}处免责条款',
                'significance': '重要'
            })

        return analysis

    def analyze_practical_dimension(self, contract_text: str) -> Dict:
        """
        实务维度分析

        核心问题: 在实践中是否可执行、可操作?

        分析要点:
        1. 可执行性
        2. 可操作性
        3. 争议预防
        """
        analysis = {
            'dimension': '实务维度',
            'rating': '良好',
            'findings': [],
            'risks': [],
            'suggestions': []
        }

        # 检查1: 条款明确性
        vague_terms = self._find_vague_terms(contract_text)
        if vague_terms:
            analysis['risks'].append({
                'risk_type': '一般风险',
                'description': f'发现{len(vague_terms)}处模糊表述',
                'level': '一般风险',
                'suggestion': '建议明确时间、金额、标准等关键要素'
            })

        # 检查2: 验收标准
        acceptance_clauses = self._find_acceptance_clauses(contract_text)
        if not acceptance_clauses:
            analysis['risks'].append({
                'risk_type': '重要风险',
                'description': '缺少明确的验收标准',
                'level': '重要风险',
                'suggestion': '建议补充具体的验收标准、程序和时间'
            })

        # 检查3: 争议解决
        dispute_clauses = self._find_dispute_clauses(contract_text)
        if dispute_clauses:
            analysis['findings'].append({
                'category': '争议解决',
                'content': f'已约定争议解决方式: {dispute_clauses[0]}',
                'significance': '重要'
            })
        else:
            analysis['risks'].append({
                'risk_type': '一般风险',
                'description': '未约定争议解决方式',
                'level': '一般风险',
                'suggestion': '建议明确约定仲裁或诉讼管辖'
            })

        return analysis

    def apply_sanguan_foursteps(self, contract_text: str, user_context: Dict) -> Dict:
        """
        应用三观四步法

        四步:
        1. 理解交易
        2. 设计结构 (宏观)
        3. 起草合同 (中观)
        4. 审查完善 (微观)
        """
        foursteps_analysis = {
            'method': '三观四步法',
            'steps': []
        }

        # 第一步: 理解交易
        step1 = {
            'step': '第一步: 理解交易',
            'analysis': {
                'commercial_background': self._analyze_commercial_background(contract_text, user_context),
                'key_risks': self._identify_key_commercial_risks(contract_text, user_context),
                'true_intent': self._infer_true_intent(contract_text, user_context)
            }
        }
        foursteps_analysis['steps'].append(step1)

        # 第二步: 设计结构 (宏观)
        step2 = {
            'step': '第二步: 设计结构 (宏观层面)',
            'analysis': {
                'transaction_type': self._determine_transaction_type(contract_text),
                'transaction_path': self._analyze_transaction_path(contract_text),
                'transaction_parties': self._analyze_transaction_parties(contract_text),
                'transaction_timeline': self._analyze_transaction_timeline(contract_text)
            }
        }
        foursteps_analysis['steps'].append(step2)

        # 第三步: 起草合同 (中观)
        step3 = {
            'step': '第三步: 起草合同 (中观层面)',
            'analysis': {
                'contract_form': self._assess_contract_form(contract_text),
                'clause_completeness': self._check_clause_completeness(contract_text),
                'balance_assessment': self._assess_rights_obligations_balance(contract_text)
            }
        }
        foursteps_analysis['steps'].append(step3)

        # 第四步: 审查完善 (微观)
        step4 = {
            'step': '第四步: 审查完善 (微观层面)',
            'analysis': {
                'legality_check': self._legality_review(contract_text),
                'completeness_check': self._completeness_review(contract_text),
                'executability_check': self._executability_review(contract_text)
            }
        }
        foursteps_analysis['steps'].append(step4)

        return foursteps_analysis

    # ============ 辅助方法 ============

    def _extract_parties(self, text: str) -> List[str]:
        """提取合同主体"""
        parties = []
        # 查找甲方、乙方等
        pattern = r'(甲方|乙方|丙方|委托方|受托方)[：:]\s*([^\n]+)'
        matches = re.findall(pattern, text)
        for role, name in matches:
            parties.append(f"{role}: {name.strip()}")
        return parties

    def _extract_price_terms(self, text: str) -> str:
        """提取价格条款"""
        # 查找价款、价格、费用等
        pattern = r'(总价款|价款|价格|费用|报酬)[：:]\s*([^\n]+)'
        matches = re.findall(pattern, text)
        if matches:
            return f"{matches[0][0]}: {matches[0][1].strip()}"
        return ""

    def _extract_delivery_terms(self, text: str) -> str:
        """提取交付/履行条款"""
        pattern = r'(交付|履行|提供)[：:]\s*([^\n]+)'
        matches = re.findall(pattern, text)
        if matches:
            return f"{matches[0][0]}: {matches[0][1].strip()}"
        return ""

    def _check_essential_clauses(self, text: str, contract_type: str) -> Dict:
        """检查必要条款"""
        essential_by_type = {
            '买卖合同': ['标的', '数量', '价款'],
            '租赁合同': ['租赁物', '租金', '租赁期限'],
            '借款合同': ['借款金额', '利率', '还款期限'],
            'default': ['标的', '价款', '履行期限']
        }

        required = essential_by_type.get(contract_type, essential_by_type['default'])
        found = []
        missing = []

        for clause in required:
            if clause in text:
                found.append(clause)
            else:
                missing.append(clause)

        return {'found': found, 'missing': missing}

    def _assess_balance(self, text: str) -> float:
        """评估权利义务平衡性 (0-1, 1表示完全平衡)"""
        # 简化评估: 统计甲方、乙方义务数量
        party_a_obligations = len(re.findall(r'甲方.*?(应|应当|须)', text))
        party_b_obligations = len(re.findall(r'乙方.*?(应|应当|须)', text))

        if party_a_obligations + party_b_obligations == 0:
            return 0.5  # 默认中等平衡

        ratio = min(party_a_obligations, party_b_obligations) / max(party_a_obligations, party_b_obligations)
        return ratio

    def _find_exemption_clauses(self, text: str) -> List[str]:
        """查找免责条款"""
        pattern = r'(免责|不承担.*责任|概不负责)'
        matches = re.findall(pattern, text)
        return matches

    def _find_vague_terms(self, text: str) -> List[str]:
        """查找模糊表述"""
        vague_patterns = [
            r'合理.*时间',
            r'尽快',
            r'适当',
            r'相关',
            r'等(?!.*等.*具体)'
        ]
        vague_found = []
        for pattern in vague_patterns:
            if re.search(pattern, text):
                vague_found.append(pattern)
        return vague_found

    def _find_acceptance_clauses(self, text: str) -> List[str]:
        """查找验收条款"""
        pattern = r'(验收|检验|检查|测试).*?(标准|条件|要求)'
        matches = re.findall(pattern, text)
        return matches

    def _find_dispute_clauses(self, text: str) -> List[str]:
        """查找争议解决条款"""
        pattern = r'(争议|纠纷).*(仲裁|诉讼|法院)'
        matches = re.findall(pattern, text)
        return matches

    def _analyze_commercial_background(self, text: str, context: Dict) -> Dict:
        """分析商业背景"""
        return {
            'parties': self._extract_parties(text),
            'market_position': context.get('position', '未知'),
            'transaction_history': context.get('history', '无'),
            'focus': context.get('focus', '未明确')
        }

    def _identify_key_commercial_risks(self, text: str, context: Dict) -> List[Dict]:
        """识别关键商业风险"""
        risks = []

        if context.get('position') == '弱势':
            risks.append({
                'type': '市场地位风险',
                'description': '处于弱势地位,可能接受不利条款',
                'mitigation': '争取平衡关键条款,引入第三方担保'
            })

        return risks

    def _infer_true_intent(self, text: str, context: Dict) -> Dict:
        """推断真实意图"""
        return {
            'declared_intent': '从合同条款推断的表面意图',
            'possible_hidden_intent': '可能的深层意图',
            'note': '需结合用户访谈确认真实意图'
        }

    def _determine_transaction_type(self, text: str) -> str:
        """确定交易类型"""
        return '基于合同标题和内容判断的交易类型'

    def _analyze_transaction_path(self, text: str) -> Dict:
        """分析交易路径"""
        return {
            'direct_transaction': True,
            'stages': ['签约', '履行', '验收', '付款', '质保']
        }

    def _analyze_transaction_parties(self, text: str) -> List[str]:
        """分析交易主体"""
        return self._extract_parties(text)

    def _analyze_transaction_timeline(self, text: str) -> Dict:
        """分析交易时序"""
        return {
            'phases': '一次性交易 vs 分阶段交易',
            'key_milestones': '关键时间节点'
        }

    def _assess_contract_form(self, text: str) -> Dict:
        """评估合同形式"""
        return {
            'contract_type': '合同类型',
            'structure': '合同结构完整性',
            'completeness': '条款完整性'
        }

    def _check_clause_completeness(self, text: str) -> Dict:
        """检查条款完整性"""
        return {
            'essential_clauses': '必要条款检查',
            'missing_clauses': '缺失条款'
        }

    def _assess_rights_obligations_balance(self, text: str) -> Dict:
        """评估权利义务平衡性"""
        return {
            'balance_score': self._assess_balance(text),
            'imbalance_clauses': '不平衡条款'
        }

    def _legality_review(self, text: str) -> Dict:
        """合法性审查"""
        return {
            'legal_mode': '交易模式合法性',
            'subject_qualification': '主体资格',
            'mandatory_provisions': '是否违反强制性规定'
        }

    def _completeness_review(self, text: str) -> Dict:
        """完整性审查"""
        return {
            'essential_clauses': '必要条款是否齐全',
            'omissions': '是否存在遗漏'
        }

    def _executability_review(self, text: str) -> Dict:
        """可执行性审查"""
        return {
            'specificity': '条款是否具体',
            'operability': '是否可操作',
            'dispute_prevention': '争议预防机制'
        }


if __name__ == '__main__':
    # 测试代码
    print("=== 三观四步法分析模块测试 ===\n")

    analyzer = SanguanAnalysis()

    sample_contract = """
    买卖合同

    甲方：A公司
    乙方：B公司

    第一条 标的物
    本合同标的物为XXX产品。

    第二条 价款
    总价款人民币100万元。

    第三条 交付
    甲方应尽快交付产品。

    第四条 违约责任
    任何一方违约应承担责任。
    """

    user_context = {
        'party': '甲方',
        'position': '弱势',
        'history': '无',
        'focus': '付款安全'
    }

    # 测试三维审查法
    print("=== 三维审查法 ===")
    commercial = analyzer.analyze_commercial_dimension(sample_contract, user_context)
    print(f"商业维度: {commercial['rating']}")
    print(f"发现数量: {len(commercial['findings'])}")
    print(f"风险数量: {len(commercial['risks'])}\n")

    legal = analyzer.analyze_legal_dimension(sample_contract, '买卖合同')
    print(f"法律维度: {legal['rating']}")
    print(f"发现数量: {len(legal['findings'])}")
    print(f"风险数量: {len(legal['risks'])}\n")

    practical = analyzer.analyze_practical_dimension(sample_contract)
    print(f"实务维度: {practical['rating']}")
    print(f"发现数量: {len(practical['findings'])}")
    print(f"风险数量: {len(practical['risks'])}\n")

    # 测试三观四步法
    print("\n=== 三观四步法 ===")
    foursteps = analyzer.apply_sanguan_foursteps(sample_contract, user_context)
    for step in foursteps['steps']:
        print(f"\n{step['step']}")
        for key, value in step['analysis'].items():
            print(f"  {key}: {value}")
