import tkinter as tk
from tkinter import messagebox
from models.product_model import ProductModel
from views.product_view import ProductView
from controllers.movimientos_controllers import MovementController
from models.export_manager import ExportManager

class ProductController:
    def __init__(self, app):
        self.app = app
        self.model = ProductModel()
        self.view = ProductView(frame=None, app=app)
        self.view.set_controller(self)  # Conectar vista con controlador

    def show_inventory(self):
        """Mostrar gestión de inventario"""
        from helpers import clear_frame
        clear_frame(self.app.content_frame)

        title_frame = tk.Frame(self.app.content_frame,
                            bg=self.app.colors["background"])
        title_frame.pack(fill="x", pady=(5, 5))

        tk.Label(title_frame, text="Gestión de Inventario",
                font=self.app.title_font, bg=self.app.colors["background"]).pack(side="left")
        
        # Mostrar inventario en un único frame (sin pestañas)
        inventory_frame = tk.Frame(self.app.content_frame, bg=self.app.colors["background"])
        inventory_frame.pack(fill="both", expand=True, padx=0, pady=0)

        self.setup_inventory_tab(inventory_frame)

    def setup_inventory_tab(self, frame):
        """Configurar pestaña de inventario"""
        self.view.frame = frame
        self.view.setup_styles()
        self.view.setup_inventory_tab(frame)

        # Cargar datos iniciales
        self.refresh_table()

        # Actualizar combobox de categorías
        categorias = self.model.get_combobox_data("categorias")
        self.view.update_categories_combo(categorias)
        marcas = self.model.get_combobox_data("marcas")
        self.view.update_marcas_combo(marcas)

    def refresh_table(self):
        """Refrescar tabla de productos"""
        try:
            inventario_data = self.model.update_product_stock_status()
            formatted_data = self._format_table_data(inventario_data)
            self.view.refresh_table(formatted_data)

            if hasattr(self.app, 'notification_manager'):
                self.app.notification_manager.check_low_stock()

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar datos: {e}")

    def _format_table_data(self, inventario_data):
        """Formatear datos para la tabla"""
        formatted_data = []
        for item in inventario_data:
            formatted_data.append((
                item[0],  # Nro (id_producto)
                item[2],  # Producto
                item[3] if item[3] else "N/A",  # Marca
                item[4] if item[4] else "N/A",  # Categoría
                item[1],  # Código
                item[5] if item[5] else 0,      # Stock
                item[6] if item[6] else "N/A",  # Ubicación
                item[7] if item[7] else "disponible"  # Estado
            ))
        return formatted_data

    def search_products(self):
        """Buscar productos"""
        try:
            search_term = self.view.get_search_term()
            filters = self.view.get_filters()

            extra = " AND (p.nombre ILIKE %s OR p.codigo ILIKE %s)"
            params = [f"%{search_term}%", f"%{search_term}%"]

            if filters['categoria'] != "Todas":
                extra += " AND c.nombre = %s"
                params.append(filters['categoria'])

            if filters['estado'] != "Todos":
                extra += " AND i.estado_stock = %s"
                params.append(filters['estado'].lower() if filters['estado'] != "Stock bajo" else "stock bajo")

            inventario_data = self.model.get_products(extra, tuple(params))
            formatted_data = self._format_table_data(inventario_data)
            self.view.refresh_table(formatted_data)

        except Exception as e:
            messagebox.showerror("Error", f"Error al buscar productos: {e}")

    def apply_filters(self):
        """Aplicar filtros a la tabla"""
        try:
            filters = self.view.get_filters()

            extra = ""
            params = []

            if filters['categoria'] != "Todas":
                extra += " AND c.nombre = %s"
                params.append(filters['categoria'])

            if filters['estado'] != "Todos":
                extra += " AND i.estado_stock = %s"
                params.append(filters['estado'].lower() if filters['estado'] != "Stock bajo" else "stock bajo")

            inventario_data = self.model.get_products(extra, tuple(params))
            formatted_data = self._format_table_data(inventario_data)
            self.view.refresh_table(formatted_data)

        except Exception as e:
            messagebox.showerror("Error", f"Error al aplicar filtros: {e}")

    def new_product(self):
        """Crear nuevo producto"""
        self.show_product_form()

    def show_product_form(self, product_id=None):
        """Mostrar formulario de producto"""
        try:
            # Obtener datos activos
            marcas = self.model.get_combobox_data("marcas")
            categorias = self.model.get_combobox_data("categorias")
            ubicaciones = self.model.get_combobox_data("ubicaciones")

            # Si es edición, obtener también la relación actual aunque esté inactiva
            if product_id:
                producto_data = self.model.get_product_data(product_id)
                # producto_data: (id_producto, codigo, nombre, id_marca, id_categoria, stock, id_ubicacion, estado_stock)
                id_marca = producto_data[3]
                id_categoria = producto_data[4]
                id_ubicacion = producto_data[6]

                # Buscar si la relación actual está en los activos, si no, agregarla
                if id_marca and not any(m[0] == id_marca for m in marcas):
                    self.model.cursor.execute("SELECT id_marca, nombre FROM marcas WHERE id_marca = %s", (id_marca,))
                    inactiva = self.model.cursor.fetchone()
                    if inactiva:
                        marcas.append(inactiva)
                if id_categoria and not any(c[0] == id_categoria for c in categorias):
                    self.model.cursor.execute("SELECT id_categoria, nombre FROM categorias WHERE id_categoria = %s", (id_categoria,))
                    inactiva = self.model.cursor.fetchone()
                    if inactiva:
                        categorias.append(inactiva)
                if id_ubicacion and not any(u[0] == id_ubicacion for u in ubicaciones):
                    self.model.cursor.execute("SELECT id_ubicacion, nombre FROM ubicaciones WHERE id_ubicacion = %s", (id_ubicacion,))
                    inactiva = self.model.cursor.fetchone()
                    if inactiva:
                        ubicaciones.append(inactiva)

            form_window, entries, buttons, save_btn = self.view.show_product_form(product_id)

            entries["Marca:"]['values'] = [m[1] for m in marcas]
            entries["Categoría:"]['values'] = [c[1] for c in categorias]
            entries["Ubicación:"]['values'] = [u[1] for u in ubicaciones]

            for label, btn in buttons.items():
                tabla = {"Marca:": "marcas", "Categoría:": "categorias",
                         "Ubicación:": "ubicaciones"}[label]
                btn.configure(command=lambda t=tabla: self.add_new_value(t))

            save_btn.configure(command=lambda: self.save_product(
                entries, product_id, marcas, categorias, ubicaciones, form_window))

            if product_id:
                self.load_product_data(product_id, entries, marcas, categorias, ubicaciones)

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar formulario: {e}")

    def load_product_data(self, product_id, entries, marcas, categorias, ubicaciones):
        """Cargar datos de producto en formulario"""
        try:
            producto_data = self.model.get_product_data(product_id)
            if not producto_data:
                raise Exception("Producto no encontrado")

            entries["Código:"].insert(0, producto_data[1])
            entries["Producto:"].insert(0, producto_data[2])

            if producto_data[3]:  # ID marca
                marca_nombre = next((m[1] for m in marcas if m[0] == producto_data[3]), "")
                entries["Marca:"].set(marca_nombre)

            if producto_data[4]:  # ID categoría
                categoria_nombre = next((c[1] for c in categorias if c[0] == producto_data[4]), "")
                entries["Categoría:"].set(categoria_nombre)

            if producto_data[5] is not None:  # Stock
                entries["Stock inicial:"].insert(0, producto_data[5])

            if producto_data[7]:  # Estado
                entries["Estado:"].set(producto_data[7])

            if producto_data[6]:  # ID ubicación
                ubicacion_nombre = next((u[1] for u in ubicaciones if u[0] == producto_data[6]), "")
                entries["Ubicación:"].set(ubicacion_nombre)

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar datos: {str(e)}")

    def save_product(self, entries, product_id, marcas, categorias, ubicaciones, window):
        """Guardar producto"""
        try:
            # Obtener valores del formulario
            codigo = entries["Código:"].get().strip()
            producto = entries["Producto:"].get().strip()
            stock_txt = entries["Stock inicial:"].get().strip()
            marca_nombre = entries["Marca:"].get()
            categoria_nombre = entries["Categoría:"].get()
            ubicacion_nombre = entries["Ubicación:"].get()
            estado = entries["Estado:"].get()

            # Validaciones
            if not self._validate_product_data(codigo, producto, stock_txt):
                return

            # Obtener IDs de relaciones
            marca_id = self.model.get_id_by_name("marcas", marca_nombre)
            categoria_id = self.model.get_id_by_name("categorias", categoria_nombre)
            ubicacion_id = self.model.get_id_by_name("ubicaciones", ubicacion_nombre)

            # Identificar cuál está inactivo
            errores = []
            if marca_id is None:
                errores.append("Marca")
            if categoria_id is None:
                errores.append("Categoría")
            if ubicacion_id is None and ubicacion_nombre:  # Solo si es obligatorio
                errores.append("Ubicación")

            if errores:
                mensaje = (
                    f"Error: {', '.join(errores)} seleccionada se encuentra inactiva.\n"
                    "Para permitir la edición, por favor actívela en Ajustes."
                )
                messagebox.showerror("Error de relación inactiva", mensaje)
                return

            # Preparar datos para guardar
            product_data = {
                'codigo': codigo,
                'nombre': producto,
                'marca_id': marca_id,
                'categoria_id': categoria_id,
                'stock': int(stock_txt),
                'ubicacion_id': ubicacion_id,
                'estado': estado
            }

            # Guardar producto
            saved_id = self.model.save_product(product_data, product_id)

            # Registrar movimiento
            self._register_product_movement(product_id, saved_id, int(stock_txt), ubicacion_id)

            messagebox.showinfo("Éxito", "Producto guardado correctamente")
            window.destroy()
            self.refresh_table()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el producto: {e}")

    def _validate_product_data(self, codigo, producto, stock_txt):
        """Validar datos del producto"""
        if not codigo or not producto or not stock_txt:
            messagebox.showwarning("Campos requeridos", "Todos los campos deben estar llenos.")
            return False

        if not stock_txt.isdigit() or int(stock_txt) < 0:
            messagebox.showerror("Stock inválido", "El stock debe ser un número entero positivo.")
            return False

        if not codigo.replace("-", "").isalnum():
            messagebox.showerror("Código inválido", "El código solo debe contener letras, números y guiones.")
            return False

        if not all(c.isalnum() or c.isspace() for c in producto):
            messagebox.showerror("Nombre inválido", "El nombre del producto solo debe contener letras, números y espacios.")
            return False

        return True

    def _register_product_movement(self, product_id, saved_id, stock, ubicacion_id):
        """Registrar movimiento de producto"""
        movement_controller = MovementController(None, self.app, create_ui=False)
        current_user = getattr(self.app, 'current_user', None)
        current_user_id = getattr(current_user, 'id', None)

        if product_id:  # Edición
            old_stock = self.model.get_old_stock(product_id)
            # Si old_stock es None, tratarlo como 0
            old_stock = old_stock if old_stock is not None else 0
            stock_diff = stock - old_stock
            
            if stock_diff != 0:
                movement_type = "Entrada" if stock_diff > 0 else "Salida"
                movement_controller.register_movement(
                    id_producto=product_id,
                    tipo=movement_type,
                    cantidad=abs(stock_diff),
                    id_ubicacion=ubicacion_id,
                    id_responsable=current_user_id,
                    referencia="Edición de stock inicial"  # Corregido - sin tilde
                )
        else:  # Nuevo producto
            try:
                movement_controller.register_movement(
                    id_producto=saved_id,
                    tipo="Entrada",
                    cantidad=stock,
                    id_ubicacion=ubicacion_id,
                    id_responsable=current_user_id,
                    referencia="Producto nuevo"
                )
            except Exception as e:
                messagebox.showwarning("Advertencia", f"Producto creado pero no se pudo registrar el movimiento: {e}")

    def edit_selected_product(self):
        """Editar producto seleccionado"""
        selected = self.view.get_selected_product()
        if not selected:
            messagebox.showwarning("Advertencia", "Por favor seleccione un producto")
            return

        product_id = selected['tags'][0]
        self.show_product_form(product_id)

    def delete_selected_product(self):
        """Eliminar producto seleccionado"""
        selected = self.view.get_selected_product()
        if not selected:
            messagebox.showwarning("Advertencia", "Por favor seleccione un producto")
            return

        product_id = selected['tags'][0]

        if messagebox.askyesno("Confirmar", "¿Está seguro de marcar este producto como inactivo?"):
            try:
                self.model.delete_product(product_id)
                messagebox.showinfo("Éxito", "Producto marcado como inactivo")
                self.refresh_table()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar: {e}")

    def show_add_stock_form(self):
        """Mostrar formulario para agregar stock"""
        selected = self.view.get_selected_product()
        if not selected:
            messagebox.showwarning("Advertencia", "Seleccione un producto primero")
            return

        item_data = selected['values']
        product_id = selected['tags'][0]
        product_name = item_data[1]
        current_stock = item_data[5] if item_data[5] else 0

        form_window, qty_entry, add_btn = self.view.show_add_stock_form(product_name, current_stock)
        add_btn.configure(command=lambda: self.add_stock(product_id, qty_entry.get(), form_window))

    def add_stock(self, product_id, quantity, window):
        """Agregar stock a producto"""
        try:
            if not quantity.isdigit() or int(quantity) <= 0:
                messagebox.showerror("Error", "Ingrese una cantidad válida (número positivo)")
                return

            self.model.add_stock(product_id, quantity)

            # Registrar movimiento
            ubicacion_id = self.model.get_ubicacion_id(product_id)
            movement_controller = MovementController(None, self.app, create_ui=False)
            current_user = getattr(self.app, 'current_user', None)
            current_user_id = getattr(current_user, 'id', None)
            movement_controller.register_movement(
                id_producto=product_id,
                tipo="Entrada",
                cantidad=int(quantity),
                id_ubicacion=ubicacion_id,
                id_responsable=current_user_id,
                referencia="Entrada de stock"
            )

            messagebox.showinfo("Éxito", "Stock actualizado correctamente")
            window.destroy()
            self.refresh_table()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar el stock: {e}")

    def add_new_value(self, table):
        """Agregar nuevo valor a tabla relacionada"""
        form_window, entry, save_btn = self.view.show_new_value_form(table)
        save_btn.configure(command=lambda: self.guardar_valor(table, entry.get(), form_window))

    def guardar_valor(self, table, value, window):
        """Guardar nuevo valor en tabla relacionada"""
        try:
            if not value:
                messagebox.showwarning("Advertencia", "El campo no puede estar vacío.")
                return

            self.model.add_new_value(table, value)
            window.destroy()
            # Recargar el formulario actual si está abierto
            self.refresh_table()
            # Refrescar el combobox correspondiente
            if table == "ubicaciones":
                ubicaciones = self.model.get_combobox_data("ubicaciones")
                self.view.update_ubicaciones_combo(ubicaciones)
            elif table == "categorias":
                categorias = self.model.get_combobox_data("categorias")
                self.view.update_categories_combo(categorias)
            elif table == "marcas":
                marcas = self.model.get_combobox_data("marcas")
                self.view.update_marcas_combo(marcas)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")

    def export_inventory(self):
        """Exportar inventario a CSV"""
        try:
            # Obtener datos actuales de la tabla
            filtered_data = []
            for item in self.view.tree.get_children():
                row_data = self.view.tree.item(item)['values']
                filtered_data.append(row_data)

            filename, error = ExportManager.export_inventory(filtered_data)

            if error:
                messagebox.showerror("Error", f"Error al exportar: {error}")
            else:
                messagebox.showinfo("Éxito", f"Inventario exportado en {filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar inventario: {str(e)}")
            
    def refresh_comboboxes(self):
        """Refrescar todos los combobox con datos actualizados"""
        try:
            categorias = self.model.get_combobox_data("categorias")
            self.view.update_categories_combo(categorias)
            marcas = self.model.get_combobox_data("marcas")
            self.view.update_marcas_combo(marcas)
        except Exception as e:
            print(f"Error al refrescar comboboxes: {e}")