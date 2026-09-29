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

    total_inv_valor = sum(p["cantidad"] * p["precio"] for p in inventario) if inventario else 0.0
    pocos_prod = [p for p in inventario if p["cantidad"] <= 3] if inventario else []

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ventas del Día", f"${ventas_hoy:,.2f}")
    c2.metric("Capital y Crecimiento", f"${d_reinv:,.2f}")
    c3.metric("Rendimiento Propietario", f"${d_libre:,.2f}")
    c4.metric("Reserva Operativa", f"${d_emerg:,.2f}")

    st.subheader("📦 Estado General de Inventario")
    col_a, col_b = st.columns(2)
    col_a.metric("Valor Comercial en Stock", f"${total_inv_valor:,.2f}")
    col_b.metric("Alertas de Stock Bajo (≤ 3 pcs)", f"{len(pocos_prod)} prendas")

    if pocos_prod:
        st.warning("⚠️ **Atención:** Las siguientes prendas requieren reabastecimiento urgente:")
        st.dataframe(pd.DataFrame(pocos_prod)[["modelo", "tela", "color", "talla", "cantidad"]], use_container_width=True)

# ============================================================
# 2. INVENTARIO Y ENTRADA DE INVENTARIO
# ============================================================
elif seccion == "📦 Inventario y Entrada de Inventario":
    st.header("📦 Gestión de Almacén e Ingresos")
    st.caption("Control centralizado de mercancía. Permite auditar existencias por modelo, tela, color y talla, así como ingresar nueva producción.")
    st.divider()

    tab1, tab2 = st.tabs(["📋 Ver Inventario en Stock", "📥 Registrar Entrada de Mercancía"])

    with tab1:
        st.subheader("Resumen General de Existencias por Talla")
        datos_raw = supabase.table("inventario_ropa").select("*").execute().data

        if datos_raw:
            df_raw = pd.DataFrame(datos_raw)
            # Sanitización visual: limpiar espacios y estandarizar mayúsculas/minúsculas
            df_raw["modelo"] = df_raw["modelo"].astype(str).str.strip().str.title()
            df_raw["tela"] = df_raw["tela"].astype(str).str.strip().str.title()
            df_raw["color"] = df_raw["color"].astype(str).str.strip().str.title()
            df_raw["talla"] = df_raw["talla"].astype(str).str.strip().str.upper()

            # Agrupamiento automático para evitar duplicados en pantalla
            df_grouped = df_raw.groupby(["modelo", "tela", "color", "talla", "precio"], as_index=False)["cantidad"].sum()

            # Totales por Categoría / Tipo de Producto
            st.markdown("### 📊 Totales Globales por Tipo de Producto")
            totales_modelo = df_grouped.groupby("modelo")["cantidad"].sum()
            
            total_piezas_general = totales_modelo.sum()
            
            # Mostrar Métricas resumen
            cols_mod = st.columns(len(totales_modelo) + 1 if len(totales_modelo) > 0 else 1)
            cols_mod[0].metric("Total Piezas Global", f"{total_piezas_general} pcs")
            for idx, (mod_nombre, mod_cant) in enumerate(totales_modelo.items()):
                cols_mod[idx + 1].metric(f"Total {mod_nombre}s", f"{mod_cant} pcs")

            st.divider()

            resumen_tallas = df_grouped.groupby(["modelo", "tela", "talla"])["cantidad"].sum().unstack(fill_value=0)
            st.dataframe(resumen_tallas, use_container_width=True)
            
            st.divider()
            st.subheader("Consulta Detallada de Inventario (Consolidado)")
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
            st.dataframe(df_display, use_container_width=True)

            # Ajuste Directo de Stock
            st.divider()
            st.subheader("🛠️ Ajuste Directo de Stock")
            st.caption("Modifica únicamente la cantidad final en caso de mermas o recuentos de almacén.")
            
            registros_opciones = {
                f"ID #{r['id']} - {r['modelo']} | {r['tela']} | {r['color']} | Talla: {r['talla']} (Actual: {r['cantidad']} pcs)": r 
                for r in datos_raw
            }
            if registros_opciones:
                sel_reg_key = st.selectbox("Selecciona el registro específico a ajustar", list(registros_opciones.keys()))
                reg_sel = registros_opciones[sel_reg_key]

                col_aj1, col_aj2 = st.columns(2)
                nueva_cant = col_aj1.number_input("Nueva cantidad total en Stock", min_value=0, value=int(reg_sel["cantidad"]))
                
                if col_aj2.button("💾 Guardar Ajuste de Stock", type="primary"):
                    supabase.table("inventario_ropa").update({"cantidad": nueva_cant}).eq("id", reg_sel["id"]).execute()
                    
                    st.success(f"Stock actualizado. {reg_sel['modelo']} {reg_sel['color']} ({reg_sel['talla']}): Antes {reg_sel['cantidad']} pcs ➔ Ahora {nueva_cant} pcs.")
                    time.sleep(2.0)
                    st.rerun()
        else:
            st.info("Sin mercancía registrada en inventario.")

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

            if "talla_entrada_fija" not in st.session_state:
                st.session_state["talla_entrada_fija"] = "CH"

            tallas_posibles = ["CH", "M", "G", "XL"]
            talla_index = tallas_posibles.index(st.session_state["talla_entrada_fija"]) if st.session_state["talla_entrada_fija"] in tallas_posibles else 0

            e_talla = st.radio("Talla", tallas_posibles, index=talla_index, horizontal=True, key="radio_talla_ent")
            st.session_state["talla_entrada_fija"] = e_talla

            col_cant, col_btn = st.columns(2)
            e_cant = col_cant.number_input("Cantidad de Piezas a Sumar", min_value=1, value=1)

            cfg_item = next((c for c in configs if str(c.get("modelo")).strip().lower() == e_modelo.lower() and str(c.get("tela")).strip().lower() == e_tela.lower()), None) if configs else None
            default_precio = cfg_item.get("precio_venta", 65.0) if cfg_item else 65.0
            default_costo = cfg_item.get("costo_fabricacion", 30.0) if cfg_item else 30.0

            if st.button("📥 Registrar Entrada al Inventario", type="primary"):
                existe = next((p for p in datos_inv_exist if p["modelo"].strip().title() == e_modelo and p["tela"].strip().title() == e_tela and p["color"].strip().title() == e_color and p["talla"].strip().upper() == e_talla), None)

                if existe:
                    cant_anterior = existe["cantidad"]
                    cant_nueva = cant_anterior + e_cant
                    supabase.table("inventario_ropa").update({
                        "cantidad": cant_nueva, "precio": default_precio
                    }).eq("id", existe["id"]).execute()
                    prod_id = existe["id"]
                else:
                    cant_anterior = 0
                    cant_nueva = e_cant
                    ins = supabase.table("inventario_ropa").insert({
                        "modelo": e_modelo, "tela": e_tela, "color": e_color, "talla": e_talla, "cantidad": e_cant, "precio": default_precio
                    }).execute()
                    prod_id = ins.data[0]["id"] if ins.data else None

                supabase.table("historial").insert({
                    "tipo": "ENTRADA",
                    "detalle": f"Entrada: {e_modelo} {e_tela} {e_color} {e_talla}",
                    "cantidad": e_cant,
                    "monto": e_cant * default_costo,
                    "costo_unitario": default_costo,
                    "precio_unitario": default_precio,
                    "producto_id": prod_id
                }).execute()

                st.success(f"Inventario Actualizado | Stock actualizado: Tenías {cant_anterior} pcs + Agregaste {e_cant} pcs = Total {cant_nueva} pcs ({e_modelo} {e_tela} {e_color} {e_talla}). Movimiento Exitoso.")
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
                
                n_cant = st.number_input("Cantidad de Piezas Iniciales", min_value=1, value=1)
                n_precio = st.number_input("Precio de Venta Unitario ($)", min_value=0.0, value=65.0)
                n_costo = st.number_input("Costo de Fabricación Unitario ($)", min_value=0.0, value=30.0)

                if st.form_submit_button("Registrar Nueva Entrada y Crear Producto"):
                    n_modelo_clean = n_modelo.strip().title()
                    n_tela_clean = n_tela.strip().title()
                    n_color_clean = n_color.strip().title()
                    n_talla_clean = n_talla.strip().upper()

                    ins = supabase.table("inventario_ropa").insert({
                        "modelo": n_modelo_clean, "tela": n_tela_clean, "color": n_color_clean, "talla": n_talla_clean, "cantidad": n_cant, "precio": n_precio
                    }).execute()
                    
                    prod_id = ins.data[0]["id"] if ins.data else None

                    supabase.table("historial").insert({
                        "tipo": "ENTRADA",
                        "detalle": f"Entrada Nueva: {n_modelo_clean} {n_tela_clean} {n_color_clean} {n_talla_clean}",
                        "cantidad": n_cant,
                        "monto": n_cant * n_costo,
                        "costo_unitario": n_costo,
                        "precio_unitario": n_precio,
                        "producto_id": prod_id
                    }).execute()

                    st.success(f"Inventario Actualizado | Stock inicial: {n_cant} pcs agregadas de {n_modelo_clean} {n_tela_clean} ({n_color_clean} / {n_talla_clean}). Movimiento Exitoso.")
                    st.balloons()
                    time.sleep(2.0)
                    st.rerun()

