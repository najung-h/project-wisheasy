// TODO: API 또는 전체 데이터베이스에서 가져온 실제 역 목록으로 교체해야 합니다.
// 각 역 객체에는 고유 ID, 역명, 호선 목록, 시설 정보, 실시간 도착 정보 등이 포함되어야 합니다.
// Mock data for stations with detailed information
const stations = [
    {
        name: '강남역',
        lines: ['2호선', '분당선'],
        lineInfo: [
            { line: '2호선', detail: '신정네거리 ↔ 까치산' },
            { line: '분당선', detail: '왕십리 ↔ 수원' }
        ],
        facilities: [
            { name: '에스컬레이터', location: '1,2,3,4번 출구', icon: 'fas fa-walking' },
            { name: '엘리베이터', location: '2,4번 출구', icon: 'fas fa-wheelchair' },
            { name: '화장실', location: '1,3번 출구 근처', icon: 'fas fa-restroom' }
        ],
        realtime: [
            { line: '2호선', direction: '신정네거리행', time: '2분 후 도착' },
            { line: '2호선', direction: '까치산행', time: '5분 후 도착' },
            { line: '분당선', direction: '왕십리행', time: '3분 후 도착' },
            { line: '분당선', direction: '수원행', time: '7분 후 도착' }
        ]
    },
    {
        name: '선릉역',
        lines: ['2호선', '분당선'],
        lineInfo: [
            { line: '2호선', detail: '신정네거리 ↔ 까치산' },
            { line: '분당선', detail: '왕십리 ↔ 수원' }
        ],
        facilities: [
            { name: '에스컬레이터', location: '1,2,3번 출구', icon: 'fas fa-walking' },
            { name: '엘리베이터', location: '1,3번 출구', icon: 'fas fa-wheelchair' },
            { name: '화장실', location: '2번 출구 근처', icon: 'fas fa-restroom' }
        ],
        realtime: [
            { line: '2호선', direction: '신정네거리행', time: '1분 후 도착' },
            { line: '2호선', direction: '까치산행', time: '4분 후 도착' }
        ]
    },
    {
        name: '삼성역',
        lines: ['2호선'],
        lineInfo: [
            { line: '2호선', detail: '신정네거리 ↔ 까치산' }
        ],
        facilities: [
            { name: '에스컬레이터', location: '1,2번 출구', icon: 'fas fa-walking' },
            { name: '엘리베이터', location: '1번 출구', icon: 'fas fa-wheelchair' },
            { name: '화장실', location: '2번 출구 근처', icon: 'fas fa-restroom' }
        ],
        realtime: [
            { line: '2호선', direction: '신정네거리행', time: '3분 후 도착' },
            { line: '2호선', direction: '까치산행', time: '6분 후 도착' }
        ]
    },
    {
        name: '신도림역',
        lines: ['2호선', '1호선'],
        lineInfo: [
            { line: '2호선', detail: '신정네거리 ↔ 까치산' },
            { line: '1호선', detail: '소요산 ↔ 인천' }
        ],
        facilities: [
            { name: '에스컬레이터', location: '1,2,3,4번 출구', icon: 'fas fa-walking' },
            { name: '엘리베이터', location: '2,4번 출구', icon: 'fas fa-wheelchair' },
            { name: '화장실', location: '1,3번 출구 근처', icon: 'fas fa-restroom' }
        ],
        realtime: [
            { line: '2호선', direction: '신정네거리행', time: '2분 후 도착' },
            { line: '1호선', direction: '소요산행', time: '4분 후 도착' }
        ]
    },
    {
        name: '여의도역',
        lines: ['5호선', '9호선'],
        lineInfo: [
            { line: '5호선', detail: '방화 ↔ 마천' },
            { line: '9호선', detail: '개화 ↔ 중앙보훈병원' }
        ],
        facilities: [
            { name: '에스컬레이터', location: '1,2,3번 출구', icon: 'fas fa-walking' },
            { name: '엘리베이터', location: '2번 출구', icon: 'fas fa-wheelchair' },
            { name: '화장실', location: '1,3번 출구 근처', icon: 'fas fa-restroom' }
        ],
        realtime: [
            { line: '5호선', direction: '방화행', time: '3분 후 도착' },
            { line: '9호선', direction: '개화행', time: '5분 후 도착' }
        ]
    },
    {
        name: '여의나루역',
        lines: ['5호선', '9호선'],
        lineInfo: [
            { line: '5호선', detail: '방화 ↔ 마천' },
            { line: '9호선', detail: '개화 ↔ 중앙보훈병원' }
        ],
        facilities: [
            { name: '에스컬레이터', location: '1,2번 출구', icon: 'fas fa-walking' },
            { name: '엘리베이터', location: '1번 출구', icon: 'fas fa-wheelchair' },
            { name: '화장실', location: '2번 출구 근처', icon: 'fas fa-restroom' }
        ],
        realtime: [
            { line: '5호선', direction: '방화행', time: '1분 후 도착' },
            { line: '9호선', direction: '개화행', time: '4분 후 도착' }
        ]
    },
    {
        name: '시청역',
        lines: ['1호선', '2호선'],
        lineInfo: [
            { line: '1호선', detail: '소요산 ↔ 인천' },
            { line: '2호선', detail: '신정네거리 ↔ 까치산' }
        ],
        facilities: [
            { name: '에스컬레이터', location: '1,2,3,4번 출구', icon: 'fas fa-walking' },
            { name: '엘리베이터', location: '2,4번 출구', icon: 'fas fa-wheelchair' },
            { name: '화장실', location: '1,3번 출구 근처', icon: 'fas fa-restroom' }
        ],
        realtime: [
            { line: '1호선', direction: '소요산행', time: '2분 후 도착' },
            { line: '2호선', direction: '신정네거리행', time: '3분 후 도착' }
        ]
    },
    {
        name: '종각역',
        lines: ['1호선', '3호선'],
        lineInfo: [
            { line: '1호선', detail: '소요산 ↔ 인천' },
            { line: '3호선', detail: '대화 ↔ 수서' }
        ],
        facilities: [
            { name: '에스컬레이터', location: '1,2,3번 출구', icon: 'fas fa-walking' },
            { name: '엘리베이터', location: '2번 출구', icon: 'fas fa-wheelchair' },
            { name: '화장실', location: '1,3번 출구 근처', icon: 'fas fa-restroom' }
        ],
        realtime: [
            { line: '1호선', direction: '소요산행', time: '4분 후 도착' },
            { line: '3호선', direction: '대화행', time: '2분 후 도착' }
        ]
    },
    {
        name: '홍대입구역',
        lines: ['2호선', '6호선', '경의중앙선'],
        lineInfo: [
            { line: '2호선', detail: '신정네거리 ↔ 까치산' },
            { line: '6호선', detail: '응암순환 ↔ 신내' },
            { line: '경의중앙선', detail: '문산 ↔ 용문' }
        ],
        facilities: [
            { name: '에스컬레이터', location: '1,2,3,4번 출구', icon: 'fas fa-walking' },
            { name: '엘리베이터', location: '2,4번 출구', icon: 'fas fa-wheelchair' },
            { name: '화장실', location: '1,3번 출구 근처', icon: 'fas fa-restroom' }
        ],
        realtime: [
            { line: '2호선', direction: '신정네거리행', time: '1분 후 도착' },
            { line: '6호선', direction: '응암순환행', time: '3분 후 도착' },
            { line: '경의중앙선', direction: '문산행', time: '5분 후 도착' }
        ]
    },
    {
        name: '합정역',
        lines: ['2호선', '6호선'],
        lineInfo: [
            { line: '2호선', detail: '신정네거리 ↔ 까치산' },
            { line: '6호선', detail: '응암순환 ↔ 신내' }
        ],
        facilities: [
            { name: '에스컬레이터', location: '1,2,3번 출구', icon: 'fas fa-walking' },
            { name: '엘리베이터', location: '2번 출구', icon: 'fas fa-wheelchair' },
            { name: '화장실', location: '1,3번 출구 근처', icon: 'fas fa-restroom' }
        ],
        realtime: [
            { line: '2호선', direction: '신정네거리행', time: '2분 후 도착' },
            { line: '6호선', direction: '응암순환행', time: '4분 후 도착' }
        ]
    }
];

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
    
    searchInput.addEventListener('input', function() {
        const value = this.value;
        suggestionsContainer.innerHTML = ''; // Clear previous suggestions

        if (value.length < 1) {
            suggestionsContainer.style.display = 'none';
            return;
        }
        
        const filtered = stations.filter(station => 
            hangulStartsWith(station.name, value)
        );
        
        if (filtered.length > 0) {
            filtered.forEach(station => {
                const div = document.createElement('div');
                div.className = 'suggestion-item';
                div.innerHTML = `${station.name} (${station.lines.join(', ')})`;
                div.dataset.stationName = station.name; // Store name in data attribute
                suggestionsContainer.appendChild(div);
            });
            suggestionsContainer.style.display = 'block';
        } else {
            suggestionsContainer.style.display = 'none';
        }
    });
    
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

