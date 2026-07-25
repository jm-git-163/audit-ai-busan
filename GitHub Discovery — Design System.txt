GitHub Discovery — Design System
이 문서는 GitHub Discovery 앱에 실제로 적용된 비주얼 디자인 규칙을 코드에서 역추출해 정리한 것입니다. 다른 프로젝트에 이 스타일을 그대로 이식할 때 참고용으로 쓰세요. (기존 README가 언급했던 DESIGN.md가 실제로는 저장소에 커밋된 적이 없어서, 이번에 구현된 코드를 기준으로 새로 작성했습니다.)

한 줄 요약: 어두운 배경 + 인디고/시안 네온 포인트 + 반투명 유리 카드 + Material Design 3 색 체계 + Geist/Inter/JetBrains Mono 서체 조합으로 만든 "AI SaaS 대시보드" 톤의 다크 UI.

1. 설치 스니펫 (다른 프로젝트에 그대로 붙이기)
1-1. 의존성
npm install tailwindcss @tailwindcss/vite
1-2. vite.config.ts
import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [tailwindcss()],
})
1-3. index.html — 폰트 & 아이콘 로드
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
  href="https://fonts.googleapis.com/css2?family=Geist:wght@400;600;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0&display=swap"
  rel="stylesheet"
/>
참고: Claude 아티팩트처럼 외부 폰트 CDN 요청이 CSP로 막히는 환경에서는 이 방식이 조용히 실패(fallback)하니, 그런 환경에선 폰트를 base64 @font-face로 내장하거나 시스템 폰트 스택으로 대체해야 합니다. 일반 웹앱(Vite/Next 등)에서는 문제없습니다.

1-4. src/index.css — 디자인 토큰 전체
@import 'tailwindcss';

@theme {
  /* Material Design 3 색상 역할 (surface/on-surface/primary-container 패턴) */
  --color-surface: #0b1326;
  --color-surface-dim: #0b1326;
  --color-surface-bright: #31394d;
  --color-surface-container-lowest: #060e20;
  --color-surface-container-low: #131b2e;
  --color-surface-container: #171f33;
  --color-surface-container-high: #222a3d;
  --color-surface-container-highest: #2d3449;
  --color-on-surface: #dae2fd;
  --color-on-surface-variant: #c7c4d7;
  --color-inverse-surface: #dae2fd;
  --color-inverse-on-surface: #283044;
  --color-outline: #908fa0;
  --color-outline-variant: #464554;
  --color-surface-tint: #c0c1ff;
  --color-primary: #c0c1ff;
  --color-on-primary: #1000a9;
  --color-primary-container: #8083ff;
  --color-on-primary-container: #0d0096;
  --color-inverse-primary: #494bd6;
  --color-secondary: #4cd7f6;
  --color-on-secondary: #003640;
  --color-secondary-container: #03b5d3;
  --color-on-secondary-container: #00424e;
  --color-tertiary: #4edea3;
  --color-on-tertiary: #003824;
  --color-tertiary-container: #00885d;
  --color-on-tertiary-container: #000703;
  --color-error: #ffb4ab;
  --color-on-error: #690005;
  --color-error-container: #93000a;
  --color-on-error-container: #ffdad6;
  --color-background: #0b1326;
  --color-on-background: #dae2fd;
  --color-surface-variant: #2d3449;

  /* 강조색은 M3 팔레트와 별개로 Tailwind 기본 색을 그대로 사용 */
  --color-slate-900: #0f172a;
  --color-slate-800: #1e293b;
  --color-slate-700: #334155;
  --color-slate-400: #94a3b8;
  --color-indigo-500: #6366f1;
  --color-indigo-600: #4f46e5;
  --color-cyan-500: #06b6d4;
  --color-emerald-500: #10b981;
  --color-rose-500: #f43f5e;

  /* 폰트 역할 */
  --font-display: 'Geist', sans-serif;
  --font-headline: 'Geist', sans-serif;
  --font-body: 'Inter', sans-serif;
  --font-code: 'JetBrains Mono', monospace;
  --font-button: 'Geist', sans-serif;

  /* 타이포 스케일 */
  --text-display-lg: 48px;
  --text-display-lg--line-height: 56px;
  --text-display-lg--letter-spacing: -0.02em;
  --text-display-lg--font-weight: 700;

  --text-headline-lg: 32px;
  --text-headline-lg--line-height: 40px;
  --text-headline-lg--letter-spacing: -0.01em;
  --text-headline-lg--font-weight: 600;

  --text-headline-md: 24px;
  --text-headline-md--line-height: 32px;
  --text-headline-md--font-weight: 600;

  --text-headline-sm: 18px;
  --text-headline-sm--line-height: 24px;
  --text-headline-sm--font-weight: 600;

  --text-body-lg: 18px;
  --text-body-lg--line-height: 28px;
  --text-body-lg--font-weight: 400;

  --text-body-md: 16px;
  --text-body-md--line-height: 24px;
  --text-body-md--font-weight: 400;

  --text-body-sm: 14px;
  --text-body-sm--line-height: 20px;
  --text-body-sm--font-weight: 400;

  --text-code-label: 13px;
  --text-code-label--line-height: 16px;
  --text-code-label--font-weight: 500;

  --text-button: 14px;
  --text-button--line-height: 20px;
  --text-button--font-weight: 600;

  /* 간격 스케일 (px-lg, gap-md 등에서 사용) */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
  --spacing-2xl: 3rem;
  --spacing-gutter: 1.5rem;
  --spacing-container-max: 1280px;

  --max-width-md: 28rem;
  --max-width-lg: 32rem;
  --max-width-2xl: 42rem;

  /* 둥근 정도 */
  --radius-sm: 0.25rem;
  --radius-DEFAULT: 0.5rem;
  --radius-md: 0.75rem;
  --radius-lg: 1rem;
  --radius-xl: 1.5rem;
  --radius-2xl: 1.5rem;
  --radius-3xl: 1.5rem;
  --radius-full: 9999px;
}

