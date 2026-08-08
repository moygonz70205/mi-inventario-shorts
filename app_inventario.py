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

    # Obtener datos
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

    # Métricas principales
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
        datos = supabase.table("inventario_ropa").select("*").execute().data

        if datos:
            df = pd.DataFrame(datos)
            
            # Resumen agrupado
            resumen_tallas = df.groupby(["modelo", "tela", "talla"])["cantidad"].sum().unstack(fill_value=0)
            st.dataframe(resumen_tallas, use_container_width=True)
            
            st.divider()
            st.subheader("Consulta Detallada de Inventario")
            busqueda = st.text_input("🔍 Buscar por Modelo, Tela, Color o Talla")
            if busqueda:
                b = busqueda.lower()
                df = df[
                    df["modelo"].astype(str).str.lower().str.contains(b) |
                    df["tela"].astype(str).str.lower().str.contains(b) |
                    df["color"].astype(str).str.lower().str.contains(b) |
                    df["talla"].astype(str).str.lower().str.contains(b)
                ]
            st.dataframe(df, use_container_width=True)

            # Módulo de edición/eliminación
            st.divider()
            st.subheader("🛠️ Modificar o Eliminar Registro de Almacén")
            id_mod = st.number_input("Ingresa el ID del registro a modificar/eliminar", min_value=1, step=1)
            prod_mod = next((p for p in datos if p["id"] == id_mod), None)

            if prod_mod:
                with st.form("form_edit_inv"):
                    st.write(f"Editando ID #{prod_mod['id']}: {prod_mod['modelo']} {prod_mod['tela']}")
                    e1, e2, e3 = st.columns(3)
                    nm = e1.text_input("Modelo", prod_mod["modelo"])
                    nt = e1.text_input("Tela", prod_mod["tela"])
                    nc = e2.text_input("Color", prod_mod["color"])
                    nz = e2.text_input("Talla", prod_mod["talla"])
                    nq = e3.number_input("Cantidad", min_value=0, value=prod_mod["cantidad"])
                    np_v = e3.number_input("Precio", min_value=0.0, value=float(prod_mod["precio"]))

                    if st.form_submit_button("Guardar Cambios"):
                        supabase.table("inventario_ropa").update({
                            "modelo": nm, "tela": nt, "color": nc, "talla": nz, "cantidad": nq, "precio": np_v
                        }).eq("id", id_mod).execute()
                        st.success("Registro actualizado correctamente.")
                        st.rerun()

                if st.button("❌ Eliminar este Registro"):
                    supabase.table("inventario_ropa").delete().eq("id", id_mod).execute()
                    st.success("Registro eliminado exitosamente.")
                    st.rerun()
        else:
            st.info("Sin mercancía registrada en inventario.")

    with tab2:
        st.subheader("Ingreso de Mercancía Producida")
        configs = supabase.table("configuracion_productos").select("*").execute().data

        with st.form("form_entrada_mercancia"):
            col1, col2 = st.columns(2)
            with col1:
                e_modelo = st.text_input("Modelo", "Short")
                e_tela = st.selectbox("Tela", ["Liso", "Camuflaje"])
                e_color = st.text_input("Color", "Negro")
            with col2:
                e_talla = st.radio("Talla", ["CH", "M", "G"], horizontal=True)
                e_cant = st.number_input("Cantidad de Piezas", min_value=1, value=1)
                
                cfg_item = next((c for c in configs if c.get("tela") == e_tela), None) if configs else None
                default_precio = cfg_item.get("precio_venta", 65.0) if cfg_item else 65.0
                default_costo = cfg_item.get("costo_fabricacio", 30.0) if cfg_item else 30.0
                
                e_precio = st.number_input("Precio de Venta Unitario ($)", min_value=0.0, value=float(default_precio))

            if st.form_submit_button("📥 Registrar Entrada al Inventario"):
                inv_actual = supabase.table("inventario_ropa").select("*").execute().data
                existe = next((p for p in inv_actual if p["modelo"]==e_modelo and p["tela"]==e_tela and p["color"]==e_color and p["talla"]==e_talla), None)

                if existe:
                    supabase.table("inventario_ropa").update({
                        "cantidad": existe["cantidad"] + e_cant, "precio": e_precio
                    }).eq("id", existe["id"]).execute()
                    prod_id = existe["id"]
                else:
                    ins = supabase.table("inventario_ropa").insert({
                        "modelo": e_modelo, "tela": e_tela, "color": e_color, "talla": e_talla, "cantidad": e_cant, "precio": e_precio
                    }).execute()
                    prod_id = ins.data[0]["id"] if ins.data else None

                supabase.table("historial").insert({
                    "tipo": "ENTRADA",
                    "detalle": f"Entrada: {e_modelo} {e_tela} {e_color} {e_talla}",
                    "cantidad": e_cant,
                    "monto": e_cant * default_costo,
                    "costo_unitario": default_costo,
                    "precio_unitario": e_precio,
                    "producto_id": prod_id
                }).execute()

                st.success(f"✅ ¡Entrada Registrada! Se añadieron {e_cant} piezas de {e_modelo} {e_tela} ({e_color} / {e_talla}).")
                st.balloons()
                time.sleep(1.5)
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
        talla = st.radio("Talla Disponible", tallas_disp, horizontal=True)

        prod = next((p for p in datos if p["modelo"]==modelo and p["tela"]==tela and p["color"]==color and p["talla"]==talla), None)

        if prod:
            st.divider()
            col_info1, col_info2 = st.columns(2)
            
            if prod["cantidad"] <= 0:
                col_info1.error("❌ **PRODUCTO AGOTADO** - Stock: 0 piezas")
            elif prod["cantidad"] <= 3:
                col_info1.warning(f"⚠️ **STOCK BAJO** - Quedan solo {prod['cantidad']} pieza(s)")
            else:
                col_info1.success(f"📦 **Stock Disponible:** {prod['cantidad']} pieza(s)")

            col_info2.info(f"💲 **Precio Unitario:** ${prod['precio']:.2f}")

            if prod["cantidad"] > 0:
                cant_vender = st.number_input("Cantidad a vender", min_value=1, max_value=prod["cantidad"], value=1)
                
                cfg_item = next((c for c in configs if c.get("tela") == tela), None) if configs else None
                costo_fab = cfg_item.get("costo_fabricacio", 30.0) if cfg_item else 30.0
                
                pct_crec = (cfg_item.get("porcentaje_creci", 60) / 100) if cfg_item else 0.60
                pct_disp = (cfg_item.get("porcentaje_dispo", 30) / 100) if cfg_item else 0.30
                pct_emer = (cfg_item.get("porcentaje_emer", 10) / 100) if cfg_item else 0.10

                monto_total = cant_vender * prod["precio"]
                costo_total = cant_vender * costo_fab
                utilidad_total = monto_total - costo_total

                utilidad_crecimiento = utilidad_total * pct_crec
                c_reinv_total = costo_total + utilidad_crecimiento
                c_libre = utilidad_total * pct_disp
                c_emerg = utilidad_total * pct_emer

                st.write(f"**Desglose estimado:** Total: **${monto_total:,.2f}** | Capital + Crecimiento: **${c_reinv_total:,.2f}** | Rendimiento: **${c_libre:,.2f}** | Reserva: **${c_emerg:,.2f}**")

                if st.button("🛒 Confirmar y Registrar Venta", type="primary"):
                    # 1. Descontar Inventario
                    supabase.table("inventario_ropa").update({"cantidad": prod["cantidad"] - cant_vender}).eq("id", prod["id"]).execute()

                    # 2. Actualizar Finanzas con el Líquido Rojo (utilidad_reinversion_acumulada)
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

                    # 3. Registrar en Historial
                    supabase.table("historial").insert({
                        "tipo": "VENTA",
                        "detalle": f"Venta: {modelo} {tela} {color} {talla}",
                        "cantidad": cant_vender,
                        "monto": monto_total,
                        "costo_unitario": costo_fab,
                        "precio_unitario": prod["precio"],
                        "utilidad_unitaria": prod["precio"] - costo_fab,
                        "producto_id": prod["id"]
                    }).execute()

                    st.success("✅ ¡Venta registrada exitosamente!")
                    st.balloons()
                    time.sleep(1.5)
                    st.rerun()
    else:
        st.info("Sin existencias registradas en inventario.")

