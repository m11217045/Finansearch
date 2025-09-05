"""
自定義Agent角色範例
展示如何擴展多代理人系統，添加新的專家角色
"""

def create_custom_agents():
    """創建自定義的專家代理人"""
    
    custom_agents = [
        # ESG投資專家
        ValueInvestmentAgent(
            name="ESG永續投資專家",
            role="永續投資分析師",
            expertise="ESG評分、永續經營、環境風險評估",
            investment_style="關注企業永續發展、社會責任投資"
        ),
        
        # 量化投資專家
        ValueInvestmentAgent(
            name="量化投資分析師",
            role="量化策略分析師",
            expertise="數據建模、統計分析、演算法交易",
            investment_style="基於數據驅動的系統化投資"
        ),
        
        # 行業專家
        ValueInvestmentAgent(
            name="科技產業專家",
            role="科技行業分析師",
            expertise="科技趨勢、創新評估、數位轉型",
            investment_style="專注科技股、關注破壞式創新"
        ),
        
        # 總經分析師
        ValueInvestmentAgent(
            name="總體經濟分析師",
            role="宏觀經濟分析師",
            expertise="貨幣政策、經濟週期、通膨分析",
            investment_style="從總經角度評估投資機會"
        ),
        
        # 行為金融專家
        ValueInvestmentAgent(
            name="行為金融專家",
            role="投資心理分析師",
            expertise="市場情緒、投資者行為、認知偏誤",
            investment_style="利用市場非理性創造投資機會"
        )
    ]
    
    return custom_agents

def customize_agent_prompt(agent, stock_data, context, round_type):
    """為特定角色自定義提示詞"""
    
    if "ESG" in agent.name:
        # ESG專家的特殊提示詞
        esg_context = """
請特別關注以下ESG指標：
- 環境：碳排放、再生能源使用、環境合規
- 社會：員工權益、產品安全、社會影響
- 治理：董事會結構、透明度、股東權益
"""
        context += esg_context
    
    elif "量化" in agent.name:
        # 量化專家的特殊提示詞
        quant_context = """
請從數據角度分析：
- 財務比率趨勢
- 技術指標訊號
- 統計顯著性
- 風險調整後報酬
"""
        context += quant_context
    
    elif "科技" in agent.name:
        # 科技專家的特殊提示詞
        tech_context = """
請評估科技面向：
- 技術護城河
- 創新能力
- 數位化程度
- 競爭優勢持續性
"""
        context += tech_context
    
    return context

def create_specialized_analysis_framework():
    """創建專業化的分析框架"""
    
    analysis_frameworks = {
        "ESG永續投資專家": {
            "evaluation_criteria": [
                "ESG評分等級",
                "永續發展目標對齊度",
                "環境風險曝險",
                "社會責任實踐",
                "公司治理品質"
            ],
            "decision_factors": [
                "永續營運模式",
                "監管風險",
                "品牌聲譽",
                "長期競爭力"
            ]
        },
        
        "量化投資分析師": {
            "evaluation_criteria": [
                "歷史波動率",
                "夏普比率",
                "最大回撤",
                "貝塔係數",
                "動能指標"
            ],
            "decision_factors": [
                "統計套利機會",
                "風險調整報酬",
                "相關性分析",
                "回歸模型預測"
            ]
        },
        
        "科技產業專家": {
            "evaluation_criteria": [
                "研發投入比例",
                "專利組合強度",
                "技術成熟度",
                "市場接受度",
                "競爭壁壘"
            ],
            "decision_factors": [
                "技術趨勢對齊",
                "創新週期位置",
                "平台效應",
                "網路效應"
            ]
        }
    }
    
    return analysis_frameworks

# 使用範例
if __name__ == "__main__":
    # 創建自定義專家團隊
    custom_team = create_custom_agents()
    
    # 顯示專家資訊
    for agent in custom_team:
        print(f"專家：{agent.name}")
        print(f"角色：{agent.role}")
        print(f"專業：{agent.expertise}")
        print(f"風格：{agent.investment_style}")
        print("-" * 50)
