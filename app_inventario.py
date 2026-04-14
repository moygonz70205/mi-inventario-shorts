import streamlit as st
from supabase import create_client
import pandas as pd

# --- SUPABASE ---
URL = "https://gfsaxfsnaksilxomaivt.supabase.co"
KEY = "sb_publishable_xN5SQe0Eq6bxTwv7PKyitQ_oG4VwnCd"
supabase = create_client(URL, KEY)

st.set_page_config(page_title="Negocio Shorts", layout="wide")

# --- MENÚ ---
with st.sidebar:
    seccion = st.radio("Menú", [
        "📦 Inventario",
        "💰 Ventas",
        "🚚 Envíos",
        "💸 Finanzas",
        "📜 Historial",
        "📊 Reporte"
    ])

# ============================================================
# 📦 INVENTARIO (SIN DUPLICADOS)
# ============================================================
if seccion == "📦 Inventario":
    st.header("Inventario")

    with st.form("inv"):
        modelo = st.text_input("Modelo", "Short")
        tela = st.selectbox("Tela", ["Liso", "Camuflaje"])
        color = st.text_input("Color")
        talla = st.selectbox("Talla", ["CH", "M", "G"])
        cantidad = st.number_input("Cantidad", min_value=1)
        precio = st.number_input("Precio", min_value=0.0)

        if st.form_submit_button("Guardar"):
            res = supabase.table("inventario_ropa").select("*").execute()
            datos = res.data

            existe = next((p for p in datos if p["modelo"] == modelo and p["tela"] == tela and p["color"] == color and p["talla"] == talla), None)

            if existe:
                nueva = existe["cantidad"] + cantidad
                supabase.table("inventario_ropa").update({"cantidad": nueva}).eq("id", existe["id"]).execute()
            else:
                supabase.table("inventario_ropa").insert({
                    "modelo": modelo,
                    "tela": tela,
                    "color": color,
                    "talla": talla,
                    "cantidad": cantidad,
                    "precio": precio,
                    "enviado": 0
                }).execute()

            st.success("Guardado")

# ============================================================
# 💰 VENTAS
# ============================================================
elif seccion == "💰 Ventas":
    st.header("Ventas")

    res = supabase.table("inventario_ropa").select("*").execute()
    datos = res.data

    if datos:
        nombres = [f"{d['id']} - {d['color']} {d['talla']}" for d in datos]
        sel = st.selectbox("Producto", nombres)

        id_sel = int(sel.split(" - ")[0])
        prod = next(p for p in datos if p["id"] == id_sel)

        st.info(f"Stock disponible: {prod['cantidad']}")

        cant = st.number_input("Cantidad", 1, prod["cantidad"])

        if st.button("Vender"):
            if prod["tela"] == "Liso":
                reinv = 35.66 * cant
                libre = 29.34 * cant
            else:
                reinv = 41.60 * cant
                libre = 23.40 * cant

            # actualizar inventario
            supabase.table("inventario_ropa").update({
                "cantidad": prod["cantidad"] - cant
            }).eq("id", prod["id"]).execute()

            # finanzas
            f = supabase.table("finanzas").select("*").eq("id", 1).execute().data[0]

            supabase.table("finanzas").update({
                "dinero_reinversion": f["dinero_reinversion"] + reinv,
                "dinero_libre": f["dinero_libre"] + libre
            }).eq("id", 1).execute()

            # historial
            supabase.table("historial").insert({
                "tipo": "VENTA",
                "detalle": sel,
                "cantidad": cant,
                "monto": reinv + libre
            }).execute()

            st.success("Venta hecha")
            st.rerun()

# ============================================================
# 🚚 ENVÍOS
# ============================================================
elif seccion == "🚚 Envíos":
    st.header("Control de Envíos")

    datos = supabase.table("inventario_ropa").select("*").execute().data

    nombres = [f"{d['id']} - {d['color']} {d['talla']}" for d in datos]
    sel = st.selectbox("Producto", nombres)

    id_sel = int(sel.split(" - ")[0])
    prod = next(p for p in datos if p["id"] == id_sel)

    st.write(f"Stock: {prod['cantidad']} | Enviado: {prod['enviado']}")

    enviar = st.number_input("Enviar", 0, prod["cantidad"])
    recibir = st.number_input("Recibir", 0, prod["enviado"])

    if st.button("Actualizar"):
        nuevo_stock = prod["cantidad"] - enviar + recibir
        nuevo_env = prod["enviado"] + enviar - recibir

        supabase.table("inventario_ropa").update({
            "cantidad": nuevo_stock,
            "enviado": nuevo_env
        }).eq("id", prod["id"]).execute()

        st.success("Actualizado")
        st.rerun()

# ============================================================
# 💸 FINANZAS (PRO)
# ============================================================
elif seccion == "💸 Finanzas":
    st.header("Finanzas")

    fin = supabase.table("finanzas").select("*").eq("id", 1).execute().data[0]

    total = fin["dinero_reinversion"] + fin["dinero_libre"]

    st.metric("Total", total)
    st.metric("Reinversión", fin["dinero_reinversion"])
    st.metric("Libre", fin["dinero_libre"])

    st.divider()

    st.subheader("Transferir dinero")

    monto = st.number_input("Monto", min_value=1.0)
    tipo = st.radio("Movimiento", ["Libre → Reinversión", "Reinversión → Libre"])

    if st.button("Transferir"):
        if tipo == "Libre → Reinversión":
            if fin["dinero_libre"] >= monto:
                supabase.table("finanzas").update({
                    "dinero_libre": fin["dinero_libre"] - monto,
                    "dinero_reinversion": fin["dinero_reinversion"] + monto
                }).eq("id", 1).execute()

        else:
            if fin["dinero_reinversion"] >= monto:
                supabase.table("finanzas").update({
                    "dinero_reinversion": fin["dinero_reinversion"] - monto,
                    "dinero_libre": fin["dinero_libre"] + monto
                }).eq("id", 1).execute()

        st.success("Transferido")
        st.rerun()

    st.divider()

    st.subheader("Registrar gasto")

    gasto = st.number_input("Cantidad gasto", min_value=1.0)
    tipo_g = st.radio("De dónde sale", ["Reinversion", "Libre"])

    if st.button("Gastar"):
        campo = "dinero_reinversion" if tipo_g == "Reinversion" else "dinero_libre"

        if fin[campo] >= gasto:
            supabase.table("finanzas").update({
                campo: fin[campo] - gasto
            }).eq("id", 1).execute()

            supabase.table("historial").insert({
                "tipo": "GASTO",
                "detalle": tipo_g,
                "monto": gasto
            }).execute()

            st.success("Gasto aplicado")
            st.rerun()

# ============================================================
# 📜 HISTORIAL CON BUSCADOR
# ============================================================
elif seccion == "📜 Historial":
    st.header("Historial")

    busqueda = st.text_input("Buscar")

    datos = supabase.table("historial").select("*").order("created_at", desc=True).execute().data

    if busqueda:
        datos = [d for d in datos if busqueda.lower() in str(d).lower()]

    st.dataframe(datos)

# ============================================================
# 📊 REPORTE CON GRÁFICA
# ============================================================
elif seccion == "📊 Reporte":
    st.header("Reporte")

    datos = supabase.table("historial").select("*").eq("tipo", "VENTA").execute().data

    if datos:
        df = pd.DataFrame(datos)
        st.metric("Total vendido", df["monto"].sum())

        df["fecha"] = pd.to_datetime(df["created_at"]).dt.date
        resumen = df.groupby("fecha")["monto"].sum()

        st.line_chart(resumen)
