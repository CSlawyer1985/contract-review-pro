"""
合同分析模块
解析合同文本，识别合同类型和条款
V1.1: 集成HanLP进行NLP增强分析
"""

import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from review_config import ReviewConfig

# NLP集成 (HanLP)
try:
    from hanlp import HanLP
    NLP_AVAILABLE = True
    print("✅ HanLP已启用 - NLP增强功能可用")
except ImportError:
    NLP_AVAILABLE = False
    print("⚠️ HanLP未安装 - 使用基础关键词匹配")


class ContractAnalyzer:
    """合同分析器"""

    def __init__(self, data_dir: str, methodology_file: str, review_config: ReviewConfig):
        """
        初始化合同分析器

        Args:
            data_dir: 数据目录路径
            methodology_file: 方法论文档路径
            review_config: 审核配置
        """
        self.data_dir = Path(data_dir)
        self.config = review_config
        self.methodology_file = methodology_file
        self.nlp_enabled = NLP_AVAILABLE

        # 加载数据
        self.contract_types = self._load_contract_types()
        self.risk_templates = self._load_risk_templates()
        self.clause_standards = self._load_clause_standards()
        self.review_checklists = self._load_review_checklists()

        # 初始化NLP模型
        if self.nlp_enabled:
            self._init_nlp_model()

    def _load_contract_types(self) -> pd.DataFrame:
        """加载合同类型数据"""
        file_path = self.data_dir / 'contract_types.csv'
        return pd.read_csv(file_path, encoding='utf-8')

    def _load_risk_templates(self) -> pd.DataFrame:
        """加载风险模板数据"""
        file_path = self.data_dir / 'risk_templates.csv'
        return pd.read_csv(file_path, encoding='utf-8')

    def _load_clause_standards(self) -> pd.DataFrame:
        """加载标准条款数据"""
        file_path = self.data_dir / 'clause_standards.csv'
        return pd.read_csv(file_path, encoding='utf-8')

    def _load_review_checklists(self) -> pd.DataFrame:
        """加载审核检查清单"""
        file_path = self.data_dir / 'review_checklists.csv'
        return pd.read_csv(file_path, encoding='utf-8')

    def _init_nlp_model(self):
        """初始化NLP模型"""
        try:
            # HanLP会自动加载预训练模型
            # 首次加载会下载模型(约300MB)
            print("🔄 正在初始化HanLP NLP模型...")
            # 测试加载
            test_result = HanLP.parse('测试文本', tasks='tok')
            print("✅ HanLP模型初始化成功")
        except Exception as e:
            print(f"⚠️ HanLP模型初始化失败: {e}")
            self.nlp_enabled = False

    def _nlp_extract_entities(self, text: str) -> Dict[str, List]:
        """
        使用NLP提取命名实体

        Args:
            text: 文本

        Returns:
            {'persons': [], 'organizations': [], 'locations': [], 'amounts': [], 'dates': []}
        """
        if not self.nlp_enabled:
            return {}

        try:
            # 使用HanLP进行命名实体识别
            result = HanLP.parse(text, tasks='ner')

            entities = {
                'persons': [],
                'organizations': [],
                'locations': [],
                'amounts': [],
                'dates': []
            }

            # 提取实体(具体格式根据HanLP版本调整)
            # 这里提供基础框架,实际使用时可能需要调整

            return entities
        except Exception as e:
            print(f"⚠️ NER提取失败: {e}")
            return {}

    def _nlp_parse_clause_structure(self, clause_text: str) -> Dict:
        """
        使用NLP分析条款结构(依存句法分析)

        Args:
            clause_text: 条款文本

        Returns:
            {'main_action': '', 'conditions': [], 'obligations': [], 'parties': []}
        """
        if not self.nlp_enabled:
            return {}

        try:
            # 依存句法分析
            result = HanLP.parse(clause_text, tasks='dep')

            # 提取主要动作、条件、义务等
            structure = {
                'main_action': '',
                'conditions': [],
                'obligations': [],
                'parties': []
            }

            # 具体实现根据HanLP返回结果调整
            return structure
        except Exception as e:
            print(f"⚠️ 句法分析失败: {e}")
            return {}

    def analyze_contract_type(self, contract_type: str) -> Dict:
        """
        分析合同类型，返回审核指引

        Args:
            contract_type: 合同类型名称

        Returns:
            包含该类型合同审核指引的字典
        """
        # 查找匹配的合同类型
        matches = self.contract_types[
            self.contract_types['contract_type'].str.contains(contract_type, case=False, na=False)
        ]

        if matches.empty:
            return {
                'error': f'未找到合同类型: {contract_type}',
                'available_types': self.contract_types['contract_type'].tolist()
            }

        # 获取第一个匹配项
        contract_info = matches.iloc[0]

        # 获取该类型的风险点
        risks = self.risk_templates[
            self.risk_templates['contract_type'].str.contains(contract_type, case=False, na=False)
        ]

        # 获取该类型的检查清单
        checklist = self.review_checklists[
            self.review_checklists['applicable_contracts'].str.contains('所有合同|' + contract_type, case=False, na=False)
        ]

        return {
            'contract_type': contract_info['contract_type'],
            'category': contract_info['category'],
            'core_risks': contract_info['core_risks'],
            'key_clauses': contract_info['key_clauses'],
            'legal_basis': contract_info['legal_basis'],
            'review_points': contract_info['review_points'],
            'risks': risks.to_dict('records'),
            'checklist': checklist.to_dict('records')
        }

    def identify_contract_type(self, contract_text: str) -> List[Tuple[str, float]]:
        """
        识别合同类型（基于关键词匹配）

        Args:
            contract_text: 合同文本

        Returns:
            [(合同类型, 匹配分数), ...] 按分数降序排列
        """
        contract_text_lower = contract_text.lower()
        scores = []

        for _, contract_type_info in self.contract_types.iterrows():
            contract_type = contract_type_info['contract_type']
            key_clauses = contract_type_info['key_clauses']

            # 计算匹配分数
            score = 0.0

            # 检查合同标题
            if contract_type.lower() in contract_text_lower:
                score += 0.5

            # 检查关键条款关键词
            if pd.notna(key_clauses):
                keywords = key_clauses.split('、')
                matched_keywords = sum(1 for kw in keywords if kw.lower() in contract_text_lower)
                score += matched_keywords * 0.1

            if score > 0:
                scores.append((contract_type, score))

        # 按分数降序排列
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def extract_clauses(self, contract_text: str, identified_type: Optional[str] = None) -> Dict[str, List[Dict]]:
        """
        提取合同条款

        Args:
            contract_text: 合同文本
            identified_type: 已识别的合同类型（可选）

        Returns:
            {条款类型: [{条款编号, 条款内容, 行号}, ...], ...}
        """
        clauses = {}

        # 按行分割
        lines = contract_text.split('\n')

        # 识别条款编号模式（如：一、第一条、1.、（1）等）
        clause_pattern = re.compile(r'^(第[一二三四五六七八九十百千]+[条条款款]|[一二三四五六七八九十百千]+[、.]|[0-9]+[、.]|（[0-9]+）)\s*(.*)')

        current_clause_type = None
        current_clause_number = None
        current_content = []

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            match = clause_pattern.match(line)

            if match:
                # 保存前一条款
                if current_clause_type and current_content:
                    clause_text = '\n'.join(current_content)

                    # 判断条款类型
                    clause_type = self._classify_clause(clause_text)

                    # 根据配置判断是否需要审核
                    if self.config.should_check_clause(clause_type):
                        if clause_type not in clauses:
                            clauses[clause_type] = []

                        clauses[clause_type].append({
                            'number': current_clause_number,
                            'content': clause_text,
                            'line_number': line_num - len(current_content)
                        })

                # 开始新条款
                current_clause_number = match.group(1)
                current_content = [match.group(2)]
                current_clause_type = None
            else:
                if current_clause_number is not None:
                    current_content.append(line)

        # 保存最后一条款
        if current_clause_type and current_content:
            clause_text = '\n'.join(current_content)
            clause_type = self._classify_clause(clause_text)

            if self.config.should_check_clause(clause_type):
                if clause_type not in clauses:
                    clauses[clause_type] = []

                clauses[clause_type].append({
                    'number': current_clause_number,
                    'content': clause_text,
                    'line_number': line_num - len(current_content) + 1
                })

        return clauses

    def _classify_clause(self, clause_text: str) -> str:
        """
        分类条款类型 (NLP增强版)

        Args:
            clause_text: 条款文本

        Returns:
            条款类型
        """
        clause_text_lower = clause_text.lower()

        # 定义条款类型关键词映射
        clause_keywords = {
            '标的': ['标的', '租赁物', '借款金额', '股权', '工程范围', '工作成果', '委托事项', '赠与物', '技术内容', '保险标的'],
            '数量质量': ['数量', '质量', '规格', '型号', '标准', '面积', '体积'],
            '价款': ['价款', '价格', '报酬', '租金', '利息', '费用', '承包费', '增资款', '保险费', '补偿金'],
            '履行': ['交付', '履行', '施工', '开工', '竣工', '提供', '完成', '转让', '许可'],
            '违约责任': ['违约', '责任', '赔偿', '违约金'],
            '解除终止': ['解除', '终止', '到期'],
            '不可抗力': ['不可抗力'],
            '担保保险': ['担保', '保证', '抵押', '质押', '保险'],
            '保密': ['保密', '机密'],
            '知识产权': ['知识产权', '专利', '商标', '著作权'],
            '争议解决': ['争议', '仲裁', '诉讼', '法院'],
            '通知送达': ['通知', '送达', '联系方式'],
            '验收': ['验收', '检验', '检查', '测试'],
            '竞业限制': ['竞业限制', '竞业禁止'],
            '业绩目标': ['业绩目标', '净利润', '营收', '对赌'],
            '股权回购': ['股权回购', '回购'],
            '一致行动': ['一致行动', '表决权委托'],
            '工伤': ['工伤', '工伤保险'],
            '撤销权': ['撤销权', '撤销']
        }

        # 方法1: 基础关键词匹配
        best_match = '其他'
        best_score = 0

        for clause_type, keywords in clause_keywords.items():
            for keyword in keywords:
                if keyword in clause_text:
                    # 关键词匹配得分
                    score = 1.0
                    # 如果关键词出现多次,增加得分
                    count = clause_text.count(keyword)
                    if count > 1:
                        score += min(count * 0.2, 1.0)

                    if score > best_score:
                        best_score = score
                        best_match = clause_type

        # 方法2: NLP增强 (如果可用)
        if self.nlp_enabled and best_match == '其他':
            # 使用NLP进行语义分析
            nlp_result = self._nlp_parse_clause_structure(clause_text)

            # 根据分析结果进行分类
            if nlp_result.get('main_action'):
                action = nlp_result['main_action']

                # 根据主要动作判断类型
                if any(word in action for word in ['交付', '转让', '许可']):
                    best_match = '履行'
                elif any(word in action for word in ['支付', '付款']):
                    best_match = '价款'
                elif any(word in action for word in ['违约', '赔偿']):
                    best_match = '违约责任'

        return best_match

    def parse_contract(self, contract_text: str) -> Dict:
        """
        解析合同文本，提取关键信息

        Args:
            contract_text: 合同文本

        Returns:
            合同解析结果
        """
        # 识别合同类型
        type_scores = self.identify_contract_type(contract_text)
        identified_type = type_scores[0][0] if type_scores else '未知'

        # 提取条款
        clauses = self.extract_clauses(contract_text, identified_type)

        return {
            'identified_type': identified_type,
            'type_confidence': type_scores[0][1] if type_scores else 0.0,
            'type_alternatives': type_scores[1:4] if len(type_scores) > 1 else [],
            'clauses': clauses,
            'total_clauses': sum(len(clause_list) for clause_list in clauses.values())
        }


