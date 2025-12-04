// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    initializeRoutePage();
    initializeProgressBar();
    initializeInstructionIcon();
    initializeNextButton();
    initializeErrorModal();
});

function initializeRoutePage() {
    setupStationInputs();
    updateTrainPosition();
    setupFormValidation();
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

function normalizeAndValidateExit(value) {
  const raw = (value || '').trim();
  if (!raw) {
    // 빈 값은 JS에서는 그대로 허용 (service에서 1번출구로 처리할 것)
    return { ok: true, normalized: '' };
  }

  // 공백 제거 버전 (예: "1 번 출구" → "1번출구")
  const noSpace = raw.replace(/\s+/g, '');

  // 1 → 1번출구
  if (/^\d+$/.test(noSpace)) {
    return { ok: true, normalized: `${noSpace}번출구` };
  }

  // 1번 → 1번출구
  if (/^\d+번$/.test(noSpace)) {
    return { ok: true, normalized: `${noSpace}출구` };
  }

  // 1번출구 → 그대로
  if (/^\d+번출구$/.test(noSpace)) {
    return { ok: true, normalized: noSpace };
  }

  // 그 외는 전부 막음
  return { ok: false, normalized: raw };
}

function setupFormValidation() {
  const form = document.getElementById('inputSection');
  if (!form) return;

  const startInput = document.getElementById('startStation');
  const endInput   = document.getElementById('endStation');
  const startExit  = document.getElementById('startExit');
  const endExit    = document.getElementById('endExit');
  const errorBox   = document.getElementById('formError');
  const searchBtn  = form.querySelector('.search-btn');

  function showError(msg) {
    if (errorBox) errorBox.textContent = msg;
    else alert(msg);
  }

  function clearError() {
    if (errorBox) errorBox.textContent = '';
  }

  form.addEventListener('submit', function (event) {
    clearError();

    const start = (startInput?.value || '').trim();
    const end   = (endInput?.value || '').trim();

    // 1) 역 이름 필수
    if (!start || !end) {
      event.preventDefault();
      showError('출발역/도착역은 필수입니다.');
      return;
    }

    // 2) 같은 역 금지
    if (start === end) {
      event.preventDefault();
      showError('같은 역을 입력하셨습니다. 서로 다른 역을 입력해주세요.');
      return;
    }

    // 3) 출구 형식 체크 + 정규화
    const se = normalizeAndValidateExit(startExit?.value);
    const ee = normalizeAndValidateExit(endExit?.value);

    if (!se.ok) {
      event.preventDefault();
      showError('출발 출구는 1 / 1번 / 1번출구 형식만 사용할 수 있습니다.');
      return;
    }
    if (!ee.ok) {
      event.preventDefault();
      showError('도착 출구는 1 / 1번 / 1번출구 형식만 사용할 수 있습니다.');
      return;
    }

    if (startExit) startExit.value = se.normalized;
    if (endExit)   endExit.value   = ee.normalized;

    // 로딩 UI는 선택
    if (searchBtn) {
      searchBtn.disabled = true;
      searchBtn.dataset.originalText = searchBtn.innerHTML;
      searchBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 경로 탐색 중...';
    }
  });
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
        icon: 'icon-escalator-custom',
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

// ========================================
// 프로그레스 바 마커 생성 및 열차 아이콘 이동
// ========================================
function initializeProgressBar() {
    var progressLine = document.getElementById('progressLine');
    if (!progressLine) return;

    // 역 정보 가져오기
    var startStation = progressLine.dataset.startStation;
    var startLine = progressLine.dataset.startLine;
    var endStation = progressLine.dataset.endStation;
    var endLine = progressLine.dataset.endLine;
    var transferStationsStr = progressLine.dataset.transferStations || '';
    var transferLinesStr = progressLine.dataset.transferLines || '{}';

    // 환승역 파싱
    var transferStations = transferStationsStr ? transferStationsStr.split(',').filter(s => s.trim()) : [];
    var transferLines = {};
    try {
        transferLines = JSON.parse(transferLinesStr.replace(/'/g, '"'));
    } catch (e) {
        console.error('Failed to parse transfer lines:', e);
    }

    // 전체 역 목록 구성
    var stations = [];

    // 출발역
    stations.push({
        name: startStation,
        line: startLine,
        type: 'start'
    });

    // 환승역들
    transferStations.forEach(function(station) {
        station = station.trim();
        stations.push({
            name: station,
            line: transferLines[station] || '',
            type: 'transfer'
        });
    });

    // 도착역
    stations.push({
        name: endStation,
        line: endLine,
        type: 'end'
    });

    // 호선명을 CSS 클래스로 변환
    function getLineClass(lineName) {
        if (!lineName) return 'default';
        var match = lineName.match(/(\d+)호선/);
        if (match) return 'line-' + match[1];

        var lineMap = {
            '수인분당': 'line-bundang',
            '신분당선': 'line-shinbundang',
            '경의중앙': 'line-gyeongui',
            '공항철도': 'line-airport',
            '경춘': 'line-gyeongchun',
            '우이신설': 'line-ui'
        };
        return lineMap[lineName] || 'line-default';
    }

    // 마커 생성
    var totalStations = stations.length;
    stations.forEach(function(station, index) {
        var marker = document.createElement('div');
        marker.className = 'station-marker ' + station.type + ' ' + getLineClass(station.line);

        var stationName = document.createElement('span');
        stationName.className = 'station-name';
        stationName.textContent = station.name;
        marker.appendChild(stationName);

        // 위치 설정 로직
        var position = 0;
        if (totalStations > 1) {
            position = (index / (totalStations - 1)) * 100;
        }

        marker.style.left = position + '%';

        progressLine.appendChild(marker);
    });

    // 열차 아이콘 이동
    var icon = document.getElementById('trainIcon');
    if (icon) {
        var idx = parseInt(icon.dataset.idx || '0', 10);
        var count = parseInt(icon.dataset.count || '1', 10);
        var ratio = (count > 1) ? (idx / (count - 1)) : 0;
        icon.style.left = (ratio * 100) + '%';
    }
}

// ========================================
// 안내 내용에 따른 아이콘 동적 설정
// ========================================
function initializeInstructionIcon() {
    var instructionText = document.getElementById('instructionText');
    var instructionIcon = document.getElementById('instructionIcon');

    if (!instructionText || !instructionIcon) return;

    var text = instructionText.textContent;
    var iconElement = instructionIcon.querySelector('i');
    if (!iconElement) return;

    // 기존 아이콘 클래스 제거
    iconElement.className = '';

    // 텍스트 내용에 따라 아이콘 설정
    if (text.includes('승차')) {
        iconElement.className = 'fas fa-subway';
    } else if (text.includes('에스컬레이터')) {
        iconElement.className = 'icon-escalator-custom';
    } else if (text.includes('엘리베이터')) {
        iconElement.className = 'fas fa-wheelchair';
    } else if (text.includes('계단') || text.includes('도보')) {
        iconElement.className = 'fas fa-walking';
    } else if (text.includes('감사합니다')) {
        iconElement.className = 'fas fa-check-circle';
    } else {
        iconElement.className = 'fas fa-info-circle';
    }
}

// ========================================
// 마지막 스텝: '다음' 클릭 시 모달 → 홈 이동
// ========================================
function initializeNextButton() {
    var nextBtn = document.getElementById('nextBtn');
    if (!nextBtn) return;

    nextBtn.addEventListener('click', function (ev) {
        var hasNext = this.dataset.hasNext === '1';
        if (hasNext) return;

        ev.preventDefault();
        var modal = document.getElementById('thankyouModal');
        if (modal) modal.classList.add('show');

        setTimeout(function () {
            window.location.href = nextBtn.dataset.homeUrl || '/';
        }, 1400);
    });
}

// ========================================
// 에러 모달 초기화
// ========================================
function initializeErrorModal() {
    var modal = document.getElementById('error-modal');

    // 모달이 존재하고, 내부에 에러 메시지(<p> 태그)가 실제로 있을 때만 표시
    if (modal && modal.querySelector('p')) {
        modal.classList.add('show');
    }
}
