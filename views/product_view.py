import tkinter as tk
from tkinter import ttk
from views.base_view import BaseView

class ProductView(BaseView):
    def __init__(self, frame, app):
        super().__init__(frame, app)
        self.controller = None

    def set_controller(self, controller):
        """Establecer el controlador para esta vista"""
        self.controller = controller

    def setup_inventory_tab(self, frame):
        """Configurar pestaña de inventario"""
        # Frame principal
        main_container = self.create_main_container(frame)
        main_container.pack(fill="both", expand=True, padx=0, pady=0)

        # --- CONTENEDOR HORIZONTAL PARA BOTONES ---
        top_frame = self.create_section_frame(main_container)
        top_frame.pack(fill="x", padx=10, pady=(0, 0))

        # Botones de acción
        actions = [
            ("➕ Nuevo", self.controller.new_product),
            ("✏️ Editar", self.controller.edit_selected_product),
            ("🗑️ Eliminar", self.controller.delete_selected_product),
            ("📥 Agregar Stock", self.controller.show_add_stock_form),
            ("📤 Exportar", self.controller.export_inventory)
        ]
        button_frame, action_buttons = self.create_action_buttons(top_frame, actions)
        button_frame.pack(side="left", pady=(0, 5))

        # --- FRAME DE FILTROS ---
        filtros_frame = tk.LabelFrame(main_container, text="Filtros", font=self.label_font, bg=self.bg_color, fg=self.fg_color)
        filtros_frame.pack(fill="x", padx=10, pady=(5, 5))

        # --- FILA 1: BUSCADOR ---
        buscador_frame = tk.Frame(filtros_frame, bg=self.bg_color)
        buscador_frame.pack(fill="x", padx=5, pady=(8, 2))
        tk.Label(buscador_frame, text="Buscar por producto:", 
                font=self.label_font, bg=self.bg_color, fg=self.fg_color).pack(side="left", padx=5)
        self.search_entry = ttk.Entry(buscador_frame, width=30, font=self.entry_font)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.controller.search_products())

        # --- FILA 2: COMBOBOX Y BOTÓN ---
        filtros_inner_frame = tk.Frame(filtros_frame, bg=self.bg_color)
        filtros_inner_frame.pack(fill="x", padx=5, pady=(2, 8))

        categoria_frame, self.categoria_var, self.categoria_combo = self.create_filter_combo(
            filtros_inner_frame, "Categoría:", 
            ["Todas", "Electrónicos", "Ropa", "Hogar", "Deportes"],
            "Todas", 15
        )
        categoria_frame.pack(side="left", padx=5)

        marca_frame, self.marca_var, self.marca_combo = self.create_filter_combo(
            filtros_inner_frame, "Marca:",
            ["Todas", "Marca A", "Marca B", "Marca C"],
            "Todas", 15
        )
        marca_frame.pack(side="left", padx=5)

        estado_frame, self.estado_var, self.estado_combo = self.create_filter_combo(
            filtros_inner_frame, "Estado:",
            ["Todos", "Disponible", "Stock bajo", "Agotado"],
            "Todos", 15
        )
        estado_frame.pack(side="left", padx=5)

        # Botón aplicar filtros
        self.apply_btn = ttk.Button(filtros_inner_frame, text="Aplicar Filtros", style="Accent.TButton",
                                  command=self.controller.apply_filters)
        self.apply_btn.pack(side="left", padx=10)

        # --- TABLA ---
        columns = ("Nro", "Producto", "Marca", "Categoría", "Código", "Stock", "Ubicación", "Estado")
        col_widths = [50, 150, 100, 100, 80, 60, 80, 80]
        
        table_frame, self.tree = self.create_table(main_container, columns, col_widths, height=15)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        return self

    def get_search_term(self):
        """Obtener término de búsqueda"""
        return self.search_entry.get().strip()

    def get_filters(self):
        """Obtener valores de filtros"""
        return {
            'categoria': self.categoria_combo.get(),
            'marca': self.marca_combo.get(),
            'estado': self.estado_combo.get()
        }

    def refresh_table(self, data):
        """Refrescar tabla con nuevos datos"""
        self.tree.delete(*self.tree.get_children())
        for i, item in enumerate(data, start=1):
            # Reemplaza el primer elemento por el número de fila
            fila = (i,) + item[1:]
            self.tree.insert("", "end", values=fila, tags=(item[0],))

    def get_selected_product(self):
        """Obtener producto seleccionado"""
        selected_item = self.tree.selection()
        if not selected_item:
            return None
        return self.tree.item(selected_item[0])

    def update_categories_combo(self, categories):
        """Actualizar combobox de categorías SOLO CON ACTIVAS"""
        self.categoria_combo['values'] = ["Todas"] + [c[1] for c in categories]

    def update_marcas_combo(self, marcas):
        """Actualizar combobox de marcas SOLO CON ACTIVAS"""
        self.marca_combo['values'] = ["Todas"] + [m[1] for m in marcas]

    def show_product_form(self, product_id=None):
        """Mostrar formulario de producto"""
        form_window = self.create_modal_window(
            self.app,
            "Nuevo Producto" if not product_id else "Editar Producto",
            "420x450"
        )
        
        # Frame principal del formulario
        basic_frame = self.create_form_frame(form_window, "Datos del Producto")
        basic_frame.pack(fill="x", padx=10, pady=5)

        # Campos del formulario
        fields_config = [
            ("Código:", "entry", None),
            ("Producto:", "entry", None),
            ("Marca:", "combobox", []),
            ("Categoría:", "combobox", []),
            ("Stock inicial:", "entry", None),
            ("Ubicación:", "combobox", []),
            ("Estado:", "combobox", ["disponible", "stock bajo", "agotado", "reservado"])
        ]
        
        entries = self.create_form_fields(basic_frame, fields_config)
        buttons = {}

        # Botones adicionales para marcas, categorías, ubicaciones
        for i, (label, field_type, options) in enumerate(fields_config):
            if label in ["Marca:", "Categoría:", "Ubicación:"]:
                btn = ttk.Button(basic_frame, text="➕", width=2, style="TButton")
                btn.grid(row=i, column=2, padx=(0, 5))
                buttons[label] = btn

        # Botones principales
        btn_frame, save_btn, cancel_btn = self.create_form_buttons(form_window)
        btn_frame.pack(fill="x", pady=10)
        cancel_btn.configure(command=form_window.destroy)

        # Centrar ventana
        self.center_window(form_window)

        return form_window, entries, buttons, save_btn

    def show_add_stock_form(self, product_name, current_stock):
        """Mostrar formulario para agregar stock"""
        form_window = self.create_modal_window(
            self.app, 
            f"Agregar Stock - {product_name}"
        )
        
        # Frame principal
        main_frame = self.create_form_frame(form_window, "Agregar Stock")
        main_frame.pack(fill="both", expand=True, padx=16, pady=12)

        # Información del producto
        tk.Label(main_frame, text=f"Producto: {product_name}", 
                font=self.form_label_font, bg=self.bg_color, fg=self.fg_color).pack(anchor="w")
        tk.Label(main_frame, text=f"Stock actual: {current_stock}", 
                font=self.form_label_font, bg=self.bg_color, fg=self.fg_color).pack(anchor="w")
        tk.Label(main_frame, text="Cantidad a agregar:", 
                font=self.form_label_font, bg=self.bg_color, fg=self.fg_color).pack(anchor="w", pady=(10, 0))

        # Campo de cantidad
        qty_entry = ttk.Entry(main_frame, font=self.form_entry_font)
        qty_entry.pack(fill="x", pady=5, ipady=3)

        # Botones
        btn_frame, add_btn, cancel_btn = self.create_form_buttons(main_frame)
        btn_frame.pack(fill="x", pady=15)
        add_btn.configure(text="Agregar")
        cancel_btn.configure(command=form_window.destroy)

        self.center_window(form_window)

        return form_window, qty_entry, add_btn

    def show_new_value_form(self, table):
        """Mostrar formulario para agregar nuevo valor a tabla relacionada"""
        form_window = self.create_modal_window(
            self.app, 
            f"Agregar {table}"
        )
        
        # Frame principal
        main_frame = self.create_form_frame(form_window, f"Nuevo {table.capitalize()}")
        main_frame.pack(fill="both", expand=True)

        # Campo de nombre
        tk.Label(main_frame, text="Nombre:", 
                font=self.form_label_font, bg=self.bg_color, fg=self.fg_color).pack(pady=10)
        
        entry = ttk.Entry(main_frame, font=self.form_entry_font)
        entry.pack(pady=10, padx=20, fill="x", ipady=3)

        # Botones
        btn_frame, save_btn, cancel_btn = self.create_form_buttons(main_frame)
        btn_frame.pack(pady=10)
        cancel_btn.configure(command=form_window.destroy)

        self.center_window(form_window)

        return form_window, entry, save_btn