function triggerStationSearch() {
    const stationName = document.getElementById('stationSearch').value;
    if (!stationName) {
        alert('역 이름을 입력해주세요.');
        return;
    }

    currentStation = stations.find(s => s.name === stationName);
    if (currentStation) {
        showStationInfo(currentStation);
    } else {
        showNoResults();
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
        `<span class="line-badge line-${getLineClass(line)}">${line}</span>`
    ).join('');
    
    // Update line info
    updateLineInfo(station.lineInfo);
    
    // Update facilities
    updateFacilities(station.facilities);
    
    // Update realtime info
    updateRealtimeInfo(station.realtime);
    
    // Show station info
    document.getElementById('stationInfo').style.display = 'block';
    
    // Scroll to station info
    document.getElementById('stationInfo').scrollIntoView({ 
        behavior: 'smooth' 
    });
}

function updateLineInfo(lineInfo) {
    const container = document.getElementById('lineInfo');
    container.innerHTML = lineInfo.map(line => `
        <div class="line-item">
            <span class="line-badge line-${getLineClass(line.line)}">${line.line}</span>
            <span class="line-detail">${line.detail}</span>
        </div>
    `).join('');
}

function updateFacilities(facilities) {
    const container = document.getElementById('facilityList');
    container.innerHTML = facilities.map(facility => `
        <div class="facility-item">
            <i class="${facility.icon}"></i>
            <div class="facility-detail">
                <span class="facility-name">${facility.name}</span>
                <span class="facility-location">${facility.location}</span>
            </div>
        </div>
    `).join('');
}

