// ========================================
// 편의시설 설정
// ========================================

/**
 * 편의시설 타입별 아이콘 및 설정
 */
const FACILITY_CONFIG = {
    'ATM': {
        icon: 'fas fa-won-sign',
        showInRoute: false  // 경로 안내에서 제외
    },
    '물품보관함': {
        icon: 'fas fa-box',
        showInRoute: false
    },
    '유실물': {
        icon: 'fas fa-archive',
        showInRoute: false
    },
    '화장실': {
        icon: 'fas fa-restroom',
        showInRoute: true  // 경로 안내에 포함
    },
    '엘리베이터': {
        icon: 'fas fa-wheelchair',
        showInRoute: true,
        displayName: '엘베'
    },
    '에스컬레이터': {
        icon: 'fas fa-walking',
        showInRoute: false,  // 경로 안내에서 제외
        filterType: 'exit'   // 출구 정보만 표시
    }
};


// Current state
let currentStation = null;

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    initializeStationPage();
});

function initializeStationPage() {
    setupStationSearch();
    console.log('역 정보 페이지가 로드되었습니다.');
}

// Station search functionality
function setupStationSearch() {
    const searchInput = document.getElementById('stationSearch');
    const suggestionsContainer = document.getElementById('searchSuggestions');

    // Use event delegation for suggestion clicks
    suggestionsContainer.addEventListener('mousedown', function(e) {
        if (e.target && e.target.matches('div.suggestion-item')) {
            selectStation(e.target.dataset.stationName);
        }
    });
    
    // debounce와 fetchStations 사용
    searchInput.addEventListener('input', debounce(async function() { // <--- 1. debounce 적용
        const value = this.value;
        suggestionsContainer.innerHTML = ''; // 이전 제안 삭제

        if (value.length < 1) {
            suggestionsContainer.style.display = 'none';
            return;
        }

        // 2. API 호출로 stations 데이터를 가져옴 (search-util.js의 함수 사용)
        const stations = await fetchStations(value);

        if (stations.length > 0) {
            stations.forEach(station => {
                const div = document.createElement('div');
                div.className = 'suggestion-item';
                // 3. API 응답 구조에 맞게 수정
                div.innerHTML = station.line 
                                ? `${station.name} (${station.line})` 
                                : station.name;
                div.dataset.stationName = station.name;
                suggestionsContainer.appendChild(div);
            });
            suggestionsContainer.style.display = 'block';
        } else {
            suggestionsContainer.style.display = 'none';
        }
    }, 300)); // 300ms 지연
    
    searchInput.addEventListener('blur', function() {
        // Use a short delay to allow click events on suggestions to fire
        setTimeout(() => {
            suggestionsContainer.style.display = 'none';
        }, 200);
    });
}

function selectStation(stationName) {
    const searchInput = document.getElementById('stationSearch');
    const suggestions = document.getElementById('searchSuggestions');
    
    searchInput.value = stationName;
    suggestions.style.display = 'none';
}

async function triggerStationSearch() {
    const stationName = document.getElementById('stationSearch').value.trim();
    if (!stationName) {
        alert('역 이름을 입력해주세요.');
        return;
    }

    try {
        // 1. 역 검색 API로 station_id와 lines 정보 가져오기
        const searchResults = await fetchStations(stationName);
        const station = searchResults.find(s => s.name === stationName);

        if (!station) {
            showNoResults();
            return;
        }

        // 2. 편의시설 API로 편의시설 정보 가져오기
        const facilities = await fetchStationFacilities(station.id);

        // 3. 데이터 결합하여 표시
        showStationInfo({
            id: station.id,
            name: station.name,
            lines: station.lines,  // 검색 API에서 받은 호선 정보
            facilities: facilities  // 편의시설 API에서 받은 시설 정보
        });

    } catch (error) {
        console.error('역 정보 조회 실패:', error);
        alert('역 정보를 불러오는 중 오류가 발생했습니다.');
    }
}

/**
 * 역 편의시설 정보 조회
 * @param {string} stationId - 역 ID
 * @param {string} lineId - 호선 ID (선택사항)
 * @returns {Promise<Array>} - 편의시설 목록
 */
async function fetchStationFacilities(stationId, lineId = null) {
    try {
        let url = `/api/stations/${encodeURIComponent(stationId)}/facilities/`;
        if (lineId) {
            url += `?line_id=${encodeURIComponent(lineId)}`;
        }

        const response = await fetch(url);
        if (!response.ok) {
            console.error('Facilities API failed:', response.status);
            return [];
        }

        const data = await response.json();
        return Array.isArray(data) ? data : [];
    } catch (error) {
        console.error('Error fetching facilities:', error);
        return [];
    }
}

