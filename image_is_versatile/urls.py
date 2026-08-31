from django.urls import path

from image_is_versatile import views

app_name = "image_is_versatile"

urlpatterns = [
    path("", views.HistoryView.as_view(), name="history"),
    path("new/", views.NewAnalysisView.as_view(), name="new"),
    path("settings/", views.VisionSettingsView.as_view(), name="settings"),
    path("settings/api-keys/", views.ApiKeysSettingsView.as_view(), name="api_keys"),
    path(
        "api/model-status/<str:model_id>/",
        views.ModelStatusView.as_view(),
        name="model_status",
    ),
    path("analysis/<uuid:analysis_id>/", views.DetailView.as_view(), name="detail"),
]