# ============================================================
# 3. MÓDULO DE VENTAS
# ============================================================
elif seccion == "💰 Módulo de Ventas":
    st.header("💰 Módulo de Ventas")
    st.caption("Punto de registro de salidas comerciales. Actualiza automáticamente el stock disponible y calcula la distribución de utilidades.")
    st.divider()

    datos = supabase.table("inventario_ropa").select("*").execute().data
    configs = supabase.table("configuracion_productos").select("*").execute().data

    if datos:
        for d in datos:
            d["modelo"] = str(d["modelo"]).strip().title()
            d["tela"] = str(d["tela"]).strip().title()
            d["color"] = str(d["color"]).strip().title()
            d["talla"] = str(d["talla"]).strip().upper()

        c1, c2, c3 = st.columns(3)
        with c1:
            modelos = sorted(list(set([d["modelo"] for d in datos])))
            modelo = st.selectbox("Selecciona Modelo", modelos)
        with c2:
            telas = sorted(list(set([d["tela"] for d in datos if d["modelo"] == modelo])))
            tela = st.selectbox("Selecciona Tela", telas)
        with c3:
            colores = sorted(list(set([d["color"] for d in datos if d["modelo"] == modelo and d["tela"] == tela])))
            color = st.selectbox("Selecciona Color", colores)

        st.subheader("Selecciona Talla")
        tallas_disp = sorted(list(set([d["talla"] for d in datos if d["modelo"] == modelo and d["tela"] == tela and d["color"] == color])))

        if "talla_venta_fija" not in st.session_state:
            st.session_state["talla_venta_fija"] = tallas_disp[0] if tallas_disp else "CH"

        if st.session_state["talla_venta_fija"] in tallas_disp:
            talla_act_idx = tallas_disp.index(st.session_state["talla_venta_fija"])
        else:
            talla_act_idx = 0
            st.session_state["talla_venta_fija"] = tallas_disp[0] if tallas_disp else "CH"

        talla = st.radio("Talla Disponible", tallas_disp, index=talla_act_idx, horizontal=True, key="radio_talla_vent")
        st.session_state["talla_venta_fija"] = talla

        prods_coincidentes = [p for p in datos if p["modelo"]==modelo and p["tela"]==tela and p["color"]==color and p["talla"]==talla]
        
        if prods_coincidentes:
            cant_total_stock = sum(p["cantidad"] for p in prods_coincidentes)
            precio_unitario = prods_coincidentes[0]["precio"]
            prod_principal = prods_coincidentes[0]

            st.divider()
            col_info1, col_info2 = st.columns(2)
            
            if cant_total_stock <= 0:
                col_info1.error("❌ **PRODUCTO AGOTADO** - Stock: 0 piezas")
            elif cant_total_stock <= 3:
                col_info1.warning(f"⚠️ **STOCK BAJO** - Quedan solo {cant_total_stock} pieza(s)")
            else:
                col_info1.success(f"📦 **Stock Disponible:** {cant_total_stock} pieza(s)")

            col_info2.info(f"💲 **Precio Unitario:** ${precio_unitario:.2f}")

            if cant_total_stock > 0:
                cant_vender = st.number_input("Cantidad a vender", min_value=1, max_value=cant_total_stock, value=1)
                
                cfg_item = next((c for c in configs if str(c.get("modelo")).strip().lower() == modelo.lower() and str(c.get("tela")).strip().lower() == tela.lower()), None) if configs else None
                costo_fab = cfg_item.get("costo_fabricacion", 30.0) if cfg_item else 30.0
                
                pct_crec = (cfg_item.get("porcentaje_crecimiento", 60) / 100) if cfg_item else 0.60
                pct_disp = (cfg_item.get("porcentaje_disponibilidad", 30) / 100) if cfg_item else 0.30
                pct_emer = (cfg_item.get("porcentaje_emergencia", 10) / 100) if cfg_item else 0.10

                monto_total = cant_vender * precio_unitario
                costo_total = cant_vender * costo_fab
                utilidad_total = monto_total - costo_total

                utilidad_crecimiento = utilidad_total * pct_crec
                c_reinv_total = costo_total + utilidad_crecimiento
                c_libre = utilidad_total * pct_disp
                c_emerg = utilidad_total * pct_emer

                st.write(f"**Desglose estimado:** Total: **${monto_total:,.2f}** | Capital + Crecimiento: **${c_reinv_total:,.2f}** | Rendimiento: **${c_libre:,.2f}** | Reserva: **${c_emerg:,.2f}**")

                if st.button("🛒 Confirmar y Registrar Venta", type="primary"):
                    cant_pendiente = cant_vender
                    for p_sub in prods_coincidentes:
                        if cant_pendiente <= 0:
                            break
                        descuento = min(p_sub["cantidad"], cant_pendiente)
                        supabase.table("inventario_ropa").update({"cantidad": p_sub["cantidad"] - descuento}).eq("id", p_sub["id"]).execute()
                        cant_pendiente -= descuento

                    fin = supabase.table("finanzas").select("*").eq("id", 1).execute().data
                    if fin:
                        f_act = fin[0]
                        supabase.table("finanzas").update({
                            "dinero_reinversion": f_act.get("dinero_reinversion", 0.0) + c_reinv_total,
                            "dinero_libre": f_act.get("dinero_libre", 0.0) + c_libre,
                            "dinero_emergencia": f_act.get("dinero_emergencia", 0.0) + c_emerg
                        }).eq("id", 1).execute()

                    supabase.table("historial").insert({
                        "tipo": "VENTA",
                        "detalle": f"Venta: {modelo} {tela} {color} {talla}",
                        "cantidad": cant_vender,
                        "monto": monto_total,
                        "costo_unitario": costo_fab,
                        "precio_unitario": precio_unitario,
                        "producto_id": prod_principal["id"]
                    }).execute()

                    st.success(f"Venta Exitosa | Vendidas {cant_vender} pcs de {modelo} {tela} {color} ({talla}). Stock restante: {cant_total_stock - cant_vender} pcs.")
                    st.balloons()
                    time.sleep(2.0)
                    st.rerun()

    else:
        st.info("Sin existencias para vender.")

# ===