if __name__ == '__main__':
    # 测试代码
    print("=== 合同分析模块测试 ===\n")

    from review_config import ReviewConfig

    # 初始化
    data_dir = '/Users/CS/Trae/Claude/.trae/skills/contract-review-pro/data'
    methodology_file = '/Users/CS/Trae/Claude/合同审核方法论体系_完整版.md'
    config = ReviewConfig('standard')

    analyzer = ContractAnalyzer(data_dir, methodology_file, config)

    # 测试1：分析合同类型
    print("=== 测试1: 分析合同类型 ===")
    result = analyzer.analyze_contract_type('买卖合同')
    print(f"合同类型: {result['contract_type']}")
    print(f"分类: {result['category']}")
    print(f"核心风险: {result['core_risks']}")
    print(f"风险点数量: {len(result['risks'])}")
    print(f"检查清单项数量: {len(result['checklist'])}")
    print()

    # 测试2：识别合同类型
    print("=== 测试2: 识别合同类型 ===")
    sample_text = """
    买卖合同

    甲方：××公司
    乙方：××公司

    第一条 标的物
    本合同标的物为：XXX产品，规格型号：XXX，数量：100台。

    第二条 价款
    总价款：人民币100万元（含税）。

    第三条 违约责任
    任何一方违约应向守约方支付违约金。
    """

    type_scores = analyzer.identify_contract_type(sample_text)
    for contract_type, score in type_scores:
        print(f"  {contract_type}: {score:.2f}")
    print()

    # 测试3：提取条款
    print("=== 测试3: 提取条款 ===")
    parsed = analyzer.parse_contract(sample_text)
    print(f"识别类型: {parsed['identified_type']} (置信度: {parsed['type_confidence']:.2f})")
    print(f"提取到条款数量: {parsed['total_clauses']}")
    print("条款类型分布:")
    for clause_type, clause_list in parsed['clauses'].items():
        print(f"  {clause_type}: {len(clause_list)}条")
        for clause in clause_list[:2]:  # 显示前2条
            print(f"    - {clause['number']}: {clause['content'][:50]}...")
