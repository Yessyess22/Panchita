from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.index, name='index'),
    path('pos/', views.pos_view, name='pos'),
    path('pos/procesar-pago/', views.pos_procesar_pago, name='pos_procesar_pago'),
    path('pos/buscar-clientes/', views.pos_buscar_clientes, name='pos_buscar_clientes'),
    path('pos/crear-cliente/', views.pos_crear_cliente, name='pos_crear_cliente'),
    path('productos/', views.producto_index, name='producto_index'),
    path('productos/crear/', views.producto_crear, name='producto_crear'),
    path('productos/<int:pk>/editar/', views.producto_editar, name='producto_editar'),
    path('productos/<int:pk>/eliminar/', views.producto_eliminar, name='producto_eliminar'),
    path('clientes/', views.cliente_index, name='cliente_index'),
    path('ventas/', views.venta_index, name='venta_index'),
    path('ventas/crear/', views.venta_crear, name='venta_crear'),
]

