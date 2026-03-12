import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import jieba
import os
import platform

# --- 页面配置 ---
st.set_page_config(page_title="大学生职业规划智能体", page_icon="🎓", layout="wide")

# --- 中文字体设置 (防止图表乱码) ---
def set_font():
    system_name = platform.system()
    if system_name == 'Windows':
        font_name = 'SimHei'
    elif system_name == 'Darwin':
        font_name = 'Arial Unicode MS'
    else:
        font_name = 'WenQuanYi Micro Hei'
    
    plt.rcParams['font.sans-serif'] = [font_name, 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

set_font()

# --- 缓存数据加载函数 ---
@st.cache_data
def load_data():
    try:
        df = pd.read_excel('cleaned_job_data.xlsx')
        # 预处理防止报错
        df['岗位详情'] = df['岗位详情'].fillna('无描述').astype(str)
        df['城市'] = df['城市'].fillna('未知').astype(str)
        df['最低薪资'] = pd.to_numeric(df['最低薪资'], errors='coerce').fillna(0)
        df['平均薪资'] = pd.to_numeric(df['平均薪资'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"数据加载失败：{e}")
        return None

# --- 侧边栏：用户输入 ---
st.sidebar.title("🎓 求职者画像")
st.sidebar.markdown("请输入您的简历关键词，获取专属推荐。")

user_skills = st.sidebar.text_input("💼 技能关键词 (用逗号分隔)", "Python, 数据分析, 沟通")
user_city = st.sidebar.text_input("📍 期望城市", "广州")
user_min_salary = st.sidebar.number_input("💰 期望最低薪资 (元)", min_value=0, value=8000, step=1000)

# 将技能字符串转为列表
skills_list = [s.strip() for s in user_skills.split(',') if s.strip()]

# --- 主界面 ---
st.title("🚀 大学生职业规划智能体")
st.markdown("基于真实招聘数据，为您提供**市场洞察**与**人岗匹配**服务。")

df = load_data()

if df is not None:
    # 选项卡布局
    tab1, tab2, tab3 = st.tabs(["📊 市场洞察大屏", "🤖 智能岗位推荐", "📑 原始数据预览"])

    # === 选项卡 1: 市场洞察 ===
    with tab1:
        st.header("📊 就业市场全景分析")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏙️ 十大高薪城市")
            city_salary = df.groupby('城市')['平均薪资'].mean().reset_index()
            city_salary = city_salary.sort_values(by='平均薪资', ascending=False).head(10)
            
            fig1, ax1 = plt.subplots(figsize=(8, 5))
            sns.barplot(data=city_salary, x='平均薪资', y='城市', ax=ax1, palette='viridis')
            ax1.set_xlabel('平均薪资 (元)')
            ax1.set_ylabel('')
            st.pyplot(fig1)
            plt.close(fig1)

        with col2:
            st.subheader("🏢 热门行业分布")
            industry_count = df['所属行业'].value_counts().head(8)
            # 处理其他
            if len(df['所属行业'].unique()) > 8:
                other_sum = df['所属行业'].value_counts()[8:].sum()
                industry_count['其他'] = other_sum
            
            fig2, ax2 = plt.subplots(figsize=(6, 6))
            ax2.pie(industry_count, labels=industry_count.index, autopct='%1.1f%%', startangle=140)
            ax2.axis('equal')
            st.pyplot(fig2)
            plt.close(fig2)

        st.subheader("☁️ 岗位技能词云")
        # 生成词云
        text = " ".join(df['岗位详情'])
        words = jieba.lcut(text)
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '负责', '工作', '提供', '具有', '相关', '经验', '优先', '能力', '团队', '合作', '无详细描述', 'nan'}
        clean_words = [w for w in words if len(w) > 1 and w not in stop_words]
        text_clean = " ".join(clean_words)
        
        if text_clean.strip():
            wc = WordCloud(background_color='white', width=800, height=400, max_words=100, colormap='magma').generate(text_clean)
            fig3, ax3 = plt.subplots(figsize=(10, 5))
            ax3.imshow(wc, interpolation='bilinear')
            ax3.axis('off')
            st.pyplot(fig3)
            plt.close(fig3)
        else:
            st.warning("暂无足够文本生成词云。")

    # === 选项卡 2: 智能推荐 ===
    with tab2:
        st.header("🤖 为您定制的岗位推荐")
        
        if st.button("🔍 开始匹配"):
            with st.spinner('正在计算匹配度...'):
                results = []
                for index, row in df.iterrows():
                    score = 0
                    reasons = []
                    
                    # 技能匹配
                    job_desc_lower = row['岗位详情'].lower()
                    matched_skills = [s for s in skills_list if s.lower() in job_desc_lower]
                    if matched_skills:
                        score += 50 * (len(matched_skills) / len(skills_list)) # 归一化
                        reasons.append(f"✅ 技能匹配：{', '.join(matched_skills)}")
                    
                    # 地点匹配
                    if user_city in str(row['城市']):
                        score += 30
                        reasons.append(f"📍 地点匹配：{row['城市']}")
                    
                    # 薪资匹配
                    if row['最低薪资'] >= user_min_salary:
                        score += 20
                        reasons.append(f"💰 薪资达标")
                    elif row['平均薪资'] >= user_min_salary * 0.8:
                        score += 10
                        reasons.append(f"💰 薪资接近")
                    
                    if score > 0:
                        results.append({
                            '得分': round(score, 1),
                            '岗位': row['岗位名称'],
                            '公司': row['公司名称'],
                            '城市': row['城市'],
                            '薪资': row['薪资范围'],
                            '理由': "; ".join(reasons),
                            '链接': row['岗位来源地址'] if pd.notna(row['岗位来源地址']) else '#'
                        })
                
                if results:
                    res_df = pd.DataFrame(results).sort_values(by='得分', ascending=False).head(10)
                    
                    # 展示结果
                    for i, row in res_df.iterrows():
                        with st.expander(f"🏆 匹配度 {row['得分']}分 - {row['岗位']} @ {row['公司']}"):
                            st.write(f"**📍 地点**: {row['城市']}")
                            st.write(f"**💰 薪资**: {row['薪资']}")
                            st.write(f"**🧠 推荐理由**: {row['理由']}")
                            if row['链接'] != '#':
                                st.markdown(f"[🔗 查看原职位]({row['链接']})")
                else:
                    st.warning("未找到完全匹配的岗位，建议放宽技能或薪资要求。")

    # === 选项卡 3: 数据预览 ===
    with tab3:
        st.header("📑 数据预览")
        st.dataframe(df.head(10))
        st.download_button(
            label="📥 下载清洗后的数据 (Excel)",
            data=open('cleaned_job_data.xlsx', 'rb'),
            file_name='cleaned_job_data.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

else:
    st.error("无法加载数据，请检查 cleaned_job_data.xlsx 是否存在。")