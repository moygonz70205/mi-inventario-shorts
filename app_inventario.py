import streamlit as st
from supabase import create_client
import pandas as pd

# --- CONFIGURACIÓN SUPABASE ---
URL_DE_MI_PROYECTO = "https://gfsaxfsnaksilxomaivt.supabase.co"
LLAVE_DE_MI_PROYECTO = "sb_publishable_xN5SQe0Eq6bxTwv7PKyitQ_oG4VwnCd"

supabase = create_client(URL_DE_MI_PROYECTO, LLAVE_DE_MI_PROYECTO)

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Taller de Shorts", layout="wide")

# --- MENÚ ---
with st.sidebar:
    st.title("🧵 Mi Negocio")
    seccion = st.radio(
        "Selecciona una opción:",
        [
            "📦 Registro de Entradas",
            "📊 Ver Stock Actual",
            "💰 Registrar Venta",
            "📒 Gastos y Materiales",
            "📜 Historial Completo",
            "📈 Reporte Semanal"
        ]
    )

# ============================================================
# 📦 REGISTRO DE ENTRADAS
# ============================================================
if seccion == "📦 Registro de Entradas":
    st.header("Entrada de Mercancía")

    with st.form("nuevo_registro"):
        col1, col2 = st.columns(2)

        with col1:
            modelo = st.selectbox("Modelo", ["Short"])
            tela = st.selectbox("Tela", ["Liso", "Camuflaje"])
            color = st.text_input("Color")

        with col2:
            talla = st.selectbox("Talla", ["CH", "M", "G"])
            cantidad = st.number_input("Cantidad", min_value=1)
            precio = st.number_input("Precio", min_value=0.0)

        if st.form_submit_button("Guardar"):
            datos = {
                "modelo": modelo,
                "tela": tela,
                "color": color,
                "talla": talla,
                "cantidad": cantidad,
                "precio": precio
            }

            supabase.table("inventario_ropa").insert(datos).execute()
            st.success("Guardado correctamente")

# ============================================================
# 📊 VER INVENTARIO
# ============================================================
elif seccion == "📊 Ver Stock Actual":
    st.header("Inventario")

    res = supabase.table("inventario_ropa").select("*").execute()
    datos = res.data

    if datos:
        st.dataframe(datos)
    else:
        st.warning("No hay productos")

# ============================================================
# 💰 REGISTRAR VENTA
# ============================================================
elif seccion == "💰 Registrar Venta":
    st.header("Registrar Venta")

    res = supabase.table("inventario_ropa").select("*").execute()
    datos = res.data

    if datos:
        modelos = list(set([d["modelo"] for d in datos]))
        modelo = st.selectbox("Modelo", modelos)

        telas = list(set([d["tela"] for d in datos if d["modelo"] == modelo]))
        tela = st.selectbox("Tela", telas)

        colores = list(set([d["color"] for d in datos if d["modelo"] == modelo and d["tela"] == tela]))
        color = st.selectbox("Color", colores)

        tallas = list(set([d["talla"] for d in datos if d["modelo"] == modelo and d["tela"] == tela and d["color"] == color]))
        talla = st.selectbox("Talla", tallas)

        producto = next(
            (p for p in datos if p["modelo"] == modelo and p["tela"] == tela and p["color"] == color and p["talla"] == talla),
            None
        )

        if producto:
            st.info(f"Stock: {producto['cantidad']} | Precio: ${producto['precio']}")

            cantidad = st.number_input("Cantidad a vender", min_value=1, max_value=producto["cantidad"])

            if st.button("Vender"):
                if producto["tela"] == "Liso":
                    reinv = 35.66 * cantidad
                    libre = 29.34 * cantidad
                else:
                    reinv = 41.60 * cantidad
                    libre = 23.40 * cantidad

                # actualizar inventario
                supabase.table("inventario_ropa").update({
                    "cantidad": producto["cantidad"] - cantidad
                }).eq("id", producto["id"]).execute()

                # finanzas
                res_f = supabase.table("finanzas").select("*").eq("id", 1).execute()

                if res_f.data:
                    fin = res_f.data[0]

                    supabase.table("finanzas").update({
                        "dinero_reinversion": fin["dinero_reinversion"] + reinv,
                        "dinero_libre": fin["dinero_libre"] + libre
                    }).eq("id", 1).execute()

                # historial
                supabase.table("historial").insert({
                    "tipo": "VENTA",
                    "detalle": f"{modelo} {tela} {color} {talla}",
                    "cantidad": cantidad,
                    "monto": reinv + libre
                }).execute()

                st.success("Venta registrada")
                st.rerun()
        else:
            st.warning("Producto no encontrado")

# ============================================================
# 📒 GASTOS
# ============================================================
elif seccion == "📒 Gastos y Materiales":
    st.header("Gastos")

    res_f = supabase.table("finanzas").select("*").eq("id", 1).execute()

    if res_f.data:
        fin = res_f.data[0]

        st.metric("Reinversión", fin["dinero_reinversion"])
        st.metric("Libre", fin["dinero_libre"])

        with st.form("gasto"):
            tipo = st.radio("De dónde sale", ["Reinversion", "Libre"])
            motivo = st.text_input("Motivo")
            monto = st.number_input("Monto", min_value=1.0)

            if st.form_submit_button("Guardar gasto"):
                campo = "dinero_reinversion" if tipo == "Reinversion" else "dinero_libre"

                nuevo = fin[campo] - monto

                if nuevo >= 0:
                    supabase.table("finanzas").update({
                        campo: nuevo
                    }).eq("id", 1).execute()

                    supabase.table("historial").insert({
                        "tipo": "GASTO",
                        "detalle": motivo,
                        "monto": monto
                    }).execute()

                    st.success("Gasto registrado")
                    st.rerun()
                else:
                    st.error("No hay dinero suficiente")
    else:
        st.error("No existe registro en finanzas")

# ============================================================
# 📜 HISTORIAL
# ============================================================
elif seccion == "📜 Historial Completo":
    st.header("Historial")

    res = supabase.table("historial").select("*").order("created_at", desc=True).execute()

    if res.data:
        st.dataframe(res.data)
    else:
        st.info("Sin movimientos")

# ============================================================
# 📈 REPORTE
# ============================================================
elif seccion == "📈 Reporte Semanal":
    st.header("Reporte")

    res = supabase.table("historial").select("*").eq("tipo", "VENTA").execute()

    if res.data:
        df = pd.DataFrame(res.data)
        total = df["monto"].sum()

        st.metric("Total vendido", total)
        st.dataframe(df)
    else:
        st.info("No hay ventas") 