# ============================================================
# 4. TESORERÍA Y FINANZAS (CUBETA TRANSPARENTE)
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

        # Evitar errores de cálculo si la utilidad registrada supera temporalmente la cubeta
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

        # ==========================================
        # 🥛 MONITOR VISUAL DE LA CUBETA TRANSPARENTE
        # ==========================================
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

        # Barra visual gráfica
        st.progress(pct_blue / 100 if d_reinv > 0 else 0.0)
        st.caption(f"🔵 **Capital Base:** {pct_blue:.1f}% | 🔴 **Utilidad Crecimiento:** {pct_red:.1f}% (Total Gastable: **${d_reinv:,.2f} MXN**)")

        st.divider()

        # TRANSFERENCIAS REALES
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

                    # Ajuste proporcional de utilidad si la transferencia sale de Capital y Crecimiento
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
                    st.rerun()
                else:
                    st.error("Fondos insuficientes en la cuenta de origen seleccionada.")

        st.divider()

        # REGISTRO DE GASTOS / RETIROS
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

                # Descuento proporcional del líquido rojo si se gasta de Capital y Crecimiento
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
                st.rerun()
            else:
                st.error("Fondos insuficientes en la cuenta seleccionada.")

# ============================================================
# 5. HISTORIAL DE MOVIMIENTOS
# ============================================================
elif seccion == "📜 Historial de Movimientos":
    st.header("📜 Bitácora de Auditoría y Movimientos")
    st.caption("Bitácora detallada de todas las entradas, salidas de mercancía, transferencias entre cuentas y egresos registrados.")
    st.divider()

    f1, f2 = st.columns([3, 1])
    with f1:
        busq_h = st.text_input("🔍 Buscar por concepto o detalle")
    with f2:
        filtro_tipo = st.selectbox("Filtrar Evento", ["Todos", "VENTA", "ENTRADA", "TRANSFERENCIA", "GASTO"])

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
    st.caption("Configuración de costos de producción, precios de venta y porcentajes de asignación de margen de utilidad por producto.")
    st.divider()

    cfg_data = supabase.table("configuracion_productos").select("*").execute().data

    if cfg_data:
        st.subheader("Matriz Actual")
        st.dataframe(pd.DataFrame(cfg_data), use_container_width=True)
        st.divider()

    st.subheader("Actualizar Parámetros por Tela")
    with st.form("form_config"):
        c_tela = st.selectbox("Selecciona Tela a Configurar", ["Liso", "Camuflaje"])
        c_costo = st.number_input("Costo de Fabricación ($)", min_value=0.0, value=30.0)
        c_precio = st.number_input("Precio de Venta ($)", min_value=0.0, value=65.0)
        
        st.markdown("**Porcentajes de Utilidad (%)**")
        col_p1, col_p2, col_p3 = st.columns(3)
        p_crec = col_p1.number_input("% Crecimiento / Reinversión", value=60)
        p_disp = col_p2.number_input("% Rendimiento Propietario", value=30)
        p_emer = col_p3.number_input("% Reserva Operativa", value=10)

        if st.form_submit_button("Guardar Parámetros"):
            if (p_crec + p_disp + p_emer) != 100:
                st.error("La suma de los 3 porcentajes debe ser exactamente 100%.")
            else:
                item_exist = next((x for x in cfg_data if x.get("tela") == c_tela), None) if cfg_data else None

                datos_upd = {
                    "tela": c_tela,
                    "costo_fabricacio": c_costo,
                    "precio_venta": c_precio,
                    "porcentaje_creci": p_crec,
                    "porcentaje_dispo": p_disp,
                    "porcentaje_emer": p_emer
                }

                if item_exist:
                    supabase.table("configuracion_productos").update(datos_upd).eq("id", item_exist["id"]).execute()
                else:
                    supabase.table("configuracion_productos").insert(datos_upd).execute()

                st.success("Matriz de costos actualizada correctamente.")
                st.rerun()
