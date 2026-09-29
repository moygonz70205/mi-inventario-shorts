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

# --- FUNCIONES DE SANEAMIENTO Y LIMPIEZA DE TEXTO ---
def estandarizar_texto(texto: str) -> str:
    """Elimina espacios extras y estandariza a formato Title Case."""
    if not texto or not isinstance(texto, str):
        return ""
    return " ".join(texto.strip().split()).title()

def consolidar_inventario(datos_raw):
    """Agrupa filas duplicadas en la base de datos sumando sus cantidades."""
    if not datos_raw:
        return pd.DataFrame(columns=["id", "modelo", "tela", "color", "talla", "cantidad", "precio"])
    
    df = pd.DataFrame(datos_raw)
    df["modelo"] = df["modelo"].apply(estandarizar_texto)
    df["tela"] = df["tela"].apply(estandarizar_texto)
    df["color"] = df["color"].apply(estandarizar_texto)
    df["talla"] = df["talla"].apply(lambda x: str(x).strip().upper())

    # Agrupación estricta para eliminar duplicados visuales
    df_consolidado = df.groupby(["modelo", "tela", "color", "talla"], as_index=False).agg({
        "cantidad": "sum",
        "precio": "first",
        "id": "first"
    })
    return df_consolidado

# --- MENÚ LATERAL ---
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
    datos_inv_raw = supabase.table("inventario_ropa").select("*").execute().data
    finanzas = supabase.table("finanzas").select("*").eq("id", 1).execute().data

    # Consolidar inventario para eliminar duplicados de la vista principal
    df_inv_consolidado = consolidar_inventario(datos_inv_raw)

    hoy = datetime.today().strftime('%Y-%m-%d')
    ventas_hoy = sum(v["monto"] for v in ventas if str(v.get("created_at", "")).startswith(hoy)) if ventas else 0.0

    d_reinv = finanzas[0].get("dinero_reinversion", 0.0) if finanzas else 0.0
    d_libre = finanzas[0].get("dinero_libre", 0.0) if finanzas else 0.0
    d_emerg = finanzas[0].get("dinero_emergencia", 0.0) if finanzas else 0.0

    total_inv_valor = (df_inv_consolidado["cantidad"] * df_inv_consolidado["precio"]).sum() if not df_inv_consolidado.empty else 0.0
    pocos_prod = df_inv_consolidado[df_inv_consolidado["cantidad"] <= 3] if not df_inv_consolidado.empty else pd.DataFrame()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ventas del Día", f"${ventas_hoy:,.2f}")
    c2.metric("Capital y Crecimiento", f"${d_reinv:,.2f}")
    c3.metric("Rendimiento Propietario", f"${d_libre:,.2f}")
    c4.metric("Reserva Operativa", f"${d_emerg:,.2f}")

    st.subheader("📦 Estado General de Inventario")
    col_a, col_b = st.columns(2)
    col_a.metric("Valor Comercial en Stock", f"${total_inv_valor:,.2f}")
    col_b.metric("Alertas de Stock Bajo (≤ 3 pcs)", f"{len(pocos_prod)} variantes")

    if not pocos_prod.empty:
        st.warning("⚠️ **Atención:** Las siguientes prendas requieren reabastecimiento urgente:")
        st.dataframe(pocos_prod[["modelo", "tela", "color", "talla", "cantidad"]], use_container_width=True)

