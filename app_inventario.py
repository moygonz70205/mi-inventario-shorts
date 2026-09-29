import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime
import time

# --- CONEXIÓN A SUPABASE ---
URL = "https://gfsaxfsnaksilxomaivt.supabase.co"
KEY = "sb_publishable_xN5SQe0Eq6bxTwv7PKyitQ_oG4VwnCd"
supabase = create_client(URL, KEY)

st.set_page_config(page_title="Taller Shorts - Gestión Empresarial", layout="wide")

# --- MENÚ LATERAL FORMAL ---
with st.sidebar:
    st.title("🧵 Taller Shorts")
    st.caption("Sistema Integrado de Control Operativo y Financiero")
    st.divider()
    seccion = st.radio("Menú Principal", [
        "🏠 Panel de Control Operativo",
        "📦 Inventario y Entrada de Inventario",
        "💰 Módulo de Ventas",
        "💸 Tesorería y Finanzas",
        "📜 Historial de Movimientos",
        "📊 Reporte del Negocio",
        "⚙️ Configuración de Productos"
    ])

# ============================================================
# 1. PANEL DE CONTROL OPERATIVO
# ============================================================
if seccion == "🏠 Panel de Control Operativo":
    st.header("🏠 Panel de Control Operativo")
    st.caption("Resumen ejecutivo en tiempo real sobre el estado financiero, ventas del día y nivel de existencias en almacén.")
    st.divider()

    ventas = supabase.table("historial").select("*").eq("tipo", "VENTA").execute().data
    inventario = supabase.table("inventario_ropa").select("*").execute().data
    finanzas = supabase.table("finanzas").select("*").eq("id", 1).execute().data

    hoy = datetime.today().strftime('%Y-%m-%d')
    ventas_hoy = sum(v["monto"] for v in ventas if str(v.get("created_at", "")).startswith(hoy)) if ventas else 0.0

    d_reinv = finanzas[0].get("dinero_reinversion", 0.0) if finanzas else 0.0
    d_libre = finanzas[0].get("dinero_libre", 0.0) if finanzas else 0.0
    d_emerg = finanzas[0].get("dinero_emergencia", 0.0) if finanzas else 0.0

    # El valor comercial se calcula SOLO con piezas disponibles (correctas)
    total_inv_valor = sum(p["cantidad"] * p["precio"] for p in inventario) if inventario else 0.0
    total_defectuosas = sum(p.get("cantidad_defectuosa", 0) or 0 for p in inventario) if inventario else 0
    pocos_prod = [p for p in inventario if p["cantidad"] <= 3] if inventario else []

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ventas del Día", f"${ventas_hoy:,.2f}")
    c2.metric("Capital y Crecimiento", f"${d_reinv:,.2f}")
    c3.metric("Rendimiento Propietario", f"${d_libre:,.2f}")
    c4.metric("Reserva Operativa", f"${d_emerg:,.2f}")

    st.subheader("📦 Estado General de Inventario")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Valor Comercial (Disponible)", f"${total_inv_valor:,.2f}")
    col_b.metric("Alertas Stock Bajo (≤ 3 pcs)", f"{len(pocos_prod)} prendas")
    col_c.metric("Piezas en Reproceso/Defecto", f"{total_defectuosas} pcs")

    if pocos_prod:
        st.warning("⚠️ **Atención:** Las siguientes prendas requieren reabastecimiento urgente (Stock Disponible ≤ 3):")
        st.dataframe(pd.DataFrame(pocos_prod)[["modelo", "tela", "color", "talla", "cantidad"]], use_container_width=True)

