# ============================================================
# NOTA PARA MOISÉS: CÓMO CORRER EL PROGRAMA
# 1. Si marca error "File does not exist", usa el truco:
#    Escribe en la terminal: streamlit run (y deja un espacio)
#    Luego arrastra este archivo desde tu carpeta a la terminal.
# 2. El comando manual es: streamlit run app_inventario.py
# ============================================================

import streamlit as st
from supabase import create_client
# Aquí pegas lo que copiaste:
URL_DE_MI_PROYECTO = "https://gfsaxfsnaksilxomaivt.supabase.co"
LLAVE_DE_MI_PROYECTO = "sb_publishable_xN5SQe0Eq6bxTwv7PKyitQ_oG4VwnCd"

# Esto crea la conexión
supabase = create_client(URL_DE_MI_PROYECTO, LLAVE_DE_MI_PROYECTO)

st.success("¡Conexión configurada! Ahora dime cuando estés listo para el siguiente paso.")


# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Taller de Shorts", layout="wide")

# --- MENÚ LATERAL (BARRA DE NAVEGACIÓN) ---
with st.sidebar:
    st.title("🧵 Mi Negocio")
    st.write("Control de Producción")
    st.markdown("---")
    # Aquí están los 6 apartados que definimos
    seccion = st.radio(
        "Selecciona una opción:",
        ["📦 Registro de Entradas", 
         "📊 Ver Stock Actual", 
         "💰 Registrar Venta", 
         "📒 Gastos y Materiales", 
         "📜 Historial Completo", 
         "📈 Reporte Semanal"]
    )

# --- LÓGICA DE CADA APARTADO ---

if seccion == "📦 Registro de Entradas":
    st.header("Entrada de Mercancía")
    st.info("Aquí es donde anotarás los shorts que vas terminando en el taller.")
    
    with st.form("nuevo_registro"):
        col1, col2 = st.columns(2)
        with col1:
            modelo = st.selectbox("Modelo", ["Short"])
            tela = st.selectbox("Tela", ["Liso", "Camuflaje"])
            color = st.text_input("Color del Short")
        with col2:
            talla = st.selectbox("Talla", ["CH", "M", "G"])
            cantidad = st.number_input("¿Cuántas piezas entran?", min_value=1)
            precio = st.number_input("Precio de venta ($)", min_value=0.0)
        
        if st.form_submit_button("Guardar en Inventario"):
            datos = {
                "modelo": modelo,
                "tela": tela,
                "color": color,
                "talla": talla,
                "cantidad": cantidad,
                "precio": precio
            }
            # Esto manda los datos a la nube
            supabase.table("inventario_ropa").insert(datos).execute()
            st.success(f"✅ ¡Guardado en la nube! {cantidad} {modelo}")

elif seccion == "📊 Ver Stock Actual":
    st.header("Inventario de Prendas")
    
    # 1. Creamos botones para elegir el orden
    col_orden, col_sentido = st.columns(2)
    with col_orden:
        criterio = st.selectbox("Ordenar por:", ["modelo", "tela", "color", "talla", "cantidad", "precio"])
    with col_sentido:
        sentido = st.radio("Sentido:", ["Ascendente", "Descendente"], horizontal=True)
    
    asc = True if sentido == "Ascendente" else False

    # 2. Pedimos los datos a la nube con ese orden
    respuesta = supabase.table("inventario_ropa").select("*").order(criterio, desc=not asc).execute()

    if respuesta.data:
        st.table(respuesta.data)
    else:
        st.warning("No hay datos en la base de datos todavía.")

elif seccion == "💰 Registrar Venta":
    st.header("Nueva Venta")
    st.write("Al vender aquí, el número en 'Ver Stock' bajará automáticamente.")
    st.selectbox("Selecciona producto vendido", ["Short Liso Negro - M", "Short Camuflajeado Gris - G"])
    st.number_input("Cantidad vendida", min_value=1)
    st.button("Confirmar Venta")

elif seccion == "📒 Gastos y Materiales":
    st.header("Gastos del Taller")
    st.text_input("¿En qué gastaste? (Ej: Elástico, Hilos)")
    st.number_input("Costo total ($)", min_value=0.0)
    st.button("Registrar Gasto")

elif seccion == "📜 Historial Completo":
    st.header("Bitácora de Movimientos")
    st.write("1 de Abril: Entrada de 10 Shorts Lisos")
    st.write("1 de Abril: Venta de 2 Shorts Camuflajeados")

elif seccion == "📈 Reporte Semanal":
    st.header("Resumen de la Semana")
    st.metric(label="Ventas Totales", value="$1,500 MXN", delta="+10%")
    st.write("Modelo más vendido: **Short Liso**")