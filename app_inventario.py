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
    st.header("Gestión de Inventario")
    
    respuesta = supabase.table("inventario_ropa").select("*").order("id").execute()
    datos = respuesta.data

    if datos:
        st.table(datos) # Seguimos viendo la tabla arriba
        
        st.divider()
        st.subheader("📝 Corregir o Modificar Producto")
        
        # Seleccionas por ID para no fallar
        opciones_edit = [f"{d['id']} - {d['modelo']} {d['color']} ({d['talla']})" for d in datos]
        edit_sel = st.selectbox("Selecciona el ID que quieres corregir:", opciones_edit)
        id_a_corregir = int(edit_sel.split(" - ")[0])
        
        # Traemos los datos de ese producto específico
        prod = next(p for p in datos if p['id'] == id_a_corregir)
        
        col_e1, col_e2, col_e3 = st.columns(3)
        with col_e1:
            nuevo_nombre = st.text_input("Modelo:", value=prod['modelo'])
            nueva_tela = st.text_input("Tela:", value=prod['tela'])
        with col_e2:
            nuevo_color = st.text_input("Color:", value=prod['color'])
            nueva_talla = st.text_input("Talla:", value=prod['talla'])
        with col_e3:
            nueva_cant = st.number_input("Stock actual:", value=prod['cantidad'])
            nuevo_precio = st.number_input("Precio:", value=prod['precio'])

        if st.button("Actualizar Cambios"):
            # .strip() elimina espacios accidentales al principio o final
            datos_update = {
                "modelo": nuevo_nombre.strip(),
                "tela": nueva_tela.strip(),
                "color": nuevo_color.strip(),
                "talla": nueva_talla.strip(),
                "cantidad": nueva_cant,
                "precio": nuevo_precio
            }
            supabase.table("inventario_ropa").update(datos_update).eq("id", id_a_corregir).execute()
            st.success("¡Producto corregido con éxito!")
            st.rerun()
    else:
        st.warning("No hay nada que mostrar.")

elif seccion == "💰 Registrar Venta":
    st.header("Nueva Venta")
    
    # 1. Traemos los datos actuales
    respuesta = supabase.table("inventario_ropa").select("*").execute()
    datos = respuesta.data

    if datos:
        # --- FILTROS EN CASCADA (4 COLUMNAS) ---
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            modelos_disp = sorted(list(set([d['modelo'] for d in datos])))
            mod_sel = st.selectbox("1. Modelo:", modelos_disp)
            
        with c2:
            # Filtramos telas basadas en el modelo
            telas_disp = sorted(list(set([d['tela'] for d in datos if d['modelo'] == mod_sel])))
            tela_sel = st.selectbox("2. Tela:", telas_disp)
            
        with c3:
            # Filtramos colores basados en modelo Y tela
            colores_disp = sorted(list(set([d['color'] for d in datos if d['modelo'] == mod_sel and d['tela'] == tela_sel])))
            col_sel = st.selectbox("3. Color:", colores_disp)
            
        with c4:
            # Filtramos tallas basadas en modelo, tela Y color
            tallas_disp = sorted(list(set([d['talla'] for d in datos if d['modelo'] == mod_sel and d['tela'] == tela_sel and d['color'] == col_sel])))
            talla_sel = st.radio("4. Talla:", tallas_disp, horizontal=True)

        # 2. Buscamos el producto exacto con los 4 filtros
        producto_actual = next((p for p in datos if p['modelo'] == mod_sel and p['tela'] == tela_sel and p['color'] == col_sel and p['talla'] == talla_sel), None)

        if producto_actual:
            st.info(f"📦 **Stock:** {producto_actual['cantidad']} piezas | 💵 **Precio:** ${producto_actual['precio']}")
            cant_venta = st.number_input("Cantidad a vender:", min_value=1, max_value=producto_actual['cantidad'], value=1)
            if st.button("🚀 Confirmar Venta", use_container_width=True):
                # 1. Definimos costos según el tipo de tela
                if producto_actual['tela'] == "Liso":
                    costo_reinv = 35.66 * cant_venta
                    ganancia_libre = 29.34 * cant_venta
                else: # Camuflaje
                    costo_reinv = 41.60 * cant_venta
                    ganancia_libre = 23.40 * cant_venta
                
                # 2. Restamos stock de la prenda
                nueva_cantidad = producto_actual['cantidad'] - cant_venta
                supabase.table("inventario_ropa").update({"cantidad": nueva_cantidad}).eq("id", producto_actual['id']).execute()
                
                # 3. Sumamos el dinero a la tabla de finanzas
                # Primero leemos lo que hay actualmente en la "bóveda"
                res_f = supabase.table("finanzas").select("*").eq("id", 1).execute()
                fin_actual = res_f.data[0]
                
                nuevo_reinv = fin_actual['dinero_reinversion'] + costo_reinv
                nuevo_libre = fin_actual['dinero_libre'] + ganancia_libre
                
                supabase.table("finanzas").update({
                    "dinero_reinversion": nuevo_reinv,
                    "dinero_libre": nuevo_libre
                }).eq("id", 1).execute()
                # --- REGISTRO EN HISTORIAL ---
                supabase.table("historial").insert({
                    "tipo": "VENTA",
                    "detalle": f"{producto_actual['modelo']} {producto_actual['tela']} {producto_actual['color']} ({producto_actual['talla']})",
                    "cantidad": cant_venta,
                    "monto": (costo_reinv + ganancia_libre)
                }).execute()
                st.balloons()
                st.success(f"✅ Venta exitosa. Guardado en Reinversión: ${costo_reinv} | Ganancia Libre: ${ganancia_libre}")
                st.rerun()
        else:
            st.warning("Combinación no encontrada en el inventario.")
    else:
        st.warning("No hay productos registrados.")

