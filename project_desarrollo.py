import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import random
import numpy as np
import pandas as pd
from datetime import datetime

# Variables globales
datos_historicos = {}
articulos_guardados = []

# Función para cargar el archivo CSV
def cargar_csv():
    global datos_historicos
    file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
    if file_path:
        # Leer el archivo CSV y agrupar por el nombre del periódico
        df = pd.read_csv(file_path)
        
        # Asegurarse de que el archivo tenga las columnas correctas
        if 'periodico' not in df.columns or 'fecha' not in df.columns or 'cantidad' not in df.columns:
            messagebox.showerror("Error", "El archivo CSV debe contener las columnas 'periodico', 'fecha' y 'cantidad'.")
            return

        # Agrupar por el nombre del periódico y sumar la cantidad de artículos por cada uno
        datos_agrupados = df.groupby('periodico')['cantidad'].apply(list).to_dict()
        datos_historicos.update(datos_agrupados)
        
        # Actualizar el combobox con los nombres de los periódicos únicos
        combobox_diarios['values'] = list(datos_historicos.keys())
        messagebox.showinfo("Carga Exitosa", "Datos cargados correctamente desde el archivo CSV.")

# Calcular el promedio de artículos de los últimos 6 meses
def calcular_promedio(datos_historicos):
    return {diario: np.mean(articulos) for diario, articulos in datos_historicos.items()}

# Guardar el número de artículos ingresado
def guardar_articulos():
    diario_seleccionado = combobox_diarios.get()
    validacion = False
        
    try:
        cantidad_articulos = int(entry_cantidad_articulos.get())
    except ValueError:
        messagebox.showerror("Error", "Por favor, ingresa un número válido de artículos.")
        return
    
    if not diario_seleccionado or cantidad_articulos is None:
        messagebox.showerror("Error", "Por favor, selecciona un diario y ingresa la cantidad de artículos.")
        return


    # Validación estadística
    articulos_historicos = datos_historicos.get(diario_seleccionado)
    if not articulos_historicos:
        messagebox.showerror("Error", f"No hay datos históricos para {diario_seleccionado}.")
        return
    
    promedio_diario = np.mean(articulos_historicos)
    umbral = promedio_diario * 0.8

    print(umbral)

    
    # --- Fase 1: Verificación si la cantidad está por debajo del umbral ---
    if cantidad_articulos < umbral:
        messagebox.showwarning("Advertencia", f"La cantidad de artículos ({cantidad_articulos}) está por debajo del umbral del 80% del promedio ({promedio_diario:.2f}).")
        mostrar_alerta_no_subida(diario_seleccionado, cantidad_articulos, promedio_diario, umbral)
        return  # Terminar ejecución, no se permite guardar
    else:
        validacion = True
        exit

    print(promedio_diario)

    # --- Fase 2: Calcular coeficiente de variación ---
    q1, q3, iqr, coef_variacion = calcular_estadisticas(articulos_historicos)

    print(coef_variacion)

    if coef_variacion > 0.2:  # Consideramos 0.2 como un umbral razonable para alta variabilidad
        # Variabilidad alta: revisar si está por debajo de Q1 o fuera del IQR
        validacion = True
        if cantidad_articulos < q1:
            messagebox.showerror("Rechazado", f"La cantidad de artículos ({cantidad_articulos}) está por debajo del primer cuartil ({q1:.2f}) de los datos históricos.")
            return
        elif cantidad_articulos < (q1 - 1.5 * iqr):  # Revisión fuera del rango intercuartílico
            messagebox.showerror("Rechazado", f"La cantidad de artículos ({cantidad_articulos}) está por fuera del rango intercuartílico (IQR) con un valor de {iqr:.2f}.")
            return
    else:
        # --- Fase 3: Variabilidad baja, revisar la tabla de frecuencias ---
        frecuencias = tabla_frecuencias(articulos_historicos)
        mayor_frecuencia = max(frecuencias.values())
        articulo_moda = [art for art, freq in frecuencias.items() if freq == mayor_frecuencia][0]
        
        if cantidad_articulos == articulo_moda:
            validacion = True
            messagebox.showinfo("Validación Exitosa", f"La cantidad de artículos ({cantidad_articulos}) coincide con la categoría de mayor frecuencia ({articulo_moda}).")
        else:
            messagebox.showerror("Rechazado", f"La cantidad de artículos ({cantidad_articulos}) no coincide con la categoría de mayor frecuencia ({articulo_moda}).")
            return
    
    if validacion:
        fecha_actual = datetime.now().strftime("%Y-%m-%d")
        articulos_guardados.append({
            "fecha": fecha_actual,
            "diario": diario_seleccionado,
            "cantidad": cantidad_articulos
        })

    # Mostrar los datos guardados en la tabla
    mostrar_tabla_articulos()

# Calcular el coeficiente de variación
def calcular_estadisticas(articulos):
    q1 = np.percentile(articulos, 25)
    q3 = np.percentile(articulos, 75)
    iqr = q3 - q1
    std_dev = np.std(articulos)
    mean = np.mean(articulos)
    coef_variacion = std_dev / mean if mean != 0 else 0
    return q1, q3, iqr, coef_variacion