# ============================================================
# 2. INVENTARIO Y ENTRADA DE INVENTARIO
# ============================================================
elif seccion == "📦 Inventario y Entrada de Inventario":
    st.header("📦 Gestión de Almacén e Ingresos")
    st.caption("Control centralizado de mercancía. Permite auditar existencias, consultar totales e ingresar nueva producción.")
    st.divider()

    tab1, tab2, tab3 = st.tabs([
        "📋 Ver Inventario en Stock", 
        "📥 Registrar Entrada (Existentes)", 
        "✨ Crear Nuevo Producto / Variante"
    ])

    datos_raw = supabase.table("inventario_ropa").select("*").execute().data
    df_inv = consolidar_inventario(datos_raw)

    # ---------------- TAB 1: CONSULTA DE INVENTARIO ----------------
    with tab1:
        if not df_inv.empty:
            total_piezas_global = int(df_inv["cantidad"].sum())
            
            st.subheader("📊 Totales Generales de Inventario")
            m_col1, m_col2 = st.columns([1, 3])
            m_col1.metric("Total de Piezas en Almacén", f"{total_piezas_global} pcs")

            totales_por_modelo = df_inv.groupby("modelo")["cantidad"].sum().to_dict()
            with m_col2:
                st.write("**Desglose por Tipo de Producto:**")
                cols_mod = st.columns(max(len(totales_por_modelo), 1))
                for idx, (mod, cant) in enumerate(totales_por_modelo.items()):
                    cols_mod[idx % len(cols_mod)].metric(f"Total {mod}", f"{int(cant)} pcs")

            st.divider()
            st.subheader("Resumen General de Existencias por Talla")
            resumen_tallas = df_inv.groupby(["modelo", "tela", "talla"])["cantidad"].sum().unstack(fill_value=0)
            st.dataframe(resumen_tallas, use_container_width=True)

            st.divider()
            st.subheader("Consulta Detallada de Inventario")
            busqueda = st.text_input("🔍 Buscar por Modelo, Tela, Color o Talla")
            df_mostrar = df_inv.copy()
            if busqueda:
                b = busqueda.lower()
                df_mostrar = df_mostrar[
                    df_mostrar["modelo"].str.lower().str.contains(b) |
                    df_mostrar["tela"].str.lower().str.contains(b) |
                    df_mostrar["color"].str.lower().str.contains(b) |
                    df_mostrar["talla"].str.lower().str.contains(b)
                ]
            st.dataframe(df_mostrar[["modelo", "tela", "color", "talla", "cantidad", "precio"]], use_container_width=True)

            st.divider()
            st.subheader("🛠️ Ajuste Auditado de Stock")
            st.caption("Corrección directa de inventario por merma, conteo físico o revisión de almacén.")
            
            col_adj1, col_adj2 = st.columns(2)
            with col_adj1:
                item_sel = st.selectbox(
                    "Selecciona prenda a ajustar", 
                    options=df_inv.to_dict('records'),
                    format_func=lambda x: f"{x['modelo']} {x['tela']} - {x['color']} ({x['talla']}) | Actual: {x['cantidad']} pcs"
                )
            with col_adj2:
                nueva_cant = st.number_input("Nueva Cantidad en Stock", min_value=0, value=int(item_sel["cantidad"]) if item_sel else 0)
                motivo_adj = st.text_input("Motivo del ajuste", "Revisión de conteo físico / Auditoría")

            if st.button("🔧 Aplicar Ajuste de Stock", type="secondary"):
                if item_sel:
                    diferencia = nueva_cant - item_sel["cantidad"]
                    supabase.table("inventario_ropa").update({"cantidad": nueva_cant}).eq("id", item_sel["id"]).execute()
                    
                    supabase.table("historial").insert({
                        "tipo": "AJUSTE",
                        "detalle": f"Ajuste Stock: {item_sel['modelo']} {item_sel['tela']} {item_sel['color']} {item_sel['talla']} ({motivo_adj})",
                        "cantidad": diferencia,
                        "monto": 0.0,
                        "producto_id": item_sel["id"]
                    }).execute()

                    st.success(f"✅ Stock actualizado a {nueva_cant} piezas correctamente.")
                    time.sleep(2)
                    st.rerun()
        else:
            st.info("Sin mercancía registrada en inventario.")

    # ---------------- TAB 2: ENTRADA DE PRODUCTOS EXISTENTES ----------------
    with tab2:
        st.subheader("Añadir Cantidades a Productos Existentes")
        configs = supabase.table("configuracion_productos").select("*").execute().data

        if not df_inv.empty:
            c1, c2, c3 = st.columns(3)
            with c1:
                modelos_opt = sorted(list(set(df_inv["modelo"])))
                e_mod = st.selectbox("Modelo", modelos_opt, key="ent_mod")
            with c2:
                telas_opt = sorted(list(set(df_inv[df_inv["modelo"] == e_mod]["tela"])))
                e_tel = st.selectbox("Tela", telas_opt, key="ent_tel")
            with c3:
                colores_opt = sorted(list(set(df_inv[(df_inv["modelo"] == e_mod) & (df_inv["tela"] == e_tel)]["color"])))
                e_col = st.selectbox("Color", colores_opt, key="ent_col")

            tallas_opt = sorted(list(set(df_inv[(df_inv["modelo"] == e_mod) & (df_inv["tela"] == e_tel) & (df_inv["color"] == e_col)]["talla"])))

            if "talla_entrada_sel" not in st.session_state or st.session_state["talla_entrada_sel"] not in tallas_opt:
                st.session_state["talla_entrada_sel"] = tallas_opt[0] if tallas_opt else "CH"

            e_tal = st.radio("Talla", tallas_opt, index=tallas_opt.index(st.session_state["talla_entrada_sel"]) if st.session_state["talla_entrada_sel"] in tallas_opt else 0, key="radio_tal_ent", horizontal=True)
            st.session_state["talla_entrada_sel"] = e_tal

            col_add1, col_add2 = st.columns(2)
            e_cant = col_add1.number_input("Cantidad de piezas a agregar", min_value=1, value=1)
            
            cfg_item = next((c for c in configs if estandarizar_texto(c.get("tela", "")) == e_tel and estandarizar_texto(c.get("modelo", "")) == e_mod), None) if configs else None
            def_precio = cfg_item.get("precio_venta", 65.0) if cfg_item else 65.0
            def_costo = cfg_item.get("costo_fabricacion", 30.0) if cfg_item else 30.0

            e_precio = col_add2.number_input("Precio de Venta Unitario ($)", min_value=0.0, value=float(def_precio))

            if st.button("📥 Registrar Entrada al Inventario", type="primary"):
                existe = next((p for p in datos_raw if estandarizar_texto(p["modelo"]) == e_mod and estandarizar_texto(p["tela"]) == e_tel and estandarizar_texto(p["color"]) == e_col and str(p["talla"]).strip().upper() == e_tal), None)

                if existe:
                    cant_final = existe["cantidad"] + e_cant
                    supabase.table("inventario_ropa").update({"cantidad": cant_final, "precio": e_precio}).eq("id", existe["id"]).execute()
                    prod_id = existe["id"]
                else:
                    cant_final = e_cant
                    ins = supabase.table("inventario_ropa").insert({
                        "modelo": e_mod, "tela": e_tel, "color": e_col, "talla": e_tal, "cantidad": e_cant, "precio": e_precio
                    }).execute()
                    prod_id = ins.data[0]["id"] if ins.data else None

                supabase.table("historial").insert({
                    "tipo": "ENTRADA",
                    "detalle": f"Entrada: {e_mod} {e_tel} {e_col} {e_tal}",
                    "cantidad": e_cant,
                    "monto": e_cant * def_costo,
                    "costo_unitario": def_costo,
                    "precio_unitario": e_precio,
                    "producto_id": prod_id
                }).execute()

                st.success(f"✅ Stock actualizado. Se añadieron {e_cant} piezas de {e_mod} {e_tel} ({e_col} / {e_tal}). Total en stock: {cant_final} pcs.")
                st.balloons()
                time.sleep(2.5)
                st.rerun()
        else:
            st.info("No hay categorías creadas. Utiliza la pestaña 'Crear Nuevo Producto / Variante' para el primer registro.")

    # ---------------- TAB 3: CREAR NUEVA VARIANTE O PRODUCTO ----------------
    with tab3:
        st.subheader("Registrar Nueva Prenda o Categoría")
        st.caption("Escribe los datos manualmente. La aplicación formateará los textos automáticamente para evitar celdas duplicadas.")

        with st.form("form_nuevo_prod"):
            cn1, cn2 = st.columns(2)
            n_modelo = cn1.text_input("Tipo de Producto / Modelo (ej. Short, Playera, Pant)", "Short")
            n_tela = cn1.text_input("Tipo de Tela (ej. Liso, Camuflaje, Algodón)", "Liso")
            n_color = cn2.text_input("Color", "Negro")
            n_talla = cn2.selectbox("Talla", ["CH", "M", "G", "XL", "2XL"])
            
            cn3, cn4 = st.columns(2)
            n_cant = cn3.number_input("Cantidad Inicial de Piezas", min_value=1, value=1)
            n_precio = cn4.number_input("Precio de Venta ($)", min_value=0.0, value=65.0)

            if st.form_submit_button("✨ Crear y Registrar en Almacén"):
                m_clean = estandarizar_texto(n_modelo)
                t_clean = estandarizar_texto(n_tela)
                c_clean = estandarizar_texto(n_color)
                z_clean = n_talla.strip().upper()

                existe = next((p for p in datos_raw if estandarizar_texto(p["modelo"]) == m_clean and estandarizar_texto(p["tela"]) == t_clean and estandarizar_texto(p["color"]) == c_clean and str(p["talla"]).strip().upper() == z_clean), None)

                if existe:
                    cant_tot = existe["cantidad"] + n_cant
                    supabase.table("inventario_ropa").update({"cantidad": cant_tot, "precio": n_precio}).eq("id", existe["id"]).execute()
                    p_id = existe["id"]
                else:
                    cant_tot = n_cant
                    ins = supabase.table("inventario_ropa").insert({
                        "modelo": m_clean, "tela": t_clean, "color": c_clean, "talla": z_clean, "cantidad": n_cant, "precio": n_precio
                    }).execute()
                    p_id = ins.data[0]["id"] if ins.data else None

                supabase.table("historial").insert({
                    "tipo": "ENTRADA",
                    "detalle": f"Alta Nueva: {m_clean} {t_clean} {c_clean} {z_clean}",
                    "cantidad": n_cant,
                    "monto": 0.0,
                    "precio_unitario": n_precio,
                    "producto_id": p_id
                }).execute()

                st.success(f"✅ ¡Producto Guardado! {m_clean} {t_clean} ({c_clean} / {z_clean}) ahora cuenta con {cant_tot} piezas en total.")
                st.balloons()
                time.sleep(2.5)
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
        df_vta = consolidar_inventario(datos)

        c1, c2, c3 = st.columns(3)
        with c1:
            modelos = sorted(list(set(df_vta["modelo"])))
            modelo = st.selectbox("Selecciona Modelo", modelos)
        with c2:
            telas = sorted(list(set(df_vta[df_vta["modelo"] == modelo]["tela"])))
            tela = st.selectbox("Selecciona Tela", telas)
        with c3:
            colores = sorted(list(set(df_vta[(df_vta["modelo"] == modelo) & (df_vta["tela"] == tela)]["color"])))
            color = st.selectbox("Selecciona Color", colores)

        st.subheader("Selecciona Talla")
        tallas_disp = sorted(list(set(df_vta[(df_vta["modelo"] == modelo) & (df_vta["tela"] == tela) & (df_vta["color"] == color)]["talla"])))

        if "talla_venta_sel" not in st.session_state or st.session_state["talla_venta_sel"] not in tallas_disp:
            st.session_state["talla_venta_sel"] = tallas_disp[0] if tallas_disp else "CH"

        talla = st.radio("Talla Disponible", tallas_disp, index=tallas_disp.index(st.session_state["talla_venta_sel"]) if st.session_state["talla_venta_sel"] in tallas_disp else 0, key="radio_tal_vta", horizontal=True)
        st.session_state["talla_venta_sel"] = talla

        prods = [p for p in datos if estandarizar_texto(p["modelo"]) == modelo and estandarizar_texto(p["tela"]) == tela and estandarizar_texto(p["color"]) == color and str(p["talla"]).strip().upper() == talla]
        
        cant_total_disp = sum(p["cantidad"] for p in prods)
        precio_vta = prods[0]["precio"] if prods else 0.0

        st.divider()
        col_info1, col_info2 = st.columns(2)
        
        if cant_total_disp <= 0:
            col_info1.error("❌ **PRODUCTO AGOTADO** - Stock: 0 piezas")
        elif cant_total_disp <= 3:
            col_info1.warning(f"⚠️ **STOCK BAJO** - Quedan solo {cant_total_disp} pieza(s)")
        else:
            col_info1.success(f"📦 **Stock Disponible:** {cant_total_disp} pieza(s)")

        col_info2.info(f"💲 **Precio Unitario:** ${precio_vta:.2f}")

        if cant_total_disp > 0:
            cant_vender = st.number_input("Cantidad a vender", min_value=1, max_value=cant_total_disp, value=1)
            
            cfg_item = next((c for c in configs if estandarizar_texto(c.get("tela", "")) == tela and estandarizar_texto(c.get("modelo", "")) == modelo), None) if configs else None
            costo_fab = cfg_item.get("costo_fabricacion", 30.0) if cfg_item else 30.0
            
            pct_crec = (cfg_item.get("porcentaje_crecimiento", 60) / 100) if cfg_item else 0.60
            pct_disp = (cfg_item.get("porcentaje_disponibilidad", 30) / 100) if cfg_item else 0.30
            pct_emer = (cfg_item.get("porcentaje_emergencia", 10) / 100) if cfg_item else 0.10

            monto_total = cant_vender * precio_vta
            costo_total = cant_vender * costo_fab
            utilidad_total = monto_total - costo_total

            utilidad_crecimiento = utilidad_total * pct_crec
            c_reinv_total = costo_total + utilidad_crecimiento
            c_libre = utilidad_total * pct_disp
            c_emerg = utilidad_total * pct_emer

            st.write(f"**Desglose estimado:** Total: **${monto_total:,.2f}** | Capital + Crecimiento: **${c_reinv_total:,.2f}** | Rendimiento: **${c_libre:,.2f}** | Reserva: **${c_emerg:,.2f}**")

            if st.button("🛒 Confirmar y Registrar Venta", type="primary"):
                cant_restante = cant_vender
                for pr in prods:
                    if cant_restante <= 0:
                        break
                    descuento = min(pr["cantidad"], cant_restante)
                    supabase.table("inventario_ropa").update({"cantidad": pr["cantidad"] - descuento}).eq("id", pr["id"]).execute()
                    cant_restante -= descuento

                fin = supabase.table("finanzas").select("*").eq("id", 1).execute().data
                if fin:
                    f_curr = fin[0]
                    u_acum_prev = f_curr.get("utilidad_reinversion_acumulada", 0.0) or 0.0
                    e_prev = f_curr.get("dinero_emergencia", 0.0) or 0.0

                    supabase.table("finanzas").update({
                        "dinero_reinversion": f_curr["dinero_reinversion"] + c_reinv_total,
                        "dinero_libre": f_curr["dinero_libre"] + c_libre,
                        "dinero_emergencia": e_prev + c_emerg,
                        "utilidad_reinversion_acumulada": u_acum_prev + utilidad_crecimiento
                    }).eq("id", 1).execute()

                supabase.table("historial").insert({
                    "tipo": "VENTA",
                    "detalle": f"Venta exitosa: {cant_vender} pcs {modelo} {tela} {color} Talla {talla}",
                    "cantidad": cant_vender,
                    "monto": monto_total,
                    "costo_unitario": costo_fab,
                    "precio_unitario": precio_vta,
                    "utilidad_unitaria": precio_vta - costo_fab,
                    "producto_id": prods[0]["id"] if prods else None
                }).execute()

                st.success(f"✅ ¡Venta exitosa! Se vendieron {cant_vender} pieza(s) de {modelo} {tela} ({color} / {talla}).")
                st.balloons()
                time.sleep(2.5)
                st.rerun()
    else:
        st.info("Sin existencias registradas en inventario.")

