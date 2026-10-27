from rest_framework import permissions


class ProfilePermission(permissions.BasePermission):
  # 読み取り（GET等）は誰でもOK。更新・削除はプロフィール本人だけ許可する。

  def has_object_permission(self, request, view, obj):
    if request.method in permissions.SAFE_METHODS:
      return True
    return obj.userProfile == request.user


class HaikuPermission(permissions.BasePermission):
  # 読み取り（GET等）は誰でもOK。更新・削除は投稿者本人だけ許可する。
  # （APIを直接呼べば他人の句も編集・削除できてしまう、という抜け道を防ぐため）

  def has_object_permission(self, request, view, obj):
    if request.method in permissions.SAFE_METHODS:
      return True
    return obj.userPost == request.user


class CommentPermission(permissions.BasePermission):
  # 読み取り（GET等）は誰でもOK。更新・削除はコメント投稿者本人だけ許可する。

  def has_object_permission(self, request, view, obj):
    if request.method in permissions.SAFE_METHODS:
      return True
    return obj.userComment == request.user


class FollowPermission(permissions.BasePermission):
  # 読み取り（GET等）は誰でもOK。削除はフォローした本人だけ許可する。

  def has_object_permission(self, request, view, obj):
    if request.method in permissions.SAFE_METHODS:
      return True
    return obj.follower == request.user
