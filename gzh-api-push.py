#!/usr/bin/env python3
"""公众号 API 直推草稿箱工具
用法：
  python3 gzh-api-push.py token
  python3 gzh-api-push.py upload --file cover.jpg
  python3 gzh-api-push.py push --file content.html --title "标题" --thumb media_id
  python3 gzh-api-push.py get-draft --id 草稿ID
  python3 gzh-api-push.py update --id 草稿ID --title "新标题"
"""
import sys, os, json, base64, mimetypes, argparse, requests

WX_APPID = os.environ.get('WX_APPID')
WX_APPSECRET = os.environ.get('WX_APPSECRET')
BASE_URL = 'https://api.weixin.qq.com/cgi-bin'

def check_env():
    if not WX_APPID or not WX_APPSECRET:
        print('❌ 缺少环境变量 WX_APPID 或 WX_APPSECRET')
        print('   获取方式：公众号后台「设置与开发 → 基本配置」')
        sys.exit(1)

def get_token():
    """获取 access_token"""
    url = f'{BASE_URL}/token'
    params = {'grant_type': 'client_credential', 'appid': WX_APPID, 'secret': WX_APPSECRET}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.encoding = 'utf-8'  # 强制 UTF-8 编码
        data = r.json()
        if 'access_token' in data:
            print(f'✅ access_token: {data["access_token"][:20]}...')
            print(f'   有效期: {data.get("expires_in", 7200)}秒')
            return data['access_token']
        elif data.get('errcode') == 40164:
            print('❌ 错误 40164: IP 不在白名单')
            print('   处理：公众号后台「基本配置 → IP 白名单」添加当前服务器 IP')
        elif data.get('errcode') == 48001:
            print('❌ 错误 48001: 公众号未认证')
            print('   处理：个人订阅号不行，需先完成认证')
        elif data.get('errcode') == 40001:
            print(f'❌ 错误 40001: AppSecret 无效 ({data.get("errmsg")})')
        else:
            print(f'❌ 获取 token 失败: {data}')
        sys.exit(1)
    except Exception as e:
        print(f'❌ 网络错误: {e}')
        sys.exit(1)

def upload_image(file_path):
    """上传封面图，返回 media_id"""
    token = get_token()
    if not os.path.exists(file_path):
        print(f'❌ 文件不存在: {file_path}')
        sys.exit(1)
    
    # 检测图片类型
    mime = mimetypes.guess_type(file_path)[0] or 'image/jpeg'
    
    # 封面图使用永久素材接口（type=thumb）
    url = f'{BASE_URL}/material/add_material'
    params = {'access_token': token, 'type': 'thumb'}
    with open(file_path, 'rb') as f:
        files = {'media': (os.path.basename(file_path), f, mime)}
        r = requests.post(url, params=params, files=files, timeout=30)
        data = r.json()
    
    if 'media_id' in data:
        print(f'✅ 上传成功')
        print(f'   MediaID: {data["media_id"]}')
        print(f'   URL: {data.get("url", "N/A")}')
        return data['media_id']
    else:
        print(f'❌ 上传失败: {data}')
        sys.exit(1)

def push_draft(content_html, title, thumb_media_id):
    """推送草稿到公众号"""
    token = get_token()
    url = f'{BASE_URL}/draft/add'
    params = {'access_token': token}
    
    article = {
        'title': title,
        'author': '',
        'digest': '两办首推人工智能+，从概念变为国家战略基建',
        'content': content_html,
        'content_source_url': '',
        'thumb_media_id': thumb_media_id,
        'need_open_comment': 0,
        'only_fans_can_comment': 0
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
            print(f'✅ 草稿推送成功')
            print(f'   草稿ID: {data["media_id"]}')
            print(f'   标题: {title}')
            print(f'   ⚠️  推送到草稿箱 ≠ 发布，需在公众号后台预览确认后发布')
            return data['media_id']
        else:
            print(f'❌ 推送失败: {data}')
            sys.exit(1)
    except Exception as e:
        print(f'❌ 网络错误: {e}')
        sys.exit(1)

def get_draft(draft_id):
    """读取草稿内容"""
    token = get_token()
    url = f'{BASE_URL}/draft/get?access_token={token}'
    
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
            print(f'✅ 草稿读取成功')
            print(f'   标题: {article.get("title")}')
            print(f'   作者: {article.get("author")}')
            print(f'   摘要: {article.get("digest")}')
            print(f'   内容长度: {len(article.get("content", ""))} 字符')
            return article
        else:
            print(f'❌ 读取失败: {data}')
            sys.exit(1)
    except Exception as e:
        print(f'❌ 网络错误: {e}')
        sys.exit(1)

def update_draft(draft_id, title=None, content=None, digest=None):
    """更新草稿内容"""
    # 先读取现有草稿
    article = get_draft(draft_id)
    
    if title:
        article['title'] = title
    if content:
        article['content'] = content
    if digest:
        article['digest'] = digest
    
    token = get_token()
    url = f'{BASE_URL}/draft/update?access_token={token}'
    
    payload = {'media_id': draft_id, 'articles': [article]}
    
    try:
        r = requests.post(url, 
                         data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                         headers={'Content-Type': 'application/json; charset=utf-8'},
                         timeout=30)
        r.encoding = 'utf-8'  # 强制 UTF-8 解码响应
        data = r.json()
        if data.get('errcode') == 0:
            print(f'✅ 草稿更新成功')
            print(f'   草稿ID: {draft_id}')
        else:
            print(f'❌ 更新失败: {data}')
            sys.exit(1)
    except Exception as e:
        print(f'❌ 网络错误: {e}')
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='公众号 API 直推草稿箱')
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # token 命令
    subparsers.add_parser('token', help='获取 access_token')
    
    # upload 命令
    upload_parser = subparsers.add_parser('upload', help='上传封面图')
    upload_parser.add_argument('--file', required=True, help='图片文件路径')
    
    # push 命令
    push_parser = subparsers.add_parser('push', help='推送草稿')
    push_parser.add_argument('--file', required=True, help='HTML 内容文件')
    push_parser.add_argument('--title', required=True, help='文章标题')
    push_parser.add_argument('--thumb', required=True, help='封面图 media_id 或 URL')
    
    # get-draft 命令
    get_parser = subparsers.add_parser('get-draft', help='读取草稿')
    get_parser.add_argument('--id', required=True, help='草稿ID')
    
    # update 命令
    update_parser = subparsers.add_parser('update', help='更新草稿')
    update_parser.add_argument('--id', required=True, help='草稿ID')
    update_parser.add_argument('--title', help='新标题')
    update_parser.add_argument('--content', help='新内容（HTML）')
    update_parser.add_argument('--digest', help='新摘要')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    check_env()
    
    if args.command == 'token':
        get_token()
    elif args.command == 'upload':
        upload_image(args.file)
    elif args.command == 'push':
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
        push_draft(content, args.title, args.thumb)
    elif args.command == 'get-draft':
        get_draft(args.id)
    elif args.command == 'update':
        update_draft(args.id, args.title, args.content, args.digest)

if __name__ == '__main__':
    main()