@layer base {
  html {
    color-scheme: dark;
  }
  body {
    margin: 0;
    min-height: 100vh;
    background-color: var(--color-background);
    color: var(--color-on-background);
    font-family: var(--font-body);
    -webkit-font-smoothing: antialiased;
    overflow-x: hidden;
  }
}

@layer utilities {
  .font-display { font-family: var(--font-display); }
  .font-headline { font-family: var(--font-headline); }
  .font-body { font-family: var(--font-body); }
  .font-code { font-family: var(--font-code); }
  .font-button { font-family: var(--font-button); }

  /* 반투명 "유리판" 카드 */
  .glass-card {
    background: rgba(30, 41, 59, 0.7);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(70, 69, 84, 0.5);
  }

  /* 카드 위쪽에 은은한 인디고 네온 라인 + 그림자 */
  .ai-glow {
    border-top: 0.5px solid rgba(99, 102, 241, 0.5);
    box-shadow: 0 0 20px rgba(99, 102, 241, 0.15);
  }

  .material-symbols-outlined {
    font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
    user-select: none;
  }
  .material-filled {
    font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24;
  }

  @keyframes float {
    0%, 100% { transform: translateY(0); }
    50%      { transform: translateY(-10px); }
  }
  .animate-float {
    animation: float 4s ease-in-out infinite;
  }
}
2. 색 — 역할별로 골라 쓰는 법
M3 규칙대로 배경(surface)과 그 위에 놓일 글자색(on-surface)이 항상 짝을 이룹니다. 새 화면을 만들 때 아래 순서로 고르면 됩니다.

역할	토큰	값	언제 쓰나
페이지 배경	background / surface	#0b1326	<body>, 전체 배경
카드/패널 배경	surface-container-high	#222a3d	불투명 카드가 필요할 때
기본 글자색	on-surface	#dae2fd	제목, 본문
보조 글자색	on-surface-variant	#c7c4d7	캡션, 설명, 메타 정보
브랜드 강조	primary	#c0c1ff (버튼은 indigo-500 #6366f1)	로고, 주요 CTA, 링크
보조 강조	secondary / cyan-500	#06b6d4	두 번째 포인트, 트렌드/성장 표시
성공/성장	tertiary / emerald-500	#10b981	긍정 지표, 상승 추세
위험/누락	error / rose-500	#f43f5e	에러, "Missing Gap" 같은 경고
테두리	outline-variant / slate-800	#464554 / #1e293b	카드 테두리, 구분선
의미 색(성공=에메랄드, 경고=로즈)은 브랜드 강조색(인디고/시안)과 분리해서 씁니다. 브랜드색을 상태 표시에 재활용하지 마세요.

