import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import networkx as nx
from io import BytesIO
import os

# --- Ініціалізація стану ---
if "executors" not in st.session_state:
    st.session_state.executors = []
if "processes" not in st.session_state:
    st.session_state.processes = []
if "roles_data" not in st.session_state:
    st.session_state.roles_data = []

roles = ["R", "A", "C", "I"]

st.title("🔷 RACI Matrix Builder")

# --- 0️⃣ Бічна панель: Завантаження та збереження проекту ---
st.sidebar.header("💾 Керування проектом")

# Завантаження проекту
uploaded_file = st.sidebar.file_uploader("📂 Завантажити проект (Excel)", type=["xlsx"])
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, index_col=None)
        st.session_state.processes = df["Процеси"].tolist()
        st.session_state.executors = df.columns[1:].tolist()
        st.session_state.roles_data = df[df.columns[1:]].values.tolist()
        st.sidebar.success("✅ Проект успішно завантажено!")
    except Exception as e:
        st.sidebar.error(f"Помилка завантаження файлу: {e}")

# Збереження проекту в Excel
def to_excel():
    output = BytesIO()
    data = {"Процеси": st.session_state.processes}
    for idx, executor in enumerate(st.session_state.executors):
        data[executor] = [roles[idx] for roles in st.session_state.roles_data]
    df = pd.DataFrame(data)
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="RACI Matrix")
    return output.getvalue()

