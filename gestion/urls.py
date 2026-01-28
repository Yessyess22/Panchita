from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.index, name='index'),
    path('pos/', views.pos_view, name='pos'),
    path('pos/procesar-pago/', views.pos_procesar_pago, name='pos_procesar_pago'),
    path('productos/', views.producto_index, name='producto_index'),
    path('productos/crear/', views.producto_crear, name='producto_crear'),
    path('productos/<int:pk>/editar/', views.producto_editar, name='producto_editar'),
    path('productos/<int:pk>/eliminar/', views.producto_eliminar, name='producto_eliminar'),
    path('ventas/', views.venta_index, name='venta_index'),
    path('ventas/crear/', views.venta_crear, name='venta_crear'),
]

