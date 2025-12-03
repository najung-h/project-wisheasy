// Main page functionality
document.addEventListener('DOMContentLoaded', function() {
    initializeMainPage();
});

function initializeMainPage() {
    // Add any initialization code here
    console.log('쉽길 메인페이지가 로드되었습니다.');

    // 페이지가 표시될 때마다 실행되는 이벤트 리스너
    window.addEventListener('pageshow', function(event) {
        // event.persisted가 true이면, 페이지가 bfcache에서 복원된 것입니다.
        if (event.persisted) {
            // 모든 메인 버튼을 찾습니다.
            const mainButtons = document.querySelectorAll('.main-btn');
            mainButtons.forEach(btn => {
                // 'loading' 클래스를 제거합니다.
                btn.classList.remove('loading');
                // 버튼의 비활성화 속성을 제거합니다.
                btn.disabled = false;
            });
        }
    });
}

function showLoginModal() {
    const loginModal = document.getElementById('loginModal');
    loginModal.classList.add('show');
}

function closeLoginModal() {
    const loginModal = document.getElementById('loginModal');
    loginModal.classList.remove('show');
}

function handleGoogleLogin() {
    const node = document.getElementById('googleLoginUrl');
    const url = node ? node.dataset.url : null;
    if (!url) {
        console.error('Google login URL not found');
        return;
    }
    window.location.href = url;   // ← 실제 allauth 구글 로그인으로 이동
}

// Keyboard navigation
document.addEventListener('keydown', function(e) {
    // Enter key on buttons
    if (e.key === 'Enter' && e.target.classList.contains('main-btn')) {
        e.target.click();
    }

    // Escape key to go back
    if (e.key === 'Escape') {
        goBack();
    }
});

// Touch feedback for mobile
document.querySelectorAll('.main-btn').forEach(btn => {
    btn.addEventListener('touchstart', function() {
        this.style.transform = 'scale(0.98)';
    });

    btn.addEventListener('touchend', function() {
        this.style.transform = '';
    });
});
