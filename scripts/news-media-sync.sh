#!/usr/bin/env bash
# 老官网(www.xiongdaye.com)新闻媒体 → 腾讯云 COS 迁移
# 用法: ./news-media-sync.sh <下载目录>
# 之后把 <下载目录>/xdy/news/ 整体上传到 COS 的 xdy/news/ 前缀（coscmd upload -r 或现有上传方式）
set -euo pipefail
DEST="${1:-/tmp/news-media}"
MANIFEST="$(dirname "$0")/news-media-manifest.json"
python3 - "$MANIFEST" "$DEST" <<'PY'
import json, sys, os, urllib.request, ssl
ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
man = json.load(open(sys.argv[1])); dest = sys.argv[2]
ok = fail = 0
for m in man:
    out = os.path.join(dest, m['cos'])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.path.exists(out) and os.path.getsize(out) > 0:
        ok += 1; continue
    try:
        req = urllib.request.Request(m['src'], headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=60) as r, open(out,'wb') as f:
            f.write(r.read())
        ok += 1
    except Exception as e:
        print('FAIL', m['src'], e); fail += 1
print(f'done: {ok} ok, {fail} failed -> {dest}')
PY