def mostrar_alerta_no_subida(diario, cantidad, promedio, umbral):
    # Mostrar alerta en pantalla cuando los artículos están por debajo del umbral esperado
    mensaje = f"""
    No se puede subir la cantidad de artículos.

    Diario: {diario}
    Cantidad ingresada: {cantidad}
    Promedio histórico: {promedio:.2f}
    Umbral establecido (80% del promedio): {umbral:.2f}

    La cantidad ingresada está por debajo del umbral permitido.
    """
    messagebox.showerror("Error - Subida de artículos", mensaje)

# Mostrar datos históricos con scrollbar horizontal
# Mostrar datos históricos con los días de la semana (lunes a domingo)
# Mostrar datos históricos con los días de la semana (lunes a domingo) durante 6 meses
def mostrar_datos_historicos():
    if not datos_historicos:
        messagebox.showerror("Error", "Por favor, carga un archivo CSV primero.")
        return

    historic_window = tk.Toplevel(ventana)
    historic_window.title("Datos Históricos por Día de la Semana (Últimos 6 Meses)")
    historic_window.geometry("1200x600")

    frame_historico = tk.Frame(historic_window)
    frame_historico.pack(fill=tk.BOTH, expand=True)

    # Columnas: Diario y días de la semana (Lunes a Domingo)
    # Las columnas representan 6 semanas (cada semana tiene 7 días)
    columns = ["Diario", "Semana 1 (L)", "Semana 1 (M)", "Semana 1 (Mi)", "Semana 1 (J)", "Semana 1 (V)", "Semana 1 (S)", "Semana 1 (D)",
               "Semana 2 (L)", "Semana 2 (M)", "Semana 2 (Mi)", "Semana 2 (J)", "Semana 2 (V)", "Semana 2 (S)", "Semana 2 (D)",
               "Semana 3 (L)", "Semana 3 (M)", "Semana 3 (Mi)", "Semana 3 (J)", "Semana 3 (V)", "Semana 3 (S)", "Semana 3 (D)",
               "Semana 4 (L)", "Semana 4 (M)", "Semana 4 (Mi)", "Semana 4 (J)", "Semana 4 (V)", "Semana 4 (S)", "Semana 4 (D)",
               "Semana 5 (L)", "Semana 5 (M)", "Semana 5 (Mi)", "Semana 5 (J)", "Semana 5 (V)", "Semana 5 (S)", "Semana 5 (D)",
               "Semana 6 (L)", "Semana 6 (M)", "Semana 6 (Mi)", "Semana 6 (J)", "Semana 6 (V)", "Semana 6 (S)", "Semana 6 (D)"]
    
    tree_historico = ttk.Treeview(frame_historico, columns=columns, show="headings", height=10)

    for col in columns:
        tree_historico.heading(col, text=col)
        tree_historico.column(col, anchor="center", width=80)

    # Insertar los datos en la tabla distribuidos por semanas y días (Lunes a Domingo)
    for diario, articulos in datos_historicos.items():
        # Aquí asumimos que los artículos están agrupados por semanas de 7 días.
        # Si los datos exceden 42 (6 semanas * 7 días), solo tomamos los primeros 42 días
        semanas_de_articulos = [articulos[i:i + 7] for i in range(0, len(articulos), 7)]

        # Vamos a recorrer cada bloque de semanas (si son más de 6 semanas, tomamos las primeras 6)
        semanas_de_articulos = semanas_de_articulos[:6]  # Tomamos máximo 6 semanas
        
        # Convertimos el formato en una sola lista que va de semana en semana por días de lunes a domingo
        articulos_flat = [articulo for semana in semanas_de_articulos for articulo in semana]
        
        # Rellenamos si hay menos de 6 semanas (es decir, menos de 42 días en total)
        if len(articulos_flat) < 42:
            articulos_flat += [0] * (42 - len(articulos_flat))

        # Insertamos los valores en la tabla
        tree_historico.insert("", "end", values=(diario, *articulos_flat))

    # Scrollbars
    scrollbar_vertical = ttk.Scrollbar(frame_historico, orient="vertical", command=tree_historico.yview)
    scrollbar_horizontal = ttk.Scrollbar(frame_historico, orient="horizontal", command=tree_historico.xview)

    tree_historico.configure(
        yscrollcommand=scrollbar_vertical.set, xscrollcommand=scrollbar_horizontal.set
    )

    tree_historico.grid(row=0, column=0, sticky="nsew")
    scrollbar_vertical.grid(row=0, column=1, sticky="ns")
    scrollbar_horizontal.grid(row=1, column=0, sticky="ew")

    frame_historico.grid_rowconfigure(0, weight=1)
    frame_historico.grid_columnconfigure(0, weight=1)


