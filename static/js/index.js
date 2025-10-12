// Main page functionality
document.addEventListener('DOMContentLoaded', function() {
    initializeMainPage();
});

function initializeMainPage() {
    // Add any initialization code here
    console.log('쉽길 메인페이지가 로드되었습니다.');
}

// Navigation functions
const appContainer = document.getElementById('wisheasy-app');

function goToRoutePage() {
    // event.target에서부터 가장 가까운 조상 중에 .route-btn 이라는 클래스를 가진 요소를 찾는다.
    // 찾아낸 버튼에 loading이라는 CSS 클래스를 추가한다. (로딩 중인 ... 표시)
    const btn = event.target.closest('.route-btn');
    btn.classList.add('loading');

    // 0.5초(500ms)간 기다렸다가 코드를 실행한다.
    // 사용자가 "아, 내 클릭이 잘 인식되었구나"라고 인지할 시간을 벌어주는 UX 장치
    setTimeout(() => {
        const routePageUrl = appContainer.dataset.routePageUrl;
        window.location.href = routePageUrl;
    }, 500);
}

function goToStationPage() {
    // event.target에서부터 가장 가까운 조상 중에 .route-btn 이라는 클래스를 가진 요소를 찾는다.
    // 찾아낸 버튼에 loading이라는 CSS 클래스를 추가한다. (로딩 중인 ... 표시)
    const btn = event.target.closest('.station-btn');
    btn.classList.add('loading');

    // 0.5초(500ms)간 기다렸다가 코드를 실행한다.
    // 사용자가 "아, 내 클릭이 잘 인식되었구나"라고 인지할 시간을 벌어주는 UX 장치
    setTimeout(() => {
        const stationPageUrl = appContainer.dataset.stationPageUrl;
        window.location.href = stationPageUrl;
    }, 500);
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

// a 태그로 대체함
// function showMyPage() {
//     window.location.href = 'settings.html';
// }

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