# ============================================================
# 4. TESORERÍA Y FINANZAS
# ============================================================
elif seccion == "💸 Tesorería y Finanzas":
    st.header("💸 Tesorería y Capital de Trabajo")
    st.caption("Administración estratégica de cuentas institucionales: Capital de Reinversión, Rendimientos de Socios y Fondo de Reserva.")
    st.divider()

    fin = supabase.table("finanzas").select("*").eq("id", 1).execute().data
    
    if fin:
        f = fin[0]
        d_reinv = f.get("dinero_reinversion", 0.0) or 0.0
        d_libre = f.get("dinero_libre", 0.0) or 0.0
        d_emerg = f.get("dinero_emergencia", 0.0) or 0.0
        u_acum = f.get("utilidad_reinversion_acumulada", 0.0) or 0.0

        u_acum_real = min(u_acum, d_reinv)
        capital_base_real = max(0.0, d_reinv - u_acum_real)

        m_total = d_reinv + d_libre + d_emerg

        st.subheader("Balances Institucionales")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Capital Institucional Total", f"${m_total:,.2f}")
        c2.metric("⚙️ Capital y Crecimiento", f"${d_reinv:,.2f}")
        c3.metric("💼 Rendimiento Propietario", f"${d_libre:,.2f}")
        c4.metric("🛡️ Reserva Operativa", f"${d_emerg:,.2f}")

        st.divider()

        st.subheader("🥛 Monitor Visual: Cubeta de Capital y Crecimiento")
        st.caption("Análisis interno de los dos componentes acumulados dentro de la cuenta de Reinversión:")

        if d_reinv > 0:
            pct_blue = (capital_base_real / d_reinv) * 100
            pct_red = (u_acum_real / d_reinv) * 100
        else:
            pct_blue = 0.0
            pct_red = 0.0

        col_cub1, col_cub2 = st.columns(2)
        col_cub1.metric("🔵 Capital Base (Costo Recuperado)", f"${capital_base_real:,.2f}", f"{pct_blue:.1f}% del fondo")
        col_cub2.metric("🔴 Utilidad para Crecimiento (60% Ganancia)", f"${u_acum_real:,.2f}", f"{pct_red:.1f}% del fondo")

        st.progress(pct_blue / 100 if d_reinv > 0 else 0.0)
        st.caption(f"🔵 **Capital Base:** {pct_blue:.1f}% | 🔴 **Utilidad Crecimiento:** {pct_red:.1f}% (Total Gastable: **${d_reinv:,.2f} MXN**)")

        st.divider()

        st.subheader("🔄 Transferencias Monetarias Internas")
        col_t1, col_t2, col_t3 = st.columns(3)
        
        with col_t1:
            cuenta_origen = st.selectbox("Cuenta de Origen", ["Capital y Crecimiento", "Rendimiento Propietario", "Reserva Operativa"])
        with col_t2:
            cuenta_destino = st.selectbox("Cuenta de Destino", ["Rendimiento Propietario", "Capital y Crecimiento", "Reserva Operativa"])
        with col_t3:
            monto_mov = st.number_input("Monto a Transferir ($)", min_value=1.0, value=100.0)

        if st.button("Ejecutar Transferencia Real"):
            if cuenta_origen == cuenta_destino:
                st.error("Las cuentas de origen y destino deben ser distintas.")
            else:
                saldos = {
                    "Capital y Crecimiento": ("dinero_reinversion", d_reinv),
                    "Rendimiento Propietario": ("dinero_libre", d_libre),
                    "Reserva Operativa": ("dinero_emergencia", d_emerg)
                }

                col_orig, val_orig = saldos[cuenta_origen]
                col_dest, val_dest = saldos[cuenta_destino]

                if val_orig >= monto_mov:
                    n_orig = val_orig - monto_mov
                    n_dest = val_dest + monto_mov

                    upd_payload = {col_orig: n_orig, col_dest: n_dest}

                    if cuenta_origen == "Capital y Crecimiento" and d_reinv > 0:
                        ratio_utilidad = u_acum_real / d_reinv
                        upd_payload["utilidad_reinversion_acumulada"] = max(0.0, u_acum_real - (monto_mov * ratio_utilidad))

                    supabase.table("finanzas").update(upd_payload).eq("id", 1).execute()

                    supabase.table("historial").insert({
                        "tipo": "TRANSFERENCIA",
                        "detalle": f"Transferencia: {cuenta_origen} ➔ {cuenta_destino}",
                        "monto": monto_mov
                    }).execute()

                    st.success("✅ Transferencia realizada y respaldada en base de datos.")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Fondos insuficientes en la cuenta de origen seleccionada.")

        st.divider()

        st.subheader("📉 Registrar Egreso / Gasto")
        g_motivo = st.text_input("Concepto del egreso (ej. Compra de tela, luz, retiro personal)")
        g_monto = st.number_input("Monto del egreso ($)", min_value=1.0, value=50.0)
        g_cuenta = st.radio("Descontar de la cuenta:", ["Capital y Crecimiento", "Rendimiento Propietario", "Reserva Operativa"], horizontal=True)

        if st.button("Registrar Egreso"):
            saldos = {
                "Capital y Crecimiento": ("dinero_reinversion", d_reinv),
                "Rendimiento Propietario": ("dinero_libre", d_libre),
                "Reserva Operativa": ("dinero_emergencia", d_emerg)
            }
            col_g, val_g = saldos[g_cuenta]

            if val_g >= g_monto:
                upd_gasto = {col_g: val_g - g_monto}

                if g_cuenta == "Capital y Crecimiento" and d_reinv > 0:
                    ratio_utilidad = u_acum_real / d_reinv
                    upd_gasto["utilidad_reinversion_acumulada"] = max(0.0, u_acum_real - (g_monto * ratio_utilidad))

                supabase.table("finanzas").update(upd_gasto).eq("id", 1).execute()

                supabase.table("historial").insert({
                    "tipo": "GASTO",
                    "detalle": f"Egreso: {g_motivo} ({g_cuenta})",
                    "monto": g_monto
                }).execute()

                st.success("Egreso registrado correctamente.")
                time.sleep(2)
                st.rerun()
            else:
                st.error("Fondos insuficientes en la cuenta seleccionada.")

