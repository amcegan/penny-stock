from langchain_core.prompts import ChatPromptTemplate

# Sentiment Analysis Prompt
SENTIMENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a financial news analyst. Your task is to analyze a set of news headlines and summaries for a specific company and determine if there is any SIGNIFICANT negative news in the past 3 business days that would warrant caution.

Ignore minor fluctuations or general market noise. Focus on:
- Lawsuits / FRAUD allegations
- Earnings misses (major)
- CEO resignation / scanadals
- Regulatory crackdowns
- Bankruptcy fears

Return your analysis in the specified JSON format.
"""),
    ("human", """Company: {company_name} ({symbol})
    
News Items:
{news_context}
""")
])

# Company Report Prompt
COMPANY_REPORT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a senior equity research analyst. Write a concise, professional investment report for the following company. Focus on its growth potential, recent developments, and risks. The report must be under 1000 words.
Structure it with:
1. Business Overview
2. Key Catalysts / Growth Drivers
3. Key Risks
4. Financial Health Summary
"""),
    ("human", """Company: {company_name} ({symbol})
Industry: {industry}
Sector: {sector}

Recent Volume Spike Info: {volume_info}
Analyst Upside: {upside_info}
""")
])

# CEO Report Prompt
CEO_REPORT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a corporate governance expert. Write a brief report on the CEO of the following company. Focus on their track record, past experience, and any notable achievements or controversies. Max 1000 words.
"""),
    ("human", """Company: {company_name} ({symbol})
""")
])
