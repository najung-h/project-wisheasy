// Main page functionality
document.addEventListener('DOMContentLoaded', function() {
    initializeMainPage();
});

function initializeMainPage() {
    // Add any initialization code here
    console.log('쉽길 메인페이지가 로드되었습니다.');
}

// Navigation functions
function goToRoutePage() {
    const btn = event.target.closest('.route-btn');
    btn.classList.add('loading');

    // Simulate loading delay
    setTimeout(() => {
        window.location.href = 'route.html';
    }, 500);
}

function goToStationPage() {
    const btn = event.target.closest('.station-btn');
    btn.classList.add('loading');

    // Simulate loading delay
    setTimeout(() => {
        window.location.href = 'station.html';
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


function showMyPage() {
    window.location.href = 'settings.html';
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
