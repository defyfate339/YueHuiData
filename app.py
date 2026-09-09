"""
各渠道数据对比 - Streamlit 应用
依赖：pip install streamlit pandas openpyxl plotly
运行：streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ============ 1. 页面配置 ============
st.set_page_config(
    page_title="各渠道数据对比",
    layout="wide",
)

# ============ 2. 全局深色主题 ============
st.markdown(
    """
    <style>
    .stApp { background-color: #0f172a; color: #e2e8f0; }
    section[data-testid="stSidebar"] { background-color: #1e293b; }
    h1, h2, h3, h4, h5, h6, p, label, span, div { color: #e2e8f0 !important; }
    .stFileUploader { background-color: #1e293b; }

    /* 负责人筛选器：把 st.radio 横向排列变成按钮组样式
       st.radio 没有 BaseWeb 异步覆盖问题，CSS 立即生效 */
    [data-testid="stRadio"] [role="radiogroup"] {
      gap: 0;
    }
    [data-testid="stRadio"] [role="radiogroup"] label {
      background: #f8fafc;
      color: #000000 !important;
      -webkit-text-fill-color: #000000 !important;
      border: 1px solid #94a3b8;
      padding: 6px 18px;
      border-radius: 0;
      margin: 0 -1px 0 0;
      cursor: pointer;
      font-weight: 500;
    }
    /* 只覆盖 label 内的子 div（文字所在），不要给子元素加 border/background */
    [data-testid="stRadio"] [role="radiogroup"] label > div {
      color: #000000 !important;
      -webkit-text-fill-color: #000000 !important;
    }
    /* 第一个/最后一个圆角 */
    [data-testid="stRadio"] [role="radiogroup"] label:first-of-type {
      border-radius: 8px 0 0 8px;
    }
    [data-testid="stRadio"] [role="radiogroup"] label:last-of-type {
      border-radius: 0 8px 8px 0;
      margin-right: 0;
    }
    /* 选中态：用 :has(input:checked) 命中整个 label */
    [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {
      background: #4c1d95;
      color: #ffffff !important;
      -webkit-text-fill-color: #ffffff !important;
      border-color: #f43f5e;
      z-index: 1;
    }
    [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) > div {
      color: #ffffff !important;
      -webkit-text-fill-color: #ffffff !important;
    }
    /* 隐藏原生 radio 圆点 */
    [data-testid="stRadio"] [role="radiogroup"] input[type="radio"] {
      position: absolute;
      opacity: 0;
      pointer-events: none;
      width: 0;
      height: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============ 3. 标题 ============
st.title("各渠道数据对比")
st.caption("按渠道分组统计到面 / 合格 / 在职 人数")

# ============ 4. 渠道映射表 ============
# 编号 → 渠道名称；空值统一映射到 "小迳网招部"
NUMBER_TO_NAME = {
    5996.0: "自媒体",
    9666.0: "捷飞",
    2222.0: "企事通",
}
# 渠道名称 → 负责人
NAME_TO_MANAGER = {
    "滕晨":   "柳杨",
    "联晟":   "柳杨",
    "企事通": "张静",
    "捷飞":   "张静",
    "铂睿":   "张静",
    "自媒体": "张静",
    "小迳网招部": "王志英",  
}
NA_NAME = "小迳网招部"


# 渠道 → 固定颜色映射：保证饼图在不同企业之间切换时，颜色保持一致
CHANNEL_COLORS = {
    "自媒体":     "#1f77b4",  # 蓝
    "小迳网招部": "#ff7f0e",  # 橙
    "企事通":    "#2ca02c",  # 绿
    "捷飞":      "#d62728",  # 红
    "铂睿":      "#9467bd",  # 紫
    "滕晨":      "#8c564b",  # 棕
    "联晟":      "#e377c2",  # 粉
    "未知":      "#7f7f7f",  # 灰（兜底）
}
DEFAULT_PIE_COLOR = "#7f7f7f"


def map_channel(v) -> str:
    if pd.isna(v):
        return NA_NAME
    if v in NUMBER_TO_NAME:
        return NUMBER_TO_NAME[v]
    s = str(v).strip()
    if s in NUMBER_TO_NAME.values():
        return s
    return s 


# ============ 5. 数据加载 ============
DEFAULT_PATH = r"D:\YueHuiProject\公司数据\在离职数据与模板\最新状态.xlsx"

try:
    df = pd.read_excel(DEFAULT_PATH)
except Exception as e:
    st.error(f"文件读取失败：{DEFAULT_PATH}\n\n{e}")
    st.stop()

# ============ 6. 计算指标 ============
col_supplier = "供应商"
col_status = "状态"
col_channel = "渠道名称"

if col_supplier not in df.columns or col_status not in df.columns:
    st.error(f"缺少必要列：{col_supplier} 或 {col_status}")
    st.write("当前列：", list(df.columns))
    st.stop()

# 派生：渠道名称 + 负责人
df[col_channel] = df[col_supplier].apply(map_channel)
df["负责人"] = df[col_channel].map(NAME_TO_MANAGER).fillna("—")


def calc(group: pd.DataFrame) -> pd.Series:
    s = group[col_status].astype(str)
    return pd.Series(
        {
            "到面": len(group),                              # 有数据就算到面
            "合格": (s != "面试-未通过").sum(),               # 不等于 未通过 即合格
            "在职": (s == "在离职-在职").sum(),               # 在离职-在职 = 入职
        }
    )


result = (
    df.groupby(col_channel, dropna=False)
    .apply(calc, include_groups=False)
    .reset_index()
)
# 取每个渠道对应的负责人（同一渠道应是固定的，取 first 即可）
extra = df.groupby(col_channel)["负责人"].first()
result = result.merge(extra.rename("负责人"), on=col_channel, how="left")
result = result.sort_values("到面", ascending=False).reset_index(drop=True)

# 调整列顺序：渠道 / 负责人 / 数据
result = result[[col_channel, "负责人", "到面", "合格", "在职"]]

st.subheader("汇总数据")
st.dataframe(result, width="stretch")

# ============ 7. 旭日图：到面数据（负责人 → 渠道） ============
st.subheader("到面数据分布")
# 第一层负责人、第二层渠道；result 中每渠道一行且已带负责人
sun_data = result[["负责人", col_channel, "到面"]].copy()
sun_data = sun_data.sort_values("到面", ascending=False).reset_index(drop=True)

sun_fig = px.sunburst(
    sun_data,
    path=["负责人", col_channel],   # 第一层：负责人；第二层：渠道
    values="到面",
    color="负责人",
    color_discrete_sequence=px.colors.qualitative.Set2,
)

sun_fig.update_traces(
    textinfo="label+value",
    hovertemplate="<b>%{label}</b><br>到面：%{value} 人<extra></extra>",
    textfont=dict(color="black", size=14),
    marker=dict(line=dict(color="black", width=1.5)),
)
sun_fig.update_layout(
    paper_bgcolor="#0f172a",
    font=dict(color="black"),   # 图框统一标题等字符为黑
    margin=dict(l=10, r=10, t=40, b=10),
    height=560,
)

st.plotly_chart(sun_fig, width="stretch")

# ============ 8. 负责人筛选器（仅作用于下方柱状图） ============
managers = ["全部"] + sorted(result["负责人"].dropna().unique().tolist())

title_col, ctrl_col = st.columns([1.1, 2.4], vertical_alignment="center")
with title_col:
    st.markdown("### 分组柱状图")
with ctrl_col:
    # 用 st.radio(horizontal=True) 替代 segmented_control，避免 BaseWeb 异步覆盖
    selected_manager = st.radio(
        "负责人",
        managers,
        index=0,
        horizontal=True,
        label_visibility="collapsed",
        key="manager_filter",
    )

st.caption("选一位负责人只看 TA 名下的渠道，默认「全部」")

# 筛选柱状图数据（不影响上方旭日图）
if selected_manager == "全部":
    chart_data = result
else:
    chart_data = result[result["负责人"] == selected_manager]

if chart_data.empty:
    st.info(f"负责人「{selected_manager}」名下暂无渠道数据")
    st.stop()

# ============ 9. 分组柱状图绘制函数 ============
colors = {
    "到面": "#2ca58d",   # 青绿
    "合格": "#e09f3e",   # 橙黄
    "在职": "#f4a6c0",   # 粉色
}

categories = ["到面", "合格", "在职"]


def make_group_bar(data: pd.DataFrame, x_col: str, title: str, xaxis_title: str) -> go.Figure:
    """通用分组柱状图：X 轴为 data[x_col] 的类别，每组柱子 = 到面/合格/在职"""
    fig = go.Figure()
    for cat in categories:
        fig.add_trace(
            go.Bar(
                name=cat,
                x=data[x_col],
                y=data[cat],
                marker_color=colors[cat],
                text=data[cat],
                textposition="outside",
                cliponaxis=False,
            )
        )
    fig.update_layout(
        title=dict(
            text=title,
            x=0.02,
            font=dict(color="#e2e8f0", size=20),
        ),
        barmode="group",
        bargap=0.25,
        bargroupgap=0.05,
        plot_bgcolor="#0f172a",
        paper_bgcolor="#0f172a",
        font=dict(color="#e2e8f0"),
        xaxis=dict(
            title=dict(text=xaxis_title, font=dict(color="#94a3b8")),
            tickfont=dict(color="#cbd5e1"),
            gridcolor="#1e293b",
            linecolor="#334155",
        ),
        yaxis=dict(
            title=dict(text="人数", font=dict(color="#94a3b8")),
            tickfont=dict(color="#cbd5e1"),
            gridcolor="#1e293b",
            linecolor="#334155",
            rangemode="tozero",
        ),
        legend=dict(
            title=dict(text="状态", font=dict(color="#e2e8f0")),
            font=dict(color="#e2e8f0"),
            bgcolor="rgba(0,0,0,0)",
            orientation="v",
            x=1.02,
            y=1,
            xanchor="left",
        ),
        margin=dict(l=70, r=140, t=70, b=70),
        height=520,
    )
    return fig


def make_pie(data: pd.DataFrame, name_col: str, value_col: str, title: str) -> go.Figure:
    """单维度占比饼图：name_col 是类别（渠道名），value_col 是数值列（到面/在职）
    颜色按 CHANNEL_COLORS 锁死，切换筛选器时同一渠道保持同一颜色。"""
    labels = data[name_col].tolist()
    colors = [CHANNEL_COLORS.get(n, DEFAULT_PIE_COLOR) for n in labels]
    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=data[value_col],
            marker=dict(colors=colors, line=dict(color="black", width=1.5)),
            textinfo="label+value",
            hovertemplate="<b>%{label}</b><br>%{value} 人<extra></extra>",
            textfont=dict(color="black", size=13),
        )
    )
    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(color="#e2e8f0", size=16)),
        paper_bgcolor="#0f172a",
        font=dict(color="#e2e8f0"),
        margin=dict(l=10, r=10, t=60, b=10),
        height=420,
        showlegend=True,
        legend=dict(font=dict(color="#e2e8f0")),
    )
    return fig


# 渠道维度分组柱状图（受上方负责人筛选器控制）
st.plotly_chart(
    make_group_bar(chart_data, col_channel, "各渠道数据对比", "渠道"),
    width="stretch",
)

# ============ 10. 企业维度统计 ============
# 筛选器：全部 → 各企业分组柱状图；选单个企业 → 该企业各渠道的到面饼图 + 在职饼图
col_company = "企业简称"

if col_company not in df.columns:
    st.warning(f"数据缺少「{col_company}」列，无法绘制企业人数统计图")
else:
    # ---- 10.1 企业汇总（全部模式用） ----
    company_result = (
        df.groupby(col_company, dropna=False)
        .apply(calc, include_groups=False)
        .reset_index()
    )
    company_result[col_company] = company_result[col_company].fillna("未知").astype(str)
    company_result = company_result.sort_values("到面", ascending=False).reset_index(drop=True)
    company_result = company_result[[col_company, "到面", "合格", "在职"]]

    st.subheader("各企业人数统计")

    # ---- 10.2 企业筛选器（下拉框，选项多了也不占宽） ----
    companies = ["全部"] + company_result[col_company].tolist()
    c_title_col, c_ctrl_col = st.columns([1.1, 2.4], vertical_alignment="center")
    with c_title_col:
        st.markdown("**选择企业**")
    with c_ctrl_col:
        selected_company = st.selectbox(
            "企业",
            companies,
            index=0,
            label_visibility="collapsed",
            key="company_filter",
        )

    # Streamlit 1.49+ 的 selectbox 用 React Aria，展开后的下拉选项
    # 没有 role="option" 属性，但 id 形如 *-option-N，可直接用 id 选择器定位
    st.html(
        """
        <style>
        /* 缩短下拉框：只占容器约一半宽 */
        [data-testid="stSelectbox"] {
          max-width: 46%;
          min-width: 200px;
        }
        /* 收起时选中值文字 -> 黑字 */
        [data-testid="stSelectbox"] * {
          color: #000000 !important;
          -webkit-text-fill-color: #000000 !important;
        }
        /* 展开后的下拉选项（React Aria 的 id 模式） */
        [id*="-option-"],
        [id*="-option-"] * {
          color: #000000 !important;
          -webkit-text-fill-color: #000000 !important;
        }
        </style>
        <script>
        (function () {
          function blacken(el) {
            if (!el) return;
            el.style.setProperty('color', '#000000', 'important');
            el.style.setProperty('-webkit-text-fill-color', '#000000', 'important');
            if (el.querySelectorAll) {
              el.querySelectorAll('*').forEach(blacken);
            }
          }
          function blackenAll() {
            // 方案 A：直接按 React Aria 的 id 模式找所有下拉选项
            document.querySelectorAll('[id*="-option-"]').forEach(blacken);
            // 方案 B 兜底：通过 combobox 的 aria-controls 找到 popover 容器
            document
              .querySelectorAll('[role="combobox"][aria-expanded="true"]')
              .forEach(function (cb) {
                const popId = cb.getAttribute('aria-controls');
                if (popId) {
                  const popover = document.getElementById(popId);
                  if (popover) blacken(popover);
                }
              });
          }
          blackenAll();
          new MutationObserver(blackenAll).observe(
            document.body, { childList: true, subtree: true }
          );
        })();
        </script>
        """,
    )

    # ---- 10.3 视图切换 ----
    if selected_company == "全部":
        st.caption("各企业到面 / 合格 / 在职 人数对比")
        st.plotly_chart(
            make_group_bar(company_result, col_company, "", "企业"),
            width="stretch",
        )
    else:
        # 该企业下各渠道的明细（按渠道分组）
        sub = df[df[col_company] == selected_company].copy()
        channel_stat = (
            sub.groupby(col_channel, dropna=False)
            .apply(calc, include_groups=False)
            .reset_index()
        )
        channel_stat[col_channel] = channel_stat[col_channel].fillna("未知").astype(str)
        channel_stat = channel_stat.sort_values("到面", ascending=False).reset_index(drop=True)

        st.caption(f"「{selected_company}」各渠道到面 / 在职 人数")
        left_col, right_col = st.columns(2)
        with left_col:
            st.plotly_chart(
                make_pie(channel_stat, col_channel, "到面", f"{selected_company} · 到面"),
                width="stretch",
            )
        with right_col:
            st.plotly_chart(
                make_pie(channel_stat, col_channel, "在职", f"{selected_company} · 在职"),
                width="stretch",
            )

        # 附一张小汇总表，方便核对
        with st.expander(f"查看 {selected_company} 各渠道明细"):
            st.dataframe(channel_stat, width="stretch")

# ============ 11. 转化率小卡片 ============
st.subheader("转化率概览")
total_arrived = int(result["到面"].sum())
total_qualified = int(result["合格"].sum())
total_onboard = int(result["在职"].sum())

c1, c2, c3 = st.columns(3)
c1.metric("到面总人数", total_arrived)
c2.metric("合格总人数", total_qualified,
          f"{total_qualified / total_arrived * 100:.1f}%" if total_arrived else "—")
c3.metric("在职总人数", total_onboard,
          f"{total_onboard / total_arrived * 100:.1f}%" if total_arrived else "—")
