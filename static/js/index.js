document.addEventListener('DOMContentLoaded', function() {
    initializeMainPage();       // 기본 초기화 및 bfcache 처리
    setupLoginModal();          // 로그인 모달 이벤트 연결 (NEW)
    setupWelcomeModal();        // 환영 모달 이벤트 연결 (NEW)
    setupGlobalInteractions();  // 터치 및 키보드 공통 동작
});

// ==========================================
// 1. 초기화 및 페이지 복원(bfcache) 처리
// ==========================================
function initializeMainPage() {
    console.log('쉽길 메인페이지가 로드되었습니다.');

    // 뒤로가기로 돌아왔을 때, 로딩 상태가 남아있는 문제 해결
    window.addEventListener('pageshow', function(event) {
        if (event.persisted) {
            const mainButtons = document.querySelectorAll('.main-btn');
            mainButtons.forEach(btn => {
                btn.classList.remove('loading');
                btn.disabled = false;
            });
        }
    });
}

// ==========================================
// 2. 로그인 모달 관련 로직 (onclick 제거 버전)
// ==========================================
function setupLoginModal() {
    const loginModal = document.getElementById('loginModal');
    const openBtn = document.getElementById('openLoginBtn'); // HTML id="openLoginBtn" 필요
    const closeBtn = document.getElementById('closeLoginBtn'); // HTML id="closeLoginBtn" 필요
    const googleBtn = document.getElementById('googleLoginBtn'); // HTML id="googleLoginBtn" 필요

    // 1) 로그인 버튼 클릭 시 모달 열기
    if (openBtn) {
        openBtn.addEventListener('click', () => {
            if (loginModal) {
                loginModal.style.display = 'flex';
            }
        });
    }

    // 2) 닫기 버튼 클릭 시 모달 닫기
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            if (loginModal) loginModal.style.display = 'none';
        });
    }

    // 3) 구글 로그인 버튼 처리
    if (googleBtn) {
        googleBtn.addEventListener('click', () => {
            const urlSpan = document.getElementById('googleLoginUrl');
            if (urlSpan && urlSpan.dataset.url) {
                window.location.href = urlSpan.dataset.url;
            } else {
                console.error('Google login URL not found');
            }
        });
    }

    // 4) 모달 바깥 영역 클릭 시 닫기
    window.addEventListener('click', (e) => {
        if (e.target === loginModal) {
            loginModal.style.display = 'none';
        }
    });
}

// ==========================================
// 3. 환영 모달 관련 로직
// ==========================================
function setupWelcomeModal() {
    const welcomeModal = document.getElementById('welcome-modal');
    const closeBtn = document.getElementById('closeWelcomeBtn');

    if (welcomeModal) {
        // sessionStorage를 확인하여 최초 1회만 표시
        const hasSeen = sessionStorage.getItem('hasSeenWelcome');

        if (!hasSeen) {
            // 처음 본 경우에만 표시
            welcomeModal.classList.add('show');
            
            // "봤음" 표시 저장 (브라우저 닫을 때까지 유지)
            sessionStorage.setItem('hasSeenWelcome', 'true');
        }
        
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                welcomeModal.classList.remove('show');
            });
        }
    }
}

// ==========================================
// 4. 공통 인터랙션 (키보드, 터치)
// ==========================================
function setupGlobalInteractions() {
    // [키보드] Enter로 버튼 클릭 / Escape로 모달 닫기
    document.addEventListener('keydown', function(e) {
        // Enter key on buttons
        if (e.key === 'Enter' && e.target.classList.contains('main-btn')) {
            e.target.click();
        }

        // Escape key: 모달 닫기
        if (e.key === 'Escape') {
            const loginModal = document.getElementById('loginModal');
            const welcomeModal = document.getElementById('welcome-modal');
            
            if (loginModal && loginModal.style.display === 'block') {
                loginModal.style.display = 'none';
            }
            if (welcomeModal && welcomeModal.classList.contains('show')) {
                welcomeModal.classList.remove('show');
            }
        }
    });

    // [모바일] 터치 시 눌리는 효과 (Scale down)
    document.querySelectorAll('.main-btn').forEach(btn => {
        btn.addEventListener('touchstart', function() {
            this.style.transform = 'scale(0.98)';
        });

        btn.addEventListener('touchend', function() {
            this.style.transform = '';
        });
    });
}