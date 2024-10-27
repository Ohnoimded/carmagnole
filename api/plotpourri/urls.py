from django.urls import path, re_path
from .views import serve_plot_data


urlpatterns = [
    path('plotdata/', serve_plot_data, name='plotpourri_plotdata'),
]