# ============================================================
# 5. HISTORIAL DE MOVIMIENTOS
# ============================================================
elif seccion == "📜 Historial de Movimientos":
    st.header("📜 Bitácora de Auditoría y Movimientos")
    st.caption("Bitácora detallada de todas las entradas, salidas de mercancía, transferencias entre cuentas, egresos y ajustes.")
    st.divider()

    f1, f2 = st.columns([3, 1])
    with f1:
        busq_h = st.text_input("🔍 Buscar por concepto o detalle")
    with f2:
        filtro_tipo = st.selectbox("Filtrar Evento", ["Todos", "VENTA", "ENTRADA", "TRANSFERENCIA", "GASTO", "AJUSTE"])

    datos_h = supabase.table("historial").select("*").order("created_at", desc=True).execute().data

    if datos_h:
        df_h = pd.DataFrame(datos_h)

        if filtro_tipo != "Todos":
            df_h = df_h[df_h["tipo"] == filtro_tipo]

        if busq_h:
            df_h = df_h[df_h["detalle"].astype(str).str.lower().str.contains(busq_h.lower())]

        st.dataframe(df_h, use_container_width=True)
    else:
        st.info("Sin movimientos registrados en la bitácora.")

# ============================================================
# 6. REPORTE DEL NEGOCIO
# ============================================================
elif seccion == "📊 Reporte del Negocio":
    st.header("📊 Analítica e Inteligencia de Negocio")
    st.caption("Informes estadísticos del desempeño comercial diario, semanal, mensual y anual para la toma de decisiones.")
    st.divider()

    ventas_data = supabase.table("historial").select("*").eq("tipo", "VENTA").execute().data

    if ventas_data:
        df_v = pd.DataFrame(ventas_data)
        df_v["created_at"] = pd.to_datetime(df_v["created_at"])

        periodo = st.selectbox("Selecciona Periodo de Análisis", ["Diario", "Semanal", "Mensual", "Anual"])

        if periodo == "Diario":
            df_v["grupo"] = df_v["created_at"].dt.date
        elif periodo == "Semanal":
            df_v["grupo"] = df_v["created_at"].dt.to_period("W").astype(str)
        elif periodo == "Mensual":
            df_v["grupo"] = df_v["created_at"].dt.to_period("M").astype(str)
        else:
            df_v["grupo"] = df_v["created_at"].dt.year

        resumen = df_v.groupby("grupo")["monto"].sum().reset_index()

        st.subheader(f"Total Facturado - Reporte {periodo}")
        st.dataframe(resumen, use_container_width=True)

        st.subheader("📈 Tendencia Comercial")
        st.bar_chart(data=resumen, x="grupo", y="monto")
    else:
        st.info("No existen registros de ventas para elaborar informes.")