# ============================================================
# 2. INVENTARIO Y ENTRADA DE INVENTARIO (3 Pestañas Integradas)
# ============================================================
elif seccion == "📦 Inventario y Entrada de Inventario":
    st.header("📦 Gestión de Almacén e Ingresos")
    st.caption("Control centralizado de mercancía. Audita existencias, registra producción e independiza el stock en reproceso.")
    st.divider()

    tab1, tab2, tab3 = st.tabs([
        "📋 Ver Inventario en Stock", 
        "📥 Registrar Entrada de Mercancía", 
        "🛠️ Reproceso y Control de Defectos"
    ])

    # ---------------------------------------------------------
    # TAB 1: VER INVENTARIO
    # ---------------------------------------------------------
    with tab1:
        st.subheader("Resumen General de Existencias por Talla")
        datos_raw = supabase.table("inventario_ropa").select("*").execute().data

        if datos_raw:
            df_raw = pd.DataFrame(datos_raw)
            # Asegurar columna cantidad_defectuosa
            if "cantidad_defectuosa" not in df_raw.columns:
                df_raw["cantidad_defectuosa"] = 0
            df_raw["cantidad_defectuosa"] = df_raw["cantidad_defectuosa"].fillna(0).astype(int)

            # Sanitización visual
            df_raw["modelo"] = df_raw["modelo"].astype(str).str.strip().str.title()
            df_raw["tela"] = df_raw["tela"].astype(str).str.strip().str.title()
            df_raw["color"] = df_raw["color"].astype(str).str.strip().str.title()
            df_raw["talla"] = df_raw["talla"].astype(str).str.strip().str.upper()

            # Calcular total físico real
            df_raw["total_fisico"] = df_raw["cantidad"] + df_raw["cantidad_defectuosa"]

            # Agrupamiento automático
            df_grouped = df_raw.groupby(["modelo", "tela", "color", "talla", "precio"], as_index=False).agg({
                "cantidad": "sum",
                "cantidad_defectuosa": "sum",
                "total_fisico": "sum"
            })

            # Totales globales por categoría
            st.markdown("### 📊 Totales Globales por Tipo de Producto")
            totales_modelo = df_grouped.groupby("modelo")["cantidad"].sum()
            totales_defecto = df_grouped.groupby("modelo")["cantidad_defectuosa"].sum()
            
            total_disponible_gen = df_grouped["cantidad"].sum()
            total_defectuoso_gen = df_grouped["cantidad_defectuosa"].sum()
            
            cols_mod = st.columns(len(totales_modelo) + 2 if len(totales_modelo) > 0 else 2)
            cols_mod[0].metric(" Total Disponible", f"{total_disponible_gen} pcs")
            cols_mod[1].metric("🔴 Total Defectuosas", f"{total_defectuoso_gen} pcs")
            for idx, (mod_nombre, mod_cant) in enumerate(totales_modelo.items()):
                cols_mod[idx + 2].metric(f"Disponible {mod_nombre}s", f"{mod_cant} pcs")

            st.divider()

            st.markdown("**Matriz de Tallas (Solo Stock Disponible):**")
            resumen_tallas = df_grouped.groupby(["modelo", "tela", "talla"])["cantidad"].sum().unstack(fill_value=0)
            st.dataframe(resumen_tallas, use_container_width=True)
            
            st.divider()
            st.subheader("Consulta Detallada de Inventario")
            busqueda = st.text_input("🔍 Buscar por Modelo, Tela, Color o Talla")
            
            df_display = df_grouped.copy()
            if busqueda:
                b = busqueda.lower()
                df_display = df_display[
                    df_display["modelo"].str.lower().str.contains(b) |
                    df_display["tela"].str.lower().str.contains(b) |
                    df_display["color"].str.lower().str.contains(b) |
                    df_display["talla"].str.lower().str.contains(b)
                ]

            # Renombrar columnas para la tabla visual
            df_display_renamed = df_display.rename(columns={
                "modelo": "Modelo",
                "tela": "Tela",
                "color": "Color",
                "talla": "Talla",
                "cantidad": "Stock Disponible",
                "cantidad_defectuosa": "En Defecto 🔴",
                "total_fisico": "Total Físico en Taller",
                "precio": "Precio ($)"
            })

            # Aplicar formato condicional: Resaltar en rojo la columna de defectuosas si > 0
            def resaltar_defectuosas(val):
                color = 'background-color: #ffcccc; color: #990000; font-weight: bold;' if val > 0 else ''
                return color

            styled_df = df_display_renamed.style.map(resaltar_defectuosas, subset=["En Defecto 🔴"])
            st.dataframe(styled_df, use_container_width=True)

            # Ajuste Directo de Stock
            st.divider()
            st.subheader("🛠️ Ajuste Directo de Stock")
            st.caption("Modifica la cantidad disponible o defectuosa directamente en caso de mermas o recuentos de almacén.")
            
            registros_opciones = {
                f"ID #{r['id']} - {r['modelo']} | {r['tela']} | {r['color']} | Talla: {r['talla']} (Disp: {r['cantidad']} | Def: {r.get('cantidad_defectuosa', 0)})": r 
                for r in datos_raw
            }
            if registros_opciones:
                sel_reg_key = st.selectbox("Selecciona el registro específico a ajustar", list(registros_opciones.keys()))
                reg_sel = registros_opciones[sel_reg_key]

                col_aj1, col_aj2, col_aj3 = st.columns(3)
                nueva_cant_disp = col_aj1.number_input("Nuevo Stock Disponible", min_value=0, value=int(reg_sel["cantidad"]))
                nueva_cant_def = col_aj2.number_input("Nuevo Stock Defectuoso", min_value=0, value=int(reg_sel.get("cantidad_defectuosa", 0) or 0))
                
                if col_aj3.button("💾 Guardar Ajuste Directo", type="primary"):
                    supabase.table("inventario_ropa").update({
                        "cantidad": nueva_cant_disp,
                        "cantidad_defectuosa": nueva_cant_def
                    }).eq("id", reg_sel["id"]).execute()
                    
                    st.success(f" Stock actualizado. {reg_sel['modelo']} {reg_sel['color']} ({reg_sel['talla']}): Disponibles: {nueva_cant_disp} pcs | Defectuosas: {nueva_cant_def} pcs.")
                    time.sleep(2.0)
                    st.rerun()
        else:
            st.info("Sin mercancía registrada en inventario.")

    # ---------------------------------------------------------
    # TAB 2: REGISTRAR ENTRADA DE MERCANCÍA
    # ---------------------------------------------------------
    with tab2:
        st.subheader("Ingreso de Mercancía Producida")
        
        datos_inv_exist = supabase.table("inventario_ropa").select("*").execute().data
        configs = supabase.table("configuracion_productos").select("*").execute().data

        modo_ingreso = st.radio("Tipo de Ingreso", ["Añadir a Variantes Existentes", "➕ Registrar Nueva Variante / Producto Nuevo"], horizontal=True)

        if modo_ingreso == "Añadir a Variantes Existentes" and datos_inv_exist:
            df_ex = pd.DataFrame(datos_inv_exist)
            df_ex["modelo"] = df_ex["modelo"].astype(str).str.strip().str.title()
            df_ex["tela"] = df_ex["tela"].astype(str).str.strip().str.title()
            df_ex["color"] = df_ex["color"].astype(str).str.strip().str.title()

            c1, c2, c3 = st.columns(3)
            list_mod = sorted(df_ex["modelo"].unique())
            e_modelo = c1.selectbox("Modelo", list_mod)

            df_mod = df_ex[df_ex["modelo"] == e_modelo]
            list_tel = sorted(df_mod["tela"].unique())
            e_tela = c2.selectbox("Tela", list_tel)

            df_tel = df_mod[df_mod["tela"] == e_tela]
            list_col = sorted(df_tel["color"].unique())
            e_color = c3.selectbox("Color", list_col)

            # Preservar talla seleccionada
            if "talla_entrada_fija" not in st.session_state:
                st.session_state["talla_entrada_fija"] = "CH"

            tallas_posibles = ["CH", "M", "G", "XL"]
            talla_index = tallas_posibles.index(st.session_state["talla_entrada_fija"]) if st.session_state["talla_entrada_fija"] in tallas_posibles else 0

            e_talla = st.radio("Talla", tallas_posibles, index=talla_index, horizontal=True, key="radio_talla_ent")
            st.session_state["talla_entrada_fija"] = e_talla

            st.divider()
            col_c_ok, col_c_def = st.columns(2)
            e_cant_ok = col_c_ok.number_input("Piezas Correctas (Stock Disponible)", min_value=0, value=10)
            e_cant_def = col_c_def.number_input("Piezas con Defecto / Reproceso", min_value=0, value=0)

            cant_total_ingreso = e_cant_ok + e_cant_def

            cfg_item = next((c for c in configs if str(c.get("modelo")).strip().lower() == e_modelo.lower() and str(c.get("tela")).strip().lower() == e_tela.lower()), None) if configs else None
            default_precio = cfg_item.get("precio_venta", 65.0) if cfg_item else 65.0
            default_costo = cfg_item.get("costo_fabricacion", 30.0) if cfg_item else 30.0

            if st.button("📥 Registrar Entrada al Inventario", type="primary"):
                if cant_total_ingreso <= 0:
                    st.error("Debes ingresar al menos 1 pieza (sea correcta o defectuosa).")
                else:
                    existe = next((p for p in datos_inv_exist if p["modelo"].strip().title() == e_modelo and p["tela"].strip().title() == e_tela and p["color"].strip().title() == e_color and p["talla"].strip().upper() == e_talla), None)

                    if existe:
                        cant_ok_prev = existe["cantidad"]
                        cant_def_prev = existe.get("cantidad_defectuosa", 0) or 0

                        cant_ok_nuev = cant_ok_prev + e_cant_ok
                        cant_def_nuev = cant_def_prev + e_cant_def

                        supabase.table("inventario_ropa").update({
                            "cantidad": cant_ok_nuev,
                            "cantidad_defectuosa": cant_def_nuev,
                            "precio": default_precio
                        }).eq("id", existe["id"]).execute()
                        prod_id = existe["id"]
                    else:
                        cant_ok_prev = 0
                        cant_ok_nuev = e_cant_ok
                        cant_def_nuev = e_cant_def
                        ins = supabase.table("inventario_ropa").insert({
                            "modelo": e_modelo, "tela": e_tela, "color": e_color, "talla": e_talla, 
                            "cantidad": e_cant_ok, "cantidad_defectuosa": e_cant_def, "precio": default_precio
                        }).execute()
                        prod_id = ins.data[0]["id"] if ins.data else None

                    # Registro de gasto de fabricación total
                    supabase.table("historial").insert({
                        "tipo": "ENTRADA",
                        "detalle": f"Entrada: {e_modelo} {e_tela} {e_color} {e_talla} ({e_cant_ok} OK, {e_cant_def} Defectuosas)",
                        "cantidad": cant_total_ingreso,
                        "monto": cant_total_ingreso * default_costo,
                        "costo_unitario": default_costo,
                        "precio_unitario": default_precio,
                        "producto_id": prod_id
                    }).execute()

                    st.success(f" Inventario Actualizado | Ingresadas: {e_cant_ok} correctas + {e_cant_def} defectuosas de {e_modelo} {e_tela} ({e_color} / {e_talla}). Movimiento Exitoso.")
                    st.balloons()
                    time.sleep(2.0)
                    st.rerun()

        else:
            with st.form("form_alta_nuevo"):
                st.info("Ingresa los datos del nuevo tipo de prenda o color que no existe actualmente en catálogo.")
                col_n1, col_n2 = st.columns(2)
                n_modelo = col_n1.text_input("Tipo de Producto / Modelo", "Short")
                n_tela = col_n1.text_input("Tipo de Tela", "Liso")
                n_color = col_n2.text_input("Color", "Negro")
                n_talla = col_n2.radio("Talla", ["CH", "M", "G", "XL"], horizontal=True)
                
                col_n_ok, col_n_def = st.columns(2)
                n_cant_ok = col_n_ok.number_input("Piezas Correctas Iniciales", min_value=0, value=8)
                n_cant_def = col_n_def.number_input("Piezas Defectuosas Iniciales", min_value=0, value=2)

                n_precio = st.number_input("Precio de Venta Unitario ($)", min_value=0.0, value=65.0)
                n_costo = st.number_input("Costo de Fabricación Unitario ($)", min_value=0.0, value=30.0)

                if st.form_submit_button(" Registrar Nueva Entrada y Crear Producto"):
                    n_cant_total = n_cant_ok + n_cant_def
                    if n_cant_total <= 0:
                        st.error("Debes ingresar al menos 1 pieza.")
                    else:
                        n_modelo_clean = n_modelo.strip().title()
                        n_tela_clean = n_tela.strip().title()
                        n_color_clean = n_color.strip().title()
                        n_talla_clean = n_talla.strip().upper()

                        ins = supabase.table("inventario_ropa").insert({
                            "modelo": n_modelo_clean, "tela": n_tela_clean, "color": n_color_clean, "talla": n_talla_clean, 
                            "cantidad": n_cant_ok, "cantidad_defectuosa": n_cant_def, "precio": n_precio
                        }).execute()
                        
                        prod_id = ins.data[0]["id"] if ins.data else None

                        supabase.table("historial").insert({
                            "tipo": "ENTRADA",
                            "detalle": f"Entrada Nueva: {n_modelo_clean} {n_tela_clean} {n_color_clean} {n_talla_clean} ({n_cant_ok} OK, {n_cant_def} Defectuosas)",
                            "cantidad": n_cant_total,
                            "monto": n_cant_total * n_costo,
                            "costo_unitario": n_costo,
                            "precio_unitario": n_precio,
                            "producto_id": prod_id
                        }).execute()

                        st.success(f" Inventario Actualizado | Registradas: {n_cant_ok} correctas + {n_cant_def} defectuosas de {n_modelo_clean} {n_tela_clean} ({n_color_clean} / {n_talla_clean}).")
                        st.balloons()
                        time.sleep(2.0)
                        st.rerun()

    # ---------------------------------------------------------
    # TAB 3: REPROCESO Y CONTROL DE DEFECTOS (Bidireccional)
    # ---------------------------------------------------------
    with tab3:
        st.subheader("🛠️ Gestión de Prendas en Reproceso y Liberación")
        st.caption("Administra piezas con fallas de costura. Pásalas de 'Disponible' a 'Defectuoso' si encuentras detalles, o 'Libéralas' cuando queden reparadas.")
        
        datos_inv_rep = supabase.table("inventario_ropa").select("*").execute().data

        if datos_inv_rep:
            col_rep1, col_rep2 = st.columns(2)

            # ACCIÓN A: PASAR DE DISPONIBLE ➔ DEFECTUOSO
            with col_rep1:
                st.markdown("### ⚠️ Reportar Falla Encontrada")
                st.caption("Mueve piezas de Stock Disponible hacia Defectuosas (al detectar un fallo en tienda/estante).")

                opts_disp = {
                    f"{r['modelo']} {r['tela']} {r['color']} ({r['talla']}) - Disponible: {r['cantidad']} pcs": r 
                    for r in datos_inv_rep if r['cantidad'] > 0
                }

                if opts_disp:
                    sel_rep_disp_key = st.selectbox("Selecciona prenda con detalle", list(opts_disp.keys()), key="sb_rep_disp")
                    reg_rep_disp = opts_disp[sel_rep_disp_key]

                    cant_mover_def = st.number_input("Cantidad a mover a Defectuosas", min_value=1, max_value=int(reg_rep_disp["cantidad"]), value=1, key="num_def")

                    if st.button("⚠️ Mover a Defectuosas", type="secondary"):
                        n_disp = reg_rep_disp["cantidad"] - cant_mover_def
                        n_def = (reg_rep_disp.get("cantidad_defectuosa", 0) or 0) + cant_mover_def

                        supabase.table("inventario_ropa").update({
                            "cantidad": n_disp,
                            "cantidad_defectuosa": n_def
                        }).eq("id", reg_rep_disp["id"]).execute()

                        supabase.table("historial").insert({
                            "tipo": "REPROCESO",
                            "detalle": f"Reporte Defecto: {reg_rep_disp['modelo']} {reg_rep_disp['t
