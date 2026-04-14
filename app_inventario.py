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
        st.header("📉 Control de Gastos")
        try:
            res_f = supabase.table("finanzas").select("*").eq("id", 1).execute()
            if res_f.data:
                fin = res_f.data[0]
                c1, c2 = st.columns(2)
                c1.metric("Capital Reinversión", f"${fin['dinero_reinversion']:,.2f}")
                c2.metric("Ganancia Libre", f"${fin['dinero_libre']:,.2f}")
                
                st.divider()
                with st.form("registro_gastos"):
                    fuente = st.radio("¿De dónde sale?", ["Cajón Reinversión", "Ganancia Libre"], horizontal=True)
                    motivo = st.text_input("¿En qué gastaste?")
                    monto_gasto = st.number_input("Cantidad ($):", min_value=0.1)
                    if st.form_submit_button("Aplicar Gasto"):
                        col_update = "dinero_reinversion" if fuente == "Cajón Reinversión" else "dinero_libre"
                        nuevo_valor = fin[col_update] - monto_gasto
                        if nuevo_valor >= 0:
                            supabase.table("finanzas").update({col_update: nuevo_valor}).eq("id", 1).execute()
                            supabase.table("historial").insert({"tipo": "GASTO", "detalle": f"{motivo} ({fuente})", "monto": monto_gasto}).execute()
                            st.success("✅ Gasto aplicado")
                            st.rerun()
                        else:
                            st.error("❌ Saldo insuficiente")
        except Exception as e:
            st.error(f"Error: {e}")

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
        st.header("📊 Resumen de Ventas")
        res = supabase.table("historial").select("*").eq("tipo", "VENTA").execute()
        if res.data:
            import pandas as pd
            df = pd.DataFrame(res.data)
            st.metric("Cobrado Total", f"${df['monto'].sum():,.2f}")
            st.write("### Detalle")
            st.dataframe(df[['created_at', 'detalle', 'monto']])
        else:
            st.info("No hay ventas registradas.")