elif seccion == "📉 Gastos y Materiales":
    st.header("Control de Caja y Gastos")

    # Leemos el estado actual del dinero
    res = supabase.table("historial").select("*").eq("tipo", "VENTA").execute()
    ventas = res.data
    
    # Mostramos tus saldos en tarjetas llamativas
    c1, c2 = st.columns(2)
    c1.metric("📦 Capital de Reinversión", f"${fin['dinero_reinversion']:.2f}")
    c2.metric("🔓 Ganancia Libre (Tuya)", f"${fin['dinero_libre']:.2f}")
    
    st.divider()
    
    st.subheader("Registrar nuevo gasto")
    with st.form("registro_gastos"):
        fuente = st.radio("¿De dónde sale el dinero?", ["Cajón Reinversión", "Ganancia Libre"], horizontal=True)
        motivo = st.text_input("¿En qué gastaste?")
        monto_gasto = st.number_input("Cantidad gastada ($):", min_value=0.1)
        
        if st.form_submit_button("Aplicar Gasto"):
            if fuente == "Cajón Reinversión":
                if monto_gasto <= fin['dinero_reinversion']:
                    nuevo_valor = fin['dinero_reinversion'] - monto_gasto
                    supabase.table("finanzas").update({"dinero_reinversion": nuevo_valor}).eq("id", 1).execute()
                    st.success("Gasto pagado con capital de reinversión.")
                else:
                    st.error("No hay suficiente dinero en Reinversión.")
            else:
                if monto_gasto <= fin['dinero_libre']:
                    nuevo_valor = fin['dinero_libre'] - monto_gasto
                    supabase.table("finanzas").update({"dinero_libre": nuevo_valor}).eq("id", 1).execute()
                    st.success("Gasto pagado de tu ganancia libre.")
                else:
                    st.error("No hay suficiente dinero en Ganancia Libre.")
                # --- REGISTRO EN HISTORIAL ---
                supabase.table("historial").insert({
                    "tipo": "GASTO",
                    "detalle": f"{motivo} (Pagado con {fuente})",
                    "cantidad": 0,
                    "monto": monto_gasto
                }).execute()
             
    st.divider()
    with st.expander("🔄 Mover de Ganancia Libre a Reinversión"):
        monto_mover = st.number_input("Cantidad a traspasar ($):", min_value=1.0, step=10.0)
        
        if st.button("Confirmar Traspaso"):
            # 1. Verificamos que tengas el dinero en el cajón libre
            if fin['dinero_libre'] >= monto_mover:
                nuevo_libre = fin['dinero_libre'] - monto_mover
                nuevo_reinv = fin['dinero_reinversion'] + monto_mover
                
                # 2. Actualizamos ambos valores en la tabla 'finanzas'
                supabase.table("finanzas").update({
                    "dinero_libre": nuevo_libre,
                    "dinero_reinversion": nuevo_reinv
                }).eq("id", 1).execute()
                
                # 3. (Opcional) Registrar el movimiento en el historial para que no se te olvide
                supabase.table("historial").insert({
                    "tipo": "TRASPASO",
                    "detalle": f"Movimiento de Libre a Reinversión",
                    "cantidad": 0,
                    "monto": monto_mover
                }).execute()
                
                st.success(f"✅ ¡Listo! Se movieron ${monto_mover} a Reinversión.")
                st.rerun()
            else:
                st.error("❌ No tienes suficiente dinero libre para este movimiento.")

