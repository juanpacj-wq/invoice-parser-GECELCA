import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from main import procesar_factura, procesar_directorio

# Configuración de apariencia
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class UnifiedGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Gestor de Facturas - Unified Hub")
        self.geometry("600x600")
        
        self.selected_path = ""
        self.is_folder = False
        
        # Variable para controlar el tipo de proyecto
        self.project_type = ctk.StringVar(value="Ecopetrol") 

        # --- TITULO ---
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.pack(pady=20, padx=20, fill="x")
        
        self.label_title = ctk.CTkLabel(self.header_frame, text="Procesador Inteligente de Facturas", font=("Roboto", 22, "bold"))
        self.label_title.pack(pady=15)

        # --- SELECCIÓN DE CLIENTE ---
        self.project_frame = ctk.CTkFrame(self)
        self.project_frame.pack(pady=10, padx=20, fill="x")
        
        self.lbl_project = ctk.CTkLabel(self.project_frame, text="Motor de Procesamiento:", font=("Roboto", 14, "bold"))
        self.lbl_project.pack(side="left", padx=20, pady=15)
        
        self.combo_project = ctk.CTkComboBox(
            self.project_frame, 
            values=["Ecopetrol", "Gecelca/XM"], 
            variable=self.project_type, 
            width=220,
            state="readonly",
            font=("Roboto", 14)
        )
        self.combo_project.pack(side="right", padx=20, pady=15)

        # --- SELECCIÓN DE ARCHIVOS ---
        self.files_frame = ctk.CTkFrame(self)
        self.files_frame.pack(pady=15, padx=20, fill="x")

        self.btn_file = ctk.CTkButton(self.files_frame, text="📄 Seleccionar PDF Individual", command=self.select_file)
        self.btn_file.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        
        self.btn_folder = ctk.CTkButton(self.files_frame, text="📂 Seleccionar Carpeta (Lote)", command=self.select_folder)
        self.btn_folder.grid(row=0, column=1, padx=20, pady=20, sticky="ew")
        
        # Configurar columnas para que se expandan
        self.files_frame.grid_columnconfigure(0, weight=1)
        self.files_frame.grid_columnconfigure(1, weight=1)

        self.lbl_path_title = ctk.CTkLabel(self.files_frame, text="Ruta seleccionada:", font=("Roboto", 12, "bold"))
        self.lbl_path_title.grid(row=1, column=0, columnspan=2, pady=(0, 5))

        self.lbl_path = ctk.CTkLabel(self.files_frame, text="--- Ninguna ---", text_color="gray", wraplength=500)
        self.lbl_path.grid(row=2, column=0, columnspan=2, pady=(0, 20))

        # --- OPCIONES ADICIONALES ---
        self.options_frame = ctk.CTkFrame(self)
        self.options_frame.pack(pady=10, padx=20, fill="x")
        
        self.btn_output = ctk.CTkButton(self.options_frame, text="Cambiar Carpeta de Salida (Opcional)", command=self.select_output, fg_color="#555555", hover_color="#444444")
        self.btn_output.pack(pady=10)
        
        self.output_path = ""

        # --- BOTÓN DE EJECUCIÓN ---
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.pack(pady=20, padx=20, fill="x")

        self.lbl_status = ctk.CTkLabel(self.status_frame, text="Listo para iniciar", text_color="white", font=("Roboto", 12))
        self.lbl_status.pack(pady=(0, 5))

        self.btn_process = ctk.CTkButton(
            self.status_frame, 
            text="INICIAR PROCESAMIENTO", 
            command=self.start_process, 
            font=("Roboto", 16, "bold"), 
            height=50, 
            fg_color="#28a745", 
            hover_color="#218838", 
            state="disabled"
        )
        self.btn_process.pack(fill="x")

    def select_file(self):
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if path:
            self.selected_path = path
            self.is_folder = False
            self.lbl_path.configure(text=os.path.basename(path), text_color="white")
            self.btn_process.configure(state="normal")
            self.lbl_status.configure(text=f"Archivo listo ({self.project_type.get()})")

    def select_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.selected_path = path
            self.is_folder = True
            self.lbl_path.configure(text=path, text_color="white")
            self.btn_process.configure(state="normal")
            self.lbl_status.configure(text=f"Carpeta lista ({self.project_type.get()})")

    def select_output(self):
        path = filedialog.askdirectory()
        if path:
            self.output_path = path

    def start_process(self):
        if not self.selected_path: return
        
        self.btn_process.configure(state="disabled", text="PROCESANDO...", fg_color="#e6a800")
        self.lbl_status.configure(text="El motor está trabajando. Por favor espere...", text_color="#ffa500")
        
        # Ejecutar en hilo secundario para no congelar la ventana
        threading.Thread(target=self.run_logic, daemon=True).start()

    def run_logic(self):
        tipo = self.project_type.get()
        salida = self.output_path if self.output_path else None
        
        try:
            if self.is_folder:
                resultado = procesar_directorio(self.selected_path, salida, project_type=tipo)
            else:
                resultado = procesar_factura(self.selected_path, salida, project_type=tipo)
            
            # Actualizar GUI desde el hilo principal
            if resultado:
                self.after(0, lambda: self.finish("Éxito", f"Proceso de {tipo} finalizado correctamente."))
            else:
                self.after(0, lambda: self.finish("Error", "Hubo un problema al procesar los archivos. Revisa el log.", error=True))
                
        except Exception as e:
            self.after(0, lambda: self.finish("Error Crítico", str(e), error=True))

    def finish(self, title, msg, error=False):
        self.btn_process.configure(state="normal", text="INICIAR PROCESAMIENTO", fg_color="#28a745")
        self.lbl_status.configure(text=msg, text_color="#ff4444" if error else "#00ff00")
        if error:
            messagebox.showerror(title, msg)
        else:
            messagebox.showinfo(title, msg)

if __name__ == "__main__":
    app = UnifiedGUI()
    app.mainloop()