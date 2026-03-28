"""
blog_engine_cli.py
The 4th Path 블로그 엔진 — OpenClaw 에이전트용 CLI 인터페이스

사용법:
  blog status              전체 시스템 상태 요약
  blog pipeline            파이프라인 단계별 상태
  blog content             콘텐츠 큐 현황
  blog review              검수 대기 목록
  blog approve <id>        콘텐츠 승인
  blog reject <id>         콘텐츠 반려
  blog sessions            수동(어시스트) 세션 목록
  blog session <id>        특정 세션 상세 (프롬프트 포함)
  blog assist <url>        새 수동 모드 세션 시작
  blog logs [n]            최근 로그 (기본 15줄)
  blog analytics           오늘 분석 데이터
"""
import sys
import json
import textwrap

from runtime_guard import ensure_project_runtime

ensure_project_runtime("blog CLI", ["requests"])

import requests

API = 'http://localhost:8080/api'
TIMEOUT = 10


def _get(path: str) -> dict | list:
    r = requests.get(f"{API}{path}", timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def _post(path: str, data: dict = None) -> dict:
    r = requests.post(f"{API}{path}", json=data or {}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def _put(path: str, data: dict = None) -> dict:
    r = requests.put(f"{API}{path}", json=data or {}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def _sep(char='─', width=60):
    print(char * width)


def cmd_status(_args):
    """전체 시스템 상태 요약"""
    try:
        ov  = _get('/overview')
        pip = _get('/pipeline')
    except Exception as e:
        print(f"[오류] 대시보드 연결 실패: {e}")
        print("  → 대시보드가 실행 중인지 확인하세요: python -m uvicorn dashboard.backend.server:app --port 8080")
        return

    kpi = ov.get('kpi', {})
    _sep('═')
    print("  The 4th Path 블로그 엔진 — 상태")
    _sep('═')
    print(f"  오늘 발행:   {kpi.get('today', 0)}편")
    print(f"  이번 주:     {kpi.get('this_week', 0)}편")
    print(f"  총 누적:     {kpi.get('total', 0)}편")
    rev = kpi.get('revenue', {})
    print(f"  수익 상태:   {rev.get('status', '-')}")
    _sep()
    print("  파이프라인:")
    status_icon = {'done': '✅', 'running': '🔄', 'waiting': '⏳', 'error': '❌'}
    for step in pip.get('steps', []):
        icon = status_icon.get(step.get('status', ''), '○')
        print(f"    {icon} {step.get('label', step.get('id', ''))} — {step.get('last_run', '-')}")
    _sep()

    # 수동모드 세션 요약
    try:
        sessions = _get('/assist/sessions')
        awaiting = [s for s in sessions if s.get('status') == 'awaiting']
        if awaiting:
            print(f"  ⏳ 수동모드 에셋 대기 중: {len(awaiting)}개 세션")
            for s in awaiting[:3]:
                print(f"     - {s['session_id']} : {s.get('title', s.get('url',''))[:40]}")
            _sep()
    except Exception:
        pass


def cmd_pipeline(_args):
    """파이프라인 단계별 상태"""
    pip = _get('/pipeline')
    status_icon = {'done': '✅', 'running': '🔄', 'waiting': '⏳', 'error': '❌'}
    _sep()
    print("  파이프라인 상태")
    _sep()
    for step in pip.get('steps', []):
        icon = status_icon.get(step.get('status', ''), '○')
        print(f"  {icon} {step.get('label', step.get('id', ''))}")
        if step.get('last_run'):
            print(f"       마지막 실행: {step['last_run']}")
        if step.get('error'):
            print(f"       오류: {step['error']}")
    _sep()


def cmd_content(_args):
    """콘텐츠 큐 현황"""
    data = _get('/content')
    _sep()
    print("  콘텐츠 큐 현황")
    _sep()
    cols = [
        ('queue',   '📥 글감 큐'),
        ('writing', '✍️  작성 중'),
        ('review',  '🔍 검수 대기'),
        ('published','📤 발행 완료'),
    ]
    for key, label in cols:
        items = data.get(key, [])
        print(f"  {label}: {len(items)}개")
        for item in items[:3]:
            score = item.get('quality_score', item.get('score', ''))
            score_str = f" [점수:{score}]" if score else ''
            print(f"    - {item.get('title', '제목 없음')[:45]}{score_str}")
        if len(items) > 3:
            print(f"    ... 외 {len(items)-3}개")
    _sep()


def cmd_review(_args):
    """검수 대기 목록 상세"""
    data = _get('/content')
    items = data.get('review', [])
    if not items:
        print("  검수 대기 콘텐츠가 없습니다.")
        return
    _sep()
    print(f"  검수 대기 — {len(items)}개")
    _sep()
    for item in items:
        print(f"  ID: {item.get('id', '-')}")
        print(f"  제목: {item.get('title', '-')}")
        print(f"  코너: {item.get('corner', '-')}  점수: {item.get('quality_score', '-')}")
        if item.get('summary'):
            wrapped = textwrap.fill(item['summary'][:200], width=55, initial_indent='  ', subsequent_indent='  ')
            print(f"  요약:\n{wrapped}")
        print(f"  → 승인: blog approve {item.get('id')}  |  반려: blog reject {item.get('id')}")
        _sep('-')


def cmd_approve(args):
    """콘텐츠 승인"""
    if not args:
        print("사용법: blog approve <id>")
        return
    cid = args[0]
    result = _post(f'/content/{cid}/approve')
    if result.get('ok') or result.get('status') == 'approved':
        print(f"✅ 승인 완료: {cid}")
    else:
        print(f"오류: {result}")


def cmd_reject(args):
    """콘텐츠 반려"""
    if not args:
        print("사용법: blog reject <id>")
        return
    cid = args[0]
    result = _post(f'/content/{cid}/reject')
    if result.get('ok') or result.get('status') == 'rejected':
        print(f"🚫 반려 완료: {cid}")
    else:
        print(f"오류: {result}")


def cmd_sessions(_args):
    """수동(어시스트) 세션 목록"""
    sessions = _get('/assist/sessions')
    if not sessions:
        print("  수동 모드 세션이 없습니다.")
        return
    status_icon = {
        'pending': '⏳', 'fetching': '🔄', 'generating': '🔄',
        'awaiting': '📤', 'assembling': '🔄', 'ready': '✅', 'error': '❌'
    }
    _sep()
    print(f"  수동(어시스트) 세션 목록 — {len(sessions)}개")
    _sep()
    for s in sessions:
        icon = status_icon.get(s['status'], '○')
        title = s.get('title') or s.get('url', '')
        assets = len(s.get('assets', []))
        print(f"  {icon} {s['session_id']}")
        print(f"     제목: {title[:50]}")
        print(f"     상태: {s.get('status_label', s['status'])}  에셋: {assets}개")
        if s['status'] == 'awaiting':
            print(f"     → 상세 프롬프트: blog session {s['session_id']}")
        _sep('-', 40)


def cmd_session(args):
    """특정 세션 상세 정보 및 프롬프트"""
    if not args:
        print("사용법: blog session <session_id>")
        return
    sid = args[0]
    s = _get(f'/assist/session/{sid}')
    _sep()
    print(f"  세션: {sid}")
    print(f"  제목: {s.get('title', '-')}")
    print(f"  URL:  {s.get('url', '-')}")
    print(f"  상태: {s.get('status_label', s.get('status', '-'))}")
    _sep()

    prompts = s.get('prompts', {})

    imgs = prompts.get('image_prompts', [])
    if imgs:
        print("  📸 이미지 프롬프트:")
        for p in imgs:
            print(f"  [{p.get('purpose','')}]")
            print(f"    KO: {p.get('ko','')}")
            print(f"    EN: {p.get('en','')}")
        _sep('-', 40)

    vid = prompts.get('video_prompt', {})
    if vid:
        print("  🎬 영상 프롬프트 (Sora/Runway):")
        print(f"    KO: {vid.get('ko','')}")
        print(f"    EN: {vid.get('en','')}")
        _sep('-', 40)

    narr = prompts.get('narration_script', '')
    if narr:
        print("  🎙 나레이션 스크립트:")
        for line in textwrap.wrap(narr, 55):
            print(f"    {line}")
        _sep('-', 40)

    assets = s.get('assets', [])
    if assets:
        print(f"  📁 등록된 에셋 ({len(assets)}개):")
        for a in assets:
            print(f"    [{a['type']}] {a['filename']}")
    else:
        print("  ⏳ 에셋 없음 — 이미지/영상 생성 후 대시보드에서 업로드하세요")
    _sep()


def cmd_assist(args):
    """새 수동 모드 세션 시작"""
    if not args:
        print("사용법: blog assist <url>")
        return
    url = args[0]
    result = _post('/assist/session', {'url': url})
    sid = result.get('session_id', '')
    print(f"✅ 세션 생성: {sid}")
    print(f"   URL: {url}")
    print(f"   상태: {result.get('status_label', result.get('status', '-'))}")
    print(f"   프롬프트 생성 중... 잠시 후 'blog session {sid}' 로 확인하세요.")


def cmd_logs(args):
    """최근 로그"""
    limit = int(args[0]) if args else 15
    data = _get(f'/logs?limit={limit}')
    logs = data if isinstance(data, list) else data.get('logs', [])
    level_icon = {'ERROR': '❌', 'WARNING': '⚠️', 'INFO': '•', 'DEBUG': '·'}
    _sep()
    print(f"  최근 로그 (최대 {limit}줄)")
    _sep()
    for log in logs[-limit:]:
        lvl = log.get('level', 'INFO')
        icon = level_icon.get(lvl, '•')
        ts  = log.get('time', log.get('timestamp', ''))[:16]
        mod = log.get('module', '')
        msg = log.get('message', '')
        print(f"  {icon} [{ts}] {mod}: {msg[:70]}")
    _sep()


def cmd_analytics(_args):
    """오늘 분석 데이터"""
    data = _get('/analytics')
    _sep()
    print("  분석 데이터")
    _sep()
    print(f"  방문자:    {data.get('visitors', 0):,}")
    print(f"  페이지뷰:  {data.get('pageviews', 0):,}")
    print(f"  평균 체류: {data.get('avg_duration', '-')}")
    print(f"  CTR:       {data.get('ctr', '-')}")

    top = data.get('top_posts', [])
    if top:
        _sep('-', 40)
        print("  🏆 인기 글 TOP 5:")
        for i, post in enumerate(top[:5], 1):
            print(f"  {i}. {post.get('title','')[:45]} ({post.get('views',0)}뷰)")
    _sep()


COMMANDS = {
    'status':    cmd_status,
    'pipeline':  cmd_pipeline,
    'content':   cmd_content,
    'review':    cmd_review,
    'approve':   cmd_approve,
    'reject':    cmd_reject,
    'sessions':  cmd_sessions,
    'session':   cmd_session,
    'assist':    cmd_assist,
    'logs':      cmd_logs,
    'analytics': cmd_analytics,
}

HELP = """
blog <command> [args]

  status              전체 시스템 상태 요약
  pipeline            파이프라인 단계별 상태
  content             콘텐츠 큐 현황 (큐/작성중/검수/발행)
  review              검수 대기 목록 상세
  approve <id>        콘텐츠 승인
  reject <id>         콘텐츠 반려
  sessions            수동(어시스트) 세션 목록
  session <id>        특정 세션 프롬프트/에셋 확인
  assist <url>        새 수동 모드 세션 시작 (URL 입력)
  logs [n]            최근 로그 (기본 15줄)
  analytics           분석 데이터
"""


def main():
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help', 'help'):
        print(HELP)
        return

    cmd = args[0].lower()
    rest = args[1:]

    if cmd not in COMMANDS:
        print(f"알 수 없는 명령: {cmd}")
        print(HELP)
        sys.exit(1)

    try:
        COMMANDS[cmd](rest)
    except requests.exceptions.ConnectionError:
        print("[오류] 대시보드에 연결할 수 없습니다.")
        print("  → 대시보드를 먼저 시작하세요:")
        print("    cd D:\\workspace\\blog-writer")
        print("    python -m uvicorn dashboard.backend.server:app --port 8080")
    except Exception as e:
        print(f"[오류] {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
