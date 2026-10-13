#!/usr/bin/env python3
"""公众号 API 直推草稿箱工具。

v4.0.0 重建：干净重写，命令与参数与 v3.3.0 一致。
用法：
  python3 gzh-api-push.py token
  python3 gzh-api-push.py upload --file cover.jpg
  python3 gzh-api-push.py push --file content.html --title "标题" --thumb media_id
  python3 gzh-api-push.py get-draft --id 草稿ID
  python3 gzh-api-push.py update --id 草稿ID --title "新标题"

退出码：0 成功；1 接口调用失败；2 参数错误 / 缺配置 / 缺 requests 依赖。
"""
import json
import mimetypes
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gzhkit import cli as gzh_cli

BASE_URL = 'https://api.weixin.qq.com/cgi-bin'


def _requests():
    try:
        import requests
        return requests
    except ImportError:
        gzh_cli.missing_dependency('requests', '安装：pip install requests')


def _creds():
    return os.environ.get('WX_APPID'), os.environ.get('WX_APPSECRET')


def check_env():
    """检查环境变量。缺失返回 False（调用方 exit 2）。"""
    appid, secret = _creds()
    if not appid or not secret:
        print('❌ 缺少环境变量 WX_APPID 或 WX_APPSECRET')
        print('   获取方式：公众号后台「设置与开发 → 基本配置」')
        return False
    return True


def get_token():
    """获取 access_token。成功返回 token，失败返回 None。"""
    requests = _requests()
    appid, secret = _creds()
    url = '%s/token' % BASE_URL
    params = {'grant_type': 'client_credential', 'appid': appid, 'secret': secret}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.encoding = 'utf-8'  # 强制 UTF-8 编码
        data = r.json()
        if 'access_token' in data:
            print('✅ access_token: %s...' % data["access_token"][:20])
            print('   有效期: %s秒' % data.get("expires_in", 7200))
            return data['access_token']
        elif data.get('errcode') == 40164:
            print('❌ 错误 40164: IP 不在白名单')
            print('   处理：公众号后台「基本配置 → IP 白名单」添加当前服务器 IP')
        elif data.get('errcode') == 48001:
            print('❌ 错误 48001: 公众号未认证')
            print('   处理：个人订阅号不行，需先完成认证')
        elif data.get('errcode') == 40001:
            print('❌ 错误 40001: AppSecret 无效 (%s)' % data.get("errmsg"))
        else:
            print('❌ 获取 token 失败: %s' % data)
        return None
    except Exception as e:
        print('❌ 网络错误: %s' % e)
        return None


def upload_image(file_path):
    """上传封面图，返回 media_id（失败返回 None）。"""
    requests = _requests()
    token = get_token()
    if not token:
        return None
    if not os.path.exists(file_path):
        print('❌ 文件不存在: %s' % file_path)
        return None

    # 检测图片类型
    mime = mimetypes.guess_type(file_path)[0] or 'image/jpeg'

    # 封面图使用永久素材接口（type=thumb）
    url = '%s/material/add_material' % BASE_URL
    params = {'access_token': token, 'type': 'thumb'}
    with open(file_path, 'rb') as f:
        files = {'media': (os.path.basename(file_path), f, mime)}
        r = requests.post(url, params=params, files=files, timeout=30)
        data = r.json()

    if 'media_id' in data:
        print('✅ 上传成功')
        print('   MediaID: %s' % data["media_id"])
        print('   URL: %s' % data.get("url", "N/A"))
        return data['media_id']
    print('❌ 上传失败: %s' % data)
    return None


def push_draft(content_html, title, thumb_media_id):
    """推送草稿到公众号。成功返回草稿ID，失败返回 None。"""
    requests = _requests()
    token = get_token()
    if not token:
        return None
    url = '%s/draft/add' % BASE_URL
    params = {'access_token': token}

    article = {
        'title': title,
        'author': '',
        'digest': '两办首推人工智能+，从概念变为国家战略基建',
        'content': content_html,
        'content_source_url': '',
        'thumb_media_id': thumb_media_id,
        'need_open_comment': 0,
        'only_fans_can_comment': 0,
    }

    payload = {'articles': [article]}

    try:
        # 关键：ensure_ascii=False 保留中文字符，并手动编码为 UTF-8
        json_str = json.dumps(payload, ensure_ascii=False)
        r = requests.post(url,
                          params=params,
                          data=json_str.encode('utf-8'),
                          headers={'Content-Type': 'application/json; charset=utf-8'},
                          timeout=30)
        r.encoding = 'utf-8'  # 强制 UTF-8 解码响应
        data = r.json()
        if 'media_id' in data:
            print('✅ 草稿推送成功')
            print('   草稿ID: %s' % data["media_id"])
            print('   标题: %s' % title)
            print('   ⚠️  推送到草稿箱 ≠ 发布，需在公众号后台预览确认后发布')
            return data['media_id']
        print('❌ 推送失败: %s' % data)
        return None
    except Exception as e:
        print('❌ 网络错误: %s' % e)
        return None