3. 타이포그래피
역할	서체	크기/굵기 예시	쓰는 곳
Display / Headline	Geist	48px/700 ~ 18px/600	히어로 문구, 섹션 제목, 카드 제목
Body	Inter	16px/400	문단, 설명, 카드 본문
Code / Label	JetBrains Mono	13px/500, 대문자 + tracking-wider	뱃지, 태그, 통계 라벨, 타임스탬프
Button	Geist	14px/600	모든 버튼 텍스트
규칙: 제목=Geist, 본문=Inter, 태그·숫자·코드=JetBrains Mono 이 3분할만 지키면 어떤 화면에서도 톤이 일관됩니다.

4. 표면 효과 (Elevation)
4-1. 유리 카드 (.glass-card)
<div class="glass-card rounded-2xl border border-slate-800 p-lg">
  ...
</div>
반투명 배경(rgba(30,41,59,0.7)) + backdrop-filter: blur(12px) + 얇은 테두리. 뒤 배경이 살짝 비쳐서 "유리판이 떠 있는" 느낌을 줍니다.

4-2. AI 네온 강조 (.ai-glow)
<div class="glass-card ai-glow rounded-2xl p-xl">
  ...
</div>
카드 위쪽에만 인디고색 얇은 라인을 긋고, 은은한 인디고 그림자를 깔아 "AI가 이 카드를 강조하고 있다"는 느낌을 줍니다. 대시보드의 핵심 카드에만 선택적으로 사용 (남용하면 효과가 사라짐).

4-3. 카드 등급
강조 카드: glass-card ai-glow (Developer DNA, 핵심 지표)
일반 카드: glass-card border border-slate-800
불투명 패널: bg-slate-900 border border-slate-800 (히어로, 큰 배너)
5. 모션
이름	코드	용도
animate-float	@keyframes float (0%/100% translateY(0), 50% translateY(-10px), 4s ease-in-out infinite)	랜딩 페이지의 강조 배지 등 작은 요소를 둥실거리게
hover lift	transition-all hover:-translate-y-0.5 hover:shadow-[0_0_20px_rgba(99,102,241,0.15)]	추천 카드, 클릭 가능한 카드의 hover
pulse dot	h-2 w-2 animate-pulse rounded-full bg-emerald-500	"LIVE" 상태 표시 점
모션은 위 세 가지 정도로 제한하고, 화면 전체에 애니메이션을 남발하지 않습니다. prefers-reduced-motion을 존중해 다른 프로젝트에 이식할 땐 @media (prefers-reduced-motion: reduce)로 끄는 처리를 추가하는 걸 권장합니다.

6. 아이콘
Google Material Symbols Outlined 폰트를 그대로 사용합니다. 새 아이콘이 필요하면 Material Symbols 목록에서 이름만 찾아 쓰면 됩니다.

<span class="material-symbols-outlined text-indigo-500">psychology</span>
<!-- 활성 상태엔 채워진 버전 -->
<span class="material-symbols-outlined material-filled">dashboard</span>
7. 컴포넌트 레시피
7-1. 버튼
<!-- Primary -->
<button class="rounded-lg bg-indigo-500 px-md py-sm font-button text-button text-white transition-all hover:bg-indigo-600 hover:shadow-[0_0_15px_rgba(99,102,241,0.4)]">
  Sign in with GitHub
</button>

<!-- Secondary (outline) -->
<button class="rounded-lg border border-slate-700 bg-slate-800 px-md py-sm font-button text-button text-on-surface hover:bg-slate-700">
  Cancel
</button>
7-2. 뱃지 / 칩
<!-- 상태 뱃지: 색/10 배경 + 색-500 텍스트 + 색/20 테두리 -->
<span class="rounded-full border border-indigo-500/20 bg-indigo-500/10 px-3 py-1 font-code text-[12px] uppercase text-indigo-500">
  AI-Driven Curation
