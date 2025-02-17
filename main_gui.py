import os
import csv
import datetime
import customtkinter as ctk
from tkinter import filedialog, messagebox, BooleanVar

from Llegir_Fitxer_Dades import llegir_header_datafile, llegir_dades

# Afegim el diccionari de períodes d'exportació (en segons)
EXPORT_PERIODS = {
    "20 segons": 20,
    "1 minut": 60,
    "10 minuts": 600,
    "30 minuts": 1800,
    "1 hora": 3600,
    "12 hores": 43200,
    "1 dia": 86400
}

def aggregate_samples(samples: list, export_period_sec: int) -> list:
    """
    Agrupa les mostres basant-se en buckets de temps amb la durada 'export_period_sec'.
    Calcula la mitjana dels valors de cada bucket.
    """
    groups = {}
    for sample in samples:
        # Utilitzem el timestamp per agrupar. Es calcula el bucket com a interval interger.
        ts = sample["time"].timestamp()
        bucket = int(ts // export_period_sec) * export_period_sec
        groups.setdefault(bucket, []).append(sample["value"])
    aggregated = []
    for bucket, values in groups.items():
        avg_value = round(sum(values)/len(values), 3)
        bucket_time = datetime.datetime.fromtimestamp(bucket)
        aggregated.append({"time": bucket_time, "value": avg_value})
    aggregated.sort(key=lambda s: s["time"])
    return aggregated

def process_subfolder(source_folder: str, export_folder: str, export_period_sec: int, progress_callback=None) -> str:
    """
    Processa una subcarpeta llegint fitxers de dades amb una extensió numèrica
    i exporta les mostres (aggregades segons el període d'exportació) a un CSV amb el nom de la subcarpeta.
    
    Args:
        source_folder (str): Ruta de la subcarpeta.
        export_folder (str): Carpeta on es guarda l'export CSV.
        export_period_sec (int): Interval d'exportació seleccionat (en segons).
        progress_callback (func, opcional): Funció cridada després de processar cada fitxer.
    
    Returns:
        str: Missatge indicant el resultat de l'exportació.
    """
    log_messages = []
    data_files = [f for f in os.listdir(source_folder)
                  if os.path.splitext(f)[1][1:].isdigit()]
    if not data_files:
        msg = f"[!] No s'han trobat fitxers de dades a {source_folder}"
        log_messages.append(msg)
        return "\n".join(log_messages)
    data_files.sort()

    all_samples = []
    for data_file in data_files:
        data_file_path = os.path.join(source_folder, data_file)
        header_info = llegir_header_datafile(data_file_path)
        if not header_info:
            msg = f"[!] Error llegint la capçalera del fitxer: {data_file_path}"
            log_messages.append(msg)
            if progress_callback:
                progress_callback()
            continue
        samples = llegir_dades(data_file_path, header_info)
        if samples:
            all_samples.extend(samples)
        if progress_callback:
            progress_callback()

    if not all_samples:
        msg = f"[!] No s'han trobat samples a {source_folder}"
        log_messages.append(msg)
        return "\n".join(log_messages)

    all_samples.sort(key=lambda s: s["time"])
    # Agrupació de mostres segons el període seleccionat
    aggregated_samples = aggregate_samples(all_samples, export_period_sec)
    csv_filename = os.path.join(export_folder, os.path.basename(source_folder) + ".csv")
    try:
        with open(csv_filename, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Time", "Value"])
            for sample in aggregated_samples:
                writer.writerow([
                    sample["time"].strftime('%d/%m/%Y %H:%M:%S'),
                    sample["value"]
                ])
        msg = f"[OK] Exportació completada: {csv_filename}"
        log_messages.append(msg)
    except Exception as e:
        msg = f"[!] Error exportant CSV per {source_folder}: {e}"
        log_messages.append(msg)

    return "\n".join(log_messages)


class FilterableItemFrame(ctk.CTkFrame):
    """
    Widget que mostra una llista filtrable d'elements amb un CTkSwitch per a cada element.
    Permet seleccionar i deseleccionar elements amb feedback visual canviant el color del text.
    """

    def __init__(self, master, item_list: list = None, command=None, **kwargs):
        item_list = item_list or []
        super().__init__(master, **kwargs)
        self.command = command  # Funció opcional a executar en canviar la selecció.
        self.full_item_list = item_list  # Llista completa d'elements.
        self.selected_items = set()  # Conjunt d'elements seleccionats.
        self.item_widgets = {}  # Diccionari per emmagatzemar els widgets per a cada element.

        # Entrada per filtrar amb text per defecte en negre.
        self.filter_entry = ctk.CTkEntry(self, placeholder_text="Filtra...", text_color="black")
        self.filter_entry.pack(pady=(5, 10), padx=5, fill="x")
        self.filter_entry.bind("<KeyRelease>", self._on_filter_change)

        # Marc scrollable per mostrar els elements.
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.pack(padx=5, pady=5, fill="both", expand=True)

        # Dibuixa la llista inicial.
        self._draw_items(self.full_item_list)

    def _draw_items(self, items: list):
        """
        Dibuixa tots els elements de la llista 'items' en el scrollable_frame.
        Esborra primer els widgets existents i omple el diccionari item_widgets.
        """
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.item_widgets = {}
        for i, item in enumerate(items):
            var = BooleanVar(value=(item in self.selected_items))
            color = "blue" if item in self.selected_items else "black"
            switch = ctk.CTkSwitch(
                self.scrollable_frame,
                text=item,
                text_color=color,
                variable=var,
                command=lambda item=item, var=var: self._toggle_item(item, var)
            )
            switch.grid(row=i, column=0, pady=(0, 10), padx=5, sticky="w")
            self.item_widgets[item] = switch

    def _toggle_item(self, item: str, var: BooleanVar):
        """
        Alterna la selecció d'un element i actualitza l'aspecte del seu widget.
        """
        if var.get():
            self.selected_items.add(item)
        else:
            self.selected_items.discard(item)

        widget = self.item_widgets.get(item)
        if widget is not None:
            new_color = "blue" if item in self.selected_items else "black"
            widget.configure(text=item, text_color=new_color)
        else:
            current_filter = self.filter_entry.get().strip().lower()
            filtered = [it for it in self.full_item_list if current_filter in it.lower()]
            self._draw_items(filtered)

        if self.command:
            self.command()

    def _on_filter_change(self, event):
        """Aplicació d'un debounce per evitar redibuixar la llista en cada tecla."""
        if hasattr(self, "_filter_job"):
            self.after_cancel(self._filter_job)
        self._filter_job = self.after(300, self._apply_filter)

    def _apply_filter(self):
        """Aplica el filtre segons el text introduït i redibuixa la llista."""
        filter_text = self.filter_entry.get().lower()
        filtered = [item for item in self.full_item_list if filter_text in item.lower()]
        self._draw_items(filtered)

    def update_items(self, item_list: list):
        """Actualitza la llista completa d'elements i reinicia la selecció."""
        self.full_item_list = item_list
        self.selected_items.clear()
        self.filter_entry.delete(0, "end")
        self._draw_items(item_list)

    def get_selected_items(self) -> list:
        """Retorna una llista dels elements seleccionats."""
        return list(self.selected_items)


def log_message_console(message):
    print(message)


class App(ctk.CTk):
    """Aplicació principal per exportar CSV des de subcarpetes."""
    def __init__(self):
        super().__init__()
        self.title("Exportador de CSV")
        self.geometry("400x600")

        # Marc superior amb botons de selecció de carpeta i exportació
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(pady=20, padx=20, fill="x")
        source_btn = ctk.CTkButton(top_frame, text="Selecciona carpeta d'origen",
                                   command=self.select_source_folder)
        source_btn.grid(row=0, column=0, padx=10, sticky="w")
        export_btn = ctk.CTkButton(top_frame, text="Exporta a CSV",
                                   command=self.export_selected_folders)
        export_btn.grid(row=0, column=1, padx=10, sticky="w")
        
        # Nou frame per al selector d'interval d'exportació amb menys marge inferior
        selector_frame = ctk.CTkFrame(self)
        selector_frame.pack(pady=(0, 10), padx=20, fill="x")  # abans tenia pady=(0,20)
        label = ctk.CTkLabel(selector_frame, text="Període:")
        label.grid(row=0, column=0, padx=5, sticky="w")
        self.export_period_option = ctk.CTkOptionMenu(selector_frame, values=list(EXPORT_PERIODS.keys()))
        self.export_period_option.set("20 segons")
        self.export_period_option.grid(row=0, column=1, padx=5, sticky="w")
        
        # Widget filtrable per la llista de subcarpetes amb menys marge superior
        self.item_frame = FilterableItemFrame(self, item_list=[], width=650, height=300)
        self.item_frame.pack(padx=20, pady=(5, 20), fill="both", expand=True)  # abans tenia pady=20

        # Diccionari {nom_subcarpeta: ruta_completa}.
        self.subfolder_mapping = {}

        # Àrea de log per mostrar missatges d'exportació.
        self.log_textbox = ctk.CTkTextbox(self, height=100, state="disabled", font=("Helvetica", 11))
        self.log_textbox.pack(padx=20, pady=(5, 20), fill="x")

        # Fitxer de configuració.
        self.config_file = "config.txt"
        self.load_source_folder_from_config()

    def load_source_folder_from_config(self):
        """Carrega automàticament la carpeta d'origen si existeix i és vàlida."""
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                source_folder = f.read().strip()
            if os.path.isdir(source_folder):
                try:
                    subdirs = [os.path.join(source_folder, name)
                               for name in os.listdir(source_folder)
                               if os.path.isdir(os.path.join(source_folder, name)) and "TR2" in name]
                except Exception as e:
                    messagebox.showerror("Error", f"No s'ha pogut llegir la carpeta.\n{e}")
                    return
                if subdirs:
                    self.subfolder_mapping = {os.path.basename(subdir): subdir for subdir in subdirs}
                    self.item_frame.update_items(list(self.subfolder_mapping.keys()))
                    self.log_message(f"Carpeta d'origen carregada automàticament: {source_folder}")

    def select_source_folder(self):
        """Permet seleccionar la carpeta d'origen i actualitza la llista de subcarpetes."""
        source_folder = filedialog.askdirectory(title="Selecciona carpeta d'origen")
        if not source_folder:
            messagebox.showinfo("Informació", "No s'ha seleccionat cap carpeta.")
            return

        # Desa la selecció de carpeta en el fitxer de configuració
        with open(self.config_file, "w") as f:
            f.write(source_folder)

        try:
            subdirs = [
                os.path.join(source_folder, name)
                for name in os.listdir(source_folder)
                if os.path.isdir(os.path.join(source_folder, name)) and "TR2" in name
            ]
        except Exception as e:
            messagebox.showerror("Error", f"No s'ha pogut llegir la carpeta.\n{e}")
            return

        if not subdirs:
            messagebox.showinfo("Informació", "La carpeta seleccionada no conté subcarpetes amb 'TR2'.")
            return

        self.subfolder_mapping = {os.path.basename(subdir): subdir for subdir in subdirs}
        items = list(self.subfolder_mapping.keys())
        self.item_frame.update_items(items)
        self.log_message(f"Carpeta d'origen seleccionada: {source_folder}")

    def log_message(self, message):
        """Afegeix el missatge a l'àrea de log sense aplicar colors."""
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def export_selected_folders(self):
        """Exporta a CSV les subcarpetes seleccionades amb l'agrupació segons el període seleccionat."""
        selected_items = self.item_frame.get_selected_items()
        if not selected_items:
            messagebox.showinfo("Informació", "No s'han seleccionat subcarpetes.")
            return

        export_folder = filedialog.askdirectory(title="Selecciona carpeta d'exportació")
        if not export_folder:
            return

        # Recuperem el període d'exportació seleccionat i la seva durada en segons
        export_period_label = self.export_period_option.get()
        export_period_sec = EXPORT_PERIODS.get(export_period_label, 20)

        # Neteja l'àrea de log
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")
        
        # Registra al log que s'ha iniciat l'exportació
        self.log_message("Exportació iniciada.")

        # Comptar el nombre total de fitxers en totes les subcarpetes seleccionades
        total_files = 0
        for item in selected_items:
            folder_path = self.subfolder_mapping.get(item)
            if folder_path:
                files = [f for f in os.listdir(folder_path)
                         if os.path.splitext(f)[1][1:].isdigit()]
                total_files += len(files)
        if total_files == 0:
            self.log_message("No s'han trobat fitxers de dades en les subcarpetes seleccionades.")
            return

        # Crea la progress bar amb la mateixa amplada que l'àrea de log
        progress_bar = ctk.CTkProgressBar(self)
        progress_bar.pack(pady=(0, 20), padx=20, fill="x")
        self.update()

        # Contador mutable per emmagatzemar el nombre de fitxers processats
        progress_counter = [0]

        def update_progress():
            progress_counter[0] += 1
            progress_bar.set(progress_counter[0] / total_files)
            self.update_idletasks()

        # Processa cada subcarpeta passant el callback per actualitzar la progress bar
        for item in selected_items:
            folder_path = self.subfolder_mapping.get(item)
            if folder_path:
                result_msg = process_subfolder(folder_path, export_folder, export_period_sec, progress_callback=update_progress)
                print(result_msg)
                self.log_message(result_msg)

        self.log_message("Exportació finalitzada.")
        progress_bar.destroy()


if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = App()
    app.mainloop()