function showStationInfo(station) {
    // Hide search section and no results
    document.querySelector('.search-section').style.display = 'none';
    document.getElementById('noResults').style.display = 'none';
    
    // Update station header
    document.getElementById('stationName').textContent = station.name;
    
    // Update line badges
    const lineContainer = document.getElementById('stationLines');
    lineContainer.innerHTML = station.lines.map(line =>
        `<span class="line-badge line-${getLineClass(line.name)}">${line.name}</span>`
    ).join('');

    // Update facilities
    updateFacilities(station.facilities);

    // Show station info
    document.getElementById('stationInfo').style.display = 'block';
    
    // Scroll to station info
    document.getElementById('stationInfo').scrollIntoView({ 
        behavior: 'smooth' 
    });
}

function updateFacilities(facilities) {
    const container = document.getElementById('facilityList');

    // 역 정보 페이지용 필터링 적용
    const filteredFacilities = filterFacilitiesForStationInfo(facilities);

    if (filteredFacilities.length === 0) {
        container.innerHTML = '<p class="no-data">편의시설 정보가 없습니다.</p>';
        return;
    }

    container.innerHTML = filteredFacilities.map(facility => `
        <div class="facility-item">
            <i class="${facility.icon}"></i>
            <div class="facility-detail">
                <span class="facility-name">${facility.displayName}</span>
                <span class="facility-location">${facility.detail_loc || '위치 정보 없음'}</span>
            </div>
        </div>
    `).join('');
}

// ========================================
// 편의시설 필터링
// ========================================

/**
 * 편의시설 필터링 (역 정보 페이지용)
 * - 에스컬레이터: 출구 정보만 포함
 * - 나머지: 전부 표시
 */
function filterFacilitiesForStationInfo(facilities) {
    return facilities.map(facility => {
        const config = FACILITY_CONFIG[facility.facility_name] || {
            icon: 'fas fa-info-circle',
            showInRoute: false
        };

        // 에스컬레이터인 경우 "출구"가 포함된 것만 표시
        if (facility.facility_name === '에스컬레이터') {
            if (!facility.detail_loc || !facility.detail_loc.includes('출구')) {
                return null;  // 필터링 제외
            }
        }

        return {
            ...facility,
            icon: config.icon,
            displayName: config.displayName || facility.facility_name
        };
    }).filter(f => f !== null);  // null 제거
}

/**
 * 편의시설 필터링 (경로 안내 페이지용)
 * - 화장실, 엘베만 포함
 * - 에스컬레이터 제외
 */
function filterFacilitiesForRoute(facilities) {
    return facilities.filter(facility => {
        const config = FACILITY_CONFIG[facility.facility_name];
        return config && config.showInRoute === true;
    }).map(facility => ({
        ...facility,
        icon: FACILITY_CONFIG[facility.facility_name].icon,
        displayName: FACILITY_CONFIG[facility.facility_name].displayName || facility.facility_name
    }));
}

function showNoResults() {
    document.getElementById('stationInfo').style.display = 'none';
    document.getElementById('noResults').style.display = 'block';
}

function hideAllResults() {
    document.getElementById('stationInfo').style.display = 'none';
    document.getElementById('noResults').style.display = 'none';
}

// Navigation
const appContainer = document.getElementById('wisheasy-app');

function goBack() {
    const stationInfo = document.getElementById('stationInfo');
    // 역 정보 상세가 화면에 표시된 상태라면, 역 정보 상세를 숨기고 다시 검색 화면으로 이동
    if (stationInfo.style.display === 'block') {
        stationInfo.style.display = 'none';
        document.querySelector('.search-section').style.display = 'block';
        document.getElementById('stationSearch').value = '';
        hideAllResults();
    } 
    // 검색 화면 상태이고 뒤로 갈 방문 기록이 있다면, 이전 페이지로 이동
    else if (window.history.length > 1 && document.referrer) {
        window.history.back();
    } 
    // 검색 화면 상태인데 뒤로 갈 방문 기록이 없다면, 메인 페이지로 이동
    else {
        const mainPageUrl = appContainer.dataset.mainPageUrl;
        window.location.href = mainPageUrl;
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Escape key to go back
    if (e.key === 'Escape') {
        goBack();
    }
    
    // Enter key on search input
    if (e.key === 'Enter' && e.target.id === 'stationSearch') {
        const value = e.target.value;
        if (value) {
            const station = stations.find(s => s.name === value);
            if (station) {
                selectStation(station.name);
            } else {
                showNoResults();
            }
        }
    }
});