</span>

<!-- 토픽 태그 -->
<span class="rounded bg-slate-700/50 px-2 py-0.5 font-code text-[11px] text-slate-400">
  TypeScript
</span>
7-3. 진행률 바
<div class="h-2 flex-1 overflow-hidden rounded-full bg-slate-800">
  <div class="h-full bg-gradient-to-r from-indigo-500 to-cyan-500" style="width: 72%"></div>
</div>
7-4. 테이블
<table class="w-full text-left">
  <thead class="bg-slate-800/50">
    <tr>
      <th class="px-lg py-4 font-code text-code-label uppercase tracking-wider text-slate-400">
        Technology
      </th>
    </tr>
  </thead>
  <tbody class="divide-y divide-slate-800">
    <tr class="transition-colors hover:bg-slate-800/30">
      <td class="px-lg py-5">...</td>
    </tr>
  </tbody>
</table>
7-5. 타임라인 (Activity Stream)
<div class="relative pl-10">
  <div class="absolute top-2 bottom-0 left-[11px] w-px bg-slate-800"></div>
  <div class="absolute top-1 left-0 z-10 flex h-6 w-6 items-center justify-center rounded-full border-2 border-indigo-500 bg-slate-900 shadow-[0_0_10px_rgba(99,102,241,0.4)]">
    <span class="material-symbols-outlined text-[14px] text-indigo-500">add</span>
  </div>
  <p class="mb-1 font-code text-code-label text-slate-400">Today, 10:24 AM</p>
  <h5 class="font-headline text-headline-sm">Created repo</h5>
</div>
7-6. 검색 입력
<div class="relative flex-1">
  <span class="material-symbols-outlined absolute top-1/2 left-4 -translate-y-1/2 text-on-surface-variant">search</span>
  <input class="w-full rounded-xl border border-slate-700 bg-slate-800/50 py-3 pr-4 pl-12 outline-none backdrop-blur-sm transition-all focus:border-indigo-500" />
</div>
7-7. 내비게이션
TopNav: fixed top-0 h-16 w-full border-b border-surface-variant bg-slate-900/80 backdrop-blur-md — 로고 + (선택) 검색창 + 페이지 링크 + 우측 로그인/아바타
SideNav (데스크톱 전용, md:flex): fixed left-0 top-0 h-[calc(100%-4rem)] w-[280px] border-r border-slate-800 bg-slate-900, 활성 링크는 bg-secondary-container text-on-secondary-container
MobileBottomNav (md:hidden): fixed bottom-0 h-16 w-full border-t border-slate-800 bg-slate-900, 활성 아이콘은 material-filled + text-primary + 굵게
8. 레이아웃 규칙
콘텐츠 최대 너비: max-w-container-max (1280px), 좌우 패딩 px-lg
그리드는 12컬럼 기준 (lg:grid-cols-12), 카드 사이 간격은 gap-gutter(1.5rem)
앱 내부 페이지는 AppShell이 TopNav + SideNav + MobileBottomNav를 공통으로 두르고, 본문은 md:ml-[280px]로 사이드바만큼 밀어서 배치
반응형 분기점은 Tailwind 기본값 그대로 (md, lg, xl) 사용, 커스텀 breakpoint 없음
9. 다른 앱에 이식할 때 체크리스트
src/index.css의 @theme 블록을 그대로 복사 (색/폰트/간격/라운딩 토큰)
index.html에 Google Fonts 링크(Geist, Inter, JetBrains Mono, Material Symbols Outlined) 추가
.glass-card, .ai-glow, .animate-float 유틸리티 클래스 그대로 이식
새 화면을 만들 땐 위 "컴포넌트 레시피"에서 가장 가까운 걸 골라 복사 후 내용만 교체 — 색/굵기/라운딩 값을 새로 만들지 말 것
브랜드 강조색(인디고/시안)과 의미 색(에메랄드=성공, 로즈=경고)을 섞지 않기
모션은 animate-float / hover-lift / pulse dot 세 가지 이내로 제한