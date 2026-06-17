import streamlit as st
from supabase import create_client
import pandas as pd

# --- CONEXIÓN ---
URL = "https://gfsaxfsnaksilxomaivt.supabase.co"
KEY = "sb_publishable_xN5SQe0Eq6bxTwv7PKyitQ_oG4VwnCd"
supabase = create_client(URL, KEY)

st.set_page_config(page_title="Taller Shorts", layout="wide")

# --- MENÚ ---
with st.sidebar:
    st.title("🧵 Taller")
    seccion = st.radio("Menú", [
        "📥 Entrada de Mercancía",
        "📦 Inventario",
        "💰 Ventas",
        "💸 Finanzas",
        "📜 Historial",
        "📊 Reporte"
    ])

# ============================================================
# 📥 ENTRADA
# ============================================================
if seccion == "📥 Entrada de Mercancía":
    st.header("Registrar producto")

    with st.form("entrada"):
        c1, c2, c3 = st.columns(3)

        with c1:
            modelo = st.text_input("Modelo", "Short")
            tela = st.selectbox("Tela", ["Liso", "Camuflaje"])

        with c2:
            color = st.text_input("Color")
            talla = st.radio("Talla", ["CH", "M", "G"], horizontal=True)

        with c3:
            cantidad = st.number_input("Cantidad", min_value=1)
            precio = st.number_input("Precio", min_value=0.0)

        if st.form_submit_button("Guardar"):
            datos = supabase.table("inventario_ropa").select("*").execute().data

            existe = next((p for p in datos if p["modelo"]==modelo and p["tela"]==tela and p["color"]==color and p["talla"]==talla), None)

            if existe:
                supabase.table("inventario_ropa").update({
                    "cantidad": existe["cantidad"] + cantidad
                }).eq("id", existe["id"]).execute()
            else:
                supabase.table("inventario_ropa").insert({
                    "modelo": modelo,
                    "tela": tela,
                    "color": color,
                    "talla": talla,
                    "cantidad": cantidad,
                    "precio": precio
                }).execute()

            else:
                supabase.table("inventario_ropa").insert({
                    "modelo": modelo,
                    "tela": tela,
                    "color": color,
                    "talla": talla,
                    "cantidad": cantidad,
                    "precio": precio
                }).execute()

            if existe:
                st.success(
                    f"✅ Stock actualizado correctamente\n\n"
                    f"Se agregaron {cantidad} pieza(s)\n\n"
                    f"{modelo} • {tela}\n"
                    f"Color: {color}\n"
                    f"Talla: {talla}"
                )
            else:
                st.success(
                    f"✅ Inventario registrado correctamente\n\n"
                    f"{cantidad} pieza(s)\n\n"
                    f"{modelo} • {tela}\n"
                    f"Color: {color}\n"
                    f"Talla: {talla}"
                )

            st.balloons()

            import time
            time.sleep(2)

            st.rerun()

# ============================================================
# 📦 INVENTARIO
# ============================================================
elif seccion == "📦 Inventario":
    st.header("Inventario")

    datos = supabase.table("inventario_ropa").select("*").execute().data

    if datos:
        df = pd.DataFrame(datos)
        total = df["cantidad"].sum()

        st.metric("Total de piezas", total)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Sin productos")

# ============================================================
# 💰 VENTAS
# ============================================================
elif seccion == "💰 Ventas":
    st.header("Registrar venta")

    datos = supabase.table("inventario_ropa").select("*").execute().data

    if datos:
        c1, c2, c3, c4 = st.columns([1,1,2,1])

        with c1:
            modelos = sorted(set([d["modelo"] for d in datos]))
            modelo = st.selectbox("Modelo", modelos)

        with c2:
            telas = sorted(set([d["tela"] for d in datos if d["modelo"] == modelo]))
            tela = st.selectbox("Tela", telas)

        with c3:
            colores = sorted(set([d["color"] for d in datos if d["modelo"] == modelo and d["tela"] == tela]))
            color = st.selectbox("Color", colores)

        with c4:
            tallas = [d["talla"] for d in datos if d["modelo"] == modelo and d["tela"] == tela and d["color"] == color]
            talla = st.radio("Talla", tallas, horizontal=True)

        prod = next((p for p in datos if p["modelo"]==modelo and p["tela"]==tela and p["color"]==color and p["talla"]==talla), None)

        if prod:
            st.info(f"Stock: {prod['cantidad']} | Precio: ${prod['precio']}")

            cant = st.number_input("Cantidad", 1, prod["cantidad"])

            if st.button("Vender"):
                if prod["tela"] == "Liso":
                    reinv = 35.66 * cant
                    libre = 29.34 * cant
                else:
                    reinv = 41.60 * cant
                    libre = 23.40 * cant

                # INVENTARIO
                supabase.table("inventario_ropa").update({
                    "cantidad": prod["cantidad"] - cant
                }).eq("id", prod["id"]).execute()

                # FINANZAS
                res_f = supabase.table("finanzas").select("*").eq("id", 1).execute()

                if res_f.data:
                    fin = res_f.data[0]

                    supabase.table("finanzas").update({
                        "dinero_reinversion": fin["dinero_reinversion"] + reinv,
                        "dinero_libre": fin["dinero_libre"] + libre
                    }).eq("id", 1).execute()

                # HISTORIAL
                supabase.table("historial").insert({
                    "tipo": "VENTA",
                    "detalle": f"{modelo} {tela} {color} {talla}",
                    "cantidad": cant,
                    "monto": reinv + libre
                }).execute()

                st.success("Venta registrada")
                st.rerun()