# Mostrar reporte de la última semana
def mostrar_reporte():
    if not datos_historicos:
        messagebox.showerror("Error", "Por favor, carga un archivo CSV primero.")
        return

    articulos_semana = generar_articulos_semana()
    
    report_window = tk.Toplevel(ventana)
    report_window.title("Reporte de artículos - Última Semana")
    report_window.geometry("1000x400")

    tree_reporte = ttk.Treeview(
        report_window,
        columns=(
            "Diario", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo",
        ),
        show="headings",
    )
    tree_reporte.heading("Diario", text="Diario")
    days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    
    for day in days:
        tree_reporte.heading(day, text=day)

    for diario, articulos in articulos_semana.items():
        tree_reporte.insert("", "end", values=(diario, *articulos))
    
    tree_reporte.pack(fill=tk.BOTH, expand=True)

# Crear artículos para la semana aleatoriamente
def generar_articulos_semana():
    articulos_semanales = {}
    for diario, articulos in datos_historicos.items():
        articulos_semanales[diario] = [random.choice(articulos) for _ in range(7)]
    return articulos_semanales

# Mostrar la tabla de los artículos guardados
def mostrar_tabla_articulos():
    for row in tabla_articulos.get_children():
        tabla_articulos.delete(row)
    
    for articulo in articulos_guardados:
        tabla_articulos.insert("", "end", values=(articulo["fecha"], articulo["diario"], articulo["cantidad"]))

# Calcular la tabla de frecuencias de los artículos
def tabla_frecuencias(articulos):
    unique, counts = np.unique(articulos, return_counts=True)
    return dict(zip(unique, counts))

def mostrar_predicciones():
    if not datos_historicos:
        messagebox.showerror("Error", "Por favor, carga un archivo CSV primero.")
        return

    predic_window = tk.Toplevel(ventana)
    predic_window.title("Predicciones")
    predic_window.geometry("800x400")

    frame_predic = tk.Frame(predic_window)
    frame_predic.pack(fill=tk.BOTH, expand=True)

    columns = ["Diario", "Promedio Artículos (Histórico)", "Predicción de Artículos"]
    tree_predic = ttk.Treeview(frame_predic, columns=columns, show="headings", height=10)

    for col in columns:
        tree_predic.heading(col, text=col)
        tree_predic.column(col, anchor="center")

    # Generar predicciones basadas en el promedio histórico
    promedios = calcular_promedio(datos_historicos)
    for diario, promedio in promedios.items():
        # Generamos predicciones con un pequeño factor aleatorio
        prediccion = promedio + random.uniform(-5, 5)
        tree_predic.insert("", "end", values=(diario, f"{promedio:.2f}", f"{prediccion:.2f}"))

    # Scrollbars
    scrollbar_vertical = ttk.Scrollbar(frame_predic, orient="vertical", command=tree_predic.yview)
    scrollbar_horizontal = ttk.Scrollbar(frame_predic, orient="horizontal", command=tree_predic.xview)

    tree_predic.configure(
        yscrollcommand=scrollbar_vertical.set, xscrollcommand=scrollbar_horizontal.set
    )

    tree_predic.grid(row=0, column=0, sticky="nsew")
    scrollbar_vertical.grid(row=0, column=1, sticky="ns")
    scrollbar_horizontal.grid(row=1, column=0, sticky="ew")

    frame_predic.grid_rowconfigure(0, weight=1)
    frame_predic.grid_columnconfigure(0, weight=1)
# Crear la ventana principal
ventana = tk.Tk()
ventana.title("Control de Artículos")
ventana.geometry("1000x600")

# Crear widgets
label_cargar = tk.Label(ventana, text="Cargar archivo CSV")
label_cargar.pack()

boton_cargar = tk.Button(ventana, text="Cargar CSV", command=cargar_csv)
boton_cargar.pack()

label_diarios = tk.Label(ventana, text="Selecciona un Diario")
label_diarios.pack()

combobox_diarios = ttk.Combobox(ventana, state="readonly")
combobox_diarios.pack()

label_cantidad_articulos = tk.Label(ventana, text="Cantidad de Artículos")
label_cantidad_articulos.pack()

entry_cantidad_articulos = tk.Entry(ventana)
entry_cantidad_articulos.pack()

boton_guardar = tk.Button(ventana, text="Guardar Artículos", command=guardar_articulos)
boton_guardar.pack()

# Crear tabla para mostrar los artículos guardados
tabla_articulos = ttk.Treeview(
    ventana,
    columns=("Fecha", "Diario", "Cantidad"),
    show="headings",
)
tabla_articulos.heading("Fecha", text="Fecha")
tabla_articulos.heading("Diario", text="Diario")
tabla_articulos.heading("Cantidad", text="Cantidad de Artículos")
tabla_articulos.pack(fill=tk.BOTH, expand=True)

# Botones para mostrar datos y reportes
boton_historico = tk.Button(ventana, text="Mostrar Datos Históricos", command=mostrar_datos_historicos)
boton_historico.pack()

boton_reporte = tk.Button(ventana, text="Mostrar Reporte de la Última Semana", command=mostrar_reporte)
boton_reporte.pack()

btn_predicciones = tk.Button(ventana, text="Mostrar Predicciones", command=mostrar_predicciones)
btn_predicciones.pack(pady=10)

ventana.mainloop()