function updateRealtimeInfo(realtime) {
    const container = document.getElementById('realtimeInfo');
    container.innerHTML = realtime.map(train => `
        <div class="train-info">
            <span class="line-badge line-${getLineClass(train.line)}">${train.line}</span>
            <div class="train-detail">
                <span class="train-direction">${train.direction}</span>
                <span class="train-time">${train.time}</span>
            </div>
        </div>
    `).join('');
}

function showNoResults() {
    document.getElementById('stationInfo').style.display = 'none';
    document.getElementById('noResults').style.display = 'block';
}

function hideAllResults() {
    document.getElementById('stationInfo').style.display = 'none';
    document.getElementById('noResults').style.display = 'none';
}

// Tab functionality
function showTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(tabName + 'Tab').classList.add('active');
}

// Navigation
function goBack() {
    const stationInfo = document.getElementById('stationInfo');
    if (stationInfo.style.display === 'block') {
        stationInfo.style.display = 'none';
        document.querySelector('.search-section').style.display = 'block';
        document.getElementById('stationSearch').value = '';
        hideAllResults();
    } else if (window.history.length > 1) {
        window.history.back();
    } else {
        window.location.href = 'main.html';
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

// Auto-refresh realtime data (mock)
function refreshRealtimeData() {
    if (currentStation) {
        // TODO: 실제 API 호출로 교체 필요
        // 여기서는 단순히 시간을 업데이트하는 것으로 시뮬레이션
        // Simulate realtime data update
        const updatedRealtime = currentStation.realtime.map(train => ({
            ...train,
            time: `${Math.floor(Math.random() * 5) + 1}분 후 도착`
        }));
        
        updateRealtimeInfo(updatedRealtime);
    }
}

// Refresh realtime data every 30 seconds
setInterval(refreshRealtimeData, 30000);