if st.session_state.processes:
    excel_data = to_excel()
    st.sidebar.download_button(
        label="⬇️ Завантажити проект (Excel)",
        data=excel_data,
        file_name="raci_project.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# --- 1️⃣ Введення та видалення виконавців ---
st.header("Управління виконавцями")
executor_name = st.text_input("Введіть виконавця для додавання/видалення", key="executor_input")

col1, col2 = st.columns(2)
with col1:
    if st.button("➕ Додати виконавця"):
        if executor_name.strip() == "":
            st.error("Введіть виконавця.")
        elif executor_name in st.session_state.executors:
            st.warning("Такий виконавець вже існує.")
        else:
            st.session_state.executors.append(executor_name)
            st.success(f"Додано виконавця: {executor_name}")

with col2:
    if st.button("❌ Видалити виконавця"):
        if executor_name.strip() == "":
            st.error("Введіть виконавця для видалення.")
        elif executor_name not in st.session_state.executors:
            st.warning("Такого виконавця немає.")
        else:
            idx = st.session_state.executors.index(executor_name)
            st.session_state.executors.pop(idx)
            for roles_list in st.session_state.roles_data:
                roles_list.pop(idx)
            st.success(f"Виконавець '{executor_name}' видалений.")

if st.session_state.executors:
    st.write("**Поточні виконавці:**", ", ".join(map(str, st.session_state.executors)))

# --- 2️⃣ Введення та видалення процесів ---
st.header("Управління процесами")
process_name = st.text_input("Введіть назву процесу для додавання/видалення", key="process_input")

roles_for_process = {}
if st.session_state.executors:
    st.subheader("Оберіть ролі для нового процесу")
    for ex in st.session_state.executors:
        cols = st.columns([1, 2])
        with cols[0]:
            st.markdown(f"**{ex}**")
        with cols[1]:
            roles_for_process[ex] = st.radio(
                "",
                options=roles,
                index=0,
                horizontal=True,
                key=f"role_{ex}_{process_name}"
            )

col3, col4 = st.columns(2)
with col3:
    if st.button("➕ Додати процес"):
        if not process_name:
            st.error("Введіть назву процесу.")
        elif process_name in st.session_state.processes:
            st.error("Такий процес вже існує.")
        elif any(r == "" for r in roles_for_process.values()):
            st.error("Оберіть роль для кожного виконавця.")
        else:
            st.session_state.processes.append(process_name)
            st.session_state.roles_data.append(list(roles_for_process.values()))
            st.success(f"Процес '{process_name}' додано!")

with col4:
    if st.button("❌ Видалити процес"):
        if not process_name:
            st.error("Введіть назву процесу для видалення.")
        elif process_name not in st.session_state.processes:
            st.warning("Такого процесу немає.")
        else:
            idx = st.session_state.processes.index(process_name)
            st.session_state.processes.pop(idx)
            st.session_state.roles_data.pop(idx)
            st.success(f"Процес '{process_name}' видалено.")

if st.session_state.processes:
    st.write("**Поточні процеси:**", ", ".join(map(str, st.session_state.processes)))

# --- 3️⃣ Відображення RACI матриці ---
if st.session_state.processes:
    data = {"Процеси": st.session_state.processes}
    for idx, executor in enumerate(st.session_state.executors):
        data[executor] = [roles[idx] for roles in st.session_state.roles_data]

    raci_df = pd.DataFrame(data)
    st.subheader("📋 RACI Матриця")
    st.dataframe(raci_df)

# --- 4. Візуалізації ---
if st.session_state.processes:

    st.subheader("📊 Візуалізації")

    # Heatmap
    if st.button("Показати Heatmap"):
        role_map = {"R": 4, "A": 3, "C": 2, "I": 1, None: 0}
        heatmap_data = raci_df.drop(columns=["Процеси"]).apply(lambda col: col.map(lambda x: role_map.get(x, 0)))
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.heatmap(
            heatmap_data,
            annot=raci_df.drop(columns=["Процеси"]),
            fmt='',
            cmap="YlGnBu",
            yticklabels=[f"{i+1}" for i in range(len(raci_df))],
            ax=ax
        )
        plt.title("Ступінь залучення учасників у процесах")
        plt.xlabel("Учасники")
        plt.ylabel("Процеси")
        st.pyplot(fig)

    # Bar chart
    if st.button("Показати Bar Chart"):
        counts = {}
        for col in raci_df.columns[1:]:
            counts[col] = [raci_df[col].tolist().count(role) for role in roles]
        df_counts = pd.DataFrame(counts, index=roles)
        fig, ax = plt.subplots(figsize=(10, 5))
        df_counts.plot(kind="bar", ax=ax)
        plt.title("Розподіл ролей за учасниками")
        plt.ylabel("Кількість процесів")
        plt.xlabel("Ролі")
        plt.xticks(rotation=0)
        st.pyplot(fig)

    # Network graph
    if st.button("Показати Network Graph"):
        G = nx.Graph()
        process_nodes = raci_df["Процеси"].tolist()
        role_nodes = raci_df.columns[1:].tolist()
        G.add_nodes_from(process_nodes, bipartite=0)
        G.add_nodes_from(role_nodes, bipartite=1)

        for _, row in raci_df.iterrows():
            proc = row["Процеси"]
            for role in role_nodes:
                val = row[role]
                if val in roles:
                    G.add_edge(proc, role, role=val)

        # Розташування вузлів у два стовпці
        pos = dict()
        pos.update((node, (0, i)) for i, node in enumerate(process_nodes))
        pos.update((node, (3, i * 1.5)) for i, node in enumerate(role_nodes))

        plt.figure(figsize=(12, 6))
        nx.draw_networkx_nodes(G, pos, nodelist=process_nodes, node_color='lightblue', node_size=400)
        nx.draw_networkx_nodes(G, pos, nodelist=role_nodes, node_color='orange', node_size=400)

        # Підписи вузлів
        labels_all = {node: (str(i+1) if node in process_nodes else node) 
                      for i, node in enumerate(process_nodes)}
        labels_all.update({node: node for node in role_nodes})
        nx.draw_networkx_labels(G, pos, labels=labels_all)

        # Ребра з кольорами
        edge_colors = {'R':'red', 'A':'green', 'C':'blue', 'I':'gray'}
        nx.draw_networkx_edges(G, pos, edge_color=[edge_colors[G[u][v]['role']] for u,v in G.edges()])

        # Додаємо назву графіка та підписи для "Процеси" і "Виконавці"
        plt.title("Мережа взаємодій учасників та процесів", fontsize=14, fontweight='bold')
        plt.text(-0.5, -1, "Процеси", fontsize=12, color='black', ha='center')
        plt.text(3, -1, "Виконавці", fontsize=12, color='black', ha='center')

        plt.axis("off")
        st.pyplot(plt.gcf())

    # Activity chart: Частота ролей для кожного виконавця
    if st.button("Показати Activity Chart"):
        # Перетворюємо у довгий формат
        melted = raci_df.melt(id_vars='Процеси', var_name='Виконавець', value_name='Роль')
        role_counts = melted.value_counts(['Виконавець', 'Роль']).unstack(fill_value=0)

        # Побудова stacked bar chart
        fig, ax = plt.subplots(figsize=(12, 6))
        role_counts.plot(kind='bar', stacked=True, ax=ax, colormap='tab20')
        plt.xlabel('Виконавець', fontsize=11)
        plt.ylabel('Кількість ролей', fontsize=11)
        plt.title('Частота ролей RACI для кожного виконавця', fontsize=14, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
        plt.legend(title='Роль', bbox_to_anchor=(1.05, 1), loc='upper left')
        st.pyplot(fig)

# --- 5. Збереження в Excel ---
if st.session_state.processes:
    st.subheader("💾 Завантаження Excel")
    excel_path = "raci_table.xlsx"
    raci_df.to_excel(excel_path, index=False)
    with open(excel_path, "rb") as f:
        st.download_button("⬇️ Завантажити Excel", f, file_name="raci_table.xlsx")