def get_draft(draft_id):
    """读取草稿内容。成功返回 article，失败返回 None。"""
    requests = _requests()
    token = get_token()
    if not token:
        return None
    url = '%s/draft/get?access_token=%s' % (BASE_URL, token)

    payload = {'media_id': draft_id}
    try:
        r = requests.post(url,
                          data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                          headers={'Content-Type': 'application/json; charset=utf-8'},
                          timeout=10)
        r.encoding = 'utf-8'  # 强制 UTF-8 解码响应
        data = r.json()
        if 'article' in data:
            article = data['article'][0]
            print('✅ 草稿读取成功')
            print('   标题: %s' % article.get("title"))
            print('   作者: %s' % article.get("author"))
            print('   摘要: %s' % article.get("digest"))
            print('   内容长度: %d 字符' % len(article.get("content", "")))
            return article
        print('❌ 读取失败: %s' % data)
        return None
    except Exception as e:
        print('❌ 网络错误: %s' % e)
        return None


def update_draft(draft_id, title=None, content=None, digest=None):
    """更新草稿内容。成功返回 True，失败返回 False。"""
    requests = _requests()
    # 先读取现有草稿
    article = get_draft(draft_id)
    if not article:
        return False

    if title:
        article['title'] = title
    if content:
        article['content'] = content
    if digest:
        article['digest'] = digest

    token = get_token()
    if not token:
        return False
    url = '%s/draft/update?access_token=%s' % (BASE_URL, token)

    payload = {'media_id': draft_id, 'articles': [article]}

    try:
        r = requests.post(url,
                          data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                          headers={'Content-Type': 'application/json; charset=utf-8'},
                          timeout=30)
        r.encoding = 'utf-8'  # 强制 UTF-8 解码响应
        data = r.json()
        if data.get('errcode') == 0:
            print('✅ 草稿更新成功')
            print('   草稿ID: %s' % draft_id)
            return True
        print('❌ 更新失败: %s' % data)
        return False
    except Exception as e:
        print('❌ 网络错误: %s' % e)
        return False


def main():
    parser = gzh_cli.build_parser("gzh-api-push.py", "公众号 API 直推草稿箱")
    sub = parser.add_subparsers(dest='command', required=True)

    # token 命令
    sub.add_parser('token', help='获取 access_token')

    # upload 命令
    upload_parser = sub.add_parser('upload', help='上传封面图')
    upload_parser.add_argument('--file', required=True, help='图片文件路径')

    # push 命令
    push_parser = sub.add_parser('push', help='推送草稿')
    push_parser.add_argument('--file', required=True, help='HTML 内容文件')
    push_parser.add_argument('--title', required=True, help='文章标题')
    push_parser.add_argument('--thumb', required=True, help='封面图 media_id 或 URL')

    # get-draft 命令
    get_parser = sub.add_parser('get-draft', help='读取草稿')
    get_parser.add_argument('--id', required=True, help='草稿ID')

    # update 命令
    update_parser = sub.add_parser('update', help='更新草稿')
    update_parser.add_argument('--id', required=True, help='草稿ID')
    update_parser.add_argument('--title', help='新标题')
    update_parser.add_argument('--content', help='新内容（HTML）')
    update_parser.add_argument('--digest', help='新摘要')

    args = parser.parse_args()

    if not check_env():
        return 2

    if args.command == 'token':
        return 0 if get_token() else 1
    if args.command == 'upload':
        return 0 if upload_image(args.file) else 1
    if args.command == 'push':
        content = gzh_cli.read_text(args.file)
        return 0 if push_draft(content, args.title, args.thumb) else 1
    if args.command == 'get-draft':
        return 0 if get_draft(args.id) is not None else 1
    if args.command == 'update':
        return 0 if update_draft(args.id, args.title, args.content, args.digest) else 1
    return 2


if __name__ == '__main__':
    gzh_cli.run_main(main)