# ============================================================
# 💸 FINANZAS
# ============================================================
elif seccion == "💸 Finanzas":
    st.header("Finanzas")

    # =========================
    # 1. VENTAS (BASE REAL)
    # =========================
    ventas = supabase.table("historial").select("*").eq("tipo", "VENTA").execute().data

    reinversion = 0
    libre = 0

    if ventas:
        for v in ventas:
            if "Liso" in v["detalle"]:
                reinversion += 35.66 * v["cantidad"]
                libre += 29.34 * v["cantidad"]
            else:
                reinversion += 41.60 * v["cantidad"]
                libre += 23.40 * v["cantidad"]

    # =========================
    # 2. GASTOS
    # =========================
    gastos = supabase.table("historial").select("*").eq("tipo", "GASTO").execute().data

    if gastos:
        for g in gastos:
            if "Reinversion" in g["detalle"]:
                reinversion -= g["monto"]
            else:
                libre -= g["monto"]

    total = reinversion + libre

    # =========================
    # MOSTRAR (YA CUADRA CON REPORTE)
    # =========================
    c1, c2, c3 = st.columns(3)
    c1.metric("Total (igual que reporte)", f"${total:,.2f}")
    c2.metric("Reinversión", f"${reinversion:,.2f}")
    c3.metric("Libre", f"${libre:,.2f}")

    st.divider()

    # =========================
    # TRANSFERENCIAS (SOLO VISUAL / CONTROL)
    # =========================
    st.subheader("Transferir dinero")

    monto = st.number_input("Monto", min_value=1.0)
    tipo = st.radio("Movimiento", ["Libre → Reinversión", "Reinversión → Libre"])

    if st.button("Transferir"):
        # Solo se registra en historial para control
        supabase.table("historial").insert({
            "tipo": "TRANSFERENCIA",
            "detalle": tipo,
            "monto": monto
        }).execute()

        st.success("Transferencia registrada")
        st.rerun()

    st.divider()

    # =========================
    # GASTOS CON NOMBRE
    # =========================
    st.subheader("Registrar gasto")

    motivo = st.text_input("Nombre del gasto (ej: tela, comida, transporte)")
    monto_gasto = st.number_input("Cantidad", min_value=1.0)
    tipo_g = st.radio("De dónde sale", ["Reinversion", "Libre"])

    if st.button("Registrar gasto"):
        supabase.table("historial").insert({
            "tipo": "GASTO",
            "detalle": f"{motivo} ({tipo_g})",
            "monto": monto_gasto
        }).execute()

        st.success("Gasto registrado")
        st.rerun()

# ============================================================
# 📜 HISTORIAL
# ============================================================
elif seccion == "📜 Historial":
    st.header("Historial")

    busqueda = st.text_input("Buscar")

    datos = supabase.table("historial").select("*").order("created_at", desc=True).execute().data

    if busqueda:
        datos = [d for d in datos if busqueda.lower() in str(d).lower()]

    st.dataframe(datos)

# ============================================================
# 📊 REPORTE
# ============================================================
elif seccion == "📊 Reporte":
    st.header("Reporte")

    datos = supabase.table("historial").select("*").eq("tipo", "VENTA").execute().data

    if datos:
        df = pd.DataFrame(datos)

        st.metric("Total vendido", df["monto"].sum())

        df["fecha"] = pd.to_datetime(df["created_at"]).dt.date
        resumen = df.groupby("fecha")["monto"].sum()

        st.bar_chart(resumen)
    else:
        st.info("No hay ventas registradas")
