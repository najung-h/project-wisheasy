// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    initializeRoutePage();
});

function initializeRoutePage() {
    setupStationInputs();
    updateTrainPosition();
    console.log('길찾기 페이지가 로드되었습니다.');
}

// 역 입력 시 자동완성 기능
function setupStationInputs() {
    const startInput = document.getElementById('startStation');
    const endInput = document.getElementById('endStation');

    setupAutocomplete(startInput, 'startSuggestions');
    setupAutocomplete(endInput, 'endSuggestions');
}

function setupAutocomplete(input, suggestionsId) {
    const suggestionsContainer = document.getElementById(suggestionsId);
    if (!suggestionsContainer || !input) return; 
    
    let isStationSelected = false; // 역 선택 상태를 추적하는 플래그

    // Use event delegation for suggestion clicks
    suggestionsContainer.addEventListener('mousedown', function(e) {
        if (e.target && e.target.matches('div.suggestion-item')) {
            selectStation(e.target.dataset.stationName, input.id);

            // 역 선택 시 리스트를 즉시 숨기고 선택 상태로 변경
            suggestionsContainer.style.display = 'none';
            suggestionsContainer.innerHTML = ''; 
            isStationSelected = true;
        }
    });
    
    // 사용자가 다시 타이핑을 시작하면 선택 상태 해제
    input.addEventListener('input', function() {
        isStationSelected = false;
    });

    // debounce와 fetchStations 사용
    input.addEventListener('input', debounce(async function() { // <--- 1. debounce 적용
        // 역이 선택된 상태라면 자동완성 검색을 수행하지 않음 (지연된 호출 방지)
        if (isStationSelected) return;

        const value = this.value;
        suggestionsContainer.innerHTML = ''; // 이전 제안 삭제

        if (value.length < 1) {
            suggestionsContainer.style.display = 'none';
            return;
        }

        // 2. API 호출로 stations 데이터를 가져옴 (search-util.js의 함수 사용)
        const stations = await fetchStations(value);

        // 비동기 요청 완료 후에도 사용자가 그 사이 역을 선택했다면 리스트를 열지 않음
        if (isStationSelected) {
            suggestionsContainer.style.display = 'none';
            return;
        }

        if (stations.length > 0) {
            stations.forEach(station => {
                const div = document.createElement('div');
                div.className = 'suggestion-item';
                // 3. API 응답 구조에 맞게 수정 (station.line이 있는지 확인)
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

    input.addEventListener('blur', function() {
        // Use a short delay to allow click events on suggestions to fire
        setTimeout(() => {
            suggestionsContainer.style.display = 'none';
        }, 200);
    });
}

function selectStation(stationName, inputId) {
    const input = document.getElementById(inputId);
    const suggestions = document.getElementById(inputId.replace('Station', 'Suggestions'));

    input.value = stationName;
    suggestions.style.display = 'none';
}

/* 현재 스텝(idx)에 맞춰 진행 바의 기차 아이콘 위치를 설정하는 함수 */
function updateTrainPosition() {
    const trainIcon = document.getElementById('trainIcon');
    if (!trainIcon) return;

    // HTML data 속성에서 값 가져오기 (Django 템플릿에서 렌더링된 값)
    const idx = parseInt(trainIcon.dataset.idx) || 0;     // 현재 인덱스 (0부터 시작)
    const count = parseInt(trainIcon.dataset.count) || 1; // 전체 단계 수

    // 진행률 계산 (0% ~ 100%)
    // idx가 0이면 0%, idx가 count-1이면 100%가 되도록 계산
    let percentage = 0;
    if (count > 1) {
        percentage = (idx / (count - 1)) * 100;
    }

    // 범위 제한 (0~100)
    percentage = Math.min(100, Math.max(0, percentage));

    // CSS left 속성 업데이트
    trainIcon.style.left = `${percentage}%`;
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

/**
 * 편의시설 설정 (station_info.js와 동일)
 */
const FACILITY_CONFIG = {
    'ATM': {
        icon: 'fas fa-won-sign',
        showInRoute: false
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
        showInRoute: true
    },
    '엘리베이터': {
        icon: 'fas fa-wheelchair',
        showInRoute: true,
    },
    '에스컬레이터': {
        icon: 'fas fa-walking',
        showInRoute: false,
        filterType: 'exit'
    }
};

/**
 * 편의시설 필터링 (경로 안내 페이지용)
 * - 화장실, 엘베만 포함
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

// ========================================
// 편의시설 모달 관련
// ========================================

/**
 * 편의시설 모달 표시
 * - 출발역, 도착역, 환승역(있을 경우)의 편의시설 정보를 API로 가져와서 표시
 */
async function showFacilities() {
    const modal = document.getElementById('facilitiesModal');
    
    // 1. 모달에서 역 정보 가져오기 (Django 템플릿에서 data 속성으로 전달된 값)
    const startStation = modal.dataset.startStation;
    const endStation = modal.dataset.endStation;
    const transferStationsStr = modal.dataset.transferStations || '';

    if (!startStation || !endStation) {
        alert('경로 정보를 찾을 수 없습니다.');
        return;
    }
    
    // 2. 모달 표시
    modal.classList.add('show');
    
    // 3. 경로에 포함된 역 목록 생성 (출발역, 도착역)
    const stations = [
        { name: startStation, label: '출발역' }
    ];
    
    // 환승역 추가
    if (transferStationsStr.trim()) {
        const transferStations = transferStationsStr.split(',').filter(s => s.trim());
        transferStations.forEach((station, index) => {
            stations.push({
                name: station.trim(),
                label: transferStations.length > 1 ? `환승역 ${index + 1}` : '환승역'
            });
        });
    }
    
    stations.push({ name: endStation, label: '도착역' });
    
    // 4. 역 버튼 생성
    const stationsContainer = document.getElementById('facilityStations');
    stationsContainer.innerHTML = stations.map((station, index) => `
        <button class="station-btn ${index === 0 ? 'active' : ''}"
                data-station-name="${station.name}"
                onclick="selectFacilityStation('${station.name}', '${station.label}')">
            ${station.name}역
        </button>
    `).join('');

    // 5. 첫 번째 역(출발역)의 편의시설 자동 로드
    await selectFacilityStation(startStation, '출발역');
}

/**
 * 특정 역의 편의시설 정보 로드 및 표시
 * @param {string} stationName - 역 이름
 * @param {string} stationLabel - 역 라벨 (출발역, 도착역 등)
 */
async function selectFacilityStation(stationName, stationLabel) {
    const detailsContainer = document.getElementById('facilityDetails');

    // 활성화된 버튼 업데이트
    const allButtons = document.querySelectorAll('.station-btn');
    allButtons.forEach(btn => {
        if (btn.dataset.stationName === stationName) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // 로딩 표시
    detailsContainer.innerHTML = `
        <div class="loading-message">
            <i class="fas fa-spinner fa-spin"></i>
            <p>편의시설 정보를 불러오는 중...</p>
        </div>
    `;

    try {
        // 1. 역 검색 API로 station_id와 lines 정보 가져오기
        const searchResults = await fetchStations(stationName);
        const station = searchResults.find(s => s.name === stationName);

        if (!station) {
            detailsContainer.innerHTML = `
                <div class="no-data">
                    <i class="fas fa-info-circle"></i>
                    <p>${stationName} 정보를 찾을 수 없습니다.</p>
                </div>
            `;
            return;
        }

        // 2. 호선별로 편의시설 API 호출
        const lines = station.lines || [];

        if (lines.length === 0) {
            detailsContainer.innerHTML = `
                <div class="no-data">
                    <i class="fas fa-info-circle"></i>
                    <p>호선 정보가 없습니다.</p>
                </div>
            `;
            return;
        }

        // 각 호선별로 편의시설 조회
        const lineFacilitiesData = await Promise.all(
            lines.map(async (line) => {
                const facilities = await fetchStationFacilities(station.id, line.id);
                const filteredFacilities = filterFacilitiesForRoute(facilities);
                return {
                    lineName: line.name,
                    facilities: filteredFacilities
                };
            })
        );

        // 3. 결과 표시
        const hasAnyFacilities = lineFacilitiesData.some(data => data.facilities.length > 0);

        if (!hasAnyFacilities) {
            detailsContainer.innerHTML = `
                <div class="no-data">
                    <i class="fas fa-info-circle"></i>
                    <p>편의시설 정보가 없습니다.</p>
                </div>
            `;
        } else {
            // 호선별로 편의시설 표시
            const facilitiesHTML = lineFacilitiesData.map(data => {
                if (data.facilities.length === 0) {
                    return ''; // 편의시설이 없는 호선은 표시하지 않음
                }

                return `
                    <div class="line-facilities-section">
                        <h5 class="line-subtitle">${data.lineName}</h5>
                        <div class="facility-list">
                            ${data.facilities.map(facility => `
                                <div class="facility-item">
                                    <i class="${facility.icon}"></i>
                                    <span>${facility.displayName}: ${facility.detail_loc || '위치 정보 없음'}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }).filter(html => html).join('');

            detailsContainer.innerHTML = `
                ${facilitiesHTML}
            `;
        }

    } catch (error) {
        console.error('편의시설 정보 조회 실패:', error);
        detailsContainer.innerHTML = `
            <div class="no-data">
                <i class="fas fa-exclamation-triangle"></i>
                <p>편의시설 정보를 불러오는 중 오류가 발생했습니다.</p>
            </div>
        `;
    }
}

function closeFacilitiesModal() {
    document.getElementById('facilitiesModal').classList.remove('show');
}

// '이용 불가' 버튼 -> 모달 창 띄우기
function reportClosure() {
    document.getElementById('reportClosureModal').classList.add('show');
}

// (추가) '이용 불가' 모달 닫기
function closeReportClosureModal() {
    document.getElementById('reportClosureModal').classList.remove('show');
}

// Close modals when clicking outside
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('show');
    }
});
