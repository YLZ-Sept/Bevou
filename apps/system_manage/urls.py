from django.urls import path

from . import views

app_name = "system_manage"
# @formatter:off
# fmt: off
urlpatterns = [
    path('workspace/<str:workspace_id>/user_resource_permission/user/<str:user_id>/resource/<str:resource>', views.WorkSpaceUserResourcePermissionView.as_view()),
    path('workspace/<str:workspace_id>/user_resource_permission/user/<str:user_id>/resource/<str:resource>/<int:current_page>/<int:page_size>', views.WorkSpaceUserResourcePermissionView.Page.as_view()),
    path('workspace/<str:workspace_id>/resource_user_permission/resource/<str:target>/resource/<str:resource>', views.WorkspaceResourceUserPermissionView.as_view()),
    path('workspace/<str:workspace_id>/resource_user_permission/resource/<str:target>/resource/<str:resource>/<int:current_page>/<int:page_size>', views.WorkspaceResourceUserPermissionView.Page.as_view()),
    path('workspace/<str:workspace_id>/resource_mapping/<str:resource>/<str:resource_id>/<int:current_page>/<int:page_size>', views.ResourceMappingView.as_view()),
    path('workspace/<str:workspace_id>/mapping_resource/<str:resource>/<str:resource_id>/<int:current_page>/<int:page_size>', views.MappingResourceView.as_view()),
    path('system/chat_user/authorize/knowledge/<str:knowledge_id>', views.KnowledgeChatUserAuthView.Operate.as_view()),
    path('system/chat_user/list', views.ChatUserView.List.as_view()),
    path('system/chat_user/user_manage/<int:current_page>/<int:page_size>', views.ChatUserView.Page.as_view()),
    path('system/chat_user/sync_types', views.ChatUserView.SyncTypes.as_view()),
    path('system/chat_user/sync/<str:sync_type>', views.ChatUserView.Sync.as_view()),
    path('system/chat_user/batch_add_group', views.ChatUserView.BatchAddGroup.as_view()),
    path('system/chat_user/batch_delete', views.ChatUserView.BatchDelete.as_view()),
    path('system/chat_user/<str:user_id>/re_password', views.ChatUserView.Password.as_view()),
    path('system/chat_user', views.ChatUserView.Create.as_view()),
    path('system/chat_user/<str:user_id>', views.ChatUserView.Operate.as_view()),
    path('system/group', views.UserGroupView.List.as_view()),
    path('system/group/<str:group_id>/add_member', views.UserGroupView.AddMember.as_view()),
    path('system/group/<str:group_id>/remove_member', views.UserGroupView.RemoveMember.as_view()),
    path('system/group/<str:group_id>/user_list/<int:current_page>/<int:page_size>', views.UserGroupView.UserPage.as_view()),
    path('system/group/<str:group_id>', views.UserGroupView.Operate.as_view()),
    path('display/info', views.DisplayView.Info.as_view()),
    path('display/update', views.DisplayView.Update.as_view()),
    path('display/image/<str:image_name>', views.DisplayImageView.as_view()),
    path('operate_log/menu_operation_option/', views.OperateLogView.Menu.as_view()),
    path('operate_log/get_clean_time', views.OperateLogView.CleanTime.as_view()),
    path('operate_log/save', views.OperateLogView.CleanTime.as_view()),
    path('operate_log/export/', views.OperateLogView.Export.as_view()),
    path('operate_log/<int:current_page>/<int:page_size>', views.OperateLogView.Page.as_view()),
    path('email_setting', views.SystemSetting.Email.as_view()),
    path('profile', views.SystemProfile.as_view()),
    path('valid/<str:valid_type>/<int:valid_count>', views.Valid.as_view())
]
