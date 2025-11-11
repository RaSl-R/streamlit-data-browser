import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from utils.db import get_engine
import math
import re
import os

DEFAULT_ROW_LIMIT = 10000
PAGE_SIZE = 50

@st.cache_data
def list_schemas(_conn):
    result = _conn.execute(text("SELECT schema_name FROM information_schema.schemata"))
    return [row[0] for row in result]

@st.cache_data
def list_user_schemas(user_email: str):
    from utils.db import get_engine
    with get_engine().begin() as conn:
        query = text("""
            SELECT DISTINCT p.schema_name
            FROM auth.users u
            JOIN auth.user_groups ug ON u.id = ug.user_id
            JOIN auth.group_schema_permissions p ON ug.group_id = p.group_id
            WHERE u.email = :email
            ORDER BY p.schema_name;
        """)
        result = conn.execute(query, {"email": user_email})
        return [row[0] for row in result]

@st.cache_data
def list_tables(schema_name: str):
    from utils.db import get_engine
    with get_engine().begin() as conn:
        result = conn.execute(
            text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = :schema
            """),
            {"schema": schema_name}
        )
        return {row[0]: f"{schema_name}.{row[0]}" for row in result}

def validate_table_id(table_id: str) -> str:
    try:
        schema_name, table_name = table_id.split('.', 1)
    except ValueError:
        raise ValueError(f"Neplatný formát table_id: {table_id}. Očekáván 'schema.table'.")

    tables_dict = list_tables(schema_name)
    if table_id not in tables_dict.values():
        raise ValueError(f"Neplatný nebo nepovolený název tabulky: {table_id}")
    
    safe_table_sql = f'"{schema_name}"."{table_name}"'
    return safe_table_sql

def validate_where_clause(where_clause: str, df_columns: list = None) -> str:
    if not where_clause:
        return ""
    
    if ";" in where_clause:
        raise ValueError("WHERE klauzule nesmí obsahovat středník")
    
    forbidden = re.compile(r"\b(DELETE|UPDATE|INSERT|DROP|ALTER|EXEC|EXECUTE)\b", re.IGNORECASE)
    if forbidden.search(where_clause):
        raise ValueError("WHERE klauzule obsahuje zakázané SQL příkazy")
    
    if "--" in where_clause or "/*" in where_clause:
        raise ValueError("WHERE klauzule nesmí obsahovat komentáře")
    
    if df_columns:
        column_pattern = r"\b(" + "|".join(re.escape(col) for col in df_columns) + r")\b"
        if not re.search(column_pattern, where_clause, re.IGNORECASE):
            raise ValueError(f"WHERE klauzule neobsahuje žádný platný sloupec z: {df_columns}")
    
    return where_clause.strip()

@st.cache_data
def get_row_count(table_id: str, where_clause: str = None) -> int:
    """Vrací celkový počet řádků v tabulce (s volitelným WHERE)."""
    try:
        safe_table_sql = validate_table_id(table_id)
        query = f"SELECT COUNT(*) FROM {safe_table_sql}"

        if where_clause:
            safe_where_clause = validate_where_clause(where_clause)
            if safe_where_clause:
                query += f" WHERE {safe_where_clause}"

        from utils.db import get_engine
        with get_engine().begin() as conn:
            result = conn.execute(text(query)).scalar()
            return int(result)
    except Exception as e:
        st.error(f"Chyba při zjišťování počtu řádků: {e}")
        return 0

@st.cache_data(ttl=3600)
def load_table(table_id, offset=0, limit=PAGE_SIZE):
    try:
        safe_table_sql = validate_table_id(table_id)
        from utils.db import get_engine
        with get_engine().begin() as conn:
            query_sql = f"SELECT * FROM {safe_table_sql} ORDER BY 1 LIMIT :limit OFFSET :offset"
            result = conn.execute(text(query_sql), {"limit": limit, "offset": offset})
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            return df
    except Exception as e:
        st.error(f"Došlo k chybě při načítání tabulky: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_table_filtered(table_id, where_clause=None, offset=0, limit=PAGE_SIZE):
    try:
        safe_table_sql = validate_table_id(table_id)
        query_sql = f"SELECT * FROM {safe_table_sql}"
        from utils.db import get_engine
        with get_engine().begin() as conn:
            if where_clause:
                safe_where_clause = validate_where_clause(where_clause)
                if safe_where_clause:
                    query_sql += f" WHERE {safe_where_clause}"
                else:
                    st.warning("WHERE výraz není validní. Byl ignorován.")
            query_sql += " ORDER BY 1 LIMIT :limit OFFSET :offset"
            result = conn.execute(text(query_sql), {"limit": limit, "offset": offset})
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            return df
    except Exception as e:
        st.error(f"Došlo k chybě při načítání tabulky: {e}")
        return pd.DataFrame()

def replace_table(table_id, df):
    try:
        from utils.db import get_engine
        safe_table_sql = validate_table_id(table_id)
        schema_name, table_name = table_id.split('.', 1) 
        with get_engine().begin() as conn:
            conn.execute(text(f'DROP TABLE IF EXISTS {safe_table_sql} CASCADE'))
            create_sql = pd.io.sql.get_schema(df, table_name, con=conn, schema=schema_name)
            conn.execute(text(create_sql))
            df.to_sql(table_name, conn, schema=schema_name, if_exists='append', index=False,
                      method='multi')
    except Exception as e:
        st.error(f"Došlo k chybě při načítání tabulky: {e}")
        return pd.DataFrame()

def display_data_editor(df_to_edit, editor_key):
    edited_df = st.data_editor(
        df_to_edit,
        num_rows="dynamic",
        width='stretch',
        key=editor_key
    )
    return edited_df

def clear_filter_callback():
    st.session_state.where_input = ""
    st.session_state.where_clause = ""
    st.session_state.filter_applied = False
    st.session_state.current_page = 1
    st.session_state.reload_data = True

def main_data_browser():
    st.set_page_config(layout="wide")
    st.title("📊 Data browser")

    if "message" in st.session_state:
        st.success(st.session_state.message)
        del st.session_state.message

    if "editor_key_counter" not in st.session_state:
        st.session_state.editor_key_counter = 0
    if "filter_applied" not in st.session_state:
        st.session_state.filter_applied = False
    if "where_clause" not in st.session_state:
        st.session_state.where_clause = ""

    # Načteme schémata specifická pro přihlášeného uživatele
    schemas = list_user_schemas(st.session_state.user_email)

    # Důležitá kontrola pro případ, že uživatel nemá přístup nikam
    if not schemas:
        st.warning("Nemáte přiřazeno oprávnění k žádnému schématu. Obraťte se na administrátora.")
        st.stop()

    selected_schema = st.selectbox(
        "📁 Vyber schéma",
        schemas,
        # 'public' už nemusí být vždy dostupné, tak index nastavíme na 0
        index=0,
        key="selected_schema"
    )

    tables_dict = list_tables(selected_schema)

    if not tables_dict:
        st.info("Zvolené schéma neobsahuje žádnou tabulku.")
        st.stop()

    selected_table_name = st.selectbox("📂 Vyber tabulku", options=list(tables_dict.keys()))
    selected_table_id = tables_dict[selected_table_name]

    # --- PŘIDAT TUTO NOVOU LOGIKU ---
    # Sledujeme ID aktuální tabulky, abychom zjistili, zda se změnila
    if "current_table_id" not in st.session_state:
        st.session_state.current_table_id = selected_table_id

    # Pokud se nově vybraná tabulka liší od té, co byla v session state
    if st.session_state.current_table_id != selected_table_id:
        st.session_state.current_page = 1
        st.session_state.reload_data = True
        st.session_state.current_table_id = selected_table_id
        # Musíme také vymazat filtr, protože se vztahoval ke staré tabulce
        clear_filter_callback() 
        st.rerun() # Okamžitě znovu načteme s novým stavem
        
    st.session_state.current_table_id = selected_table_id
    # --- KONEC NOVÉ LOGIKY ---

    if not selected_table_id:
        st.info("Nebyla vybrána žádná validní tabulka.")
        st.stop()

    col_expander, col2, col3, _, _ = st.columns([2.5, 1, 1, 0.5, 0.5])

    with col_expander:
        expander_label = "🔍 Filtrováno" if st.session_state.filter_applied else "🔍 Filtr"
        expander_style = (
            "background-color: rgba(255, 255, 0, 0.1); border-radius: 5px;"
            if st.session_state.filter_applied else ""
        )

        with st.expander(expander_label):
            where_clause = st.text_input(
                "Zadej WHERE podmínku (bez klíčového slova 'WHERE')",
                placeholder="např.: amount > 100 AND status = 'active'",
                key="where_input"
            )
            col_clear_btn, col_filter_btn = st.columns(2)
            with col_clear_btn:
                st.button("❌ Zrušit filtr", key="clear_filter_button", on_click=clear_filter_callback)
            with col_filter_btn:
                apply_filter = st.button("🔽 Filtrovat", key="filter_button")

    if "reload_data" not in st.session_state:
        st.session_state.reload_data = True

    # Inicializace session state pro stránkování
    if "current_page" not in st.session_state:
        st.session_state.current_page = 1

    # Pokud se změní filtr nebo tabulka, resetujeme stránku na 1
    # (Toto je zjednodušená logika, možná bude potřeba ji zpřesnit)
    # if st.session_state.reload_data:
    #     st.session_state.current_page = 1

    # Získání celkového počtu řádků
    where_cond = st.session_state.where_clause if st.session_state.filter_applied else None
    total_rows = get_row_count(selected_table_id, where_cond)
    total_pages = math.ceil(total_rows / PAGE_SIZE) if total_rows > 0 else 1

    # Výpočet offsetu
    current_offset = (st.session_state.current_page - 1) * PAGE_SIZE

    # Načtení dat pro aktuální stránku
    df = None
    editor_key = f"editor_{st.session_state.editor_key_counter}"

    if st.session_state.reload_data:
        if st.session_state.filter_applied and st.session_state.where_clause:
            df = load_table_filtered(
                selected_table_id,
                st.session_state.where_clause,
                offset=current_offset,
                limit=PAGE_SIZE
            )
        else:
            df = load_table(selected_table_id, offset=current_offset, limit=PAGE_SIZE)

        st.session_state.reload_data = False

    if df is None:
        df = load_table(selected_table_id, offset=current_offset, limit=PAGE_SIZE)

    if apply_filter and where_clause:
        st.session_state.where_clause = where_clause
        st.session_state.filter_applied = True
        st.session_state.reload_data = True
        st.session_state.current_page = 1
        st.session_state.editor_key_counter += 1
        st.rerun()

    st.caption(f"Zobrazeno {len(df)} z {total_rows} záznamů | Stránka {st.session_state.current_page}/{total_pages}")
    edited_df = display_data_editor(df, editor_key)

    # --- NOVÉ UI PRO STRÁNKOVÁNÍ ---
    if (total_rows > PAGE_SIZE):
        p_col1, p_col2, p_col3, p_col4, spacer = st.columns([1.2, 1.8, 1.8, 1.2, 6], gap="small")
        if p_col1.button("<< První", width='stretch', disabled=(st.session_state.current_page == 1)):
            st.session_state.current_page = 1
            st.session_state.reload_data = True
            st.session_state.editor_key_counter += 1
            st.rerun()
        if p_col2.button("< Předchozí", width='stretch', disabled=(st.session_state.current_page == 1)):
            st.session_state.current_page -= 1
            st.session_state.reload_data = True
            st.session_state.editor_key_counter += 1
            st.rerun()
        if p_col3.button("Další >", width='stretch', disabled=(st.session_state.current_page == total_pages)):
            st.session_state.current_page += 1
            st.session_state.reload_data = True
            st.session_state.editor_key_counter += 1
            st.rerun()
        if p_col4.button("Poslední >>", width='stretch', disabled=(st.session_state.current_page == total_pages)):
            st.session_state.current_page = total_pages
            st.session_state.reload_data = True
            st.session_state.editor_key_counter += 1
            st.rerun()
        st.info(f"💡 Zobrazeno {len(df)} řádků z celkových {total_rows}. Pro další data použijte tlačítka stránkování výše.")
    # --- Konec UI pro stránkování ---

    if col2.button("🔁 ROLLBACK", width='stretch'):
        load_table.clear()
        st.session_state.reload_data = True
        st.session_state.editor_key_counter += 1
        st.session_state.message = "Změny byly zahozeny (ROLLBACK) – data byla znovu načtena z databáze."
        st.rerun()

    if col3.button("💾 COMMIT", width='stretch'):
        # KROK 1: Zkontrolujeme oprávnění uživatele na základě nového modelu
        schema_name, _ = selected_table_id.split('.', 1)
        user_permissions = st.session_state.get('permissions', {})
        permission_for_schema = user_permissions.get(schema_name)

        # Oprávnění 'write' je vyžadováno pro změn
        if permission_for_schema != 'write':
            st.error(f"🚫 Nemáte oprávnění 'write' k zápisu do schématu '{schema_name}'.")
        else:
            # KROK 2: Pokud má uživatel oprávnění 'write', provedeme původní logiku
            try:
                # ... (zbytek logiky pro COMMIT zůstává stejný) ...
                replace_table(selected_table_id, edited_df)
                load_table.clear()
                st.session_state.reload_data = True
                st.session_state.editor_key_counter += 1
                st.session_state.message = "Změny byly uloženy (COMMIT)."
                st.rerun()
            except Exception as e:
                st.error(f"Chyba při COMMITu: {e}")

    with st.expander("⬇️ Export do CSV"):
        csv = edited_df.to_csv(index=False).encode('utf-8')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{selected_table_name}_{timestamp}.csv"
        st.download_button(
            "📥 Stáhnout aktuální pohled jako CSV",
            csv,
            file_name=file_name,
            mime='text/csv'
        )

    with st.expander("⬆️ Import CSV – přepsání tabulky"):
        uploaded_file = st.file_uploader("Vyber CSV soubor", type="csv")
        if uploaded_file:
            try:
                imported_df = pd.read_csv(uploaded_file)
                st.dataframe(imported_df, width='stretch')
                if st.button("🚨 Nahradit celou tabulku importovanými daty"):
                    replace_table(selected_table_id, imported_df)
                    load_table.clear()
                    st.session_state.reload_data = True
                    st.session_state.editor_key_counter += 1
                    st.session_state.message = "Tabulka byla nahrazena."
                    st.rerun()
            except Exception as e:
                st.error(f"Chyba při importu: {e}")

if __name__ == "__main__":
    main_data_browser()