elif seccion == "📜 Historial Completo":
    st.header("📜 Historial de Movimientos")
    
    # Buscador amigable
    busqueda = st.text_input("🔍 Buscar por producto, tipo (venta/gasto) o fecha:", "")

    # Traemos todo el historial de la nueva tabla
    res = supabase.table("historial").select("*").order("created_at", desc=True).execute()
    datos_h = res.data

    if datos_h:
        # Lógica del buscador
        if busqueda:
            # Filtra si la palabra está en tipo o en detalle
            datos_filtrados = [
                d for d in datos_h 
                if busqueda.lower() in d['tipo'].lower() or busqueda.lower() in d['detalle'].lower()
            ]
        else:
            datos_filtrados = datos_h

        # Mostramos la tabla limpia
        st.dataframe(datos_filtrados, use_container_width=True)
    else:
        st.info("Aún no hay movimientos en el historial.")

elif seccion == "📊 Reporte Semanal":
    st.header("📊 Centro de Reportes")

    # Creamos tres pestañas para organizar la info
    tab_semana, tab_mes, tab_año = st.tabs(["📅 Esta Semana", "🗓️ Este Mes", "📈 Este Año"])

    # 1. Traemos los datos de ventas
    res = supabase.table("historial").select("*").eq("tipo", "VENTA").execute()
    ventas = res.data

    if ventas:
        import pandas as pd
        from datetime import datetime, timedelta
        
        df = pd.DataFrame(ventas)
        # Convertimos la fecha de Supabase a un formato que Python entienda
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['monto'] = df['monto'].astype(float)
        df['cantidad'] = df['cantidad'].astype(int)

        ahora = datetime.now()

        # --- VISTA SEMANAL (Últimos 7 días) ---
        with tab_semana:
            fecha_inicio_sem = ahora - timedelta(days=7)
            df_sem = df
            
            c1, c2 = st.columns(2)
            c1.metric("Cobrado (7d)", f"${df_sem['monto'].sum():,.2f}")
            c2.metric("Piezas (7d)", f"{df_sem['cantidad'].sum()}")
            st.dataframe(df_sem[['created_at', 'detalle', 'cantidad', 'monto']], use_container_width=True)

        # --- VISTA MENSUAL (Últimos 30 días) ---
        with tab_mes:
            fecha_inicio_mes = ahora - timedelta(days=30)
            df_mes = df[df['created_at'] >= fecha_inicio_mes]
            
            c1, c2 = st.columns(2)
            c1.metric("Total del Mes", f"${df_mes['monto'].sum():,.2f}")
            c2.metric("Piezas del Mes", f"{df_mes['cantidad'].sum()}")
            # Gráfica rápida de ventas por día en el mes
            ventas_por_dia = df_mes.groupby(df_mes['created_at'].dt.date)['monto'].sum()
            st.line_chart(ventas_por_dia)

        # --- VISTA ANUAL (Todo el año actual) ---
        with tab_año:
            df_año = df[df['created_at'].dt.year == ahora.year]
            
            c1, c2 = st.columns(2)
            c1.metric(f"Total {ahora.year}", f"${df_año['monto'].sum():,.2f}")
            c2.metric(f"Piezas {ahora.year}", f"{df_año['cantidad'].sum()}")
            # Resumen de cuánto dinero entró por cada mes
            ventas_por_mes = df_año.groupby(df_año['created_at'].dt.month)['monto'].sum()
            st.bar_chart(ventas_por_mes)
            
    else:
        st.info("Aún no hay ventas registradas para generar reportes.")
