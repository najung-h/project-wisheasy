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
    // This is a dummy URL for demonstration purposes.
    // In a real application, you would use a proper OAuth2 client ID and redirect URI.
    const oauthURL = 'https://accounts.google.com/o/oauth2/v2/auth?' +
        'client_id=YOUR_CLIENT_ID.apps.googleusercontent.com&' +
        'redirect_uri=YOUR_REDIRECT_URI&' +
        'response_type=code&' +
        'scope=openid%20email%20profile';

    alert('구글 OAuth 동의 페이지로 이동합니다. (프로토타입)');
    // In a real app, you would use:
    // window.location.href = oauthURL;
    console.log('Redirecting to:', oauthURL);
    closeLoginModal();
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