# ============================================================
# 7. CONFIGURACIÓN DE PRODUCTOS
# ============================================================
elif seccion == "⚙️ Configuración de Productos":
    st.header("⚙️ Matriz de Costos y Margen de Utilidad")
    st.caption("Configuración escalable de costos de producción, precios de venta y porcentajes de asignación por producto y tipo de tela.")
    st.divider()

    cfg_data = supabase.table("configuracion_productos").select("*").execute().data

    if cfg_data:
        st.subheader("Matriz Actual de Configuración")
        st.dataframe(pd.DataFrame(cfg_data), use_container_width=True)
        st.divider()

    st.subheader("Actualizar o Crear Parámetros de Producto")
    
    with st.form("form_config_prod"):
        cp1, cp2 = st.columns(2)
        c_prod = cp1.text_input("Producto / Modelo", "Short")
        c_tela = cp2.text_input("Tipo de Tela", "Liso")
        
        cc1, cc2 = st.columns(2)
        c_costo = cc1.number_input("Costo de Fabricación ($)", min_value=0.0, value=30.0)
        c_precio = cc2.number_input("Precio de Venta ($)", min_value=0.0, value=65.0)
        
        st.markdown("**Porcentajes de Distribución de Utilidad (%)**")
        col_p1, col_p2, col_p3 = st.columns(3)
        p_crec = col_p1.number_input("% Crecimiento / Reinversión", value=60)
        p_disp = col_p2.number_input("% Rendimiento Propietario", value=30)
        p_emer = col_p3.number_input("% Reserva Operativa", value=10)

        if st.form_submit_button("💾 Guardar Parámetros de Producto"):
            if (p_crec + p_disp + p_emer) != 100:
                st.error("La suma de los 3 porcentajes debe ser exactamente igual al 100%.")
            else:
                m_clean = estandarizar_texto(c_prod)
                t_clean = estandarizar_texto(c_tela)

                datos_upd = {
                    "modelo": m_clean,
                    "tela": t_clean,
                    "costo_fabricacion": c_costo,
                    "precio_venta": c_precio,
                    "porcentaje_crecimiento": p_crec,
                    "porcentaje_disponibilidad": p_disp,
                    "porcentaje_emergencia": p_emer
                }

                res_live = supabase.table("configuracion_productos").select("*").eq("modelo", m_clean).eq("tela", t_clean).execute().data

                if res_live:
                    supabase.table("configuracion_productos").update(datos_upd).eq("id", res_live[0]["id"]).execute()
                    st.success(f"✅ ¡Parámetros de {m_clean} - {t_clean} actualizados correctamente!")
                else:
                    supabase.table("configuracion_productos").insert(datos_upd).execute()
                    st.success(f"✅ ¡Nueva configuración creada para {m_clean} - {t_clean}!")

                time.sleep(2)
                st.rerun()
